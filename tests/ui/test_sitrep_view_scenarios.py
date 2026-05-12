"""SITREP-VIEW_SITREP-1 — pytest translation of `sitrep-view.feature`."""

from __future__ import annotations

import datetime as dt

import pytest
from django.template.defaultfilters import date as dj_date_filter
from django.urls import reverse
from django.utils import timezone

from sitrep.models import Frago, SitRep
from tests.factories import FragoFactory, PlaybookFactory, PlaybookVersionFactory, ProjectFactory

SLUG = "atlas-backend"


@pytest.fixture()
def atlas_backend_project(commander_user, db):
    pb = PlaybookFactory(name="Atlas Engineering Playbook", slug="atlas-engineering-playbook")
    pv = PlaybookVersionFactory(playbook=pb, version_number=1)
    return ProjectFactory(
        name="Atlas Backend",
        slug=SLUG,
        assigned_playbook=pb,
        pinned_playbook_version=pv,
        imported_by=commander_user,
    )


def _view_url(sr: SitRep) -> str:
    return reverse("sitrep-detail", kwargs={"project_slug": SLUG, "pk": sr.pk})


def _background_sitrep(project, *, to_dt_override: timezone.datetime | None = None, **kwargs):
    """Fixture row matching `sitrep-view.feature` Background table."""
    gen = dt.datetime(2026, 5, 11, 13, 15, tzinfo=dt.UTC)
    from_dt = dt.datetime(2026, 5, 11, 9, 0, tzinfo=dt.UTC)
    to_dt = to_dt_override or dt.datetime(2026, 5, 11, 13, 15, tzinfo=dt.UTC)
    defaults = {
        "from_dt": from_dt,
        "to_dt": to_dt,
        "trigger": "automatic",
        "mode_at_generation": "semi_auto",
        "playbook_version": 1,
        "headline": "Delivery pace steady — no blockers detected",
        "situation_assessment": "The team shipped 12 commits in the assessed period",
        "notable_activity": [],
    }
    defaults.update(kwargs)
    sr = SitRep.objects.create(project=project, **defaults)
    SitRep.objects.filter(pk=sr.pk).update(generated_at=gen)
    sr.refresh_from_db()
    return sr


def _expected_assessed_period_text(sr: SitRep) -> str:
    lf = timezone.localtime(sr.from_dt)
    lt = timezone.localtime(sr.to_dt)
    return f"{dj_date_filter(lf, 'D H:i')} → {dj_date_filter(lt, 'H:i')}"


@pytest.mark.django_db
def test_sitrep_view_01_header_project_and_generated(commander_client, atlas_backend_project):
    sr = _background_sitrep(atlas_backend_project)
    body = commander_client.get(_view_url(sr)).content.decode()
    assert SLUG in body
    assert "2026-05-11 13:15" in body


@pytest.mark.django_db
def test_sitrep_view_02_assessed_period_timezone(commander_client, atlas_backend_project, settings):
    settings.TIME_ZONE = "Asia/Tokyo"
    timezone.activate("Asia/Tokyo")
    try:
        sr = _background_sitrep(atlas_backend_project)
        body = commander_client.get(_view_url(sr)).content.decode()
        needle = _expected_assessed_period_text(sr)
        assert needle in body
        assert 'data-testid="sitrep-assessed-period"' in body
        assert timezone.get_current_timezone_name() == "Asia/Tokyo"
    finally:
        timezone.deactivate()


@pytest.mark.django_db
def test_sitrep_view_03_trigger_badge_auto(commander_client, atlas_backend_project):
    sr = _background_sitrep(atlas_backend_project, trigger="automatic")
    body = commander_client.get(_view_url(sr)).content.decode()
    assert "sitrep-status-badge" in body
    compact = "".join(body.split())
    assert ">Auto</span>" in compact


@pytest.mark.django_db
def test_sitrep_view_04_trigger_badge_manual(commander_client, atlas_backend_project):
    sr = _background_sitrep(atlas_backend_project, trigger="manual")
    body = commander_client.get(_view_url(sr)).content.decode()
    compact = "".join(body.split())
    assert ">Manual</span>" in compact


@pytest.mark.django_db
def test_sitrep_view_05_playbook_version(commander_client, atlas_backend_project):
    sr = _background_sitrep(atlas_backend_project)
    body = commander_client.get(_view_url(sr)).content.decode()
    assert "v1</strong>" in body or ">v1<" in body


@pytest.mark.django_db
def test_sitrep_view_06_no_variables_badge(commander_client, atlas_backend_project):
    sr = _background_sitrep(atlas_backend_project)
    body = commander_client.get(_view_url(sr)).content.decode()
    assert 'data-testid="sitrep-status-badge"' in body
    idx = body.index('data-testid="sitrep-status-badge"')
    chunk = body[max(0, idx - 140) : idx + 200]
    assert "No Variables" in chunk
    assert "bg-secondary" in chunk


