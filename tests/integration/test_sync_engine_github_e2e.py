"""GitHub sync engine end-to-end with HTTP mocked at client layer."""

from unittest.mock import patch

import pytest

from ingestion.models import Increment, Milestone, Project, UnitOfWork
from ingestion.tasks import sync_project
from tests.factories import DataSourceFactory, ProjectFactory
from tests.integration.github_test_mocks import github_catalog_urlopen_side_effect


@pytest.mark.django_db
@patch("ingestion.integrations.github_client.urlopen")
def test_github_sync_ingests_commits_issues_prs_milestones(mock_urlopen) -> None:
    ds = DataSourceFactory(
        datasource_type="github",
        base_url="https://api.github.com",
        encrypted_token_ciphertext="ghp-x",
    )
    project = ProjectFactory(
        datasource=ds,
        external_project_id=9001,
        source_path="acme/widget",
        sync_state=Project.SyncState.SYNCING,
    )
    mock_urlopen.side_effect = github_catalog_urlopen_side_effect(
        [],
        commits=[
            {
                "sha": "deadbeef",
                "html_url": "https://github.com/acme/widget/commit/deadbeef",
                "commit": {
                    "message": "fix: bug",
                    "author": {"name": "Dev", "email": "dev@example.com", "date": "2026-05-06T10:00:00Z"},
                },
            }
        ],
        issues=[
            {
                "id": 101,
                "number": 7,
                "title": "Bug",
                "state": "open",
                "created_at": "2026-05-06T09:00:00Z",
                "updated_at": "2026-05-06T10:00:00Z",
                "user": {"login": "dev"},
            }
        ],
        pull_requests=[
            {
                "id": 202,
                "number": 3,
                "title": "Feature PR",
                "state": "open",
                "created_at": "2026-05-06T09:00:00Z",
                "updated_at": "2026-05-06T10:00:00Z",
                "user": {"login": "dev"},
                "head": {"ref": "feature"},
                "base": {"ref": "main"},
            }
        ],
        milestones=[
            {
                "id": 303,
                "title": "v1.0",
                "state": "open",
                "updated_at": "2026-05-06T10:00:00Z",
            }
        ],
    )

    sync_project(project.pk)

    project.refresh_from_db()
    assert project.sync_state == Project.SyncState.ACTIVE
    assert Increment.objects.filter(project=project, external_id="deadbeef").exists()
    assert UnitOfWork.objects.filter(project=project, kind=UnitOfWork.Kind.ISSUE).exists()
    assert UnitOfWork.objects.filter(project=project, kind=UnitOfWork.Kind.MERGE_REQUEST).exists()
    assert Milestone.objects.filter(project=project, external_id="303").exists()
