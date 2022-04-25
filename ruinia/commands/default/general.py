"""
General Character commands usually available to all characters
"""
from ast import alias
import re
from django.conf import settings
from evennia.utils import utils, evtable
from evennia.typeclasses.attributes import NickTemplateInvalid

COMMAND_DEFAULT_CLASS = utils.class_from_module(settings.COMMAND_DEFAULT_CLASS)


class CmdHome(COMMAND_DEFAULT_CLASS):
    """
    перенести персонажа в домашнюю локацию

    использование:
        домой

    Телепортирует вас в домашнюю локацию.
    """

    key = "домой"
    locks = "cmd:perm(home) or perm(Builder)"
    arg_regex = r"$"
    help_category = "Общее"

    def func(self):
        """Implement the command"""
        caller = self.caller
        home = caller.home
        if not home:
            caller.msg("У вас нет дома!")
        elif home == caller.location:
            caller.msg("Вы уже находитесь дома!")
        else:
            caller.msg("Нет места лучше, чем дом...")
            caller.move_to(home)


class CmdLook(COMMAND_DEFAULT_CLASS):
    """
    посмотреть на локацию или объект

    Использование:
      смотреть
      смотреть <объект>
      смотреть *<аккаунт>

    Наблюдайте за вашим окружением или за объектами поблизости.
    """

    key = "смотреть"
    aliases = ["осмотреть", "см", "смот"]
    locks = "cmd:all()"
    arg_regex = r"\s|$"
    help_category = "Общее"

    def func(self):
        """
        Обработка команды "смотреть".
        """
        caller = self.caller
        if not self.args:
            target = caller.location
            if not target:
                caller.msg("Вам не на что смотреть!")
                return
        else:
            target = caller.search(self.args)
            if not target:
                return
        self.msg((caller.at_look(target), {"type": "look"}), options=None)


