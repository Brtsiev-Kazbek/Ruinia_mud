"""
Building and world design commands
"""
from ast import literal_eval as _LITERAL_EVAL
import re
from django.conf import settings
from django.db.models import Q, Min, Max
from evennia.objects.models import ObjectDB
from evennia.locks.lockhandler import LockException
from evennia.commands.cmdhandler import get_and_merge_cmdsets
from evennia.utils import create, utils, search, logger
from evennia.utils.utils import (
    inherits_from,
    class_from_module,
    get_all_typeclasses,
    variable_from_module,
    dbref,
    interactive,
    list_to_string,
    display_len,
)
from evennia.utils.eveditor import EvEditor
from evennia.utils.evmore import EvMore
from evennia.prototypes import spawner, prototypes as protlib, menus as olc_menus
from evennia.utils.ansi import raw as ansi_raw
from evennia.utils.inlinefuncs import raw as inlinefunc_raw

COMMAND_DEFAULT_CLASS = class_from_module(settings.COMMAND_DEFAULT_CLASS)

# limit symbol import for API
__all__ = (
    "ObjManipCommand",
    "CmdSetObjAlias",
    "CmdCopy",
    "CmdCpAttr",
    "CmdMvAttr",
    "CmdCreate",
    "CmdDesc",
    "CmdDestroy",
    "CmdDig",
    "CmdTunnel",
    "CmdLink",
    "CmdUnLink",
    "CmdSetHome",
    "CmdListCmdSets",
    "CmdName",
    "CmdOpen",
    "CmdSetAttribute",
    "CmdTypeclass",
    "CmdWipe",
    "CmdLock",
    "CmdExamine",
    "CmdFind",
    "CmdTeleport",
    "CmdScript",
    "CmdTag",
    "CmdSpawn",
)

# used by set

LIST_APPEND_CHAR = "+"

# used by find
CHAR_TYPECLASS = settings.BASE_CHARACTER_TYPECLASS
ROOM_TYPECLASS = settings.BASE_ROOM_TYPECLASS
EXIT_TYPECLASS = settings.BASE_EXIT_TYPECLASS
_DEFAULT_WIDTH = settings.CLIENT_DEFAULT_WIDTH

_PROTOTYPE_PARENTS = None


class CmdTunnel(COMMAND_DEFAULT_CLASS):
    """
    create new rooms in cardinal directions only

    Usage:
      tunnel[/switch] <direction>[:typeclass] [= <roomname>[;alias;alias;...][:typeclass]]

    Switches:
      oneway - do not create an exit back to the current location
      tel - teleport to the newly created room

    Example:
      tunnel n
      tunnel n = house;mike's place;green building

    This is a simple way to build using pre-defined directions:
     |wс, св, в, юв, ю, юз, з, сз|n (север, северо-восток и т.д.)
     |wвв,вз|n (вверх and вниз)
     |wвн,сн|n (внутрь and снаружи)
    The full names (north, in, southwest, etc) will always be put as
    main name for the exit, using the abbreviation as an alias (so an
    exit will always be able to be used with both "north" as well as
    "n" for example). Opposite directions will automatically be
    created back from the new room unless the /oneway switch is given.
    For more flexibility and power in creating rooms, use dig.
    """

    key = "tunnel"
    aliases = ["tun"]
    switch_options = ("oneway", "tel")
    locks = "cmd: perm(tunnel) or perm(Builder)"
    help_category = "Building"

    # store the direction, full name and its opposite
    # directions = {
    #     "n": ("north", "s"),
    #     "ne": ("northeast", "sw"),
    #     "e": ("east", "w"),
    #     "se": ("southeast", "nw"),
    #     "s": ("south", "n"),
    #     "sw": ("southwest", "ne"),
    #     "w": ("west", "e"),
    #     "nw": ("northwest", "se"),
    #     "u": ("up", "d"),
    #     "d": ("down", "u"),
    #     "i": ("in", "o"),
    #     "o": ("out", "i"),
    # }

    directions = {
        "с": ("север", "ю"),
        "св": ("северо-восток", "юз"),
        "в": ("восток", "з"),
        "юв": ("юго-восток", "сз"),
        "ю": ("юг", "с"),
        "юз": ("юго-запад", "св"),
        "з": ("запад", "в"),
        "сз": ("северо-запад", "юв"),
        "вв": ("вверх", "вз"),
        "вз": ("вниз", "вв"),
        "вн": ("внутрь", "сн"),
        "сн": ("снаружи", "вн"),
    }

    def func(self):
        """Implements the tunnel command"""

        if not self.args or not self.lhs:
            string = (
                "Usage: tunnel[/switch] <direction>[:typeclass] [= <roomname>"
                "[;alias;alias;...][:typeclass]]"
            )
            self.caller.msg(string)
            return

        # If we get a typeclass, we need to get just the exitname
        exitshort = self.lhs.split(":")[0]

        if exitshort not in self.directions:
            string = "tunnel can only understand the following directions: %s." % ",".join(
                sorted(self.directions.keys())
            )
            string += "\n(use dig for more freedom)"
            self.caller.msg(string)
            return

        # retrieve all input and parse it
        exitname, backshort = self.directions[exitshort]
        backname = self.directions[backshort][0]

        # if we recieved a typeclass for the exit, add it to the alias(short name)
        if ":" in self.lhs:
            # limit to only the first : character
            exit_typeclass = ":" + self.lhs.split(":", 1)[-1]
            # exitshort and backshort are the last part of the exit strings,
            # so we add our typeclass argument after
            exitshort += exit_typeclass
            backshort += exit_typeclass

        roomname = "Some place"
        if self.rhs:
            roomname = self.rhs  # this may include aliases; that's fine.

        telswitch = ""
        if "tel" in self.switches:
            telswitch = "/teleport"
        backstring = ""
        if "oneway" not in self.switches:
            backstring = ", %s;%s" % (backname, backshort)

        # build the string we will use to call dig
        digstring = "dig%s %s = %s;%s%s" % (
            telswitch, roomname, exitname, exitshort, backstring)
        self.execute_cmd(digstring)