@pytest.mark.django_db
def test_sitrep_view_07_mode_badge_semi_auto(commander_client, atlas_backend_project):
    sr = _background_sitrep(atlas_backend_project, mode_at_generation="semi_auto")
    body = commander_client.get(_view_url(sr)).content.decode()
    assert 'data-testid="sitrep-mode-badge"' in body
    i = body.index('data-testid="sitrep-mode-badge"')
    assert "Semi-Auto" in body[i : i + 200]


@pytest.mark.django_db
def test_sitrep_view_08_mode_badge_auto(commander_client, atlas_backend_project):
    sr = _background_sitrep(atlas_backend_project, mode_at_generation="auto")
    body = commander_client.get(_view_url(sr)).content.decode()
    i = body.index('data-testid="sitrep-mode-badge"')
    assert "Auto" in body[i : i + 220]


@pytest.mark.django_db
def test_sitrep_view_09_section1_heading(commander_client, atlas_backend_project):
    sr = _background_sitrep(atlas_backend_project)
    body = commander_client.get(_view_url(sr)).content.decode()
    assert "Situation Assessment" in body


@pytest.mark.django_db
def test_sitrep_view_10_situation_assessment_text(commander_client, atlas_backend_project):
    sr = _background_sitrep(atlas_backend_project)
    body = commander_client.get(_view_url(sr)).content.decode()
    assert 'data-testid="sitrep-situation-assessment"' in body
    assert "The team shipped 12 commits in the assessed period" in body


@pytest.mark.django_db
def test_sitrep_view_11_inline_no_variables_chip(commander_client, atlas_backend_project):
    sr = _background_sitrep(atlas_backend_project)
    body = commander_client.get(_view_url(sr)).content.decode()
    assert "sitrep-section1-status-chip" in body
    s = body.index("section-situation")
    assert "No Variables" in body[s : s + 900]


@pytest.mark.django_db
def test_sitrep_view_12_variables_heading(commander_client, atlas_backend_project):
    sr = _background_sitrep(atlas_backend_project)
    body = commander_client.get(_view_url(sr)).content.decode()
    assert "Variables Snapshot" in body


@pytest.mark.django_db
def test_sitrep_view_13_variables_placeholder(commander_client, atlas_backend_project):
    sr = _background_sitrep(atlas_backend_project)
    body = commander_client.get(_view_url(sr)).content.decode()
    pos = body.index('id="section-variables"')
    block = body[pos : pos + 2500]
    assert "Variables will be available in a future release" in block
    assert "data-variable-row" not in block


@pytest.mark.django_db
def test_sitrep_view_14_decisions_heading(commander_client, atlas_backend_project):
    sr = _background_sitrep(atlas_backend_project)
    body = commander_client.get(_view_url(sr)).content.decode()
    assert "Decisions" in body


@pytest.mark.django_db
def test_sitrep_view_15_no_decisions_placeholder(commander_client, atlas_backend_project):
    sr = _background_sitrep(atlas_backend_project)
    body = commander_client.get(_view_url(sr)).content.decode()
    pos = body.index('id="section-decisions"')
    block = body[pos : pos + 2500]
    assert "No Decisions proposed" in block
    assert "sitrep-decision-card" not in block


@pytest.mark.django_db
def test_sitrep_view_16_fragos_heading(commander_client, atlas_backend_project):
    sr = _background_sitrep(atlas_backend_project)
    body = commander_client.get(_view_url(sr)).content.decode()
    assert "FRAGOs Applied" in body


@pytest.mark.django_db
def test_sitrep_view_17_fragos_list_with_link(commander_client, atlas_backend_project):
    sr = _background_sitrep(atlas_backend_project)
    fr = FragoFactory(project=atlas_backend_project, title="Sprint 47 bug belay", enabled=True)
    sr.fragos_applied.add(fr)

    body = commander_client.get(_view_url(sr)).content.decode()
    assert "Sprint 47 bug belay" in body
    assert reverse("fragos-detail", args=[fr.pk]) in body
    assert 'data-screen="FRAGOS-VIEW_FRAGO-1"' in body


@pytest.mark.django_db
def test_sitrep_view_18_fragos_multiple(commander_client, atlas_backend_project):
    sr = _background_sitrep(atlas_backend_project)
    a = FragoFactory(project=atlas_backend_project, title="Sprint 47 bug belay", enabled=True)
    b = FragoFactory(project=atlas_backend_project, title="GitLab outage narrative", enabled=True)
    sr.fragos_applied.add(a, b)

    body = commander_client.get(_view_url(sr)).content.decode()
    pos = body.index("FRAGOs Applied")
    blk = body[pos : pos + 4000]
    assert "Sprint 47 bug belay" in blk
    assert "GitLab outage narrative" in blk


@pytest.mark.django_db
def test_sitrep_view_19_fragos_empty_state(commander_client, atlas_backend_project):
    sr = _background_sitrep(atlas_backend_project)
    body = commander_client.get(_view_url(sr)).content.decode()
    assert "No FRAGOs were applied to this assessment" in body


@pytest.mark.django_db
def test_sitrep_view_20_disabled_frago_hidden(commander_client, atlas_backend_project):
    sr = _background_sitrep(atlas_backend_project)
    old = Frago.objects.create(project=atlas_backend_project, title="Old waiver", enabled=False)
    sr.fragos_applied.add(old)

    body = commander_client.get(_view_url(sr)).content.decode()
    assert "Old waiver" not in body


