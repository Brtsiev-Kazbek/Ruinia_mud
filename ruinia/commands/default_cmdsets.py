"""
Command sets

All commands in the game must be grouped in a cmdset.  A given command
can be part of any number of cmdsets and cmdsets can be added/removed
and merged onto entities at runtime.

To create new commands to populate the cmdset, see
`commands/command.py`.

This module wraps the default command sets of Evennia; overloads them
to add/remove commands from the default lineup. You can create your
own cmdsets by inheriting from them or directly from `evennia.CmdSet`.

Все команды в игре должны быть сгруппированы в cmdset. Команда может
быть частью любого количества набора команд, а наборы команд можно добавлять/удалять и объединять с сущностями
во время выполнения.

Для того, чтобы создать новые команды для заполнения набора команд, загляните в
`commands/command.py`.

Этот модуль включает в себя наборы команд Evennia по умолчанию; перезагружает их
и добавляет, либо удаляет команды из состояния игры по-умолчанию. Вы можете создать свой
собственный набор команд путем наследования его напрямую из `evennia.CmdSet`.

"""

from evennia import default_cmds
from commands.default import general, help, unloggedin, account, building


class CharacterCmdSet(default_cmds.CharacterCmdSet):
    """
    `CharacterCmdSet` содержит общие внутриигровые команды, такие как `смотреть`,
    `взять` и т.д., доступные для игровых объектов Character. Он объединяется с `AccountCmdSet`,
    когда учетная запись делает персонажа марионеткой.
    """

    key = "DefaultCharacter"

    def at_cmdset_creation(self):
        """
        Populates the cmdset
        """
        super().at_cmdset_creation()
        #
        # any commands you add below will overload the default ones.
        #

        # удаляем команды, поставляемые "из коробки"
        self.remove(default_cmds.CmdHome())
        self.remove(default_cmds.CmdLook())
        self.remove(default_cmds.CmdNick())
        self.remove(default_cmds.CmdInventory())
        self.remove(default_cmds.CmdGet())
        self.remove(default_cmds.CmdDrop())
        self.remove(default_cmds.CmdGive())
        self.remove(default_cmds.CmdSetDesc())
        self.remove(default_cmds.CmdSay())
        self.remove(default_cmds.CmdWhisper())
        self.remove(default_cmds.CmdPose())
        self.remove(default_cmds.CmdAccess())
        self.remove(default_cmds.CmdHelp())
        self.remove(default_cmds.CmdSetHelp())

        self.remove(default_cmds.CmdTunnel())

        # регистрируем переведенные версии
        self.add(general.CmdHome())
        self.add(general.CmdLook())
        self.add(general.CmdNick())
        self.add(general.CmdInventory())
        self.add(general.CmdGet())
        self.add(general.CmdDrop())
        self.add(general.CmdGive())
        self.add(general.CmdSetDesc())
        self.add(general.CmdSay())
        self.add(general.CmdWhisper())
        self.add(general.CmdPose())
        self.add(general.CmdAccess())
        self.add(help.CmdHelp())
        self.add(help.CmdSetHelp())

        self.add(building.CmdTunnel())


class AccountCmdSet(default_cmds.AccountCmdSet):
    """
    Этот набор команд доступен для учетной записи в любое время.
    Он объединяется с `CharacterCmdSet`, 
    когда учетная запись делает персонажа марионеткой.
    Он содержит специфичные команды для учетной записи.
    """

    key = "DefaultAccount"

    def at_cmdset_creation(self):
        """
        Populates the cmdset
        """
        super().at_cmdset_creation()
        #
        # any commands you add below will overload the default ones.
        #

        # удаляем команды, поставляемые "из коробки"
        self.remove(default_cmds.CmdNick())

        self.remove(default_cmds.CmdOOCLook())
        self.remove(default_cmds.CmdCharCreate())
        self.remove(default_cmds.CmdCharDelete())
        self.remove(default_cmds.CmdIC())
        self.remove(default_cmds.CmdOOC())
        self.remove(default_cmds.CmdSessions())
        self.remove(default_cmds.CmdWho())
        self.remove(default_cmds.CmdOption())
        self.remove(default_cmds.CmdPassword())
        self.remove(default_cmds.CmdQuit())
        self.remove(default_cmds.CmdColorTest())
        self.remove(default_cmds.CmdQuell())
        self.remove(default_cmds.CmdStyle())

        # регистрируем переведенные версии
        self.add(account.CmdOOCLook())
        self.add(account.CmdCharCreate())
        self.add(account.CmdCharDelete())
        self.add(account.CmdIC())
        self.add(account.CmdOOC())
        self.add(account.CmdSessions())
        self.add(account.CmdWho())
        self.add(account.CmdOption())
        self.add(account.CmdPassword())
        self.add(account.CmdQuit())
        self.add(account.CmdColorTest())
        self.add(account.CmdQuell())
        self.add(account.CmdStyle())


class UnloggedinCmdSet(default_cmds.UnloggedinCmdSet):
    """
    Набор команд, доступный до входа в систему.
    Содержит такие команды, как создание новой учетной записи, вход в систему и т. д.
    """

    key = "DefaultUnloggedin"

    def at_cmdset_creation(self):
        """
        Populates the cmdset
        """
        super().at_cmdset_creation()
        #
        # any commands you add below will overload the default ones.
        #

        # удаляем команды, поставляемые "из коробки"
        self.remove(default_cmds.CmdUnconnectedConnect())
        self.remove(default_cmds.CmdUnconnectedCreate())
        self.remove(default_cmds.CmdUnconnectedQuit())
        self.remove(default_cmds.CmdUnconnectedLook())
        self.remove(default_cmds.CmdUnconnectedHelp())
        self.remove(default_cmds.CmdUnconnectedEncoding())
        self.remove(default_cmds.CmdUnconnectedScreenreader())
        self.remove(default_cmds.CmdUnconnectedInfo())

        # регистрируем переведенные версии
        self.add(unloggedin.CmdUnconnectedConnect())
        self.add(unloggedin.CmdUnconnectedCreate())
        self.add(unloggedin.CmdUnconnectedQuit())
        self.add(unloggedin.CmdUnconnectedLook())
        self.add(unloggedin.CmdUnconnectedHelp())
        self.add(unloggedin.CmdUnconnectedEncoding())
        self.add(unloggedin.CmdUnconnectedScreenreader())
        self.add(unloggedin.CmdUnconnectedInfo())


class SessionCmdSet(default_cmds.SessionCmdSet):
    """
    Этот набор команд становится доступным на уровне сеанса после входа в систему.
    по умолчанию пуст.
    """

    key = "DefaultSession"

    def at_cmdset_creation(self):
        """
        This is the only method defined in a cmdset, called during
        its creation. It should populate the set with command instances.

        As and example we just add the empty base `Command` object.
        It prints some info.
        """
        super().at_cmdset_creation()
        #
        # any commands you add below will overload the default ones.
        #

        # удаляем команды, поставляемые "из коробки"
        self.remove(default_cmds.CmdSessions())

        # регистрируем переведенные версии
        self.add(account.CmdSessions())
