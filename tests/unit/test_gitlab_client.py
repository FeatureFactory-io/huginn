"""Unit tests for GitlabClient (HTTP via urllib)."""

import json
from unittest.mock import MagicMock, patch
from urllib.error import URLError

import pytest

from ingestion.integrations.gitlab_client import GitlabClient


def _mock_urlopen_chain(user_body: bytes, project_headers: dict | None = None):
    if project_headers is None:
        project_headers = {"X-Total": "4"}
    calls = [
        (user_body, {}),
        (b"[]", project_headers),
    ]
    idx = {"n": 0}

    def _fake(req, timeout=10):
        if idx["n"] >= len(calls):
            raise AssertionError("unexpected urlopen call")
        body, hdrs = calls[idx["n"]]
        idx["n"] += 1
        cm = MagicMock()
        enter = cm.__enter__.return_value
        enter.read.return_value = body
        enter.headers = hdrs
        return cm

    return _fake


@patch("ingestion.integrations.gitlab_client.urlopen")
def test_get_visible_project_count_reads_header(mock_urlopen) -> None:
    mock_urlopen.side_effect = _mock_urlopen_chain(b'{"username":"alpha"}', {"X-Total": "12"})
    client = GitlabClient("https://gitlab.example.com", "glpat-x")
    assert client.verify_token()["username"] == "alpha"
    assert client.get_visible_project_count() == 12


@patch("ingestion.integrations.gitlab_client.urlopen")
def test_get_visible_project_count_missing_header_zero(mock_urlopen) -> None:
    mock_urlopen.side_effect = _mock_urlopen_chain(b'{"username":"beta"}', {})
    client = GitlabClient("https://gitlab.example.com", "glpat-x")
    client.verify_token()
    assert client.get_visible_project_count() == 0


@patch("ingestion.integrations.gitlab_client.urlopen")
def test_get_visible_project_count_lowercase_header(mock_urlopen) -> None:
    mock_urlopen.side_effect = _mock_urlopen_chain(b"{}", {"x-total": "9"})
    client = GitlabClient("https://gitlab.example.com", "glpat-x")
    client.verify_token()
    assert client.get_visible_project_count() == 9


def _resp_cm(body: bytes, headers: dict | None = None):
    cm = MagicMock()
    enter = cm.__enter__.return_value
    enter.read.return_value = body
    enter.headers = headers or {}
    return cm


@patch("ingestion.integrations.gitlab_client.urlopen")
def test_list_visible_projects_empty_when_blank_token_raises(mock_urlopen) -> None:
    client = GitlabClient("https://gitlab.example.com", "")
    with pytest.raises(ValueError, match="blank"):
        client.list_visible_projects()
    mock_urlopen.assert_not_called()


@patch("ingestion.integrations.gitlab_client.urlopen")
def test_list_visible_projects_connection_error_wrapped(mock_urlopen) -> None:
    mock_urlopen.side_effect = URLError("nodename nor servname")
    client = GitlabClient("https://gitlab.example.com", "glpat-x")
    with pytest.raises(ConnectionError, match="reach GitLab"):
        client.list_visible_projects()


@patch("ingestion.integrations.gitlab_client.urlopen")
def test_list_visible_projects_paginates(mock_urlopen) -> None:
    p1 = [{"id": 1, "name": "A", "path_with_namespace": "g/a", "description": None, "web_url": ""}]
    p2 = [{"id": 2, "name": "B", "path_with_namespace": "g/b", "description": None, "web_url": ""}]
    mock_urlopen.side_effect = [
        _resp_cm(json.dumps(p1).encode(), {"X-Next-Page": "2"}),
        _resp_cm(json.dumps(p2).encode(), {}),
    ]
    client = GitlabClient("https://gitlab.example.com", "glpat-x")
    rows = client.list_visible_projects(per_page=1, max_pages=10)
    assert [r["id"] for r in rows] == [1, 2]
    assert mock_urlopen.call_count == 2


@patch("ingestion.integrations.gitlab_client.urlopen")
def test_list_branch_names_collects_names(mock_urlopen) -> None:
    body = [{"name": "main"}, {"name": "develop"}]
    mock_urlopen.return_value = _resp_cm(json.dumps(body).encode(), {})
    client = GitlabClient("https://gitlab.example.com", "glpat-x")
    assert client.list_branch_names(42) == ["main", "develop"]


@patch("ingestion.integrations.gitlab_client.urlopen")
def test_list_commits_passes_since_iso(mock_urlopen) -> None:
    from datetime import UTC, datetime

    commits = [{"id": "a", "title": "t", "committed_date": "2026-05-01T00:00:00Z"}]
    mock_urlopen.return_value = _resp_cm(json.dumps(commits).encode(), {})
    client = GitlabClient("https://gitlab.example.com", "glpat-x")
    since = datetime(2026, 4, 1, tzinfo=UTC)
    out = client.list_commits(7, ref_name="main", since=since, max_pages=1)
    assert len(out) == 1
    req = mock_urlopen.call_args[0][0]
    url_str = getattr(req, "full_url", str(req))
    assert "ref_name=main" in url_str
    assert "since=" in url_str
