"""
Huginn — base settings shared across all environments.
"""

import os
from pathlib import Path

from .db_config import postgres_connection_from_environ, redis_url_from_environ

# BASE_DIR is the project root (two levels up from this file)
BASE_DIR = Path(__file__).resolve().parent.parent.parent

SECRET_KEY = os.environ["SECRET_KEY"]

DEBUG = False

ALLOWED_HOSTS = os.environ.get("ALLOWED_HOSTS", "").split(",")

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.humanize",
    "django.contrib.staticfiles",
    # Third-party
    "django_htmx",
    "django_celery_beat",
    # Huginn apps
    "accounts",
    "ingestion",
    "analytics",
    "sitrep",
    "ui",
    "gjallarhorn",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "django_htmx.middleware.HtmxMiddleware",
]

ROOT_URLCONF = "huginn.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "huginn.wsgi.application"

DATABASES = {"default": postgres_connection_from_environ()}

# Redis / Celery
REDIS_URL = redis_url_from_environ()

CELERY_BROKER_URL = REDIS_URL
CELERY_RESULT_BACKEND = REDIS_URL
CELERY_BEAT_SCHEDULER = "django_celery_beat.schedulers:DatabaseScheduler"
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_TIMEZONE = "UTC"

# Cache
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": REDIS_URL,
    }
}

SESSION_ENGINE = "django.contrib.sessions.backends.db"

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

AUTH_USER_MODEL = "accounts.User"

LOGIN_URL = "/"
LOGIN_REDIRECT_URL = "/"

# Structured JSON logging to stdout — collected by CloudWatch on EB
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "json": {
            "()": "logging.Formatter",
            "fmt": '{"time":"%(asctime)s","level":"%(levelname)s","logger":"%(name)s","module":"%(module)s","func":"%(funcName)s","line":%(lineno)d,"msg":%(message)s}',
            "datefmt": "%Y-%m-%dT%H:%M:%S",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "json",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "INFO",
    },
    "loggers": {
        "django": {"handlers": ["console"], "level": "WARNING", "propagate": False},
        "huginn": {"handlers": ["console"], "level": "INFO", "propagate": False},
        "ingestion": {"handlers": ["console"], "level": "INFO", "propagate": False},
        "analytics": {"handlers": ["console"], "level": "INFO", "propagate": False},
        "sitrep": {"handlers": ["console"], "level": "INFO", "propagate": False},
        "celery": {"handlers": ["console"], "level": "INFO", "propagate": False},
        "huginn.auth": {"handlers": ["console"], "level": "INFO", "propagate": False},
    },
}

# External connector config — read from env
GITLAB_URL = os.environ.get("GITLAB_URL", "")
GITLAB_TOKEN = os.environ.get("GITLAB_TOKEN", "")

JIRA_URL = os.environ.get("JIRA_URL", "")
JIRA_USER = os.environ.get("JIRA_USER", "")
JIRA_TOKEN = os.environ.get("JIRA_TOKEN", "")

LLM_API_KEY = os.environ.get("LLM_API_KEY", "")
