"""PROJECTS-VIEW_PROJECT-1 Increments tab (see projects-view-increments-tab.feature)."""

from datetime import timedelta

import pytest
from django.urls import reverse
from django.utils import timezone

from ingestion.models import Contributor, Increment, Project
from tests.factories import ProjectFactory


def _detail_url(pk: int, **q) -> str:
    url = reverse("projects-detail", args=[pk])
    if not q:
        return url
    from urllib.parse import urlencode

    return url + "?" + urlencode(q)


@pytest.mark.django_db
def test_increments_01_tabs_visible(commander_client):
    p = ProjectFactory(name="tabs", slug="tabs", sync_state=Project.SyncState.ACTIVE)
    r = commander_client.get(_detail_url(p.pk))
    body = r.content.decode()
    assert 'data-testid="project-tab-vitals"' in body
    assert 'data-testid="project-tab-variables"' in body
    assert 'data-testid="project-tab-increments"' in body


@pytest.mark.django_db
def test_increments_02_deep_link_last_14d(commander_client):
    p = ProjectFactory(name="deep", slug="deep", sync_state=Project.SyncState.ACTIVE)
    r = commander_client.get(_detail_url(p.pk, tab="increments", range="last_14d"))
    assert r.status_code == 200
    body = r.content.decode()
    assert 'data-testid="project-tab-increments"' in body
    assert "btn-primary" in body
    assert 'data-testid="increments-range-last_14d"' in body
    assert 'class="nav-link active"' in body  # Increments pill active
    assert "increments-range-last_14d" in body


@pytest.mark.django_db
def test_increments_03_default_range_when_tab_only(commander_client):
    p = ProjectFactory(name="defr", slug="defr", sync_state=Project.SyncState.ACTIVE)
    r = commander_client.get(_detail_url(p.pk, tab="increments"))
    body = r.content.decode()
    assert 'data-testid="increments-range-last_14d"' in body
    # selected button uses btn-primary for current range
    assert "btn-primary" in body


@pytest.mark.django_db
def test_increments_04_range_buttons(commander_client):
    p = ProjectFactory(name="rng", slug="rng", sync_state=Project.SyncState.ACTIVE)
    r = commander_client.get(_detail_url(p.pk, tab="increments"))
    body = r.content.decode()
    for key in ("today", "yesterday", "this_week", "last_week", "last_14d"):
        assert f'data-testid="increments-range-{key}"' in body


@pytest.mark.django_db
def test_increments_05_today_filters(commander_client):
    p = ProjectFactory(name="todayf", slug="todayf", sync_state=Project.SyncState.ACTIVE)
    assert p.datasource_id is not None
    c = Contributor.objects.create(datasource=p.datasource, email="u@example.com", name="U")
    now = timezone.now()
    Increment.objects.create(
        project=p,
        datasource=p.datasource,
        kind=Increment.Kind.COMMIT,
        external_id="a" * 40,
        occurred_at=now,
        contributor=c,
        summary="today-msg",
        payload={},
    )
    Increment.objects.create(
        project=p,
        datasource=p.datasource,
        kind=Increment.Kind.COMMIT,
        external_id="b" * 40,
        occurred_at=now - timedelta(days=2),
        contributor=c,
        summary="old-msg",
        payload={},
    )
    r = commander_client.get(_detail_url(p.pk, tab="increments", range="today"))
    body = r.content.decode()
    assert "today-msg" in body
    assert "old-msg" not in body


@pytest.mark.django_db
def test_increments_06_table_columns_and_row_testid(commander_client):
    p = ProjectFactory(name="tbl", slug="tbl", sync_state=Project.SyncState.ACTIVE)
    c = Contributor.objects.create(datasource=p.datasource, email="u@example.com", name="U")
    sha = "c" * 40
    Increment.objects.create(
        project=p,
        datasource=p.datasource,
        kind=Increment.Kind.COMMIT,
        external_id=sha,
        occurred_at=timezone.now(),
        contributor=c,
        summary="Hi",
        payload={"web_url": "https://gitlab.example.com/x", "branches": ["main"]},
    )
    r = commander_client.get(_detail_url(p.pk, tab="increments", range="last_14d"))
    body = r.content.decode()
    assert 'data-testid="increments-table"' in body
    for label in ("Occurred at", "Author", "Kind", "Commit", "Source"):
        assert label in body
    assert f'data-testid="increments-row-commit-{sha[:12]}"' in body


