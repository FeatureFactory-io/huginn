"""Celery tasks for ingestion."""

from __future__ import annotations

import logging
from datetime import timedelta

from celery import shared_task
from django.utils import timezone

from ingestion.models import Project
from ingestion.services.sync_engine import SyncEngine

logger = logging.getLogger("ingestion.tasks")


@shared_task(name="ingestion.sync_project")
def sync_project(project_id: int) -> None:
    """Run :class:`~ingestion.services.sync_engine.SyncEngine` for one project."""
    logger.info("sync_project task start project_id=%s", project_id)
    run = SyncEngine().run_for_project(project_id)
    if run is None:
        logger.info("sync_project task finished project_id=%s result=skipped", project_id)
        return
    logger.info(
        "sync_project task finished project_id=%s run_id=%s status=%s increments=%s work_items=%s milestones=%s",
        project_id,
        run.pk,
        run.status,
        run.increments_ingested,
        run.work_items_ingested,
        run.milestones_ingested,
    )


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
    schedule = project.sync_schedule
    if schedule == Project.SyncSchedule.MANUAL:
        return False
    if project.last_sync_at is None:
        if schedule == Project.SyncSchedule.DAILY and project.sync_daily_hour is not None:
            return now.hour == project.sync_daily_hour
        if schedule == Project.SyncSchedule.WEEKLY:
            if project.sync_weekly_day is None or project.sync_weekly_hour is None:
                return False
            return now.weekday() == project.sync_weekly_day and now.hour == project.sync_weekly_hour
        return True
    delta = now - project.last_sync_at
    if schedule == Project.SyncSchedule.HOURLY:
        return delta >= timedelta(hours=1)
    if schedule == Project.SyncSchedule.EVERY_6H:
        return delta >= timedelta(hours=6)
    if schedule == Project.SyncSchedule.DAILY:
        if project.sync_daily_hour is not None:
            return now.hour == project.sync_daily_hour and delta >= timedelta(hours=23)
        return delta >= timedelta(days=1)
    if schedule == Project.SyncSchedule.WEEKLY:
        if project.sync_weekly_day is None or project.sync_weekly_hour is None:
            return False
        return (
            now.weekday() == project.sync_weekly_day
            and now.hour == project.sync_weekly_hour
            and delta >= timedelta(days=6, hours=23)
        )
    return True
