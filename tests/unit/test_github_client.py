"""Unit tests for GithubClient."""

import json
from unittest.mock import MagicMock, patch
from urllib.error import URLError

import pytest

from ingestion.integrations.github_client import (
    GITHUB_API_BASE,
    GITHUB_API_VERSION,
    GithubClient,
    normalize_github_token,
    validate_github_token,
)


def _resp(body: bytes, link: str = "") -> MagicMock:
    cm = MagicMock()
    enter = cm.__enter__.return_value
    enter.read.return_value = body
    enter.headers = {"link": link}
    return cm


@patch("ingestion.integrations.github_client.urlopen")
def test_verify_token_returns_login(mock_urlopen) -> None:
    pat = "ghp_" + "t" * 36
    mock_urlopen.return_value = _resp(b'{"login":"octocat","name":"Octocat"}')
    client = GithubClient(pat)
    meta = client.verify_token()
    assert meta["login"] == "octocat"
    assert client.base_url == GITHUB_API_BASE


@patch("ingestion.integrations.github_client.urlopen")
def test_request_uses_github_doc_headers(mock_urlopen) -> None:
    pat = "ghp_" + "t" * 36
    mock_urlopen.return_value = _resp(b'{"login":"octocat"}')
    GithubClient(pat).verify_token()
    req = mock_urlopen.call_args[0][0]
    assert req.get_header("Authorization") == f"Bearer {pat}"
    assert req.get_header("Accept") == "application/vnd.github+json"
    assert req.get_header("X-github-api-version") == GITHUB_API_VERSION
    assert req.get_header("User-agent") == "Huginn-GitHub-Integration"


@patch("ingestion.integrations.github_client.urlopen")
def test_list_visible_repos_parses_rows(mock_urlopen) -> None:
    payload = [
        {
            "id": 9001,
            "name": "widget",
            "full_name": "acme/widget",
            "description": "Core API",
            "html_url": "https://github.com/acme/widget",
            "updated_at": "2026-05-06T10:00:00Z",
        }
    ]
    mock_urlopen.return_value = _resp(json.dumps(payload).encode())
    client = GithubClient("ghp_" + "t" * 36)
    rows = client.list_visible_repos()
    assert len(rows) == 1
    assert rows[0]["full_name"] == "acme/widget"


@patch("ingestion.integrations.github_client.urlopen")
def test_network_error_wrapped(mock_urlopen) -> None:
    mock_urlopen.side_effect = URLError("network down")
    client = GithubClient("ghp_" + "t" * 36)
    with pytest.raises(ConnectionError, match="GitHub"):
        client.verify_token()


def test_normalize_github_token_strips_auth_prefix_only() -> None:
    pat = "ghp_" + "a" * 36
    assert normalize_github_token(f"Bearer {pat}") == pat
    assert normalize_github_token(f"token {pat}") == pat
    assert normalize_github_token(f'  "{pat}"  ') == pat


def test_validate_github_token_rejects_truncated_classic_pat() -> None:
    with pytest.raises(ValueError, match="truncated"):
        validate_github_token("ghp_" + "a" * 10)


def test_normalize_github_token_strips_em_dash_from_classic_pat() -> None:
    body = "a" * 36
    corrupted = f"ghp_{body[:18]}\u2014{body[18:]}"
    assert normalize_github_token(corrupted) == f"ghp_{body}"
    assert normalize_github_token(f"Bearer ghp_{body} — save this") == f"ghp_{body}"
