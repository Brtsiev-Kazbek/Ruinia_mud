from evennia.utils import gametime
from typeclasses.rooms import Room

# TODO: добавить глобальный атрибут времени суток для проверки в командах и ИИ НПС


def at_sunrise():
    for room in Room.objects.all():
        room.msg_contents(
            "\n|[004|=x * ☾ Луна заходит на западе ☽ * |n |[521 |=b* ☀ Солнце восходит на востоке ☀ *|n \n")


def at_midday():
    for room in Room.objects.all():
        room.msg_contents("\n|[550|=b* ☀ Солнце в зените ☀ *|n\n")


def at_sunset():
    for room in Room.objects.all():
        room.msg_contents(
            "\n|[521|=b* ☀ Солнце заходит на западе ☀ * |[004 |=x* ☾ Луна восходит на востоке ☽ *|n\n")


def at_fullmoon():
    for room in Room.objects.all():
        room.msg_contents("\n|[003|=x* ☾ Луна в зените ☽ *|n\n")


def set_daynight():
    sunrise = gametime.schedule(at_sunrise, repeat=True, hour=6, min=0, sec=0)
    sunrise.key = 'at sunrise'

    midday = gametime.schedule(at_midday, repeat=True, hour=12, min=0, sec=0)
    midday.key = 'at midday'

    sunset = gametime.schedule(at_sunset, repeat=True, hour=19, min=0, sec=0)
    sunset.key = 'at sunset'

    fullmoon = gametime.schedule(
        at_fullmoon, repeat=True, hour=00, min=0, sec=0)
    fullmoon.key = 'at fullmoon'
