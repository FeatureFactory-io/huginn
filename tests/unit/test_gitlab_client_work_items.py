"""GitLab client work-item API tests."""

import json
from unittest.mock import MagicMock, patch
from urllib.error import HTTPError

import pytest
from django.utils import timezone

from ingestion.integrations.gitlab_client import GitlabClient


@pytest.fixture()
def client() -> GitlabClient:
    return GitlabClient("https://gitlab.example.com", "test-token")


def _resp_cm(body: bytes, headers: dict | None = None):
    cm = MagicMock()
    enter = cm.__enter__.return_value
    enter.read.return_value = body
    enter.headers = headers or {"X-Next-Page": ""}
    return cm


@patch("ingestion.integrations.gitlab_client.urlopen")
def test_list_issues_pagination(mock_urlopen, client: GitlabClient) -> None:
    mock_urlopen.return_value = _resp_cm(json.dumps([{"id": 10, "iid": 1, "title": "Bug", "state": "opened"}]).encode())
    items = client.list_issues(1, updated_after=timezone.now())
    assert len(items) == 1
    assert items[0]["id"] == 10
    req = mock_urlopen.call_args[0][0]
    url_str = getattr(req, "full_url", str(req))
    assert "updated_after=" in url_str


@patch("ingestion.integrations.gitlab_client.urlopen")
def test_list_milestones(mock_urlopen, client: GitlabClient) -> None:
    mock_urlopen.return_value = _resp_cm(
        json.dumps([{"id": 5, "title": "v1", "state": "active", "updated_at": "2026-05-01T00:00:00Z"}]).encode()
    )
    items = client.list_milestones(2)
    assert items[0]["title"] == "v1"


@patch("ingestion.integrations.gitlab_client.urlopen")
def test_list_merge_requests_http_error(mock_urlopen, client: GitlabClient) -> None:
    mock_urlopen.side_effect = HTTPError(
        "https://gitlab.example.com/api/v4/projects/3/merge_requests",
        401,
        "Unauthorized",
        hdrs=None,
        fp=None,
    )
    with pytest.raises(ConnectionError, match="401"):
        client.list_merge_requests(3)
