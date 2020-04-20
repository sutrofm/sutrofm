from .default import *

DEBUG = False

ALLOWED_HOSTS = ['sutro-test.herokuapp.com']
SECRET_KEY = os.environ.get('SECRET_KEY')

REDIS_URL = os.environ.get('REDIS_URL')

CHANNEL_LAYERS = {
  'default': {
    'BACKEND': 'channels_redis.core.RedisChannelLayer',
    'CONFIG': {
      'hosts': [REDIS_URL],
    }
  }
}

# Parse database configuration from $DATABASE_URL
import dj_database_url

DATABASES = {'default': dj_database_url.config(conn_max_age=0)}

# Honor the 'X-Forwarded-Proto' header for request.is_secure()
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

