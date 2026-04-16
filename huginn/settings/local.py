"""
Local development settings.
All values either have safe defaults or are read from .env via Docker Compose.
"""

from .base import *  # noqa: F401, F403

DEBUG = True

ALLOWED_HOSTS = ["localhost", "127.0.0.1", "0.0.0.0"]

# Looser security for local dev
CSRF_TRUSTED_ORIGINS = ["http://localhost:8000", "http://127.0.0.1:8000"]

# Show full tracebacks in console
LOGGING["root"]["level"] = "DEBUG"  # noqa: F405
LOGGING["loggers"]["huginn"]["level"] = "DEBUG"  # noqa: F405
