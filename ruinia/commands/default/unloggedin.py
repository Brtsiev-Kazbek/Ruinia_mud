"""
Commands that are available from the connect screen.
"""
import re
import datetime
from codecs import lookup as codecs_lookup
from django.conf import settings
from evennia.comms.models import ChannelDB
from evennia.server.sessionhandler import SESSIONS

from evennia.utils import class_from_module, create, logger, utils, gametime
from evennia.commands.cmdhandler import CMD_LOGINSTART

COMMAND_DEFAULT_CLASS = utils.class_from_module(settings.COMMAND_DEFAULT_CLASS)

# limit symbol import for API
__all__ = (
    "CmdUnconnectedConnect",
    "CmdUnconnectedCreate",
    "CmdUnconnectedQuit",
    "CmdUnconnectedLook",
    "CmdUnconnectedHelp",
    "CmdUnconnectedEncoding",
    "CmdUnconnectedInfo",
    "CmdUnconnectedScreenreader"
)

MULTISESSION_MODE = settings.MULTISESSION_MODE
CONNECTION_SCREEN_MODULE = settings.CONNECTION_SCREEN_MODULE


def create_guest_account(session):
    """
    Creates a guest account/character for this session, if one is available.

    Args:
        session (Session): the session which will use the guest account/character.

    Returns:
        GUEST_ENABLED (boolean), account (Account):
            the boolean is whether guest accounts are enabled at all.
            the Account which was created from an available guest name.
    """
    enabled = settings.GUEST_ENABLED
    address = session.address

    # Get account class
    Guest = class_from_module(settings.BASE_GUEST_TYPECLASS)

    # Get an available guest account
    # authenticate() handles its own throttling
    account, errors = Guest.authenticate(ip=address)
    if account:
        return enabled, account
    else:
        session.msg("|R%s|n" % "\n".join(errors))
        return enabled, None


def create_normal_account(session, name, password):
    """
    Creates an account with the given name and password.

    Args:
        session (Session): the session which is requesting to create an account.
        name (str): the name that the account wants to use for login.
        password (str): the password desired by this account, for login.

    Returns:
        account (Account): the account which was created from the name and password.
    """
    # Get account class
    Account = class_from_module(settings.BASE_ACCOUNT_TYPECLASS)

    address = session.address

    # Match account name and check password
    # authenticate() handles all its own throttling
    account, errors = Account.authenticate(
        username=name, password=password, ip=address, session=session
    )
    if not account:
        # No accountname or password match
        session.msg("|R%s|n" % "\n".join(errors))
        return None

    return account


class CmdUnconnectedConnect(COMMAND_DEFAULT_CLASS):
    """
    войти

    Использование (на экране входа):
      войти <имя_аккаунта> <пароль>
      войти "имя аккаунта" "пароь"

    Используйте команду `создать`, для того, чтобы сначала создать учетную запись перед входом в систему.

    Если в имени есть пробелы, заключите его в двойные кавычки.
    """

    key = "войти"
    aliases = ["подключиться", "подкл"]
    locks = "cmd:all()"  # not really needed
    arg_regex = r"\s.*?|$"
    help_category = "Общее"

    def func(self):
        """
        Uses the Django admin api. Note that unlogged-in commands
        have a unique position in that their func() receives
        a session object instead of a source_object like all
        other types of logged-in commands (this is because
        there is no object yet before the account has logged in)
        """
        session = self.caller
        address = session.address

        args = self.args
        # extract double quote parts
        parts = [part.strip()
                 for part in re.split(r"\"", args) if part.strip()]
        if len(parts) == 1:
            # this was (hopefully) due to no double quotes being found, or a guest login
            parts = parts[0].split(None, 1)

            # Guest login
            if len(parts) == 1 and parts[0].lower() == "guest":
                # Get Guest typeclass
                Guest = class_from_module(settings.BASE_GUEST_TYPECLASS)

                account, errors = Guest.authenticate(ip=address)
                if account:
                    session.sessionhandler.login(session, account)
                    return
                else:
                    session.msg("|R%s|n" % "\n".join(errors))
                    return

        if len(parts) != 2:
            session.msg("\n\r Использование (без <>): войти <имя> <пароль>")
            return

        # Get account class
        Account = class_from_module(settings.BASE_ACCOUNT_TYPECLASS)

        name, password = parts
        account, errors = Account.authenticate(
            username=name, password=password, ip=address, session=session
        )
        if account:
            session.sessionhandler.login(session, account)
        else:
            session.msg("|R%s|n" % "\n".join(errors))


