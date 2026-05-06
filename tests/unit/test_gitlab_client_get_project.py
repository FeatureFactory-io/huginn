"""Unit tests for ``GitlabClient.get_project``."""

import json
from io import BytesIO
from unittest.mock import MagicMock, patch
from urllib.error import HTTPError, URLError
from urllib.request import Request

import pytest

from ingestion.integrations.gitlab_client import GitlabClient


def _make_resp(body: dict | bytes):
    cm = MagicMock()
    enter = cm.__enter__.return_value
    enter.read.return_value = body if isinstance(body, bytes) else json.dumps(body).encode()
    return cm


@pytest.mark.parametrize(
    ("body", "want_desc"),
    [
        (
            {
                "id": 42,
                "name": "x",
                "description": "hello",
                "web_url": "https://gitlab.example.com/g/x",
                "path_with_namespace": "g/x",
            },
            "hello",
        ),
    ],
)
def test_gitlab_client_get_project_returns_description(body: dict, want_desc: str) -> None:
    client = GitlabClient("https://gitlab.example.com/", "glpat-x")
    with patch("ingestion.integrations.gitlab_client.urlopen", return_value=_make_resp(body)) as mocked:
        out = client.get_project(42)
    assert out["description"] == want_desc
    assert out["web_url"].startswith("https://")

    mocked.assert_called_once()
    req_arg = mocked.call_args[0][0]
    assert isinstance(req_arg, Request)
    assert req_arg.full_url == "https://gitlab.example.com/api/v4/projects/42"


def test_gitlab_client_get_project_truncates_long_description() -> None:
    body = {
        "id": 7,
        "name": "n",
        "description": "a" * 600,
        "web_url": "",
        "path_with_namespace": "",
    }
    client = GitlabClient("https://gitlab.example.com/", "y")
    with patch("ingestion.integrations.gitlab_client.urlopen", return_value=_make_resp(body)):
        out = client.get_project(7)
    assert len(out["description"]) == 501  # 500 + ellipsis
    assert out["description"].startswith("aaa")
    assert out["description"].endswith("…")


def test_gitlab_client_get_project_404_raises_connection_error() -> None:
    client = GitlabClient("https://gitlab.example.com/", "y")
    fp = BytesIO(b"{}")
    err = HTTPError("https://gitlab.example.com/api/v4/projects/9", 404, "NF", hdrs={}, fp=fp)

    def boom(*_a, **_k):
        raise err

    with patch("ingestion.integrations.gitlab_client.urlopen", side_effect=boom):
        with pytest.raises(ConnectionError):
            client.get_project(9)


def test_gitlab_client_get_project_urlerror_raises_connection_error() -> None:
    client = GitlabClient("https://gitlab.example.com/", "y")

    with patch(
        "ingestion.integrations.gitlab_client.urlopen",
        side_effect=URLError("gone"),
    ):
        with pytest.raises(ConnectionError):
            client.get_project(1)


def test_gitlab_client_get_project_rejects_blank_token() -> None:
    client = GitlabClient("https://gitlab.example.com/", " ")
    with pytest.raises(ValueError):
        client.get_project(1)
