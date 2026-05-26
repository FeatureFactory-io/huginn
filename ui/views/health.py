"""Health check views."""

from __future__ import annotations

import logging
import sys
from datetime import datetime

import django
from django.conf import settings
from django.http import JsonResponse
from django.shortcuts import render
from django.utils import timezone

from huginn.versioning import get_deployed_revision

logger = logging.getLogger(__name__)


def _aggregate_status(checks: list[dict]) -> str:
    if any(c["status"] == "error" for c in checks):
        return "unhealthy"
    if any(c["status"] == "warn" for c in checks):
        return "degraded"
    return "healthy"


def _celery_workers_check() -> dict:
    """Ping Celery workers via the broker; no-op detail when CELERY_TASK_ALWAYS_EAGER."""
    if getattr(settings, "CELERY_TASK_ALWAYS_EAGER", False):
        return {
            "name": "Celery workers",
            "status": "ok",
            "detail": "Eager mode — tasks run in-process (no broker workers)",
        }
    try:
        from huginn.celery import app

        insp = app.control.inspect(timeout=1.0)
        if insp is None:
            return {
                "name": "Celery workers",
                "status": "error",
                "detail": "Inspect channel unreachable (broker down or timeout)",
            }
        ping = insp.ping()
        if not ping:
            return {
                "name": "Celery workers",
                "status": "error",
                "detail": "No workers answered ping",
            }
        names = ", ".join(sorted(ping.keys()))
        return {
            "name": "Celery workers",
            "status": "ok",
            "detail": f"{len(ping)} worker(s) responding ({names})",
        }
    except Exception as exc:
        return {"name": "Celery workers", "status": "error", "detail": str(exc)}


def _celery_beat_check() -> dict:
    """
    Scheduler side: django-celery-beat DB state.

    A live ``celery beat`` process is not provable here without a heartbeat;
    this row confirms periodic tasks are configured and the DB is reachable.
    """
    if getattr(settings, "CELERY_TASK_ALWAYS_EAGER", False):
        return {
            "name": "Celery Beat (scheduler)",
            "status": "ok",
            "detail": "Eager mode — beat scheduler not used",
        }
    try:
        from django_celery_beat.models import PeriodicTask

        n = PeriodicTask.objects.filter(enabled=True).count()
        if n == 0:
            return {
                "name": "Celery Beat (scheduler)",
                "status": "warn",
                "detail": "No enabled periodic tasks in DB — add schedules or run migrations",
            }
        return {
            "name": "Celery Beat (scheduler)",
            "status": "ok",
            "detail": (
                f"{n} enabled periodic task(s) in DB — run celery -A huginn beat "
                "with DatabaseScheduler for schedules to fire"
            ),
        }
    except Exception as exc:
        return {
            "name": "Celery Beat (scheduler)",
            "status": "error",
            "detail": str(exc),
        }


def _run_health_checks() -> list[dict]:
    """Run basic health checks and return results list."""
    checks: list[dict] = []

    # Database
    try:
        from django.db import connection

        connection.ensure_connection()
        checks.append({"name": "Database (PostgreSQL)", "status": "ok", "detail": "Connected"})
    except Exception as exc:
        checks.append({"name": "Database (PostgreSQL)", "status": "error", "detail": str(exc)})

    # Redis / Celery broker
    try:
        from django.core.cache import cache

        cache.set("_health_check", "ok", timeout=5)
        val = cache.get("_health_check")
        if val == "ok":
            checks.append({"name": "Redis (cache/broker)", "status": "ok", "detail": "Connected"})
        else:
            checks.append({"name": "Redis (cache/broker)", "status": "warn", "detail": "Cache miss"})
    except Exception as exc:
        checks.append({"name": "Redis (cache/broker)", "status": "error", "detail": str(exc)})

    checks.append(_celery_workers_check())
    checks.append(_celery_beat_check())

    return checks


def welcome(request):
    """Welcome page showing application health dashboard."""
    checks = _run_health_checks()
    context = {
        "title": "Huginn — Status",
        "status": _aggregate_status(checks),
        "timestamp": datetime.now(),
        "python_version": sys.version.split()[0],
        "django_version": django.__version__,
        "checks": checks,
    }
    logger.info('"event":"welcome_page_loaded","user":"%s"', request.user)
    return render(request, "ui/welcome.html", context)


def health_json(request):
    """JSON health endpoint for monitoring."""
    checks = _run_health_checks()
    status = _aggregate_status(checks)
    payload = {
        "status": status,
        "timestamp": timezone.now().isoformat(),
        "revision": get_deployed_revision(),
        "python_version": sys.version.split()[0],
        "django_version": django.__version__,
        "checks": checks,
    }
    if status == "unhealthy":
        return JsonResponse(payload, status=503)
    return JsonResponse(payload)
