"""
Room

Rooms are simple containers that has no location of their own.

"""

import datetime
from math import sqrt
from evennia import DefaultRoom
from evennia.utils.gametime import gametime
from evennia.utils.utils import list_to_string

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

        # Получаем значение игрового времени
        game_time = int(gametime(absolute=True))
        formatted_game_time = str(datetime.datetime.fromtimestamp(game_time))

        # [...]
        string = "\n %s\n" % Map(looker).show_map()

        string += f'{formatted_game_time} '
        string += f"(x: {self.x}, y: {self.y}, z: {self.z})"

        # Add all the normal stuff like room description,
        # contents, exits etc.
        string += "\n" + \
            self._return_raw_appearance(looker)

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
        visible = (con for con in self.contents if con !=
                   looker and con.access(looker, "view"))
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
                    key, _ = itemlist[0].get_numbered_name(
                        nitem, looker, key=key)
                else:
                    key = [item.get_numbered_name(nitem, looker, key=key)[1] for item in itemlist][
                        0
                    ]
                thing_strings.append(key)

            string += "\n|wВы видите:|n " + \
                list_to_string(users + thing_strings, "и")

        return string

    # ------------------
    # Система координат

    @classmethod
    def get_room_at(cls, x, y, z):
        """
        Возвращает локацию по указанным координатам или None, если такой нет

        Args:
            x (int): the X coord.
            y (int): the Y coord.
            z (int): the Z coord.

        Возвращает:
        локацию по указанным координатам или None, если такой нет.
        """
        rooms = cls.objects.filter(
            db_tags__db_key=str(x), db_tags__db_category="coord_x").filter(
            db_tags__db_key=str(y), db_tags__db_category="coord_y").filter(
            db_tags__db_key=str(z), db_tags__db_category="coord_z")

        if rooms:
            return rooms[0]

        return None

    @classmethod
    def get_rooms_around(cls, x, y, z, distance):
        """
        Возвращает список комнат вокруг заданных координат.

        Этот метод возвращает список кортежей (расстояние, комната), которые
        можно легко просмотреть. Этот список отсортирован по расстоянию (the
        ближайшая комната к указанной позиции всегда находится наверху
        из списка).

        Аргументы:
        x (int): координата X.
        y (int): координата Y.
        z (int): Z-координата.
        расстояние (int): максимальное расстояние до указанной позиции.

        Возвращает:
        Список кортежей, содержащий расстояние до указанной
        позиции и комнату на этом расстоянии. Несколько комнат
        могут находиться на равном расстоянии от позиции.
        """

        # быстрый поиск, чтобы получить только локации в квадрате
        x_r = list(reversed([str(x - i) for i in range(0, distance + 1)]))
        x_r += [str(x + i) for i in range(1, distance + 1)]
        y_r = list(reversed([str(y - i) for i in range(0, distance + 1)]))
        y_r += [str(y + i) for i in range(1, distance + 1)]
        z_r = list(reversed([str(z - i) for i in range(0, distance + 1)]))
        z_r += [str(z + i) for i in range(1, distance + 1)]
        wide = cls.objects.filter(
            db_tags__db_key__in=x_r, db_tags__db_category="coord_x").filter(
            db_tags__db_key__in=y_r, db_tags__db_category="coord_y").filter(
            db_tags__db_key__in=z_r, db_tags__db_category="coord_z")

        # Теперь нам нужно отфильтровать этот список, чтобы выяснить, является ли
        # эти комнаты действительно достаточно близко, и на каком расстоянии
        # Короче говоря: мы меняем квадрат на круг.
        rooms = []
        for room in wide:
            x2 = int(room.tags.get(category="coord_x"))
            y2 = int(room.tags.get(category="coord_y"))
            z2 = int(room.tags.get(category="coord_z"))
            distance_to_room = sqrt(
                (x2 - x) ** 2 + (y2 - y) ** 2 + (z2 - z) ** 2)
            if distance_to_room <= distance:
                rooms.append((distance_to_room, room))

        # Сортируем комнаты по расстоянию
        rooms.sort(key=lambda tup: tup[0])
        return rooms

    @property
    def x(self):
        """Возвращает координату X или None"""
        x = self.tags.get(category="coord_x")
        return int(x) if isinstance(x, str) else None

    @x.setter
    def x(self, x):
        """Изменить координату X"""
        old = self.tags.get(category="coord_x")
        if old is not None:
            self.tags.remove(old, category="coord_x")
        if x is not None:
            self.tags.add(str(x), category="coord_x")

    @property
    def y(self):
        """Возвращает координату Y или None"""
        y = self.tags.get(category="coord_y")
        return int(y) if isinstance(y, str) else None

    @y.setter
    def y(self, y):
        """Изменить координату Y"""
        old = self.tags.get(category="coord_y")
        if old is not None:
            self.tags.remove(old, category="coord_y")
        if y is not None:
            self.tags.add(str(y), category="coord_y")

    @ property
    def z(self):
        """Возвращает координату Z или None"""
        z = self.tags.get(category="coord_z")
        return int(z) if isinstance(z, str) else None

    @z.setter
    def z(self, z):
        """Изменить координату Z"""
        old = self.tags.get(category="coord_z")
        if old is not None:
            self.tags.remove(old, category="coord_z")
        if z is not None:
            self.tags.add(str(z), category="coord_z")

    pass
