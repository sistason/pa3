"""
Django settings for pa3 project.

Generated by 'django-admin startproject' using Django 2.0.2.

For more information on this file, see
https://docs.djangoproject.com/en/2.0/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/2.0/ref/settings/
"""

import os

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Pruefungsamt variables #

# Conversion of system-variables to readable strings
USER_TO_NAMES = {'pa_23': {'placement': 'H 23', 'displays': ['H 19', 'H 23', 'H 25']},
                 'pa_10': {'placement': 'H 10', 'displays': ['H 10']},
                 'pa_13': {'placement': 'H 13', 'displays':
                     ['Schalter 1/2', 'Schalter 3/4', 'Schalter 5/6',
                      'Schalter 7/8/9', 'Schalter 10/11']},
                 'pa_02': {'placement': 'H 02', 'displays': ['H 02']},
                }

with open(os.path.join('/run', "secrets", "recognizer_auth")) as f:
    RECOGNIZER_AUTH = f.read().strip()

RECOGNITION_TEMPLATES_PATH = os.path.join(BASE_DIR, 'pa3', 'recognition_templates')

RECOGNIZER_CONFIG = {
    "pa_02": {
        "ranges": [[1, 300]],
        "digits": 3,
        "rotate": 180
    },
    "pa_10": {
        "ranges": [[100, 399]],
        "digits": 3,
        "crop": [523, 320, 606, 360]
    },
    "pa_13": {
        "digits": 3,
        "ranges": [[0, 999], [0, 999], [0, 999], [0, 999], [0, 999]]
    },
    "pa_23": {
        "digits": 3,
        "ranges": [[400, 599], [600, 799], [1000, 1499]]
    }
}


# Where to write the images the recognizers based their OCR on? (for user validation. /dev/shm is the docker ramdisk)
IMAGE_DESTINATION = '/dev/shm/'

# When is the office you want to recognize open? Used to discard false-positive results and for user-display
OPENINGS = [{'weekday': 1, 'begin': 930, 'end': 1230},
            {'weekday': 2, 'begin': 1300, 'end': 1600},
            {'weekday': 3},
            {'weekday': 4, 'begin': 930, 'end': 1230},
            {'weekday': 5, 'begin': 930, 'end': 1230}
]

# TODO: You probably want to change this here according to server_url
ALLOWED_HOSTS = ['pa.freitagsrunde.org', 'www.pa.freitagsrunde.org', 'pruefungsamt.org', 'www.pruefungsamt.org',
                 '172.16.0.4', 'pa3_frontend', 'pa3.sistason.de', 'www.pa3.sistason.de', 'localhost', '172.16.0.6']


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/2.0/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
with open(os.path.join('/run', "secrets", "django_secret_key")) as f:
    # SECRET_KEY = 'h-b=@zve0t)8k_5&mfo057b^3l&u)69+dy)99=54f4q_!zsg5a'
    SECRET_KEY = f.read().strip()

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

# Application definition

INSTALLED_APPS = [
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'pa3',
    'pa3_web',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',

    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django.middleware.locale.LocaleMiddleware',
]

ROOT_URLCONF = 'pa3.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',

                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'pa3.wsgi.application'


with open(os.path.join('/run', "secrets", "mysql_root_password")) as f:
    mysql_pw = f.read()

# Database
# https://docs.djangoproject.com/en/2.0/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'HOST': 'pa3_mysql',
        'NAME': 'pa3_django',
        'USER': 'root',
        'PASSWORD': mysql_pw.strip(),
    }
}

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': '/var/log/django_debug.log',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file'],
            'level': 'DEBUG',
            'propagate': True,
        },
        '': {
            'handlers': ['file'],
            'level': 'INFO',
            'propagate': True,
        },
    },
}

# Internationalization
# https://docs.djangoproject.com/en/2.0/topics/i18n/

LANGUAGE_CODE = 'de-DE'

TIME_ZONE = 'Europe/Berlin'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/2.0/howto/static-files/

STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles/')
