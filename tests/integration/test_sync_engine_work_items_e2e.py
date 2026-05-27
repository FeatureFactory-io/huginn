"""SyncEngine end-to-end with GitLab work-item HTTP mocks."""

from unittest.mock import patch

import pytest
from django.utils import timezone

from ingestion.models import Milestone, UnitOfWork
from ingestion.services.sync_engine import SyncEngine
from tests.factories import DataSourceFactory, ProjectFactory
from tests.integration.gitlab_test_mocks import gitlab_work_items_sync_urlopen_side_effect


def _register_gitlab_adapters() -> None:
    import ingestion.adapters.gitlab_commits  # noqa: F401
    import ingestion.adapters.gitlab_issues  # noqa: F401
    import ingestion.adapters.gitlab_merge_requests  # noqa: F401
    import ingestion.adapters.gitlab_milestones  # noqa: F401


@pytest.mark.django_db
@patch("ingestion.integrations.gitlab_client.urlopen")
def test_sync_engine_work_items_e2e(mock_urlopen) -> None:
    _register_gitlab_adapters()
    ds = DataSourceFactory(base_url="https://gitlab.example.com", encrypted_token_ciphertext="tok")
    project = ProjectFactory(datasource=ds, gitlab_project_id=99)
    now = timezone.now().isoformat()

    mock_urlopen.side_effect = gitlab_work_items_sync_urlopen_side_effect(
        milestones=[{"id": 7, "title": "Release 1", "state": "active", "updated_at": now}],
        issues=[
            {
                "id": 101,
                "iid": 3,
                "title": "Fix login",
                "state": "opened",
                "labels": ["bug"],
                "created_at": now,
                "updated_at": now,
                "web_url": "https://gitlab.example.com/p/-/issues/3",
            }
        ],
        merge_requests=[
            {
                "id": 202,
                "iid": 8,
                "title": "Feature branch",
                "state": "merged",
                "author": {"email": "dev@example.com", "name": "Dev"},
                "created_at": now,
                "updated_at": now,
                "merged_at": now,
                "web_url": "https://gitlab.example.com/p/-/merge_requests/8",
                "source_branch": "feat",
                "target_branch": "main",
            }
        ],
    )

    run = SyncEngine().run_for_project(project.pk)
    assert run is not None
    assert run.status == "success"
    assert run.milestones_ingested == 1
    assert run.work_items_ingested == 2
    assert Milestone.objects.filter(project=project).count() == 1
    assert UnitOfWork.objects.filter(project=project, kind="issue").count() == 1
    assert UnitOfWork.objects.filter(project=project, kind="merge_request").count() == 1
