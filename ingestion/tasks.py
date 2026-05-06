"""Celery tasks for ingestion."""

from __future__ import annotations

from datetime import timedelta

from celery import shared_task
from django.utils import timezone

from ingestion.models import Project
from ingestion.services.sync_engine import SyncEngine


@shared_task(name="ingestion.sync_project")
def sync_project(project_id: int) -> None:
    """Run :class:`~ingestion.services.sync_engine.SyncEngine` for one project."""
    SyncEngine().run_for_project(project_id)


@shared_task(name="ingestion.sync_project_placeholder")
def sync_project_placeholder(project_id: int) -> None:
    """Deprecated name — delegating to :func:`sync_project`."""
    sync_project(project_id)


@shared_task(name="ingestion.sync_due_projects")
def sync_due_projects() -> None:
    """Enqueue :func:`sync_project` for each active project that is due per its schedule."""
    now = timezone.now()
    qs = Project.objects.filter(status=Project.Status.ACTIVE).select_related("datasource")
    for project in qs.iterator():
        if _project_sync_due(project, now):
            sync_project.delay(project.pk)


def _project_sync_due(project: Project, now) -> bool:
    if project.last_sync_at is None:
        return True
    delta = now - project.last_sync_at
    if project.sync_schedule == Project.SyncSchedule.HOURLY:
        return delta >= timedelta(hours=1)
    if project.sync_schedule == Project.SyncSchedule.EVERY_6H:
        return delta >= timedelta(hours=6)
    if project.sync_schedule == Project.SyncSchedule.DAILY:
        return delta >= timedelta(days=1)
    return True
