import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "changeme1234567890")

DEBUG = os.getenv("DJANGO_DEBUG", "True").lower() == "true"

ALLOWED_HOSTS = ["*"]

USERNAME = os.getenv('WEB_USERNAME', 'admin')
PASSWORD = os.getenv('WEB_PASSWORD', 'password')

SRT_PUBLISH_PORT = int(os.getenv("SRT_PUBLISH_PORT", 4000))
SRT_PLAYER_PORT = int(os.getenv("SRT_PLAYER_PORT", 4001))
SRTLA_PUBLISH_PORT = int(os.getenv("SRTLA_PUBLISH_PORT", 5000))
SLS_STATS_DOMAIN_IP = os.getenv("SLS_STATS_DOMAIN_IP", "localhost")
SLS_STATS_PORT = int(os.getenv("SLS_STATS_PORT", 8789))

SLS_API_URL = os.getenv("SLS_API_URL", "http://localhost:8789")
SLS_API_KEY =os.getenv("SLS_API_KEY", "")

USE_I18N = True
USE_L10N = True
LOCALE_PATHS = [os.path.join(BASE_DIR, "locale")]
LANGUAGE_CODE = os.getenv("LANG", "en")

LANGUAGES = [
    ('de', 'Deutsch'),
    ('en', 'English'),
]

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "streams",
    "django.contrib.humanize",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    'whitenoise.middleware.WhiteNoiseMiddleware',
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "slspanel.middlewares.ForceEnvLanguageMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "slspanel.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "slspanel.wsgi.application"

SESSION_ENGINE = "django.contrib.sessions.backends.signed_cookies"

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

AUTH_PASSWORD_VALIDATORS = []

TIME_ZONE = os.getenv("TZ", "UTC")
USE_TZ = True

STATIC_URL = "/static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
