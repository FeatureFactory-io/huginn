"""Project detail — Variables tab + Vitals informer bar (ACT2-PROJECT-03 / #52)."""

from urllib.parse import parse_qs, urlencode, urlparse

import pytest
from django.urls import reverse

from ingestion.models import Project
from tests.factories import (
    ProjectFactory,
    RulesOfEngagementFactory,
    RulesOfEngagementVariableFactory,
    RulesOfEngagementVersionFactory,
)


def _detail_url(pk: int, **q: str) -> str:
    url = reverse("projects-detail", args=[pk])
    if not q:
        return url
    return url + "?" + urlencode(q)


def _csrf(client):
    return client.cookies["csrftoken"].value


@pytest.mark.django_db
def test_variables_tab_nav_visible(commander_client):
    p = ProjectFactory(name="vtab", slug="vtab", sync_state=Project.SyncState.ACTIVE)
    body = commander_client.get(_detail_url(p.pk)).content.decode()
    assert 'data-testid="project-tab-variables"' in body
    assert ">Variables</a>" in body


@pytest.mark.django_db
def test_variables_deep_link_period_selected(commander_client):
    p = ProjectFactory(name="vdeep", slug="vdeep", sync_state=Project.SyncState.ACTIVE)
    r = commander_client.get(_detail_url(p.pk, tab="variables", period="last_week"))
    assert r.status_code == 200
    body = r.content.decode()
    idx = body.index('data-testid="variables-period-last_week"')
    snippet = body[max(0, idx - 160) : idx + 40]
    assert "btn-primary" in snippet


@pytest.mark.django_db
def test_variables_default_period_this_week(commander_client):
    p = ProjectFactory(name="vdef", slug="vdef", sync_state=Project.SyncState.ACTIVE)
    body = commander_client.get(_detail_url(p.pk, tab="variables")).content.decode()
    assert 'data-testid="variables-period-this_week"' in body
    assert "?tab=variables&amp;period=this_week" in body or "?tab=variables&period=this_week" in body


@pytest.mark.django_db
def test_variables_period_buttons(commander_client):
    p = ProjectFactory(name="vper", slug="vper", sync_state=Project.SyncState.ACTIVE)
    body = commander_client.get(_detail_url(p.pk, tab="variables")).content.decode()
    for key in ("today", "yesterday", "this_week", "last_week", "last_30d"):
        assert f'data-testid="variables-period-{key}"' in body


@pytest.mark.django_db
def test_variables_invalid_period_normalizes(commander_client):
    p = ProjectFactory(name="vbad", slug="vbad", sync_state=Project.SyncState.ACTIVE)
    r = commander_client.get(_detail_url(p.pk, tab="variables", period="not_real"))
    assert r.status_code == 200
    body = r.content.decode()
    assert 'data-testid="variables-period-this_week"' in body


@pytest.mark.django_db
def test_variables_grid_and_cards_when_roe_has_variables(commander_client):
    roe = RulesOfEngagementFactory(name="RoE Vars", slug="roe-vars")
    ver = RulesOfEngagementVersionFactory(roe=roe, version_number=1)
    RulesOfEngagementVariableFactory(roe_version=ver, sort_order=0, name="Throughput", abbrev="TP")
    p = ProjectFactory(
        name="vgrid",
        slug="vgrid",
        sync_state=Project.SyncState.ACTIVE,
        assigned_roe=roe,
        roe_slug=roe.slug,
    )
    body = commander_client.get(_detail_url(p.pk, tab="variables")).content.decode()
    assert 'data-testid="variables-diagram-grid"' in body
    assert 'data-testid="variables-diagram-TP"' in body
    assert "Throughput" in body


