"""Health check views."""

import logging
import sys
from datetime import datetime

import django
from django.http import JsonResponse
from django.shortcuts import render

logger = logging.getLogger(__name__)


def welcome(request):
    """Welcome page showing application health dashboard."""
    context = {
        "title": "Huginn — Status",
        "status": "healthy",
        "timestamp": datetime.now(),
        "python_version": sys.version.split()[0],
        "django_version": django.__version__,
        "checks": _run_health_checks(),
    }
    logger.info('"event":"welcome_page_loaded","user":"%s"', request.user)
    return render(request, "ui/welcome.html", context)


def health_json(request):
    """JSON health endpoint for monitoring."""
    return JsonResponse(
        {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "python_version": sys.version.split()[0],
            "django_version": django.__version__,
        }
    )


def _run_health_checks() -> list[dict]:
    """Run basic health checks and return results list."""
    checks = []

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

    return checks
