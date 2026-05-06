"""Unit tests for GitlabClient (HTTP via urllib)."""

from unittest.mock import MagicMock, patch

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


@patch("urllib.request.urlopen")
def test_get_visible_project_count_reads_header(mock_urlopen) -> None:
    mock_urlopen.side_effect = _mock_urlopen_chain(b'{"username":"alpha"}', {"X-Total": "12"})
    client = GitlabClient("https://gitlab.example.com", "glpat-x")
    assert client.verify_token()["username"] == "alpha"
    assert client.get_visible_project_count() == 12


@patch("urllib.request.urlopen")
def test_get_visible_project_count_missing_header_zero(mock_urlopen) -> None:
    mock_urlopen.side_effect = _mock_urlopen_chain(b'{"username":"beta"}', {})
    client = GitlabClient("https://gitlab.example.com", "glpat-x")
    client.verify_token()
    assert client.get_visible_project_count() == 0


@patch("urllib.request.urlopen")
def test_get_visible_project_count_lowercase_header(mock_urlopen) -> None:
    mock_urlopen.side_effect = _mock_urlopen_chain(b"{}", {"x-total": "9"})
    client = GitlabClient("https://gitlab.example.com", "glpat-x")
    client.verify_token()
    assert client.get_visible_project_count() == 9
