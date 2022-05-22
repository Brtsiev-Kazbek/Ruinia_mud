r"""
Evennia settings file.

The available options are found in the default settings file found
here:

c:\users\kazbi\desktop\ruinia\evennia\evennia\settings_default.py

Remember:

Don't copy more from the default file than you actually intend to
change; this will make sure that you don't overload upstream updates
unnecessarily.

When changing a setting requiring a file system path (like
path/to/actual/file.py), use GAME_DIR and EVENNIA_DIR to reference
your game folder and the Evennia library folders respectively. Python
paths (path.to.module) should be given relative to the game's root
folder (typeclasses.foo) whereas paths within the Evennia library
needs to be given explicitly (evennia.foo).

If you want to share your game dir, including its settings, you can
put secret game- or server-specific settings in secret_settings.py.

"""

# Use the defaults from Evennia unless explicitly overridden
import time
from datetime import datetime
from evennia.settings_default import *

######################################################################
# Evennia base server config
######################################################################

DEBUG = True

# This is the name of your game. Make it catchy!
SERVERNAME = "Ruinia"
GAME_SLOGAN = "На стадии разработки"


######################################################################
# Evennia WIKI
######################################################################

INSTALLED_APPS += (
    'django.contrib.humanize.apps.HumanizeConfig',
    'django_nyt.apps.DjangoNytConfig',
    'mptt',
    'sorl.thumbnail',
    'wiki.apps.WikiConfig',
    'wiki.plugins.attachments.apps.AttachmentsConfig',
    'wiki.plugins.notifications.apps.NotificationsConfig',
    'wiki.plugins.images.apps.ImagesConfig',
    'wiki.plugins.macros.apps.MacrosConfig',
)

# Disable wiki handling of login/signup
WIKI_ACCOUNT_HANDLING = False
WIKI_ACCOUNT_SIGNUP_ALLOWED = False

# In server/conf/settings.py
# ...


def is_superuser(article, user):
    """Return True if user is a superuser, False otherwise."""
    return not user.is_anonymous and user.is_superuser


def is_builder(article, user):
    """Return True if user is a builder, False otherwise."""
    return not user.is_anonymous and user.locks.check_lockstring(user, "perm(Builders)")


def is_anyone(article, user):
    """Return True even if the user is anonymous."""
    return True


# Who can create new groups and users from the wiki?
WIKI_CAN_ADMIN = is_superuser
# Who can change owner and group membership?
WIKI_CAN_ASSIGN = is_superuser
# Who can change group membership?
WIKI_CAN_ASSIGN_OWNER = is_superuser
# Who can change read/write access to groups or others?
WIKI_CAN_CHANGE_PERMISSIONS = is_superuser
# Who can soft-delete an article?
WIKI_CAN_DELETE = is_builder
# Who can lock an article and permanently delete it?
WIKI_CAN_MODERATE = is_superuser
# Who can edit articles?
WIKI_CAN_WRITE = is_builder
# Who can read articles?
WIKI_CAN_READ = is_anyone

# Connect custom apps
# INSTALLED_APPS.append('web.character')
INSTALLED_APPS += ('web.character',)

# Time
start = datetime(4000, 1, 1)

TIME_FACTOR = 10.0

# TIME_GAME_EPOCH = time.mktime(start.timetuple())


# print(TIME_GAME_EPOCH)

######################################################################
# Settings given in secret_settings.py override those in this file.
######################################################################
try:
    from server.conf.secret_settings import *
except ImportError:
    print("secret_settings.py file not found or failed to import.")
