"""Celery application for Huginn."""

import os
from pathlib import Path

# Load .env before Django settings so ANTHROPIC_API_KEY etc. are available in workers.
try:
    from dotenv import load_dotenv

    load_dotenv(Path(__file__).resolve().parent.parent / ".env", override=False)
except ImportError:
    pass

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "huginn.settings.local")

from celery import Celery

app = Celery("huginn")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()
