"""
Room

Rooms are simple containers that has no location of their own.

"""

from evennia import DefaultRoom
from evennia.utils.utils import list_to_string
from evennia.utils import evtable

from collections import defaultdict

from world.map import Map


class Room(DefaultRoom):
    """
    Rooms are like any Object, except their location is None
    (which is default). They also use basetype_setup() to
    add locks so they cannot be puppeted or picked up.
    (to change that, use at_object_creation instead)

    See examples/object.py for a list of
    properties and methods available on all Objects.
    """

    def return_appearance(self, looker):
        # [...]
         # string = "%s\n" % Map(looker).show_map()
        # Add all the normal stuff like room description,
        # contents, exits etc.
         # string += "\n" + self._return_raw_appearance(looker)

        local_map = evtable.wrap(Map(looker).show_map())
        location_appearance = evtable.wrap(self._return_raw_appearance(looker))

        string = evtable.EvTable("Локальная карта", "Описание", table = [local_map, location_appearance], border = "rows")

        print(string)

        return string


    def _return_raw_appearance(self, looker):
        """
        This formats a description. It is the hook a 'look' command
        should call.

        Args:
            looker (Object): Object doing the looking.
        """

        if not looker:
            return ""
        # get and identify all objects
        visible = (con for con in self.contents if con != looker and con.access(looker, "view"))
        exits, users, things = [], [], defaultdict(list)
        for con in visible:
            key = con.get_display_name(looker)
            if con.destination:
                exits.append(key)
            elif con.has_account:
                users.append("|c%s|n" % key)
            else:
                # things can be pluralized
                things[key].append(con)
        # get description, build string
        string = "|c%s|n\n" % self.get_display_name(looker)
        desc = self.db.desc
        if desc:
            string += "%s" % desc
        if exits:
            string += "\n|wВыходы:|n " + list_to_string(exits, "и")
            print(exits)
        if users or things:
            # handle pluralization of things (never pluralize users)
            thing_strings = []
            for key, itemlist in sorted(things.items()):
                nitem = len(itemlist)
                if nitem == 1:
                    key, _ = itemlist[0].get_numbered_name(nitem, looker, key=key)
                else:
                    key = [item.get_numbered_name(nitem, looker, key=key)[1] for item in itemlist][
                        0
                    ]
                thing_strings.append(key)

            string += "\n|wВы видите:|n " + list_to_string(users + thing_strings)

        return string


    pass