class CmdNick(COMMAND_DEFAULT_CLASS):
    """
    задать личный псевдоним/ник, укажите строку для
    переопределения и замените её другой прямо на ходу

    Использование:
      ник[/переключатель] <текст> [= [новый текст]]
      ник[/переключатель] <шаблон> = <новый шаблон>
      ник/удалить <текст> или число
      ники

    Переключатели:
      строка    - заменить входящую строку (по-умолчанию)
      объект    - заменить найденный объект
      аккаунт   - заменить найденный аккаунт
      список    - показать все объявленные псевдонимы/ники (работает точно так же, как и "ники")
      удалить   - удалить псевдоним/ник из списка по индексу
      очистить  - очистить все псевдонимы/ники

    Примеры:
      ник привет = Привет, я Kazbich!
      ник/объект том = высокий мужчина
      ник строить $1 $2 = create/drop $1;$2 FIXME: вставить на это место переведенную команду (create/drop)
      ник говорить $1 $2=page $1=$2 FIXME: вставить на это место переведенную команду page
      ник tm?$1=page tallman=$1 FIXME: вставить на это место переведенную команду page
      ник tm\=$1=page tallman=$1 FIXME: вставить на это место переведенную команду page

    "ник" - это инструмент, для создания псевдонимов. Используйте $1, $2, ... для того, чтобы перехватить параметры
    Поместите последний $-маркер без пробела в конце, чтобы перехватить весь оставшийся текст. 
    Ты также можешь использовать сопоставление unix-glob для левой части <текст>:

        * - совпадает все
        ? - совпадает 0 или 1 символ
        [абвг] - совпадают указанные символы в любом порядке
        [!абвг] - совпадает все, но не эти символы
        \= - экранированный символ '=' в <текст>

    Обрати внимание, что никакие объекты на самом деле не изменяются этой командой. Твои псевдонимы
    доступны только для тебя. Если ты хочешь перманентно переименовать или добавить псевдоним к объекту
    или к чему-нибудь еще, тебе понадобиться статус (привелегия) "Строитель".

    """

    key = "ник"
    switch_options = ("строка", "объект", "аккаунт",
                      "список", "удалить", "очистить")
    aliases = ["псевдоним", "ники"]
    locks = "cmd:all()"
    help_category = "Общее"

    def parse(self):
        """
        Поддержка экранирование = в виде \=
        """
        super(CmdNick, self).parse()
        args = (self.lhs or "") + (" = %s" % self.rhs if self.rhs else "")
        parts = re.split(r"(?<!\\)=", args, 1)
        self.rhs = None
        if len(parts) < 2:
            self.lhs = parts[0].strip()
        else:
            self.lhs, self.rhs = [part.strip() for part in parts]
        self.lhs = self.lhs.replace("\=", "=")

    def func(self):
        """Создание псевдонима/ника"""

        def _cy(string):
            "добавить цвет для специальных маркеров"
            return re.sub(r"(\$[0-9]+|\*|\?|\[.+?\])", r"|Y\1|n", string)

        caller = self.caller
        switches = self.switches
        nicktypes = [switch for switch in switches if switch in (
            "объект", "аккаунт", "строка")]
        specified_nicktype = bool(nicktypes)
        nicktypes = nicktypes if specified_nicktype else ["строка"]

        nicklist = (
            utils.make_iter(caller.nicks.get(
                category="строка", return_obj=True) or [])
            + utils.make_iter(caller.nicks.get(category="объект",
                              return_obj=True) or [])
            + utils.make_iter(caller.nicks.get(category="аккаунт",
                              return_obj=True) or [])
        )

        if "list" in switches or self.cmdstring in ("ники",):

            if not nicklist:
                string = "|wНиков не обнаружено.|n"
            else:
                table = self.styled_table(
                    "#", "Тип", "Псевдонимы/ники", "Замена")
                for inum, nickobj in enumerate(nicklist):
                    _, _, nickvalue, replacement = nickobj.value
                    table.add_row(
                        str(inum + 1), nickobj.db_category, _cy(nickvalue), _cy(replacement)
                    )
                string = "|wОбъявленные ники:|n\n%s" % table
            caller.msg(string)
            return

        if "очистить" in switches:
            caller.nicks.clear()
            caller.account.nicks.clear()
            caller.msg("Очищены все ники.")
            return

        if "удалить" in switches or "удал" in switches:
            if not self.args or not self.lhs:
                caller.msg(
                    "использование ник/удалить <ник> или <#число> ('ники' для списка ников)")
                return
            # see if a number was given
            arg = self.args.lstrip("#")
            oldnicks = []
            if arg.isdigit():
                # we are given a index in nicklist
                delindex = int(arg)
                if 0 < delindex <= len(nicklist):
                    oldnicks.append(nicklist[delindex - 1])
                else:
                    caller.msg(
                        "Некорректный индекс псевдонима. Попробуйте 'ники' для получения списка ников.")
                    return
            else:
                if not specified_nicktype:
                    nicktypes = ("объект", "аккаунт", "строка")
                for nicktype in nicktypes:
                    oldnicks.append(caller.nicks.get(
                        arg, category=nicktype, return_obj=True))

            oldnicks = [oldnick for oldnick in oldnicks if oldnick]
            if oldnicks:
                for oldnick in oldnicks:
                    nicktype = oldnick.category
                    nicktypestr = "%s-ник" % nicktype.capitalize()
                    _, _, old_nickstring, old_replstring = oldnick.value
                    caller.nicks.remove(old_nickstring, category=nicktype)
                    caller.msg(
                        "%s удален: '|w%s|n' -> |w%s|n."
                        % (nicktypestr, old_nickstring, old_replstring)
                    )
            else:
                caller.msg("Подходящих псевдонимов для удаления не найдено.")
            return

        if not self.rhs and self.lhs:
            # check what a nick is set to
            strings = []
            if not specified_nicktype:
                nicktypes = ("объект", "аккаунт", "строка")
            for nicktype in nicktypes:
                nicks = [
                    nick
                    for nick in utils.make_iter(
                        caller.nicks.get(category=nicktype, return_obj=True)
                    )
                    if nick
                ]
                for nick in nicks:
                    _, _, nick, repl = nick.value
                    if nick.startswith(self.lhs):
                        strings.append(
                            "{}-ник: '{}' -> '{}'".format(
                                nicktype.capitalize(), nick, repl)
                        )
            if strings:
                caller.msg("\n".join(strings))
            else:
                caller.msg(
                    "Не найдено подходящих псевдонимов '{}'".format(self.lhs))
            return

        if not self.rhs and self.lhs:
            # check what a nick is set to
            strings = []
            if not specified_nicktype:
                nicktypes = ("объект", "аккаунт", "строка")
            for nicktype in nicktypes:
                if nicktype == "аккаунт":
                    obj = account
                else:
                    obj = caller
                nicks = utils.make_iter(obj.nicks.get(
                    category=nicktype, return_obj=True))
                for nick in nicks:
                    _, _, nick, repl = nick.value
                    if nick.startswith(self.lhs):
                        strings.append(
                            "{}-ник: '{}' -> '{}'".format(
                                nicktype.capitalize(), nick, repl)
                        )
            if strings:
                caller.msg("\n".join(strings))
            else:
                caller.msg(
                    "Не найдено подходящих псевдонимов '{}'".format(self.lhs))
            return

        if not self.rhs and self.lhs:
            # check what a nick is set to
            strings = []
            if not specified_nicktype:
                nicktypes = ("объект", "аккаунт", "строка")
            for nicktype in nicktypes:
                if nicktype == "аккаунт":
                    obj = account
                else:
                    obj = caller
                nicks = utils.make_iter(obj.nicks.get(
                    category=nicktype, return_obj=True))
                for nick in nicks:
                    _, _, nick, repl = nick.value
                    if nick.startswith(self.lhs):
                        strings.append(
                            "{}-ник: '{}' -> '{}'".format(
                                nicktype.capitalize(), nick, repl)
                        )
            if strings:
                caller.msg("\n".join(strings))
            else:
                caller.msg(
                    "Не найдено подходящих псевдонимов '{}'".format(self.lhs))
            return

        if not self.args or not self.lhs:
            caller.msg(
                "Использование: ник[/переключатель] строка = [новый псевдоним]")
            return

        # setting new nicks

        nickstring = self.lhs
        replstring = self.rhs

        if replstring == nickstring:
            caller.msg(
                "Нет смысла устанавливать ник таким же, как строка для замены...")
            return

        # check so we have a suitable nick type
        errstring = ""
        string = ""
        for nicktype in nicktypes:
            nicktypestr = "%s-ник" % nicktype.capitalize()
            old_nickstring = None
            old_replstring = None

            oldnick = caller.nicks.get(
                key=nickstring, category=nicktype, return_obj=True)
            if oldnick:
                _, _, old_nickstring, old_replstring = oldnick.value
            if replstring:
                # creating new nick
                errstring = ""
                if oldnick:
                    if replstring == old_replstring:
                        string += "\nИдентичный %s уже установлен." % nicktypestr.lower()
                    else:
                        string += "\n%s '|w%s|n' обновлено на '|w%s|n'." % (
                            nicktypestr,
                            old_nickstring,
                            replstring,
                        )
                else:
                    string += "\n%s '|w%s|n' обновлено на '|w%s|n'." % (
                        nicktypestr,
                        nickstring,
                        replstring,
                    )
                try:
                    caller.nicks.add(nickstring, replstring, category=nicktype)
                except NickTemplateInvalid:
                    caller.msg(
                        "Вы должны использовать одни и те же $-маркеры как в нике, так и в замене."
                    )
                    return
            elif old_nickstring and old_replstring:
                # just looking at the nick
                string += "\n%s '|w%s|n' обновлено на '|w%s|n'." % (
                    nicktypestr,
                    old_nickstring,
                    old_replstring,
                )
                errstring = ""
        string = errstring if errstring else string
        caller.msg(_cy(string))


