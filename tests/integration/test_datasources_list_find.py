"""DATASOURCES-LIST+FIND integration tests (LIST-01..20)."""

import re
from datetime import timedelta

import pytest
from django.urls import reverse
from django.utils import timezone

from ingestion.models import DataSource
from tests.factories import DataSourceFactory


@pytest.mark.django_db
def test_list_01_page_loads(commander_client) -> None:
    r = commander_client.get(reverse("datasources-list"))
    assert r.status_code == 200


@pytest.mark.django_db
def test_list_02_count_badge_zero(commander_client) -> None:
    r = commander_client.get(reverse("datasources-list"))
    assert r.status_code == 200
    body = r.content.decode()
    assert "Data Sources (0)" in body
    assert 'data-testid="datasources-count-badge"' in body


@pytest.mark.django_db
def test_list_03_empty_state_and_cta(commander_client) -> None:
    r = commander_client.get(reverse("datasources-list"))
    body = r.content.decode()
    assert 'data-testid="datasources-empty-state"' in body
    assert 'data-testid="add-datasource-btn-empty"' in body


@pytest.mark.django_db
def test_list_04_header_add_button(commander_client) -> None:
    r = commander_client.get(reverse("datasources-list"))
    body = r.content.decode()
    assert 'data-testid="add-datasource-btn"' in body
    assert "/datasources/create/" in body


@pytest.mark.django_db
def test_list_05_filter_selects_present(commander_client) -> None:
    r = commander_client.get(reverse("datasources-list"))
    body = r.content.decode()
    assert 'data-testid="filter-type"' in body
    assert 'data-testid="filter-status"' in body


@pytest.mark.django_db
def test_list_06_row_renders_for_datasource(commander_client) -> None:
    ds = DataSourceFactory(name="row-one")
    r = commander_client.get(reverse("datasources-list"))
    body = r.content.decode()
    assert f'data-testid="datasource-row-{ds.pk}"' in body
    assert "row-one" in body


@pytest.mark.django_db
def test_list_07_seven_column_headers(commander_client) -> None:
    DataSourceFactory()
    r = commander_client.get(reverse("datasources-list"))
    body = r.content.decode()
    for label in ("Type", "Name", "Base URL", "Token expires", "Status", "Last activity", "Actions"):
        assert label in body


@pytest.mark.django_db
def test_list_08_action_testids(commander_client) -> None:
    ds = DataSourceFactory()
    r = commander_client.get(reverse("datasources-list"))
    body = r.content.decode()
    assert f'data-testid="datasource-row-name-{ds.pk}"' in body
    for action in ("edit", "import", "delete"):
        assert f'data-testid="datasource-action-{action}-{ds.pk}"' in body


@pytest.mark.django_db
def test_list_09_filter_by_type_gitlab(commander_client) -> None:
    DataSourceFactory(name="g1", datasource_type=DataSource.Type.GITLAB)
    DataSourceFactory(name="j1", datasource_type=DataSource.Type.JIRA)
    r = commander_client.get(reverse("datasources-list"), {"type": "gitlab"})
    body = r.content.decode()
    assert "g1" in body
    assert "j1" not in body


@pytest.mark.django_db
def test_list_10_filter_by_status_connected(commander_client) -> None:
    lim = timezone.now() + timedelta(days=60)
    DataSourceFactory(name="good-ds", status=DataSource.Status.CONNECTED, token_expires_at=lim)
    DataSourceFactory(name="err-ds", status=DataSource.Status.CONNECTION_ERROR)
    r = commander_client.get(reverse("datasources-list"), {"status": "connected"})
    body = r.content.decode()
    assert "good-ds" in body
    assert "err-ds" not in body


@pytest.mark.django_db
def test_list_11_filter_token_expiring(commander_client) -> None:
    soon = timezone.now() + timedelta(days=10)
    DataSourceFactory(name="soon", token_expires_at=soon)
    DataSourceFactory(name="far", token_expires_at=timezone.now() + timedelta(days=60))
    r = commander_client.get(reverse("datasources-list"), {"status": "token_expiring"})
    body = r.content.decode()
    assert "soon" in body
    assert "far" not in body


@pytest.mark.django_db
def test_list_12_filter_token_expired(commander_client) -> None:
    past = timezone.now() - timedelta(days=2)
    DataSourceFactory(name="dead", token_expires_at=past)
    DataSourceFactory(name="live", token_expires_at=timezone.now() + timedelta(days=60))
    r = commander_client.get(reverse("datasources-list"), {"status": "token_expired"})
    body = r.content.decode()
    assert "dead" in body
    assert "live" not in body


@pytest.mark.django_db
def test_list_13_filter_connection_error(commander_client) -> None:
    DataSourceFactory(name="broken-ds", status=DataSource.Status.CONNECTION_ERROR)
    DataSourceFactory(name="healthy-ds", status=DataSource.Status.CONNECTED)
    r = commander_client.get(reverse("datasources-list"), {"status": "connection_error"})
    body = r.content.decode()
    assert "broken-ds" in body
    assert "healthy-ds" not in body


@pytest.mark.django_db
def test_list_14_badge_success_connected(commander_client) -> None:
    DataSourceFactory(status=DataSource.Status.CONNECTED, token_expires_at=None)
    r = commander_client.get(reverse("datasources-list"))
    body = r.content.decode()
    assert "bg-success" in body
    assert "Connected" in body


@pytest.mark.django_db
def test_list_15_badge_warning_expiring(commander_client) -> None:
    DataSourceFactory(token_expires_at=timezone.now() + timedelta(days=5))
    r = commander_client.get(reverse("datasources-list"))
    body = r.content.decode()
    assert "bg-warning" in body
    assert "Token expiring" in body


@pytest.mark.django_db
def test_list_16_badge_danger_expired(commander_client) -> None:
    DataSourceFactory(token_expires_at=timezone.now() - timedelta(days=1))
    r = commander_client.get(reverse("datasources-list"))
    body = r.content.decode()
    assert "bg-danger" in body


@pytest.mark.django_db
def test_list_17_import_disabled_when_not_connected(commander_client) -> None:
    ds = DataSourceFactory(status=DataSource.Status.CONNECTION_ERROR)
    r = commander_client.get(reverse("datasources-list"))
    body = r.content.decode()
    fragment = f'data-testid="datasource-action-import-{ds.pk}"'
    idx = body.index(fragment)
    snippet = body[max(0, idx - 120) : idx + len(fragment) + 80]
    assert 'aria-disabled="true"' in snippet


@pytest.mark.django_db
def test_list_18_table_wrap_testid(commander_client) -> None:
    DataSourceFactory()
    r = commander_client.get(reverse("datasources-list"))
    assert 'data-testid="datasources-table-wrap"' in r.content.decode()


@pytest.mark.django_db
def test_list_19_filtered_empty_message(commander_client) -> None:
    DataSourceFactory(name="only-gitlab", datasource_type=DataSource.Type.GITLAB)
    r = commander_client.get(reverse("datasources-list"), {"type": "jira"})
    body = r.content.decode()
    assert 'data-testid="datasources-filter-empty"' in body


@pytest.mark.django_db
def test_list_20_jira_option_disabled_in_type_filter(commander_client) -> None:
    r = commander_client.get(reverse("datasources-list"))
    body = r.content.decode()
    assert "Jira" in body
    assert re.search(r'<option[^>]*value="jira"[^>]*disabled', body) or re.search(
        r'<option[^>]*disabled[^>]*value="jira"', body
    )
