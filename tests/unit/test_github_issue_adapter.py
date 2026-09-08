"""Unit tests for GithubIssueAdapter since-cursor filtering."""

from datetime import UTC, datetime
from unittest.mock import patch

import pytest

from ingestion.adapters.github_issues import GithubIssueAdapter
from ingestion.models import DataSource
from tests.factories import DataSourceFactory, ProjectFactory


@pytest.mark.django_db
@patch("ingestion.adapters.github_issues.github_client_for")
def test_fetch_work_items_skips_issue_at_since_cursor(mock_client_for) -> None:
    """A dump cursor must be exclusive so the last ingested issue is not re-counted."""
    ds = DataSourceFactory(datasource_type=DataSource.Type.GITHUB, base_url="https://api.github.com")
    project = ProjectFactory(datasource=ds, external_project_id=9001, source_path="acme/widget")
    cursor = datetime(2026, 8, 28, 21, 9, 32, tzinfo=UTC)
    issue = {
        "id": 5279645026,
        "number": 177,
        "title": "Already ingested at cursor",
        "state": "closed",
        "updated_at": "2026-08-28T21:09:32Z",
        "created_at": "2026-08-28T20:00:00Z",
        "html_url": "https://github.com/acme/widget/issues/177",
        "body": "",
        "labels": [],
    }
    client = mock_client_for.return_value
    client.list_issues.return_value = [issue]

    adapter = GithubIssueAdapter(ds)
    rows = list(adapter.fetch_work_items(project, since=cursor))

    assert rows == []
