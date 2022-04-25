"""
Room

Rooms are simple containers that has no location of their own.

"""

from evennia import DefaultRoom

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
        string = "%s\n" % Map(looker).show_map()
        # Add all the normal stuff like room description,
        # contents, exits etc.
        string += "\n" + super().return_appearance(looker)
        return string

    pass
