"""GitHub datasource create wizard integration tests."""

from unittest.mock import MagicMock, patch

import pytest
from django.urls import reverse

from ingestion.integrations.github_client import GITHUB_API_BASE
from ingestion.models import DataSource

_GHP_TEST = "ghp_" + "v" * 36


def _csrf(client) -> str:
    return client.cookies["csrftoken"].value


def _github_urlopen_ok(login: str = "octocat"):
    user_body = f'{{"login":"{login}","name":"{login}"}}'.encode()

    def _fake(req, timeout=10):
        url = getattr(req, "full_url", str(req))
        cm = MagicMock()
        enter = cm.__enter__.return_value
        enter.headers = {"link": ""}
        if "/user/repos" in url:
            enter.read.return_value = b"[]"
        else:
            enter.read.return_value = user_body
        return cm

    return _fake


@pytest.mark.django_db
def test_github_create_select_shows_step_two(commander_client) -> None:
    commander_client.get(reverse("datasources-create"))
    r = commander_client.post(
        reverse("datasources-create"),
        {"csrfmiddlewaretoken": _csrf(commander_client), "type": "github"},
    )
    body = r.content.decode()
    assert "Step 2 of 2" in body
    assert "datasource-type-github" not in body or "GitHub.com" in body
    assert 'data-testid="datasource-github-endpoint"' in body


@pytest.mark.django_db
@patch("ingestion.integrations.github_client.urlopen")
def test_github_create_slugifies_name_with_spaces(mock_urlopen, commander_client) -> None:
    mock_urlopen.side_effect = _github_urlopen_ok()
    commander_client.get(reverse("datasources-create"))
    commander_client.post(
        reverse("datasources-create"),
        {"csrfmiddlewaretoken": _csrf(commander_client), "type": "github"},
    )
    commander_client.post(
        reverse("datasources-create"),
        {
            "csrfmiddlewaretoken": _csrf(commander_client),
            "step": "2",
            "selected_type": "github",
            "name": "FF GH",
            "token": _GHP_TEST,
            "action": "test-connection",
        },
    )
    r = commander_client.post(
        reverse("datasources-create"),
        {
            "csrfmiddlewaretoken": _csrf(commander_client),
            "step": "2",
            "selected_type": "github",
            "name": "FF GH",
            "token": _GHP_TEST,
            "action": "save",
        },
    )
    assert r.status_code == 302
    assert DataSource.objects.filter(name="ff-gh").exists()


@pytest.mark.django_db
@patch("ingestion.integrations.github_client.urlopen")
def test_github_create_test_and_save(mock_urlopen, commander_client) -> None:
    mock_urlopen.side_effect = _github_urlopen_ok()
    commander_client.get(reverse("datasources-create"))
    commander_client.post(
        reverse("datasources-create"),
        {"csrfmiddlewaretoken": _csrf(commander_client), "type": "github"},
    )
    commander_client.post(
        reverse("datasources-create"),
        {
            "csrfmiddlewaretoken": _csrf(commander_client),
            "step": "2",
            "selected_type": "github",
            "name": "company-github",
            "token": _GHP_TEST,
            "action": "test-connection",
        },
    )
    r = commander_client.post(
        reverse("datasources-create"),
        {
            "csrfmiddlewaretoken": _csrf(commander_client),
            "step": "2",
            "selected_type": "github",
            "name": "company-github",
            "token": _GHP_TEST,
            "action": "save",
        },
    )
    assert r.status_code == 302
    ds = DataSource.objects.get(name="company-github")
    assert ds.datasource_type == DataSource.Type.GITHUB
    assert ds.base_url == GITHUB_API_BASE
    assert ds.status == DataSource.Status.CONNECTED