class CmdInventory(COMMAND_DEFAULT_CLASS):
    """
    показать инвентарь

    Использование:
      инвентарь
      инв

    Показывает ваш инвентарь.
    """

    key = "инвентарь"
    aliases = ["инв", "карманы"]
    locks = "cmd:all()"
    arg_regex = r"$"
    help_category = "Общее"

    def func(self):
        """проверить инвентарь"""
        items = self.caller.contents
        if not items:
            string = "У вас ничего нет."
        else:
            from evennia.utils.ansi import raw as raw_ansi

            # FIXME: проверить, что это
            table = self.styled_table(border="header")
            for item in items:
                table.add_row(
                    f"|C{item.name}|n",
                    "{}|n".format(utils.crop(
                        raw_ansi(item.db.desc), width=50) or ""),
                )
            string = f"|wУ вас в инвентаре:\n{table}"
        self.caller.msg(string)


class CmdGet(COMMAND_DEFAULT_CLASS):
    """
    взять что-нибудь

    Использование:
      взять <объект>

    Взять предмет, который находится в локации и положить его в инвентарь
    """

    key = "взять"
    aliases = "поднять"
    locks = "cmd:all()"
    arg_regex = r"\s|$"
    help_category = "Общее"

    def func(self):
        """implements the command."""

        caller = self.caller

        if not self.args:
            caller.msg("Взять что?")
            return
        obj = caller.search(self.args, location=caller.location)
        if not obj:
            return
        if caller == obj:
            caller.msg("Вы не можете поднять самого себя.")
            return
        if not obj.access(caller, "get"):
            if obj.db.get_err_msg:
                caller.msg(obj.db.get_err_msg)
            else:
                caller.msg("Вы не можете взять это.")
            return

        # calling at_before_get hook method
        if not obj.at_before_get(caller):
            return

        success = obj.move_to(caller, quiet=True)
        if not success:
            caller.msg("Это не может быть поднято.")
        else:
            caller.msg("Вы подобрали %s." % obj.name)
            caller.location.msg_contents(
                "%s подобрал %s." % (caller.name, obj.name), exclude=caller
            )
            # calling at_get hook method
            obj.at_get(caller)


