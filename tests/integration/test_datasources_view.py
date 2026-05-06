"""Integration tests for datasource detail + test-connection (VIEW-01..09)."""

from unittest.mock import MagicMock, patch

import pytest
from django.urls import reverse

from ingestion.models import DataSource
from tests.factories import DataSourceFactory


def _csrf_token(client) -> str:
    return client.cookies["csrftoken"].value


def _gitlab_urlopen_ok(username_bytes: bytes = b'{"username":"detail-user"}', total: str = "5"):
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
def test_view_01_detail_renders(commander_client) -> None:
    ds = DataSourceFactory(name="view-ds")
    r = commander_client.get(reverse("datasource-detail", args=[ds.pk]))
    assert r.status_code == 200
    assert "view-ds" in r.content.decode()


@pytest.mark.django_db
def test_view_02_key_testids_present(commander_client) -> None:
    ds = DataSourceFactory(connected_user="pat@example.com", encrypted_token_ciphertext="glpat-abcdefgh")
    r = commander_client.get(reverse("datasource-detail", args=[ds.pk]))
    body = r.content.decode()
    for tid in (
        "ds-type-badge",
        "ds-name",
        "ds-masked-token",
        "ds-token-expiry",
        "ds-connected-user",
        "ds-sync-log",
        "ds-test-connection-btn",
        "ds-edit-btn",
        "ds-delete-btn",
    ):
        assert tid in body


@pytest.mark.django_db
def test_view_03_breadcrumb_links_list(commander_client) -> None:
    ds = DataSourceFactory()
    body = commander_client.get(reverse("datasource-detail", args=[ds.pk])).content.decode()
    assert "/datasources/" in body
    assert "breadcrumb" in body


@pytest.mark.django_db
def test_view_04_edit_href(commander_client) -> None:
    ds = DataSourceFactory()
    body = commander_client.get(reverse("datasource-detail", args=[ds.pk])).content.decode()
    assert f"/datasources/{ds.pk}/edit/" in body


@pytest.mark.django_db
def test_view_05_htmx_attributes_on_test_button(commander_client) -> None:
    ds = DataSourceFactory()
    body = commander_client.get(reverse("datasource-detail", args=[ds.pk])).content.decode()
    assert "hx-post=" in body
    assert f"/datasources/{ds.pk}/test-connection/" in body


@pytest.mark.django_db
def test_view_06_post_test_connection_updates_model(commander_client) -> None:
    ds = DataSourceFactory(
        name="probe-ds",
        base_url="https://gitlab.example.com/",
        encrypted_token_ciphertext="glpat-secret",
        status=DataSource.Status.CONNECTION_ERROR,
    )
    commander_client.get(reverse("datasource-detail", args=[ds.pk]))
    with patch("urllib.request.urlopen", side_effect=_gitlab_urlopen_ok()):
        r = commander_client.post(
            reverse("datasource-test-connection", args=[ds.pk]),
            {"csrfmiddlewaretoken": _csrf_token(commander_client)},
        )
    assert r.status_code == 200
    ds.refresh_from_db()
    assert ds.status == DataSource.Status.CONNECTED
    assert ds.connected_user == "detail-user"
    assert ds.visible_project_count == 5


@pytest.mark.django_db
def test_view_07_post_test_connection_failure_state(commander_client) -> None:
    ds = DataSourceFactory(
        base_url="https://gitlab.example.com/",
        encrypted_token_ciphertext="glpat-secret",
        status=DataSource.Status.CONNECTED,
    )
    commander_client.get(reverse("datasource-detail", args=[ds.pk]))
    with patch("urllib.request.urlopen", side_effect=ConnectionError("down")):
        r = commander_client.post(
            reverse("datasource-test-connection", args=[ds.pk]),
            {"csrfmiddlewaretoken": _csrf_token(commander_client)},
        )
    assert r.status_code == 200
    assert "alert-danger" in r.content.decode()
    ds.refresh_from_db()
    assert ds.status == DataSource.Status.CONNECTION_ERROR


@pytest.mark.django_db
def test_view_08_partial_success_body(commander_client) -> None:
    ds = DataSourceFactory(base_url="https://gitlab.example.com/", encrypted_token_ciphertext="t")
    commander_client.get(reverse("datasource-detail", args=[ds.pk]))
    with patch("urllib.request.urlopen", side_effect=_gitlab_urlopen_ok(b'{"username":"u8"}', "9")):
        r = commander_client.post(
            reverse("datasource-test-connection", args=[ds.pk]),
            {"csrfmiddlewaretoken": _csrf_token(commander_client)},
        )
    body = r.content.decode()
    assert "Connected as u8" in body
    assert "9 projects" in body
    assert 'data-testid="ds-test-connection-result"' in body


@pytest.mark.django_db
def test_view_09_get_test_connection_not_allowed(commander_client) -> None:
    ds = DataSourceFactory()
    commander_client.get(reverse("datasource-detail", args=[ds.pk]))
    r = commander_client.get(reverse("datasource-test-connection", args=[ds.pk]))
    assert r.status_code == 405
