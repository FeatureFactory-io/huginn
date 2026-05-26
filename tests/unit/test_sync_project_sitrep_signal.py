"""sync_project task must not emit sitrep signal on failed/skipped runs."""

from unittest.mock import MagicMock, patch

import pytest

from ingestion.models import Project
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
    p = ProjectFactory(datasource=ds, gitlab_project_id=42)

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
        gitlab_project_id=42,
        sync_state=Project.SyncState.SYNCING,
    )
    commit = {
        "id": "abc123def456",
        "title": "hello",
        "committed_date": "2026-05-06T10:00:00+00:00",
        "author": {"name": "Bob", "email": "bob@example.com"},
        "web_url": "https://gitlab.example.com/c/abc123def456",
    }
    with (
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