class CmdDrop(COMMAND_DEFAULT_CLASS):
    """
    выбросить что-нибудь 

    Использование:
      выбросить <объект>

    Позволяет вам выбросить объект из инвентаря в локацию, 
    на которой сейчас находитесь.
    """

    key = "выбросить"
    aliases = ["выкинуть", "выкин", "выброс", "скинуть"]
    locks = "cmd:all()"
    arg_regex = r"\s|$"
    help_category = "Общее"

    def func(self):
        """Implement command"""

        caller = self.caller
        if not self.args:
            caller.msg("Выбросить что?")
            return

        # Because the DROP command by definition looks for items
        # in inventory, call the search function using location = caller
        obj = caller.search(
            self.args,
            location=caller,
            nofound_string="У вас нет %s." % self.args,
            multimatch_string="У вас больше одного %s:" % self.args,
        )
        if not obj:
            return

        # Call the object script's at_before_drop() method.
        if not obj.at_before_drop(caller):
            return

        success = obj.move_to(caller.location, quiet=True)
        if not success:
            caller.msg("Это нельзя выбросить.")
        else:
            caller.msg("Вы выбрасываете %s." % (obj.name,))
            caller.location.msg_contents("%s выкидывает %s." % (
                caller.name, obj.name), exclude=caller)
            # Call the object script's at_drop() method.
            obj.at_drop(caller)


class CmdGive(COMMAND_DEFAULT_CLASS):
    """
    дать что-то кому-то

    Использование:
      дать <объект в инвентаре> < = || => > <target>

    Передает предмет из вашего инвентаря в инвентарь другому персонажу.
    """

    key = "дать"
    aliases = ["отдать", "передать"]
    # Предпочитается " = " , но также допускается " => ".
    rhs_split = ("=", " > ")
    locks = "cmd:all()"
    arg_regex = r"\s|$"
    help_category = "Общее"

    def func(self):
        """Implement give"""

        caller = self.caller
        if not self.args or not self.rhs:
            caller.msg("Использование: дать <объект из инвентаря> = <цель>")
            return
        to_give = caller.search(
            self.lhs,
            location=caller,
            nofound_string="У вас нет %s." % self.lhs,
            multimatch_string="У вас больше одного %s:" % self.lhs,
        )
        target = caller.search(self.rhs)
        if not (to_give and target):
            return
        if target == caller:
            caller.msg(" %s Уже у вас." % to_give.key)
            return
        if not to_give.location == caller:
            caller.msg("У вас нет %s." % to_give.key)
            return

        # calling at_before_give hook method
        if not to_give.at_before_give(caller, target):
            return

        # give object
        success = to_give.move_to(target, quiet=True)
        if not success:
            caller.msg("Это нельзя передать.")
        else:
            caller.msg("Вы передали %s %s." % (to_give.key, target.key))
            target.msg("%s передал вам %s." % (caller.key, to_give.key))
            # Call the object script's at_give() method.
            to_give.at_give(caller, target)


class CmdSetDesc(COMMAND_DEFAULT_CLASS):
    """
    опишите себя

    Использование:
      описатьсебя <описание>

    Добавьте себе описание. Оно
    будет видно людям, когда они
    будут смотреть на вас
    """

    key = "описатьсебя"
    locks = "cmd:all()"
    arg_regex = r"\s|$"
    help_category = "Общее"

    def func(self):
        """add the description"""

        if not self.args:
            self.caller.msg("Вы должны добавить описание.")
            return

        self.caller.db.desc = self.args.strip()
        self.caller.msg("Вы описали себя.")


