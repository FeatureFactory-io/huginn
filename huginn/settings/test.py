"""Django settings for pytest (SQLite + locmem cache; no Postgres/Redis required)."""

import os

os.environ.setdefault("SECRET_KEY", "test-secret-key-for-pytest-not-for-production")

from .base import *  # noqa: F403, F401

SECRET_KEY = os.environ["SECRET_KEY"]
DEBUG = False
ALLOWED_HOSTS = ["testserver", "localhost"]

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    },
}

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "pytest-locmem",
    },
}

CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True

LOGIN_URL = "/"
LOGIN_REDIRECT_URL = "/projects/"
