import os.path
import os

import dj_database_url


DEBUG = 'DJANGO_DEBUG' in os.environ
TEMPLATE_DEBUG = DEBUG
INTERNAL_IPS = ('127.0.0.1',)

ADMINS = (
  ('Brandon Wilson', 'brandon.wilson@rd.io'),
  ('Rebecca Stecker', 'rebecca.stecker@rdio.com'),
  ('Emily Stumpf', 'emily.stumpf@rdio.com'),
  ('Marek Kapolka', 'marek.kapolka@rd.io'),
  ('holly.french@rd.io', 'Holly French'),
)

MANAGERS = ADMINS

TEST_DB_URI = os.environ.get('TEST_DB')
DATABASES = {
  'default': dj_database_url.config(default=TEST_DB_URI)
}

# Hosts/domain names that are valid for this site; required if DEBUG is False
# See https://docs.djangoproject.com/en/1.4/ref/settings/#allowed-hosts
ALLOWED_HOSTS = ['sutro.fm', 'rdioparty.com']

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# In a Windows environment this must be set to your system time zone.
TIME_ZONE = 'America/Los_Angeles'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en-us'

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# If you set this to False, Django will not format dates, numbers and
# calendars according to the current locale.
USE_L10N = True

# If you set this to False, Django will not use timezone-aware datetimes.
USE_TZ = True

# Absolute filesystem path to the directory that will hold user-uploaded files.
# Example: "/home/media/media.lawrence.com/media/"
MEDIA_ROOT = ''

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash.
# Examples: "http://media.lawrence.com/media/", "http://example.com/media/"
MEDIA_URL = ''

# Absolute path to the directory static files should be collected to.
# Don't put anything in this directory yourself; store your static files
# in apps' "static/" subdirectories and in STATICFILES_DIRS.
# Example: "/home/media/media.lawrence.com/static/"
STATIC_ROOT = '%s/webassets' % os.path.abspath(os.path.join(os.path.split(__file__)[0], os.pardir))
# STATIC_ROOT = os.path.join(BASE_DIR, "staticexport/")

# S3 static files
AWS_ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY')
AWS_STORAGE_BUCKET_NAME = 'rdiodj'

if DEBUG:
  STATIC_URL = '/static/'
else:
  DEFAULT_FILE_STORAGE = 'storages.backends.s3boto.S3BotoStorage'
  STATICFILES_STORAGE = 'storages.backends.s3boto.S3BotoStorage'
  STATIC_URL = 'http://' + AWS_STORAGE_BUCKET_NAME + '.s3.amazonaws.com/'

ADMIN_MEDIA_PREFIX = STATIC_URL + 'admin/'

# Additional locations of static files
STATICFILES_DIRS = (
  '%s/static' % os.path.abspath(os.path.split(__file__)[0]),
)

# List of finder classes that know how to find static files in
# various locations.
STATICFILES_FINDERS = (
  'django.contrib.staticfiles.finders.FileSystemFinder',
  'django.contrib.staticfiles.finders.AppDirectoriesFinder',
  #    'django.contrib.staticfiles.finders.DefaultStorageFinder',
)

# Make this unique, and don't share it with anybody.
SECRET_KEY = os.environ['DJANGO_SECRET_KEY']

SESSION_ENGINE = 'redis_sessions.session'

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
  'django.template.loaders.filesystem.Loader',
  'django.template.loaders.app_directories.Loader',
  #     'django.template.loaders.eggs.Loader',
)

MIDDLEWARE_CLASSES = (
  'django.middleware.common.CommonMiddleware',
  'django.contrib.sessions.middleware.SessionMiddleware',
  'django.middleware.csrf.CsrfViewMiddleware',
  'django.contrib.auth.middleware.AuthenticationMiddleware',
  'django.contrib.messages.middleware.MessageMiddleware',
  # Uncomment the next line for simple clickjacking protection:
  # 'django.middleware.clickjacking.XFrameOptionsMiddleware',
)

ROOT_URLCONF = 'sutrofm.urls'

# Python dotted path to the WSGI application used by Django's runserver.
WSGI_APPLICATION = 'ws4redis.django_runserver.application'

TEMPLATE_DIRS = (
  '%s/template' % os.path.abspath(os.path.split(__file__)[0]),
)

INSTALLED_APPS = (
  'django.contrib.auth',
  'django.contrib.contenttypes',
  'django.contrib.sessions',
  'django.contrib.sites',
  'django.contrib.messages',
  'django.contrib.staticfiles',
  'django.contrib.admin',
  'django.contrib.admindocs',
  'social_auth',
  'storages',
  'library',
  'ws4redis',
  'sutrofm'
)

TEMPLATE_CONTEXT_PROCESSORS = (
  'django.template.context_processors.debug',
  'django.template.context_processors.i18n',
  'django.template.context_processors.media',
  'django.template.context_processors.static',
  'django.template.context_processors.request',
  'django.contrib.auth.context_processors.auth',
  'django.contrib.messages.context_processors.messages',
  'social_auth.context_processors.social_auth_by_name_backends',
  'sutrofm.context_processors.rdio',
  'ws4redis.context_processors.default',
)

# A sample logging configuration. The only tangible logging
# performed by this configuration is to send an email to
# the site admins on every HTTP 500 error when DEBUG=False.
# See http://docs.djangoproject.com/en/dev/topics/logging for
# more details on how to customize your logging configuration.
LOGGING = {
  'version': 1,
  'disable_existing_loggers': True,
  'root': {
    'level': 'DEBUG',
    'handlers': ['sentry'],
  },
  'formatters': {
    'verbose': {
      'format': '%(levelname)s %(asctime)s %(module)s %(process)d %(thread)d %(message)s'
    },
  },
  'handlers': {
    'sentry': {
      'level': 'DEBUG',
      'class': 'raven.contrib.django.handlers.SentryHandler',
    },
    'console': {
      'level': 'DEBUG',
      'class': 'logging.StreamHandler',
      'formatter': 'verbose'
    }
  },
  'loggers': {
    'django.db.backends': {
      'level': 'DEBUG',
      'handlers': ['console'],
      'propagate': False,
    },
    'raven': {
      'level': 'DEBUG',
      'handlers': ['console'],
      'propagate': False,
    },
    'sentry.errors': {
      'level': 'DEBUG',
      'handlers': ['console'],
      'propagate': False,
    },
  },
}

# social_auth
AUTHENTICATION_BACKENDS = (
  'social_auth.backends.contrib.rdio.RdioOAuth2Backend',
  'django.contrib.auth.backends.ModelBackend',
)

RDIO_OAUTH2_KEY = os.environ['RDIO_OAUTH2_KEY']
RDIO_OAUTH2_SECRET = os.environ['RDIO_OAUTH2_SECRET']
RDIO2_PERMISSIONS = []

LOGIN_URL = '/auth/login/rdio-oauth2/'
LOGIN_REDIRECT_URL = '/parties/'

SENTRY_DSN = os.environ.get('SENTRY_DSN')
FIREBASE_TOKEN = os.environ.get('FIREBASE_TOKEN')

FIREBASE_URL = 'https://rdioparty.firebaseio.com'

# URL that distinguishes websocket connections from normal requests
WEBSOCKET_URL = '/ws/'

# Set the number of seconds each message shall persited
WS4REDIS_EXPIRE = 3600

WS4REDIS_HEARTBEAT = '--heartbeat--'

WS4REDIS_PREFIX = 'sutrofm'

WS4REDIS_CONNECTION = {
  'host': 'localhost',
  'port': 6379,
  'db': 0,
  'password': None,
}
