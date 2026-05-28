"""Unit tests for GithubCommitAdapter."""

from datetime import UTC, datetime
from unittest.mock import patch

import pytest

from ingestion.adapters.github_commits import GithubCommitAdapter
from ingestion.models import DataSource
from tests.factories import DataSourceFactory, ProjectFactory


@pytest.mark.django_db
@patch("ingestion.adapters.github_commits.github_client_for")
def test_fetch_increments_yields_commit_dto(mock_client_for) -> None:
    ds = DataSourceFactory(datasource_type=DataSource.Type.GITHUB, base_url="https://api.github.com")
    project = ProjectFactory(datasource=ds, external_project_id=9001, source_path="acme/widget")
    commit = {
        "sha": "abc123",
        "html_url": "https://github.com/acme/widget/commit/abc123",
        "commit": {
            "message": "feat: add widget",
            "author": {"name": "Dev", "email": "dev@example.com", "date": "2026-05-06T10:00:00Z"},
        },
        "author": {"login": "dev"},
    }
    client = mock_client_for.return_value
    client.list_commits.return_value = [commit]

    adapter = GithubCommitAdapter(ds)
    since = datetime(2026, 5, 1, tzinfo=UTC)
    rows = list(adapter.fetch_increments(project, since=since))

    assert len(rows) == 1
    assert rows[0].external_id == "abc123"
    assert rows[0].contributor.email == "dev@example.com"
