import os
from pathlib import Path

from django.core.management.utils import get_random_secret_key
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent

# Read a local .env file if there is one; real environment variables win over it.
load_dotenv(BASE_DIR / ".env")

def env_bool(name, default=False):
    return os.environ.get(name, str(default)).strip().lower() in {"1", "true", "yes", "on"}


# Safe defaults: DEBUG off, only local hosts allowed. For local work set
# DJANGO_DEBUG=True in .env (see .env.example).
DEBUG = env_bool("DJANGO_DEBUG", default=False)

# No secret key is stored in the code. Without DJANGO_SECRET_KEY a random one is
# generated at startup (fine for local work and tests; set a fixed one in production,
# otherwise sessions are lost on every restart).
SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY") or get_random_secret_key()

ALLOWED_HOSTS = [
    host.strip()
    for host in os.environ.get("DJANGO_ALLOWED_HOSTS", "127.0.0.1,localhost").split(",")
    if host.strip()
]


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'readings',
    "rest_framework",
    "rest_framework.authtoken",
    "django_filters",
    "drf_spectacular",
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'


# Database
# https://docs.djangoproject.com/en/5.2/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}


# Password validation
# https://docs.djangoproject.com/en/5.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/5.2/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.2/howto/static-files/

STATIC_URL = 'static/'

# Default primary key field type
# https://docs.djangoproject.com/en/5.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


LOGIN_URL = "login"
LOGIN_REDIRECT_URL = "city_list"
LOGOUT_REDIRECT_URL = "city_list"

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
       
        "rest_framework.authentication.TokenAuthentication",
       
        "rest_framework.authentication.SessionAuthentication",
    ],
     "DEFAULT_PAGINATION_CLASS": "readings.api.pagination.StandardPagination",
         "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
}

SPECTACULAR_SETTINGS = {
    "TITLE": "WeatherLog API",
    "DESCRIPTION": "Cities and weather readings. Authenticate with `Authorization: Token <key>`.",
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
}