"""ProjectsService configuration updates."""

import pytest

from ingestion.models import Project
from tests.factories import ProjectFactory
from ui.services.projects_service import ProjectsService


@pytest.mark.django_db
def test_update_sets_daily_hour() -> None:
    p = ProjectFactory(sync_schedule=Project.SyncSchedule.DAILY)
    ProjectsService().update_project_configuration(
        p.pk,
        sync_schedule=Project.SyncSchedule.DAILY,
        sync_daily_hour="8",
    )
    p.refresh_from_db()
    assert p.sync_daily_hour == 8


@pytest.mark.django_db
def test_update_clears_daily_hour_when_not_daily() -> None:
    p = ProjectFactory(
        sync_schedule=Project.SyncSchedule.DAILY,
        sync_daily_hour=8,
    )
    ProjectsService().update_project_configuration(
        p.pk,
        sync_schedule=Project.SyncSchedule.HOURLY,
    )
    p.refresh_from_db()
    assert p.sync_schedule == Project.SyncSchedule.HOURLY
    assert p.sync_daily_hour is None


@pytest.mark.django_db
def test_update_sets_weekly_fields() -> None:
    p = ProjectFactory()
    ProjectsService().update_project_configuration(
        p.pk,
        sync_schedule=Project.SyncSchedule.WEEKLY,
        sync_weekly_day="3",
        sync_weekly_hour="9",
    )
    p.refresh_from_db()
    assert p.sync_schedule == Project.SyncSchedule.WEEKLY
    assert p.sync_weekly_day == 3
    assert p.sync_weekly_hour == 9


@pytest.mark.django_db
def test_update_clears_weekly_fields_when_not_weekly() -> None:
    p = ProjectFactory(
        sync_schedule=Project.SyncSchedule.WEEKLY,
        sync_weekly_day=3,
        sync_weekly_hour=9,
    )
    ProjectsService().update_project_configuration(
        p.pk,
        sync_schedule=Project.SyncSchedule.DAILY,
    )
    p.refresh_from_db()
    assert p.sync_schedule == Project.SyncSchedule.DAILY
    assert p.sync_weekly_day is None
    assert p.sync_weekly_hour is None


@pytest.mark.django_db
def test_update_weekly_rejects_invalid_day() -> None:
    p = ProjectFactory(sync_schedule=Project.SyncSchedule.HOURLY)
    ProjectsService().update_project_configuration(
        p.pk,
        sync_schedule=Project.SyncSchedule.WEEKLY,
        sync_weekly_day="7",
        sync_weekly_hour="9",
    )
    p.refresh_from_db()
    assert p.sync_schedule == Project.SyncSchedule.HOURLY
    assert p.sync_weekly_day is None
    assert p.sync_weekly_hour is None