class CmdUnconnectedCreate(COMMAND_DEFAULT_CLASS):
    """
    создать новый аккаунт

    Использование (на экране входа):
      создать <имя_аккаунта> <пароль>
      создать "имя аккаунта" "пароль"

    Команда создает новый аккаунт.

    Если в имени есть пробелы, заключите его в двойные кавычки.
    """

    key = "создать"
    aliases = ["созд"]
    locks = "cmd:all()"
    arg_regex = r"\s.*?|$"
    help_category = "Общее"

    def func(self):
        """Do checks and create account"""

        session = self.caller
        args = self.args.strip()

        address = session.address

        # Get account class
        Account = class_from_module(settings.BASE_ACCOUNT_TYPECLASS)

        # extract double quoted parts
        parts = [part.strip()
                 for part in re.split(r"\"", args) if part.strip()]
        if len(parts) == 1:
            # this was (hopefully) due to no quotes being found
            parts = parts[0].split(None, 1)
        if len(parts) != 2:
            string = (
                "\n Использование (без <>): создать <имя> <пароль>"
                "\nЕсли <имя> или <пароль> содержит пробелы, заключите имя, либо пароль в двойные кавычки."
            )
            session.msg(string)
            return

        username, password = parts

        # everything's ok. Create the new account account.
        account, errors = Account.create(
            username=username, password=password, ip=address, session=session
        )
        if account:
            # tell the caller everything went well.
            string = "Аккаунт '%s' был успешно создан. Добро пожаловать!"
            if " " in username:
                string += (
                    "\n\nТеперь вы можете войти с помощью команды 'войти \"%s\" <пароль>'."
                )
            else:
                string += "\n\nТеперь вы можете войти с помощью команды 'войти \"%s\" <пароль>'."
            session.msg(string % (username, username))
        else:
            session.msg("|R%s|n" % "\n".join(errors))


class CmdUnconnectedQuit(COMMAND_DEFAULT_CLASS):
    """
    выйти, если вы еще не вошли в систему

    использование:
      выйти

    Мы поддерживаем другую версию команды quit
    здесь для несвязанных учетных записей для простоты. Версия для вошедших в систему
    немного сложнее.
    """

    key = "выйти"
    aliases = ["вый"]
    locks = "cmd:all()"
    help_category = "Общее"

    def func(self):
        """Simply close the connection."""
        session = self.caller
        session.sessionhandler.disconnect(session, "Прощайте! Отсоединение.")


class CmdUnconnectedLook(COMMAND_DEFAULT_CLASS):
    """
    смотреть пока вы еще не вошли в игру

    Использование:
      смотреть

    Это неподключенная версия команды смотреть для простоты..

    Она вызывается сервером и запускает все.
    Все, что она делает, это отображает экран подключения.
    """

    key = CMD_LOGINSTART
    aliases = ["смотреть", "см"]
    locks = "cmd:all()"
    help_category = "Общее"

    def func(self):
        """Show the connect screen."""

        callables = utils.callables_from_module(CONNECTION_SCREEN_MODULE)
        if "connection_screen" in callables:
            connection_screen = callables["connection_screen"]()
        else:
            connection_screen = utils.random_string_from_module(
                CONNECTION_SCREEN_MODULE)
            if not connection_screen:
                connection_screen = "No connection screen found. Please contact an admin."
        self.caller.msg(connection_screen)


class CmdUnconnectedHelp(COMMAND_DEFAULT_CLASS):
    """
    получить справку в неподключенном состоянии

    использование:
      справка

    Это неподключенная версия команды справки,
    для простоты. Он показывает панель информации.
    """

    key = "справка"
    aliases = ["помощь", "пом", "?"]
    locks = "cmd:all()"
    help_category = "Общее"

    def func(self):
        """Shows help"""

        string = """
Вы не вошли в игру. Команды, которые вам доступны:

  |wсоздать|n - создать новый аккаунт
  |wвойти|n - войти в существующий аккаунт
  |wсмотреть|n - показать предыдущий экран еще раз
  |wсправка|n - показать справку
  |wкодировка|n - сменить кодировку
  |wчитатьэкран|n - включить читалку с экрана
  |wвыйти|n - выйти

для начала создайте аккаунт с помощью |wcсоздать Anna c67jHL8p|n
затем войдите в игру: |wвойти Anna c67jHL8p|n

используйте |wсмотреть|n если хотите увидеть предыдущий экран еще раз.

"""

        if settings.STAFF_CONTACT_EMAIL:
            string += "For support, please contact: %s" % settings.STAFF_CONTACT_EMAIL
        self.caller.msg(string)


