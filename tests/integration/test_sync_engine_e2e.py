"""End-to-end sync task with GitLab HTTP mocked at the client layer."""

from unittest.mock import patch

import pytest

from ingestion.models import Increment, Project
from ingestion.tasks import sync_project
from tests.factories import DataSourceFactory, ProjectFactory


@pytest.mark.django_db
def test_sync_project_task_writes_increment_when_gitlab_returns_commit() -> None:
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

    p.refresh_from_db()
    assert p.sync_state == Project.SyncState.ACTIVE
    assert Increment.objects.filter(project=p, external_id="abc123def456").exists()
