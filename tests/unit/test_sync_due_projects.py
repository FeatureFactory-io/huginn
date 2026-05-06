"""ingestion.sync_due_projects beat fan-out."""

from datetime import timedelta
from unittest.mock import MagicMock, patch

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
