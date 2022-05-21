from django.http import Http404
from django.shortcuts import render
from django.conf import settings

from evennia.utils.search import object_search
from evennia.utils.utils import inherits_from


def sheet(request, object_id):
    object_id = '#' + object_id
    try:
        character = object_search(object_id)[0]
    except IndexError:
        raise Http404(f"Персонаж с индентификатором {object_id} не найден.")
    if not inherits_from(character, settings.BASE_CHARACTER_TYPECLASS):
        raise Http404(f"Персонаж с индентификатором {object_id} не найден."
                      "Найден другой объект с указанным идентификатором.")
    return render(request, 'character/sheet.html', {'character': character})
