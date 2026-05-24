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

# Orphan recovery thresholds set to 1 s so tests can back-date plans without long sleeps.
PLAN_ORPHAN_PENDING_SECONDS = 1
PLAN_ORPHAN_RUNNING_SECONDS = 1

LOGIN_URL = "/accounts/login/"
LOGIN_REDIRECT_URL = "/plot/"