@pytest.mark.django_db
def test_increments_07_newest_first(commander_client):
    p = ProjectFactory(name="ord", slug="ord", sync_state=Project.SyncState.ACTIVE)
    c = Contributor.objects.create(datasource=p.datasource, email="u@example.com", name="U")
    now = timezone.now()
    Increment.objects.create(
        project=p,
        datasource=p.datasource,
        kind=Increment.Kind.COMMIT,
        external_id="d" * 40,
        occurred_at=now - timedelta(hours=1),
        contributor=c,
        summary="older-row",
        payload={},
    )
    Increment.objects.create(
        project=p,
        datasource=p.datasource,
        kind=Increment.Kind.COMMIT,
        external_id="e" * 40,
        occurred_at=now,
        contributor=c,
        summary="newer-row",
        payload={},
    )
    r = commander_client.get(_detail_url(p.pk, tab="increments", range="last_14d"))
    body = r.content.decode()
    assert body.find("newer-row") < body.find("older-row")


@pytest.mark.django_db
def test_increments_08_author_name_and_email_fallback(commander_client):
    p = ProjectFactory(name="auth", slug="auth", sync_state=Project.SyncState.ACTIVE)
    c1 = Contributor.objects.create(datasource=p.datasource, email="ada@example.com", name="Ada Lovelace")
    Increment.objects.create(
        project=p,
        datasource=p.datasource,
        kind=Increment.Kind.COMMIT,
        external_id="f" * 40,
        occurred_at=timezone.now(),
        contributor=c1,
        summary="s1",
        payload={},
    )
    r = commander_client.get(_detail_url(p.pk, tab="increments", range="last_14d"))
    assert "Ada Lovelace" in r.content.decode()

    c2 = Contributor.objects.create(datasource=p.datasource, email="dev@example.com", name="")
    Increment.objects.create(
        project=p,
        datasource=p.datasource,
        kind=Increment.Kind.COMMIT,
        external_id="0" * 40,
        occurred_at=timezone.now(),
        contributor=c2,
        summary="s2",
        payload={},
    )
    r2 = commander_client.get(_detail_url(p.pk, tab="increments", range="last_14d"))
    assert "dev@example.com" in r2.content.decode()


@pytest.mark.django_db
def test_increments_09_kind_commit(commander_client):
    p = ProjectFactory(name="kind", slug="kind", sync_state=Project.SyncState.ACTIVE)
    c = Contributor.objects.create(datasource=p.datasource, email="u@example.com", name="")
    Increment.objects.create(
        project=p,
        datasource=p.datasource,
        kind=Increment.Kind.COMMIT,
        external_id="1" * 40,
        occurred_at=timezone.now(),
        contributor=c,
        summary="k",
        payload={},
    )
    body = commander_client.get(_detail_url(p.pk, tab="increments", range="last_14d")).content.decode()
    assert "commit" in body.lower()


@pytest.mark.django_db
def test_increments_10_source_link_target_blank(commander_client):
    p = ProjectFactory(name="src", slug="src", sync_state=Project.SyncState.ACTIVE)
    c = Contributor.objects.create(datasource=p.datasource, email="u@example.com", name="")
    Increment.objects.create(
        project=p,
        datasource=p.datasource,
        kind=Increment.Kind.COMMIT,
        external_id="2" * 40,
        occurred_at=timezone.now(),
        contributor=c,
        summary="k",
        payload={"web_url": "https://gitlab.example.com/repo/-/commit/abc"},
    )
    body = commander_client.get(_detail_url(p.pk, tab="increments", range="last_14d")).content.decode()
    assert 'target="_blank"' in body
    assert 'rel="noopener noreferrer"' in body


@pytest.mark.django_db
def test_increments_11_empty_state(commander_client):
    p = ProjectFactory(name="emp", slug="emp", sync_state=Project.SyncState.ACTIVE)
    r = commander_client.get(_detail_url(p.pk, tab="increments", range="last_14d"))
    body = r.content.decode()
    assert 'data-testid="increments-empty-state"' in body


@pytest.mark.django_db
def test_increments_12_range_buttons_aria_label(commander_client):
    p = ProjectFactory(name="aria", slug="aria", sync_state=Project.SyncState.ACTIVE)
    body = commander_client.get(_detail_url(p.pk, tab="increments")).content.decode()
    assert 'aria-label="Show Increments from Today"' in body
    assert 'aria-label="Show Increments from Last 14 days"' in body


@pytest.mark.django_db
def test_invalid_range_normalizes_to_last_14d(commander_client):
    p = ProjectFactory(name="bad", slug="bad", sync_state=Project.SyncState.ACTIVE)
    r = commander_client.get(_detail_url(p.pk, tab="increments", range="not_a_range"))
    assert r.status_code == 200
    # normalized: last_14d primary button
    body = r.content.decode()
    assert 'data-testid="increments-range-last_14d"' in body
