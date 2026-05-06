"""Unit tests for ingestion Celery tasks."""

from unittest.mock import MagicMock, patch

import pytest

from ingestion.models import Project
from ingestion.tasks import sync_project_placeholder
from tests.factories import ProjectFactory
from ui.services.projects_service import ProjectsService


@pytest.mark.django_db
@patch("ingestion.services.sync_engine.adapter_classes_for", lambda _t: [])
def test_sync_placeholder_sets_active_and_last_sync_at() -> None:
    p = ProjectFactory(
        sync_state=Project.SyncState.INITIAL_SYNC_QUEUED,
        last_sync_at=None,
    )
    sync_project_placeholder(p.pk)
    p.refresh_from_db()
    assert p.sync_state == Project.SyncState.ACTIVE
    assert p.last_sync_at is not None


@pytest.mark.django_db
def test_sync_placeholder_skips_archived_project() -> None:
    p = ProjectFactory(
        status=Project.Status.ARCHIVED,
        sync_state=Project.SyncState.INITIAL_SYNC_QUEUED,
        last_sync_at=None,
    )
    sync_project_placeholder(p.pk)
    p.refresh_from_db()
    assert p.sync_state == Project.SyncState.INITIAL_SYNC_QUEUED
    assert p.last_sync_at is None


@pytest.mark.django_db
@patch("ingestion.services.sync_engine.adapter_classes_for", lambda _t: [])
def test_sync_placeholder_preserves_source_path_and_url() -> None:
    p = ProjectFactory(
        sync_state=Project.SyncState.INITIAL_SYNC_QUEUED,
        source_path="acme/demo",
        source_url="https://gitlab.example.com/acme/demo",
    )
    sync_project_placeholder(p.pk)
    p.refresh_from_db()
    assert p.source_path == "acme/demo"
    assert p.source_url == "https://gitlab.example.com/acme/demo"


@pytest.mark.django_db
def test_enqueue_immediate_project_sync_sets_syncing_before_task() -> None:
    p = ProjectFactory(sync_state=Project.SyncState.ACTIVE)
    with patch("ui.services.projects_service.sync_project") as mock_task:
        mock_task.delay = MagicMock()
        ProjectsService().enqueue_immediate_project_sync(p.pk)
    p.refresh_from_db()
    assert p.sync_state == Project.SyncState.SYNCING
    mock_task.delay.assert_called_once_with(p.pk)


@pytest.mark.django_db
@patch("ingestion.services.sync_engine.adapter_classes_for", lambda _t: [])
def test_enqueue_immediate_project_sync_eager_sets_active() -> None:
    """With CELERY_TASK_ALWAYS_EAGER, placeholder runs and ends in ACTIVE."""
    p = ProjectFactory(sync_state=Project.SyncState.ACTIVE)
    ProjectsService().enqueue_immediate_project_sync(p.pk)
    p.refresh_from_db()
    assert p.sync_state == Project.SyncState.ACTIVE
    assert p.last_sync_at is not None
