"""Integration tests for datasource create wizard (CREATE-01..16)."""

from unittest.mock import MagicMock, patch

import pytest
from django.urls import reverse

from ingestion.models import DataSource


def _csrf_token(client) -> str:
    return client.cookies["csrftoken"].value


def _gitlab_urlopen_ok(username_bytes: bytes = b'{"username":"integ-user"}', total: str = "14"):
    bodies = iter(
        [
            (username_bytes, {}),
            (b"[]", {"X-Total": total}),
        ]
    )

    def _fake(req, timeout=10):
        body, hdrs = next(bodies)
        cm = MagicMock()
        enter = cm.__enter__.return_value
        enter.read.return_value = body
        enter.headers = hdrs
        return cm

    return _fake


@pytest.mark.django_db
def test_create_01_get_shows_step_one(commander_client) -> None:
    r = commander_client.get(reverse("datasources-create"))
    assert r.status_code == 200
    body = r.content.decode()
    assert "Step 1 of 2" in body
    assert "Add Data Source" in body
    assert "simpleicons.org/gitlab" in body
    assert "simpleicons.org/github" in body
    assert "simpleicons.org/jira" in body


@pytest.mark.django_db
def test_create_02_select_gitlab_shows_step_two(commander_client) -> None:
    commander_client.get(reverse("datasources-create"))
    r = commander_client.post(
        reverse("datasources-create"),
        {"csrfmiddlewaretoken": _csrf_token(commander_client), "type": "gitlab"},
    )
    assert r.status_code == 200
    body = r.content.decode()
    assert "Step 2 of 2" in body


@pytest.mark.django_db
def test_create_03_step_two_has_core_fields(commander_client) -> None:
    commander_client.get(reverse("datasources-create"))
    r = commander_client.post(
        reverse("datasources-create"),
        {"csrfmiddlewaretoken": _csrf_token(commander_client), "type": "gitlab"},
    )
    body = r.content.decode()
    for tid in (
        "datasource-name-input",
        "datasource-base-url-input",
        "datasource-token-input",
        "datasource-token-expiry",
        "datasource-test-connection",
        "datasource-save",
    ):
        assert tid in body


@pytest.mark.django_db
def test_create_04_test_connection_success_message(commander_client) -> None:
    commander_client.get(reverse("datasources-create"))
    commander_client.post(
        reverse("datasources-create"),
        {"csrfmiddlewaretoken": _csrf_token(commander_client), "type": "gitlab"},
    )
    tok = _csrf_token(commander_client)
    with patch("ingestion.integrations.gitlab_client.urlopen", side_effect=_gitlab_urlopen_ok()):
        r = commander_client.post(
            reverse("datasources-create"),
            {
                "csrfmiddlewaretoken": tok,
                "step": "2",
                "action": "test-connection",
                "name": "c1",
                "base_url": "https://gitlab.example.com/",
                "token": "glpat-x",
            },
        )
    assert r.status_code == 200
    body = r.content.decode()
    assert "datasource-test-result" in body
    assert "Connected as integ-user" in body
    assert "14 projects" in body


@pytest.mark.django_db
def test_create_05_test_connection_shows_error(commander_client) -> None:
    commander_client.get(reverse("datasources-create"))
    commander_client.post(
        reverse("datasources-create"),
        {"csrfmiddlewaretoken": _csrf_token(commander_client), "type": "gitlab"},
    )
    with patch("ingestion.integrations.gitlab_client.urlopen", side_effect=ConnectionError("fail")):
        r = commander_client.post(
            reverse("datasources-create"),
            {
                "csrfmiddlewaretoken": _csrf_token(commander_client),
                "step": "2",
                "action": "test-connection",
                "name": "c1",
                "base_url": "https://gitlab.example.com/",
                "token": "glpat-x",
            },
        )
    assert r.status_code == 200
    assert "fail" in r.content.decode()


@pytest.mark.django_db
def test_create_06_save_redirects_to_projects_import(commander_client) -> None:
    commander_client.get(reverse("datasources-create"))
    commander_client.post(
        reverse("datasources-create"),
        {"csrfmiddlewaretoken": _csrf_token(commander_client), "type": "gitlab"},
    )
    tok = _csrf_token(commander_client)
    with patch("ingestion.integrations.gitlab_client.urlopen", side_effect=_gitlab_urlopen_ok(total="2")):
        r = commander_client.post(
            reverse("datasources-create"),
            {
                "csrfmiddlewaretoken": tok,
                "step": "2",
                "action": "save",
                "name": "save-redirect-ds",
                "base_url": "https://gitlab.example.com/",
                "token": "glpat-save",
            },
            follow=False,
        )
    assert r.status_code == 302
    loc = r.headers.get("Location", "")
    assert "/projects/import/" in loc
    assert "datasource=" in loc
    assert "banner=datasource_connected" in loc


