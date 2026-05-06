"""
PostgreSQL and Redis settings derived from the environment.

Keep all Django-side interpretation here so `base` and `local` do not drift.
Compose / CI still repeat defaults in YAML (unavoidable); align with
`docker-compose.yml` and `.env.example`.
"""

from __future__ import annotations

import os
from typing import Any

# Matches docker-compose `POSTGRES_PASSWORD:-huginn` / `.env.example`.
_DEV_COMPOSE_POSTGRES_PASSWORD = "huginn"

_DEV_REDIS_IN_DOCKER = "redis://redis:6379/0"
_DEV_REDIS_ON_HOST = "redis://127.0.0.1:6379/0"


def postgres_connection_from_environ() -> dict[str, Any]:
    """Defaults target the Docker Compose network (`db` service)."""
    return {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.environ.get("POSTGRES_DB", "huginn"),
        "USER": os.environ.get("POSTGRES_USER", "huginn"),
        "PASSWORD": os.environ.get("POSTGRES_PASSWORD", ""),
        "HOST": os.environ.get("POSTGRES_HOST", "db"),
        "PORT": os.environ.get("POSTGRES_PORT", "5432"),
        "CONN_MAX_AGE": 60,
    }


def redis_url_from_environ() -> str:
    return os.environ.get("REDIS_URL", _DEV_REDIS_IN_DOCKER)


def apply_local_host_run_defaults(databases: dict[str, dict[str, Any]]) -> str | None:
    """
    When `manage.py` runs on the host, Compose hostnames and blank password defaults
    often break. If vars are unset or empty, use localhost services and the dev password.

    Returns a new Redis URL when host defaults apply; caller must assign Celery/cache.
    """
    default = databases["default"]
    if not os.environ.get("POSTGRES_HOST"):
        default["HOST"] = "localhost"
    if not os.environ.get("POSTGRES_PASSWORD"):
        default["PASSWORD"] = _DEV_COMPOSE_POSTGRES_PASSWORD

    if not os.environ.get("REDIS_URL"):
        return _DEV_REDIS_ON_HOST
    return None
