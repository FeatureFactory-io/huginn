"""
Local development settings.
All values either have safe defaults or are read from .env via Docker Compose.
"""

import os
from pathlib import Path

# Host-side runserver / Celery worker: load repo .env (Docker Compose injects env itself).
try:
    from dotenv import load_dotenv

    load_dotenv(Path(__file__).resolve().parent.parent.parent / ".env", override=False)
except ImportError:
    pass

# base.py reads os.environ["SECRET_KEY"]; allow manage.py without a shell-exported env.
os.environ.setdefault(
    "SECRET_KEY",
    "django-insecure-local-dev-only-change-in-production",
)

from .base import *  # noqa: F401, F403
from .db_config import apply_local_host_run_defaults

DEBUG = True

ALLOWED_HOSTS = ["localhost", "127.0.0.1", "0.0.0.0"]

# Host-side manage.py: see `db_config.apply_local_host_run_defaults`.
_local_redis = apply_local_host_run_defaults(DATABASES)  # noqa: F405
if _local_redis is not None:
    REDIS_URL = _local_redis  # noqa: F405
    CELERY_BROKER_URL = REDIS_URL  # noqa: F405
    CELERY_RESULT_BACKEND = REDIS_URL  # noqa: F405
    CACHES["default"]["LOCATION"] = REDIS_URL  # noqa: F405

# Looser security for local dev
CSRF_TRUSTED_ORIGINS = ["http://localhost:8000", "http://127.0.0.1:8000"]

# Show full tracebacks in console
_LOGGERS_DEBUG = (
    "huginn",
    "gjallarhorn",
    "ingestion",
    "sitrep",
    "celery",
    "httpx",
    "httpcore",
    "anthropic",
)
LOGGING["root"]["level"] = "DEBUG"  # noqa: F405
for _logger in _LOGGERS_DEBUG:
    LOGGING["loggers"].setdefault(_logger, {"handlers": ["console"], "level": "INFO", "propagate": False})  # noqa: F405
    LOGGING["loggers"][_logger]["level"] = "DEBUG"  # noqa: F405