class CmdSay(COMMAND_DEFAULT_CLASS):
    """
    сказать от лица персонажа

    Использование:
      сказать <сообщение>

    Сказать что-нибудь всем персонажам в локации.
    """

    key = "сказать"
    aliases = ['"', "'", "говорить", "сказ", "гов"]
    locks = "cmd:all()"
    help_category = "Общее"

    def func(self):
        """Run the say command"""

        caller = self.caller

        if not self.args:
            caller.msg("Сказать что?")
            return

        speech = self.args

        # Calling the at_before_say hook on the character
        # FIXME: убрать says при вводе этой команды
        speech = caller.at_before_say(speech)

        # If speech is empty, stop here
        if not speech:
            return

        # Call the at_after_say hook on the character
        caller.at_say(speech, msg_self=True)


class CmdWhisper(COMMAND_DEFAULT_CLASS):
    """
    Сказать что-то другому персонажу

    Использование:
      прошептать <персонаж> = <сообщение>
      прошептать <персонаж_1>, <персонаж_2> = <сообщение>

    Сказать что-то одному или нескольким персонажам в текущей локации.
    Остальные персонажи в локации не увидят вашего сообщения.
    """

    key = "прошептать"
    aliases = ["шептать", "шёпот", "шепт"]
    locks = "cmd:all()"
    help_category = "Общее"

    def func(self):
        """Run the whisper command"""

        caller = self.caller

        if not self.lhs or not self.rhs:
            caller.msg("Использование: прошептать <персонаж> = <сообщение>")
            return

        receivers = [recv.strip() for recv in self.lhs.split(",")]

        receivers = [caller.search(receiver) for receiver in set(receivers)]
        receivers = [recv for recv in receivers if recv]

        speech = self.rhs
        # If the speech is empty, abort the command
        if not speech or not receivers:
            return

        # Call a hook to change the speech before whispering
        speech = caller.at_before_say(
            speech, whisper=True, receivers=receivers)

        # no need for self-message if we are whispering to ourselves (for some reason)
        msg_self = None if caller in receivers else True
        caller.at_say(speech, msg_self=msg_self,
                      receivers=receivers, whisper=True)


class CmdPose(COMMAND_DEFAULT_CLASS):
    """
    принять позу

    Использование:
      поза <описание позы>

    Пример:
      поза встал и улыбнулся.
       -> остальные увидят:
      Том встал и улыбнулся.

    Описывает действие, которое производит персонаж.
    Описание позы автоматически начинается с имени вашего персонажа.
    """

    key = "поза"
    aliases = [":", "эмоция"]
    locks = "cmd:all()"
    help_category = "Общее"

    def parse(self):
        """
        Custom parse the cases where the emote
        starts with some special letter, such
        as 's, at which we don't want to separate
        the caller's name and the emote with a
        space.
        """
        args = self.args
        if args and not args[0] in ["'", ",", ":"]:
            args = " %s" % args.strip()
        self.args = args

    def func(self):
        """Hook function"""
        if not self.args:
            msg = "Какую позу принять?"
            self.caller.msg(msg)
        else:
            msg = "%s%s" % (self.caller.name, self.args)
            self.caller.location.msg_contents(
                text=(msg, {"type": "pose"}), from_obj=self.caller)


class CmdAccess(COMMAND_DEFAULT_CLASS):
    """
    показывает ваш текущий уровень доступа

    Использование:
      доступ

    Эта команда показывает вам иерархию уровней доступа и
    членами каких групп доступа вы являетесь.
    """

    key = "доступ"
    aliases = ["группы", "иерархия"]
    locks = "cmd:all()"
    arg_regex = r"$"
    help_category = "Общее"

    def func(self):
        """Load the permission groups"""

        caller = self.caller
        hierarchy_full = settings.PERMISSION_HIERARCHY
        string = "\n|wИерархия уровней доступа|n (по возрастанию):\n %s" % ", ".join(
            hierarchy_full)

        if self.caller.account.is_superuser:
            cperms = "<Superuser>"
            pperms = "<Superuser>"
        else:
            cperms = ", ".join(caller.permissions.all())
            pperms = ", ".join(caller.account.permissions.all())

        string += "\n|wВаш уровень доступа|n:"
        string += "\nПерсонаж |c%s|n: %s" % (caller.key, cperms)
        if hasattr(caller, "account"):
            string += "\nАккаунт |c%s|n: %s" % (caller.account.key, pperms)
        caller.msg(string)