@pytest.mark.django_db
def test_vitals_informer_dots_when_variables_exist(commander_client):
    roe = RulesOfEngagementFactory(name="RoE Inf", slug="roe-inf")
    ver = RulesOfEngagementVersionFactory(roe=roe, version_number=1)
    RulesOfEngagementVariableFactory(roe_version=ver, sort_order=0, name="Risk", abbrev="RS")
    p = ProjectFactory(
        name="vdot",
        slug="vdot",
        sync_state=Project.SyncState.ACTIVE,
        assigned_roe=roe,
        roe_slug=roe.slug,
    )
    body = commander_client.get(_detail_url(p.pk, tab="vitals")).content.decode()
    assert 'data-testid="project-informer-bar"' in body
    assert 'data-testid="informer-dot-RS"' in body
    assert "hg-informer-dot--grey" in body


@pytest.mark.django_db
def test_vitals_informer_no_roe(commander_client):
    p = ProjectFactory(name="vnopb", slug="vnopb", sync_state=Project.SyncState.ACTIVE)
    body = commander_client.get(_detail_url(p.pk)).content.decode()
    assert 'data-testid="informer-bar-empty"' in body


@pytest.mark.django_db
def test_vitals_informer_roe_no_variables(commander_client):
    roe = RulesOfEngagementFactory(name="RoE Empty", slug="roe-empty")
    RulesOfEngagementVersionFactory(roe=roe, version_number=1)
    p = ProjectFactory(
        name="vempty",
        slug="vempty",
        sync_state=Project.SyncState.ACTIVE,
        assigned_roe=roe,
        roe_slug=roe.slug,
    )
    body = commander_client.get(_detail_url(p.pk)).content.decode()
    assert 'data-testid="informer-bar-no-vars"' in body


@pytest.mark.django_db
def test_variables_tab_empty_when_no_variables(commander_client):
    roe = RulesOfEngagementFactory(name="RoE Empty2", slug="roe-empty2")
    RulesOfEngagementVersionFactory(roe=roe, version_number=1)
    p = ProjectFactory(
        name="vtabempty",
        slug="vtabempty",
        sync_state=Project.SyncState.ACTIVE,
        assigned_roe=roe,
        roe_slug=roe.slug,
    )
    body = commander_client.get(_detail_url(p.pk, tab="variables")).content.decode()
    assert 'data-testid="variables-empty-state"' in body


@pytest.mark.django_db
def test_effective_version_respects_pinned_version(commander_client):
    roe = RulesOfEngagementFactory(name="RoE Pin", slug="roe-pin")
    v1 = RulesOfEngagementVersionFactory(roe=roe, version_number=1)
    RulesOfEngagementVariableFactory(roe_version=v1, sort_order=0, name="Only V1", abbrev="O1")
    v2 = RulesOfEngagementVersionFactory(roe=roe, version_number=2)
    RulesOfEngagementVariableFactory(roe_version=v2, sort_order=0, name="Only V2", abbrev="O2")
    p = ProjectFactory(
        name="vpin",
        slug="vpin",
        sync_state=Project.SyncState.ACTIVE,
        assigned_roe=roe,
        pinned_roe_version=v1,
        roe_slug=roe.slug,
    )
    body = commander_client.get(_detail_url(p.pk, tab="variables")).content.decode()
    assert "Only V1" in body
    assert "O1" in body
    assert "Only V2" not in body
    assert 'data-testid="variables-diagram-O1"' in body


@pytest.mark.django_db
def test_sync_now_preserves_variables_tab_and_period(commander_client):
    roe = RulesOfEngagementFactory(name="RoE Sync", slug="roe-sync")
    RulesOfEngagementVersionFactory(roe=roe, version_number=1)
    p = ProjectFactory(
        name="vsync",
        slug="vsync",
        sync_state=Project.SyncState.ACTIVE,
        assigned_roe=roe,
        roe_slug=roe.slug,
    )
    commander_client.get(_detail_url(p.pk, tab="variables", period="last_30d"))
    r = commander_client.post(
        reverse("projects-sync-now", args=[p.pk]),
        {
            "csrfmiddlewaretoken": _csrf(commander_client),
            "tab": "variables",
            "period": "last_30d",
        },
        follow=False,
    )
    assert r.status_code == 302
    loc = r.get("Location") or ""
    qs = parse_qs(urlparse(loc).query)
    assert qs.get("tab") == ["variables"]
    assert qs.get("period") == ["last_30d"]
