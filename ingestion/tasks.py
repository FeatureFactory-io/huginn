"""Celery tasks for ingestion."""

from __future__ import annotations

from datetime import timedelta

from celery import shared_task
from django.utils import timezone

from ingestion.models import Project
from ingestion.services.sync_engine import SyncEngine
from ingestion.signals import sync_project_completed


@shared_task(name="ingestion.sync_project")
def sync_project(project_id: int) -> None:
    """Run :class:`~ingestion.services.sync_engine.SyncEngine` for one project."""
    SyncEngine().run_for_project(project_id)
    try:
        project = Project.objects.get(pk=project_id)
        sync_project_completed.send(
            sender=SyncEngine,
            project=project,
            to_dt=timezone.now(),
        )
    except Exception:  # noqa: BLE001
        pass


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
