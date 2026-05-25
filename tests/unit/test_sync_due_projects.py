"""ingestion.sync_due_projects beat fan-out."""

from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch
from zoneinfo import ZoneInfo

import pytest
from django.utils import timezone

from ingestion.models import Project
from ingestion.tasks import sync_due_projects
from tests.factories import ProjectFactory


@pytest.mark.django_db
@patch("ingestion.tasks.sync_project.delay")
def test_sync_due_enqueues_when_hourly_elapsed(mock_delay: MagicMock) -> None:
    p = ProjectFactory(
        sync_schedule=Project.SyncSchedule.HOURLY,
        last_sync_at=timezone.now() - timedelta(hours=2),
        status=Project.Status.ACTIVE,
    )
    sync_due_projects()
    mock_delay.assert_called_once_with(p.pk)


@pytest.mark.django_db
@patch("ingestion.tasks.sync_project.delay")
def test_sync_due_skips_when_daily_not_due(mock_delay: MagicMock) -> None:
    ProjectFactory(
        sync_schedule=Project.SyncSchedule.DAILY,
        last_sync_at=timezone.now() - timedelta(hours=12),
        status=Project.Status.ACTIVE,
    )
    sync_due_projects()
    mock_delay.assert_not_called()


@pytest.mark.django_db
@patch("ingestion.tasks.sync_project.delay")
def test_sync_due_enqueues_when_never_synced(mock_delay: MagicMock) -> None:
    p = ProjectFactory(
        sync_schedule=Project.SyncSchedule.HOURLY,
        last_sync_at=None,
        status=Project.Status.ACTIVE,
    )
    sync_due_projects()
    mock_delay.assert_called_once_with(p.pk)


@pytest.mark.django_db
@patch("ingestion.tasks.sync_project.delay")
def test_manual_never_due(mock_delay: MagicMock) -> None:
    ProjectFactory(
        sync_schedule=Project.SyncSchedule.MANUAL,
        last_sync_at=timezone.now() - timedelta(hours=2),
        status=Project.Status.ACTIVE,
    )
    sync_due_projects()
    mock_delay.assert_not_called()


@pytest.mark.django_db
@patch("ingestion.tasks.sync_project.delay")
@patch("ingestion.tasks.timezone.now")
def test_daily_with_hour_due_at_correct_hour(mock_now: MagicMock, mock_delay: MagicMock) -> None:
    fixed_now = datetime(2026, 5, 20, 9, 30, tzinfo=ZoneInfo("UTC"))
    mock_now.return_value = fixed_now
    p = ProjectFactory(
        sync_schedule=Project.SyncSchedule.DAILY,
        sync_daily_hour=9,
        last_sync_at=fixed_now - timedelta(hours=25),
        status=Project.Status.ACTIVE,
    )
    sync_due_projects()
    mock_delay.assert_called_once_with(p.pk)


@pytest.mark.django_db
@patch("ingestion.tasks.sync_project.delay")
@patch("ingestion.tasks.timezone.now")
def test_daily_with_hour_skipped_at_wrong_hour(mock_now: MagicMock, mock_delay: MagicMock) -> None:
    fixed_now = datetime(2026, 5, 20, 10, 30, tzinfo=ZoneInfo("UTC"))
    mock_now.return_value = fixed_now
    ProjectFactory(
        sync_schedule=Project.SyncSchedule.DAILY,
        sync_daily_hour=9,
        last_sync_at=fixed_now - timedelta(hours=25),
        status=Project.Status.ACTIVE,
    )
    sync_due_projects()
    mock_delay.assert_not_called()


@pytest.mark.django_db
@patch("ingestion.tasks.sync_project.delay")
def test_daily_without_hour_due_after_24h(mock_delay: MagicMock) -> None:
    p = ProjectFactory(
        sync_schedule=Project.SyncSchedule.DAILY,
        sync_daily_hour=None,
        last_sync_at=timezone.now() - timedelta(hours=25),
        status=Project.Status.ACTIVE,
    )
    sync_due_projects()
    mock_delay.assert_called_once_with(p.pk)


@pytest.mark.django_db
@patch("ingestion.tasks.sync_project.delay")
@patch("ingestion.tasks.timezone.now")
def test_weekly_due_on_matching_day_and_hour(mock_now: MagicMock, mock_delay: MagicMock) -> None:
    fixed_now = datetime(2026, 5, 20, 9, 30, tzinfo=ZoneInfo("UTC"))
    mock_now.return_value = fixed_now
    p = ProjectFactory(
        sync_schedule=Project.SyncSchedule.WEEKLY,
        sync_weekly_day=2,
        sync_weekly_hour=9,
        last_sync_at=fixed_now - timedelta(days=7),
        status=Project.Status.ACTIVE,
    )
    sync_due_projects()
    mock_delay.assert_called_once_with(p.pk)


@pytest.mark.django_db
@patch("ingestion.tasks.sync_project.delay")
@patch("ingestion.tasks.timezone.now")
def test_weekly_skipped_on_wrong_day(mock_now: MagicMock, mock_delay: MagicMock) -> None:
    fixed_now = datetime(2026, 5, 21, 9, 30, tzinfo=ZoneInfo("UTC"))
    mock_now.return_value = fixed_now
    ProjectFactory(
        sync_schedule=Project.SyncSchedule.WEEKLY,
        sync_weekly_day=2,
        sync_weekly_hour=9,
        last_sync_at=fixed_now - timedelta(days=7),
        status=Project.Status.ACTIVE,
    )
    sync_due_projects()
    mock_delay.assert_not_called()


@pytest.mark.django_db
@patch("ingestion.tasks.sync_project.delay")
def test_weekly_skipped_when_fields_not_set(mock_delay: MagicMock) -> None:
    ProjectFactory(
        sync_schedule=Project.SyncSchedule.WEEKLY,
        sync_weekly_day=None,
        sync_weekly_hour=9,
        last_sync_at=timezone.now() - timedelta(days=7),
        status=Project.Status.ACTIVE,
    )
    sync_due_projects()
    mock_delay.assert_not_called()