@pytest.mark.django_db
def test_sitrep_view_21_notable_heading(commander_client, atlas_backend_project):
    sr = _background_sitrep(atlas_backend_project)
    body = commander_client.get(_view_url(sr)).content.decode()
    assert "Notable Activity" in body


@pytest.mark.django_db
def test_sitrep_view_22_notable_activity_summary(commander_client, atlas_backend_project):
    sr = _background_sitrep(
        atlas_backend_project,
        notable_activity=[
            {"contributor": "alex@example.com", "detail": "authored commits"},
            {"contributor": "sam@example.com", "detail": "merged MRs"},
        ],
    )
    body = commander_client.get(_view_url(sr)).content.decode()
    pos = body.index('data-testid="sitrep-notable-activity"')
    blk = body[pos : pos + 2400]
    assert "alex@example.com" in blk
    assert "sam@example.com" in blk


@pytest.mark.django_db
def test_sitrep_view_23_notable_activity_empty(commander_client, atlas_backend_project):
    sr = _background_sitrep(atlas_backend_project, notable_activity=[])
    body = commander_client.get(_view_url(sr)).content.decode()
    assert "sitrep-notable-empty" in body
    assert "No notable activity in this period." in body


@pytest.mark.django_db
def test_sitrep_view_24_open_decisions_btn(commander_client, atlas_backend_project):
    sr = _background_sitrep(atlas_backend_project)
    body = commander_client.get(_view_url(sr)).content.decode()
    assert 'data-testid="sitrep-open-decisions-btn"' in body
    compact = "".join(body.split())
    assert "OpenDecisions" in compact


@pytest.mark.django_db
def test_sitrep_view_25_open_variables_btn(commander_client, atlas_backend_project):
    sr = _background_sitrep(atlas_backend_project)
    body = commander_client.get(_view_url(sr)).content.decode()
    assert 'data-testid="sitrep-open-variables-btn"' in body
    compact = "".join(body.split())
    assert "OpenVariables" in compact


@pytest.mark.django_db
def test_sitrep_view_26_generate_another_dropdown(commander_client, atlas_backend_project, monkeypatch):
    monkeypatch.setattr(
        timezone,
        "now",
        lambda: dt.datetime(2026, 5, 11, 13, 0, tzinfo=dt.UTC),
    )
    sr = _background_sitrep(atlas_backend_project)
    gen = dt.datetime(2026, 5, 11, 10, 0, tzinfo=dt.UTC)
    SitRep.objects.filter(pk=sr.pk).update(generated_at=timezone.make_aware(gen) if timezone.is_naive(gen) else gen)
    sr.refresh_from_db()

    body = commander_client.get(_view_url(sr)).content.decode()

    assert "sitrep-generate-another-btn" in body
    assert "Generate SitRep for another period" in body
    assert 'data-testid="sitrep-period-since-this"' in body
    assert "Since last SitRep" in body
    assert 'aria-current="true"' in body
    assert "(3h ago)" in body


@pytest.mark.django_db
def test_sitrep_view_27_open_chat_link(commander_client, atlas_backend_project):
    sr = _background_sitrep(atlas_backend_project)
    body = commander_client.get(_view_url(sr)).content.decode()
    assert "Open Chat about this SitRep" in body
    assert "CHAT-FULLSCREEN-1" in body
    assert "sitrep_pk=" + str(sr.pk) in body


@pytest.mark.django_db
def test_sitrep_view_28_no_edit_delete_controls(commander_client, atlas_backend_project):
    sr = _background_sitrep(atlas_backend_project)
    body = commander_client.get(_view_url(sr)).content.decode()
    assert ">Edit</" not in body
    assert ">Delete</" not in body
    assert ">Modify</" not in body


@pytest.mark.django_db
def test_sitrep_view_29_back_to_list_navigation(commander_client, atlas_backend_project):
    sr = _background_sitrep(atlas_backend_project)
    body = commander_client.get(_view_url(sr)).content.decode()
    list_path = reverse("sitrep-list", kwargs={"project_slug": SLUG})
    assert list_path in body
    assert 'data-testid="sitrep-back-to-list"' in body


@pytest.mark.django_db
def test_sitrep_view_30_assessed_period_accessible(commander_client, atlas_backend_project):
    sr = _background_sitrep(atlas_backend_project)
    body = commander_client.get(_view_url(sr)).content.decode()
    assert 'id="sitrep-assessed-period-label"' in body
    assert "Assessed period" in body
    assert 'data-testid="sitrep-assessed-period"' in body
    assert 'aria-labelledby="sitrep-assessed-period-label"' in body


@pytest.mark.django_db
def test_sitrep_view_31_status_badge_accessible(commander_client, atlas_backend_project):
    sr = _background_sitrep(atlas_backend_project)
    body = commander_client.get(_view_url(sr)).content.decode()
    i = body.index('data-testid="sitrep-status-badge"')
    seg = body[i : i + 160]
    assert "No Variables" in seg
    assert "aria-label" in seg
