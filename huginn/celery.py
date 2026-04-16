"""Celery application for Huginn."""

import os

from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "huginn.settings.local")

app = Celery("huginn")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()
