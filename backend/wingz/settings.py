import os
import sys

from django.core.exceptions import ImproperlyConfigured

SECRET_KEY = os.environ.get(
    'DJANGO_SECRET_KEY',
    'django-insecure-dev-key-change-in-production',
)

DEBUG = os.environ.get('DJANGO_DEBUG', 'True').lower() == 'true'

ALLOWED_HOSTS = os.environ.get('DJANGO_ALLOWED_HOSTS', '*').split(',')

# JWT auth — HS256 signed with JWT_SECRET_KEY. Separate from DJANGO_SECRET_KEY
# so rotating one does not invalidate the other. In dev it falls back to the
# Django SECRET_KEY so local runs and tests do not require extra env setup.
JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or SECRET_KEY
JWT_ALGORITHM = 'HS256'
JWT_ACCESS_TOKEN_LIFETIME_MINUTES = int(
    os.environ.get('JWT_ACCESS_TOKEN_LIFETIME_MINUTES', '15')
)
JWT_REFRESH_TOKEN_LIFETIME_DAYS = int(
    os.environ.get('JWT_REFRESH_TOKEN_LIFETIME_DAYS', '7')
)

if not JWT_SECRET_KEY:
    raise ImproperlyConfigured(
        'JWT_SECRET_KEY (or DJANGO_SECRET_KEY fallback) must be set.'
    )

INSTALLED_APPS = [
    'django.contrib.contenttypes',
    'django.contrib.auth',
    'rest_framework',
    'rides',
]

MIDDLEWARE = [
    'django.middleware.common.CommonMiddleware',
]

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rides.authentication.JWTAuthentication',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rides.pagination.StandardPagination',
    'PAGE_SIZE': 10,
    'DEFAULT_PERMISSION_CLASSES': [
        'rides.permissions.IsAdminRole',
    ],
    'EXCEPTION_HANDLER': 'rides.exceptions.custom_exception_handler',
}

if 'pytest' in sys.modules:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': ':memory:',
        }
    }
elif os.environ.get('USE_SQLITE'):
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': os.path.join(os.path.dirname(os.path.dirname(__file__)), 'db.sqlite3'),
        }
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.mysql',
            'NAME': os.environ.get('DB_NAME', 'wingz_db'),
            'USER': os.environ.get('DB_USER', 'root'),
            'PASSWORD': os.environ.get('DB_PASSWORD', ''),
            'HOST': os.environ.get('DB_HOST', 'localhost'),
            'PORT': os.environ.get('DB_PORT', '3306'),
            'OPTIONS': {'charset': 'utf8mb4'},
        }
    }

APPEND_SLASH = True
ROOT_URLCONF = 'wingz.urls'
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
