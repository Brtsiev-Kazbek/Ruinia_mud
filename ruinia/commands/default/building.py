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



class ObjManipCommand(COMMAND_DEFAULT_CLASS):
    """
    This is a parent class for some of the defining objmanip commands
    since they tend to have some more variables to define new objects.

    Each object definition can have several components. First is
    always a name, followed by an optional alias list and finally an
    some optional data, such as a typeclass or a location. A comma ','
    separates different objects. Like this:

        name1;alias;alias;alias:option, name2;alias;alias ...

    Spaces between all components are stripped.

    A second situation is attribute manipulation. Such commands
    are simpler and offer combinations

        objname/attr/attr/attr, objname/attr, ...

    """

    # OBS - this is just a parent - it's not intended to actually be
    # included in a commandset on its own!

    def parse(self):
        """
        We need to expand the default parsing to get all
        the cases, see the module doc.
        """
        # get all the normal parsing done (switches etc)
        super().parse()

        obj_defs = ([], [])  # stores left- and right-hand side of '='
        obj_attrs = ([], [])  # "

        for iside, arglist in enumerate((self.lhslist, self.rhslist)):
            # lhslist/rhslist is already split by ',' at this point
            for objdef in arglist:
                aliases, option, attrs = [], None, []
                if ":" in objdef:
                    objdef, option = [part.strip() for part in objdef.rsplit(":", 1)]
                if ";" in objdef:
                    objdef, aliases = [part.strip() for part in objdef.split(";", 1)]
                    aliases = [alias.strip() for alias in aliases.split(";") if alias.strip()]
                if "/" in objdef:
                    objdef, attrs = [part.strip() for part in objdef.split("/", 1)]
                    attrs = [part.strip().lower() for part in attrs.split("/") if part.strip()]
                # store data
                obj_defs[iside].append({"name": objdef, "option": option, "aliases": aliases})
                obj_attrs[iside].append({"name": objdef, "attrs": attrs})

        # store for future access
        self.lhs_objs = obj_defs[0]
        self.rhs_objs = obj_defs[1]
        self.lhs_objattr = obj_attrs[0]
        self.rhs_objattr = obj_attrs[1]





class CmdDig(ObjManipCommand):
    """
    build new rooms and connect them to the current location

    Usage:
      dig[/switches] <roomname>[;alias;alias...][:typeclass]
            [= <exit_to_there>[;alias][:typeclass]]
               [, <exit_to_here>[;alias][:typeclass]]

    Switches:
       tel or teleport - move yourself to the new room

    Examples:
       dig kitchen = north;n, south;s
       dig house:myrooms.MyHouseTypeclass
       dig sheer cliff;cliff;sheer = climb up, climb down

    This command is a convenient way to build rooms quickly; it creates the
    new room and you can optionally set up exits back and forth between your
    current room and the new one. You can add as many aliases as you
    like to the name of the room and the exits in question; an example
    would be 'north;no;n'.
    """

    key = "dig"
    switch_options = ("teleport",)
    locks = "cmd:perm(dig) or perm(Builder)"
    help_category = "Building"

    # lockstring of newly created rooms, for easy overloading.
    # Will be formatted with the {id} of the creating object.
    new_room_lockstring = (
        "control:id({id}) or perm(Admin); "
        "delete:id({id}) or perm(Admin); "
        "edit:id({id}) or perm(Admin)"
    )

    def func(self):
        """Do the digging. Inherits variables from ObjManipCommand.parse()"""

        caller = self.caller

        if not self.lhs:
            string = "Usage: dig[/teleport] <roomname>[;alias;alias...]" "[:parent] [= <exit_there>"
            string += "[;alias;alias..][:parent]] "
            string += "[, <exit_back_here>[;alias;alias..][:parent]]"
            caller.msg(string)
            return

        room = self.lhs_objs[0]

        if not room["name"]:
            caller.msg("You must supply a new room name.")
            return
        location = caller.location

        # Create the new room
        typeclass = room["option"]
        if not typeclass:
            typeclass = settings.BASE_ROOM_TYPECLASS

        # create room
        new_room = create.create_object(
            typeclass, room["name"], aliases=room["aliases"], report_to=caller
        )
        lockstring = self.new_room_lockstring.format(id=caller.id)
        new_room.locks.add(lockstring)
        alias_string = ""
        if new_room.aliases.all():
            alias_string = " (%s)" % ", ".join(new_room.aliases.all())
        room_string = "Created room %s(%s)%s of type %s." % (
            new_room,
            new_room.dbref,
            alias_string,
            typeclass,
        )

        # create exit to room

        exit_to_string = ""
        exit_back_string = ""

        if self.rhs_objs:
            to_exit = self.rhs_objs[0]
            if not to_exit["name"]:
                exit_to_string = "\nNo exit created to new room."
            elif not location:
                exit_to_string = "\nYou cannot create an exit from a None-location."
            else:
                # Build the exit to the new room from the current one
                typeclass = to_exit["option"]
                if not typeclass:
                    typeclass = settings.BASE_EXIT_TYPECLASS

                new_to_exit = create.create_object(
                    typeclass,
                    to_exit["name"],
                    location,
                    aliases=to_exit["aliases"],
                    locks=lockstring,
                    destination=new_room,
                    report_to=caller,
                )
                alias_string = ""
                if new_to_exit.aliases.all():
                    alias_string = " (%s)" % ", ".join(new_to_exit.aliases.all())
                exit_to_string = "\nCreated Exit from %s to %s: %s(%s)%s."
                exit_to_string = exit_to_string % (
                    location.name,
                    new_room.name,
                    new_to_exit,
                    new_to_exit.dbref,
                    alias_string,
                )

        # Create exit back from new room

        if len(self.rhs_objs) > 1:
            # Building the exit back to the current room
            back_exit = self.rhs_objs[1]
            if not back_exit["name"]:
                exit_back_string = "\nNo back exit created."
            elif not location:
                exit_back_string = "\nYou cannot create an exit back to a None-location."
            else:
                typeclass = back_exit["option"]
                if not typeclass:
                    typeclass = settings.BASE_EXIT_TYPECLASS
                new_back_exit = create.create_object(
                    typeclass,
                    back_exit["name"],
                    new_room,
                    aliases=back_exit["aliases"],
                    locks=lockstring,
                    destination=location,
                    report_to=caller,
                )
                alias_string = ""
                if new_back_exit.aliases.all():
                    alias_string = " (%s)" % ", ".join(new_back_exit.aliases.all())
                exit_back_string = "\nCreated Exit back from %s to %s: %s(%s)%s."
                exit_back_string = exit_back_string % (
                    new_room.name,
                    location.name,
                    new_back_exit,
                    new_back_exit.dbref,
                    alias_string,
                )
        caller.msg("%s%s%s" % (room_string, exit_to_string, exit_back_string))
        if new_room and "teleport" in self.switches:
            caller.move_to(new_room)




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
