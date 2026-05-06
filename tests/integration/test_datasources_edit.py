"""Integration tests for datasource edit + replace-token (EDIT-01..10)."""

from unittest.mock import MagicMock, patch

import pytest
from django.urls import reverse

from tests.factories import DataSourceFactory


def _csrf_token(client) -> str:
    return client.cookies["csrftoken"].value


def _gitlab_urlopen_ok(username_bytes: bytes = b'{"username":"edit-user"}', total: str = "11"):
    bodies = iter([(username_bytes, {}), (b"[]", {"X-Total": total})])

    def _fake(req, timeout=10):
        body, hdrs = next(bodies)
        cm = MagicMock()
        enter = cm.__enter__.return_value
        enter.read.return_value = body
        enter.headers = hdrs
        return cm

    return _fake


@pytest.mark.django_db
def test_edit_01_get_renders(commander_client) -> None:
    ds = DataSourceFactory(name="edit-one")
    r = commander_client.get(reverse("datasource-edit", args=[ds.pk]))
    assert r.status_code == 200
    assert "Edit Data Source" in r.content.decode()


@pytest.mark.django_db
def test_edit_02_save_updates_fields_without_gitlab_call(commander_client) -> None:
    ds = DataSourceFactory(name="keep-name", base_url="https://old.example.com/", encrypted_token_ciphertext="secret")
    commander_client.get(reverse("datasource-edit", args=[ds.pk]))
    r = commander_client.post(
        reverse("datasource-edit", args=[ds.pk]),
        {
            "csrfmiddlewaretoken": _csrf_token(commander_client),
            "action": "save",
            "name": "keep-name",
            "base_url": "https://new.example.com/",
            "replace_token": "0",
            "new_token": "",
            "token_expires_at": "",
        },
        follow=False,
    )
    assert r.status_code == 302
    ds.refresh_from_db()
    assert ds.base_url == "https://new.example.com/"
    assert ds.encrypted_token_ciphertext == "secret"


@pytest.mark.django_db
def test_edit_03_test_connection_reuses_stored_token(commander_client) -> None:
    ds = DataSourceFactory(base_url="https://gitlab.example.com/", encrypted_token_ciphertext="glpat-1")
    commander_client.get(reverse("datasource-edit", args=[ds.pk]))
    with patch("ingestion.integrations.gitlab_client.urlopen", side_effect=_gitlab_urlopen_ok()):
        r = commander_client.post(
            reverse("datasource-edit", args=[ds.pk]),
            {
                "csrfmiddlewaretoken": _csrf_token(commander_client),
                "action": "test-connection",
                "name": ds.name,
                "base_url": ds.base_url,
                "replace_token": "0",
                "new_token": "",
                "token_expires_at": "",
            },
        )
    assert r.status_code == 200
    body = r.content.decode()
    assert "Connected as edit-user" in body
    assert "11 projects" in body


@pytest.mark.django_db
def test_edit_04_replace_requires_new_token_for_test(commander_client) -> None:
    ds = DataSourceFactory(base_url="https://gitlab.example.com/", encrypted_token_ciphertext="t")
    commander_client.get(reverse("datasource-edit", args=[ds.pk]))
    r = commander_client.post(
        reverse("datasource-edit", args=[ds.pk]),
        {
            "csrfmiddlewaretoken": _csrf_token(commander_client),
            "action": "test-connection",
            "name": ds.name,
            "base_url": ds.base_url,
            "replace_token": "1",
            "new_token": "",
            "token_expires_at": "",
        },
    )
    assert r.status_code == 200
    assert "Enter a new token" in r.content.decode()


@pytest.mark.django_db
def test_edit_05_save_updates_token_when_replacing(commander_client) -> None:
    ds = DataSourceFactory(base_url="https://gitlab.example.com/", encrypted_token_ciphertext="old")
    commander_client.get(reverse("datasource-edit", args=[ds.pk]))
    with patch(
        "ingestion.integrations.gitlab_client.urlopen", side_effect=_gitlab_urlopen_ok(b'{"username":"repl"}', "3")
    ):
        r = commander_client.post(
            reverse("datasource-edit", args=[ds.pk]),
            {
                "csrfmiddlewaretoken": _csrf_token(commander_client),
                "action": "save",
                "name": ds.name,
                "base_url": ds.base_url,
                "replace_token": "1",
                "new_token": "glpat-fresh",
                "token_expires_at": "",
            },
            follow=False,
        )
    assert r.status_code == 302
    ds.refresh_from_db()
    assert ds.encrypted_token_ciphertext == "glpat-fresh"
    assert ds.connected_user == "repl"


@pytest.mark.django_db
def test_edit_06_save_requires_name(commander_client) -> None:
    ds = DataSourceFactory()
    commander_client.get(reverse("datasource-edit", args=[ds.pk]))
    r = commander_client.post(
        reverse("datasource-edit", args=[ds.pk]),
        {
            "csrfmiddlewaretoken": _csrf_token(commander_client),
            "action": "save",
            "name": "",
            "base_url": ds.base_url,
            "replace_token": "0",
            "new_token": "",
            "token_expires_at": "",
        },
    )
    assert r.status_code == 200
    assert "Name is required" in r.content.decode()


@pytest.mark.django_db
def test_edit_07_cancel_points_to_detail(commander_client) -> None:
    ds = DataSourceFactory()
    r = commander_client.get(reverse("datasource-edit", args=[ds.pk]))
    assert f'href="/datasources/{ds.pk}/"' in r.content.decode()


@pytest.mark.django_db
def test_edit_08_replace_token_button_present(commander_client) -> None:
    ds = DataSourceFactory()
    body = commander_client.get(reverse("datasource-edit", args=[ds.pk])).content.decode()
    assert 'data-testid="datasource-replace-token-btn"' in body


@pytest.mark.django_db
def test_edit_09_token_expiry_field(commander_client) -> None:
    ds = DataSourceFactory()
    body = commander_client.get(reverse("datasource-edit", args=[ds.pk])).content.decode()
    assert 'data-testid="datasource-token-expiry"' in body


@pytest.mark.django_db
def test_edit_10_invalid_replace_token_surfaces_error(commander_client) -> None:
    ds = DataSourceFactory(base_url="https://gitlab.example.com/", encrypted_token_ciphertext="old")
    commander_client.get(reverse("datasource-edit", args=[ds.pk]))
    with patch("ingestion.integrations.gitlab_client.urlopen", side_effect=ConnectionError("nope")):
        r = commander_client.post(
            reverse("datasource-edit", args=[ds.pk]),
            {
                "csrfmiddlewaretoken": _csrf_token(commander_client),
                "action": "save",
                "name": ds.name,
                "base_url": ds.base_url,
                "replace_token": "1",
                "new_token": "glpat-bad",
                "token_expires_at": "",
            },
        )
    assert r.status_code == 200
    assert "validate new token" in r.content.decode()
