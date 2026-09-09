"""sync_project task must not emit sitrep signal on failed/skipped/empty runs."""

from datetime import timedelta
from unittest.mock import MagicMock, patch

import pytest
from django.utils import timezone

from ingestion.models import IngestionRun, Project
from ingestion.services.sync_engine import SyncEngine
from ingestion.tasks import sync_project
from tests.factories import DataSourceFactory, ProjectFactory


@pytest.mark.django_db
@patch("ingestion.services.sync_engine.sync_project_completed.send")
@patch("gjallarhorn.tasks.sitrep_tasks.generate_sitrep_for_project.delay")
def test_sync_project_does_not_enqueue_sitrep_when_sync_errors(
    mock_generate_delay: MagicMock,
    mock_signal_send: MagicMock,
) -> None:
    ds = DataSourceFactory(encrypted_token_ciphertext="")
    p = ProjectFactory(datasource=ds, external_project_id=42)

    sync_project(p.pk)

    mock_signal_send.assert_not_called()
    mock_generate_delay.assert_not_called()
    p.refresh_from_db()
    assert p.sync_state == Project.SyncState.ERROR


@pytest.mark.django_db
@patch("gjallarhorn.tasks.sitrep_tasks.generate_sitrep_for_project.delay")
def test_sync_project_enqueues_sitrep_only_on_successful_engine_run(
    mock_generate_delay: MagicMock,
) -> None:
    ds = DataSourceFactory(base_url="https://gitlab.example.com", encrypted_token_ciphertext="glpat-x")
    p = ProjectFactory(
        datasource=ds,
        external_project_id=42,
        sync_state=Project.SyncState.SYNCING,
    )
    commit = {
        "id": "abc123def456",
        "title": "hello",
        "committed_date": (timezone.now() - timedelta(hours=2)).isoformat(),
        "author": {"name": "Bob", "email": "bob@example.com"},
        "web_url": "https://gitlab.example.com/c/abc123def456",
    }
    with (
        patch(
            "ingestion.integrations.gitlab_client.GitlabClient.list_milestones",
            return_value=[],
        ),
        patch(
            "ingestion.integrations.gitlab_client.GitlabClient.list_issues",
            return_value=[],
        ),
        patch(
            "ingestion.integrations.gitlab_client.GitlabClient.list_merge_requests",
            return_value=[],
        ),
        patch(
            "ingestion.adapters.gitlab_commits.GitlabClient.list_branch_names",
            return_value=["main"],
        ),
        patch(
            "ingestion.adapters.gitlab_commits.GitlabClient.list_commits",
            return_value=[commit],
        ),
    ):
        sync_project(p.pk)

    mock_generate_delay.assert_called_once()


@pytest.mark.django_db
@patch("ingestion.services.sync_engine.sync_project_completed.send")
def test_empty_successful_sync_still_emits_sitrep_signal(
    mock_signal_send: MagicMock,
) -> None:
    """SITREP-GEN-01: successful sync always fires sync_project_completed, even with zero rows."""
    ds = DataSourceFactory()
    p = ProjectFactory(datasource=ds, external_project_id=1)
    engine = SyncEngine(
        classes_for=lambda _t: [],
        work_classes_for=lambda _t: [],
        milestone_classes_for=lambda _t: [],
    )

    run = engine.run_for_project(p.pk)

    assert run is not None
    assert run.status == IngestionRun.Status.SUCCESS
    assert run.increments_ingested == 0
    assert run.work_items_ingested == 0
    assert run.milestones_ingested == 0
    mock_signal_send.assert_called_once()
    call_kwargs = mock_signal_send.call_args.kwargs
    assert call_kwargs["project"].pk == p.pk
    assert call_kwargs["to_dt"] is not None