@pytest.mark.django_db
def test_create_07_save_requires_name(commander_client) -> None:
    commander_client.get(reverse("datasources-create"))
    commander_client.post(
        reverse("datasources-create"),
        {"csrfmiddlewaretoken": _csrf_token(commander_client), "type": "gitlab"},
    )
    r = commander_client.post(
        reverse("datasources-create"),
        {
            "csrfmiddlewaretoken": _csrf_token(commander_client),
            "step": "2",
            "action": "save",
            "name": "",
            "base_url": "https://gitlab.example.com/",
            "token": "glpat-x",
        },
    )
    assert r.status_code == 200
    assert "Name is required" in r.content.decode()


@pytest.mark.django_db
def test_create_08_duplicate_name_shows_error(commander_client) -> None:
    DataSource.objects.create(
        name="taken-ds",
        datasource_type=DataSource.Type.GITLAB,
        base_url="https://gitlab.example.com/",
    )
    commander_client.get(reverse("datasources-create"))
    commander_client.post(
        reverse("datasources-create"),
        {"csrfmiddlewaretoken": _csrf_token(commander_client), "type": "gitlab"},
    )
    with patch("ingestion.integrations.gitlab_client.urlopen", side_effect=_gitlab_urlopen_ok()):
        r = commander_client.post(
            reverse("datasources-create"),
            {
                "csrfmiddlewaretoken": _csrf_token(commander_client),
                "step": "2",
                "action": "save",
                "name": "taken-ds",
                "base_url": "https://gitlab.example.com/",
                "token": "glpat-x",
            },
        )
    assert r.status_code == 200
    assert "already exists" in r.content.decode()


@pytest.mark.django_db
def test_create_09_step_one_gitlab_card(commander_client) -> None:
    r = commander_client.get(reverse("datasources-create"))
    assert 'data-testid="datasource-type-gitlab"' in r.content.decode()


@pytest.mark.django_db
def test_create_10_step_one_jira_disabled(commander_client) -> None:
    r = commander_client.get(reverse("datasources-create"))
    body = r.content.decode()
    assert 'data-testid="datasource-type-jira"' in body
    assert "disabled" in body


@pytest.mark.django_db
def test_create_11_breadcrumb_links_to_list(commander_client) -> None:
    r = commander_client.get(reverse("datasources-create"))
    body = r.content.decode()
    assert "/datasources/" in body
    assert "breadcrumb" in body


@pytest.mark.django_db
def test_create_12_cancel_on_step_two(commander_client) -> None:
    commander_client.get(reverse("datasources-create"))
    r = commander_client.post(
        reverse("datasources-create"),
        {"csrfmiddlewaretoken": _csrf_token(commander_client), "type": "gitlab"},
    )
    assert 'href="/datasources/"' in r.content.decode()


@pytest.mark.django_db
def test_create_13_save_enabled_without_javascript(commander_client) -> None:
    commander_client.get(reverse("datasources-create"))
    r = commander_client.post(
        reverse("datasources-create"),
        {"csrfmiddlewaretoken": _csrf_token(commander_client), "type": "gitlab"},
    )
    body = r.content.decode()
    idx = body.index('data-testid="datasource-save"')
    snippet = body[max(0, idx - 80) : idx + 80]
    assert "disabled" not in snippet


@pytest.mark.django_db
def test_create_14_test_connection_enabled_without_javascript(commander_client) -> None:
    commander_client.get(reverse("datasources-create"))
    r = commander_client.post(
        reverse("datasources-create"),
        {"csrfmiddlewaretoken": _csrf_token(commander_client), "type": "gitlab"},
    )
    body = r.content.decode()
    idx = body.index('data-testid="datasource-test-connection"')
    snippet = body[max(0, idx - 80) : idx + 80]
    assert "disabled" not in snippet


@pytest.mark.django_db
def test_create_15_unknown_step_post_redirects_to_wizard(commander_client) -> None:
    commander_client.get(reverse("datasources-create"))
    r = commander_client.post(
        reverse("datasources-create"),
        {
            "csrfmiddlewaretoken": _csrf_token(commander_client),
            "step": "9",
            "action": "save",
            "name": "x",
            "base_url": "https://gitlab.example.com/",
            "token": "t",
        },
        follow=False,
    )
    assert r.status_code == 302
    assert r.headers.get("Location", "").endswith("/datasources/create/")


@pytest.mark.django_db
def test_create_16_persists_gitlab_metadata(commander_client) -> None:
    commander_client.get(reverse("datasources-create"))
    commander_client.post(
        reverse("datasources-create"),
        {"csrfmiddlewaretoken": _csrf_token(commander_client), "type": "gitlab"},
    )
    with patch(
        "ingestion.integrations.gitlab_client.urlopen", side_effect=_gitlab_urlopen_ok(b'{"username":"persist"}', "6")
    ):
        commander_client.post(
            reverse("datasources-create"),
            {
                "csrfmiddlewaretoken": _csrf_token(commander_client),
                "step": "2",
                "action": "save",
                "name": "meta-ds",
                "base_url": "https://gitlab.example.com/",
                "token": "glpat-x",
            },
            follow=False,
        )
    ds = DataSource.objects.get(name="meta-ds")
    assert ds.connected_user == "persist"
    assert ds.visible_project_count == 6