class CmdUnconnectedEncoding(COMMAND_DEFAULT_CLASS):
    """
    установить, какую текстовую кодировку использовать в неподключенном состоянии

    Usage:
      кодировка/переключатель [<кодировка>]

    Переключатель:
      очистить - очистить вашу кодировку


    Это устанавливает кодировку текста для общения с Evennia. Это в основном
    проблема только в том случае, если вы хотите использовать символы, отличные от ASCII (т.е. буквы/символы
    на английском не нашел). Если вы видите, что ваши персонажи выглядят странно (или вы
    получить ошибки кодирования), вы должны использовать эту команду, чтобы установить сервер
    кодировка должна совпадать с используемой в вашей клиентской программе.

    Кодировка по-умолчанию utf-8 (default), latin-1, ISO-8859-1 etc.

    Если вы не отправите кодировку, будет отображаться текущая кодировка.
  """

    key = "кодировка"
    locks = "cmd:all()"
    help_category = "Общее"

    def func(self):
        """
        Sets the encoding.
        """

        if self.session is None:
            return

        sync = False
        if "clear" in self.switches:
            # remove customization
            old_encoding = self.session.protocol_flags.get("ENCODING", None)
            if old_encoding:
                string = "Ваша кодировка ('%s') очищена." % old_encoding
            else:
                string = "У вас не установлено собственной кодировки."
            self.session.protocol_flags["ENCODING"] = "utf-8"
            sync = True
        elif not self.args:
            # just list the encodings supported
            pencoding = self.session.protocol_flags.get("ENCODING", None)
            string = ""
            if pencoding:
                string += (
                    "Кодировка по-умолчанию: |g%s|n (сменить с помощью |wкодировка <кодировка>|n)" % pencoding
                )
            encodings = settings.ENCODINGS
            if encodings:
                string += (
                    "\nАльтернативная кодировка сервера:\n   |g%s|n"
                    % ", ".join(encodings)
                )
            if not string:
                string = "Кодировок не найдено."
        else:
            # change encoding
            old_encoding = self.session.protocol_flags.get("ENCODING", None)
            encoding = self.args
            try:
                codecs_lookup(encoding)
            except LookupError:
                string = (
                    "|rКодировка '|w%s|r' неверная. Возвращаем '|w%s|r'.|n"
                    % (encoding, old_encoding)
                )
            else:
                self.session.protocol_flags["ENCODING"] = encoding
                string = "Ваша кодировка изменена на '|w%s|n' to '|w%s|n'." % (
                    old_encoding,
                    encoding,
                )
                sync = True
        if sync:
            self.session.sessionhandler.session_portal_sync(self.session)
        self.caller.msg(string.strip())


class CmdUnconnectedScreenreader(COMMAND_DEFAULT_CLASS):
    """
    Включить читалку с экрана.

    Использование:
        читатьэкран

    Используется для включения и выключения режима чтения с экрана перед входом в систему (когда
    вошли в систему, включите функцию чтения с экрана).
    """

    key = "читатьэкран"
    help_category = "Общее"

    def func(self):
        """Flips screenreader setting."""
        new_setting = not self.session.protocol_flags.get(
            "SCREENREADER", False)
        self.session.protocol_flags["SCREENREADER"] = new_setting
        string = "Screenreader mode turned |w%s|n." % (
            "on" if new_setting else "off")
        self.caller.msg(string)
        self.session.sessionhandler.session_portal_sync(self.session)


class CmdUnconnectedInfo(COMMAND_DEFAULT_CLASS):
    """
    Provides MUDINFO output, so that Evennia games can be added to Mudconnector
    and Mudstats.  Sadly, the MUDINFO specification seems to have dropped off the
    face of the net, but it is still used by some crawlers.  This implementation
    was created by looking at the MUDINFO implementation in MUX2, TinyMUSH, Rhost,
    and PennMUSH.
    """

    key = "info"
    locks = "cmd:all()"
    help_category = "Общее"

    def func(self):
        self.caller.msg(
            "## BEGIN INFO 1.1\nName: %s\nUptime: %s\nConnected: %d\nVersion: Evennia %s\n## END INFO"
            % (
                settings.SERVERNAME,
                datetime.datetime.fromtimestamp(
                    gametime.SERVER_START_TIME).ctime(),
                SESSIONS.account_count(),
                utils.get_evennia_version(),
            )
        )


def _create_account(session, accountname, password, permissions, typeclass=None, email=None):
    """
    Helper function, creates an account of the specified typeclass.
    """
    try:
        new_account = create.create_account(
            accountname, email, password, permissions=permissions, typeclass=typeclass
        )

    except Exception as e:
        session.msg(
            "There was an error creating the Account:\n%s\n If this problem persists, contact an admin."
            % e
        )
        logger.log_trace()
        return False

    # This needs to be set so the engine knows this account is
    # logging in for the first time. (so it knows to call the right
    # hooks during login later)
    new_account.db.FIRST_LOGIN = True

    # join the new account to the public channel
    pchannel = ChannelDB.objects.get_channel(
        settings.DEFAULT_CHANNELS[0]["key"])
    if not pchannel or not pchannel.connect(new_account):
        string = "New account '%s' could not connect to public channel!" % new_account.key
        logger.log_err(string)
    return new_account


def _create_character(session, new_account, typeclass, home, permissions):
    """
    Helper function, creates a character based on an account's name.
    This is meant for Guest and MULTISESSION_MODE < 2 situations.
    """
    try:
        new_character = create.create_object(
            typeclass, key=new_account.key, home=home, permissions=permissions
        )
        # set playable character list
        new_account.db._playable_characters.append(new_character)

        # allow only the character itself and the account to puppet this character (and Developers).
        new_character.locks.add(
            "puppet:id(%i) or pid(%i) or perm(Developer) or pperm(Developer)"
            % (new_character.id, new_account.id)
        )

        # If no description is set, set a default description
        if not new_character.db.desc:
            new_character.db.desc = "This is a character."
        # We need to set this to have ic auto-connect to this character
        new_account.db._last_puppet = new_character
    except Exception as e:
        session.msg(
            "There was an error creating the Character:\n%s\n If this problem persists, contact an admin."
            % e
        )
        logger.log_trace()
