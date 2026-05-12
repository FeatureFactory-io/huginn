"""SITREP-LIST+FIND-1 — pytest translation of `sitrep-list-find.feature`."""

from __future__ import annotations

import datetime as dt
from unittest.mock import MagicMock, patch

import pytest
from django.urls import reverse
from django.utils import timezone

from sitrep.models import SitRep
from tests.factories import PlaybookFactory, PlaybookVersionFactory, ProjectFactory

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


def _list_url() -> str:
    return reverse("sitrep-list", kwargs={"project_slug": SLUG})


def _make_sitrep(project, **kwargs):
    defaults = {
        "from_dt": timezone.now() - dt.timedelta(hours=1),
        "to_dt": timezone.now(),
        "trigger": "automatic",
        "headline": "Headline",
        "situation_assessment": "Assessment",
        "playbook_version": 1,
    }
    defaults.update(kwargs)
    return SitRep.objects.create(project=project, **defaults)


@pytest.mark.django_db
def test_sitrep_list_find_01_page_header(commander_client, atlas_backend_project):
    r = commander_client.get(_list_url())
    assert r.status_code == 200
    assert "SitReps — atlas-backend" in r.content.decode()


@pytest.mark.django_db
def test_sitrep_list_find_02_navigate_from_project_view(commander_client, atlas_backend_project):
    p = atlas_backend_project
    detail_url = reverse("projects-detail", args=[p.pk])
    r0 = commander_client.get(detail_url)
    assert r0.status_code == 200
    body0 = r0.content.decode()
    assert 'data-testid="project-open-sitreps"' in body0
    list_path = reverse("sitrep-list", kwargs={"project_slug": p.slug})
    assert list_path in body0
    r1 = commander_client.get(list_path)
    assert r1.status_code == 200
    assert "sitrep-list-find-loaded" in r1.content.decode()


@pytest.mark.django_db
def test_sitrep_list_find_06_table_columns(commander_client, atlas_backend_project):
    _make_sitrep(atlas_backend_project)
    r = commander_client.get(_list_url())
    body = r.content.decode()
    for label in (
        "Generated at",
        "Assessed period",
        "Trigger",
        "Status",
        "Headline",
        "Decisions proposed",
        "Decisions accepted",
        "Playbook version",
        "Row actions",
    ):
        assert label in body


@pytest.mark.django_db
def test_sitrep_list_find_07_sorted_newest_first(commander_client, atlas_backend_project):
    p = atlas_backend_project
    older = dt.datetime(2026, 5, 10, 9, 0, tzinfo=dt.UTC)
    newer = dt.datetime(2026, 5, 11, 13, 15, tzinfo=dt.UTC)
    _make_sitrep(
        p,
        from_dt=older,
        to_dt=older + dt.timedelta(hours=1),
        headline="Old row",
    )
    sr_new = _make_sitrep(
        p,
        from_dt=newer - dt.timedelta(hours=1),
        to_dt=newer,
        headline="New row",
    )
    SitRep.objects.filter(pk=sr_new.pk).update(generated_at=newer)
    SitRep.objects.exclude(pk=sr_new.pk).filter(project=p).update(generated_at=older)

    r = commander_client.get(_list_url())
    body = r.content.decode()
    tbody_pos = body.index("<tbody>")
    chunk = body[tbody_pos:]
    assert chunk.index("2026-05-11 13:15") < chunk.index("2026-05-10 09:00")


@pytest.mark.django_db
def test_sitrep_list_find_08_row_view_navigates(commander_client, atlas_backend_project):
    p = atlas_backend_project
    when = dt.datetime(2026, 5, 11, 13, 15, tzinfo=dt.UTC)
    sr = _make_sitrep(
        p,
        from_dt=when - dt.timedelta(hours=1),
        to_dt=when,
        headline="Row A",
    )
    SitRep.objects.filter(pk=sr.pk).update(generated_at=when)

    r0 = commander_client.get(_list_url())
    assert r0.status_code == 200
    view_url = reverse("sitrep-detail", kwargs={"project_slug": SLUG, "pk": sr.pk})
    assert view_url in r0.content.decode()

    r1 = commander_client.get(view_url)
    assert r1.status_code == 200
    body1 = r1.content.decode()
    assert "SITREP-VIEW_SITREP-1" in body1
    assert "sitrep-view-sitrep-loaded" in body1


@pytest.mark.django_db
def test_sitrep_list_find_09_manual_trigger_label(commander_client, atlas_backend_project):
    _make_sitrep(atlas_backend_project, trigger="manual", headline="Manual SR")
    r = commander_client.get(_list_url())
    assert "Manual" in r.content.decode()


@pytest.mark.django_db
def test_sitrep_list_find_10_auto_trigger_label(commander_client, atlas_backend_project):
    _make_sitrep(atlas_backend_project, trigger="automatic", headline="Auto SR")
    body = commander_client.get(_list_url()).content.decode()
    assert ">Auto<" in body or "Auto</span>" in body


@pytest.mark.django_db
def test_sitrep_list_find_11_filter_by_manual(commander_client, atlas_backend_project):
    p = atlas_backend_project
    _make_sitrep(p, trigger="manual", headline="Only manual")
    _make_sitrep(
        p,
        trigger="automatic",
        headline="Hidden when manual filter",
        to_dt=timezone.now() + dt.timedelta(seconds=5),
    )

    r = commander_client.get(_list_url(), {"trigger": "manual"})
    body = r.content.decode()
    assert "Only manual" in body
    assert "Hidden when manual filter" not in body


@pytest.mark.django_db
def test_sitrep_list_find_12_filter_by_auto(commander_client, atlas_backend_project):
    p = atlas_backend_project
    _make_sitrep(p, trigger="automatic", headline="Only auto")
    _make_sitrep(
        p,
        trigger="manual",
        headline="Hidden when auto filter",
        to_dt=timezone.now() + dt.timedelta(seconds=5),
    )

    r = commander_client.get(_list_url(), {"trigger": "automatic"})
    body = r.content.decode()
    assert "Only auto" in body
    assert "Hidden when auto filter" not in body


@pytest.mark.django_db
def test_sitrep_list_find_13_filter_by_date_range(commander_client, atlas_backend_project):
    p = atlas_backend_project
    early = dt.datetime(2026, 5, 9, 9, 0, tzinfo=dt.UTC)
    late = dt.datetime(2026, 5, 11, 13, 15, tzinfo=dt.UTC)
    sr_early = _make_sitrep(
        p,
        from_dt=early,
        to_dt=early + dt.timedelta(hours=1),
        headline="Early SR",
    )
    SitRep.objects.filter(pk=sr_early.pk).update(generated_at=early)
    sr_late = _make_sitrep(
        p,
        from_dt=late - dt.timedelta(hours=1),
        to_dt=late,
        headline="Late SR",
    )
    SitRep.objects.filter(pk=sr_late.pk).update(generated_at=late)

    r = commander_client.get(
        _list_url(),
        {"generated_from": "2026-05-11", "generated_to": "2026-05-11"},
    )
    body = r.content.decode()
    assert "2026-05-11 13:15" in body
    assert "Early SR" not in body


@pytest.mark.django_db
def test_sitrep_list_find_14_filter_by_playbook_version(commander_client, atlas_backend_project):
    p = atlas_backend_project
    _make_sitrep(p, playbook_version=1, headline="V1 SR", to_dt=timezone.now())
    _make_sitrep(
        p,
        playbook_version=2,
        headline="V2 SR",
        to_dt=timezone.now() + dt.timedelta(seconds=10),
    )

    r = commander_client.get(_list_url(), {"pb_version": "1"})
    body = r.content.decode()
    assert "V1 SR" in body
    assert "V2 SR" not in body


@pytest.mark.django_db
def test_sitrep_list_find_15_generate_button_visible(commander_client, atlas_backend_project):
    r = commander_client.get(_list_url())
    body = r.content.decode()
    assert 'data-testid="generate-sitrep-btn"' in body
    assert "Generate SitRep" in body


@pytest.mark.django_db
def test_sitrep_list_find_16_period_presets_listed(commander_client, atlas_backend_project):
    r = commander_client.get(_list_url())
    body = r.content.decode()
    for fragment in (
        "Since last SitRep",
        "Last 2 hours",
        "Last 4 hours",
        "Today",
        "Yesterday",
        "Custom…",
    ):
        assert fragment in body


@pytest.mark.django_db
def test_sitrep_list_find_17_since_last_disabled(commander_client, atlas_backend_project):
    r = commander_client.get(_list_url())
    body = r.content.decode()
    assert 'data-testid="sitrep-period-since-last"' in body
    assert "disabled" in body
    assert "No previous SitRep — use a custom period" in body


@pytest.mark.django_db
def test_sitrep_list_find_18_since_last_window_label(commander_client, atlas_backend_project, settings):
    settings.TIME_ZONE = "UTC"
    p = atlas_backend_project
    now = timezone.now()
    past = now - dt.timedelta(hours=3, minutes=20)
    sr = _make_sitrep(
        p,
        from_dt=past - dt.timedelta(hours=1),
        to_dt=past,
        headline="Prior",
    )
    SitRep.objects.filter(pk=sr.pk).update(generated_at=past)

    r = commander_client.get(_list_url())
    body = r.content.decode()
    assert "Since last SitRep (" in body
    assert "3h 20m ago" in body


@pytest.mark.django_db
def test_sitrep_list_find_19_custom_period_fields(commander_client, atlas_backend_project):
    r = commander_client.get(_list_url(), {"period": "custom"})
    assert r.status_code == 200
    body = r.content.decode()
    assert 'data-testid="sitrep-custom-from"' in body
    assert 'data-testid="sitrep-custom-to"' in body
    assert 'data-testid="sitrep-generate-custom-panel"' in body
    assert 'name="custom_to"' in body and "value=" in body


@pytest.mark.django_db
def test_sitrep_list_find_20_preset_fires_generate_toast(commander_client, atlas_backend_project):
    p = atlas_backend_project
    prior = timezone.now() - dt.timedelta(hours=2)
    sr = _make_sitrep(
        p,
        from_dt=prior - dt.timedelta(hours=1),
        to_dt=prior,
        headline="Earlier",
    )
    SitRep.objects.filter(pk=sr.pk).update(generated_at=prior)

    delay_mock = MagicMock()
    with patch("ui.views.sitrep_views.generate_sitrep_for_project.delay", delay_mock):
        r = commander_client.post(
            reverse("sitrep-generate", kwargs={"project_slug": SLUG}),
            {"period": "since_last"},
        )
    assert r.status_code == 202
    assert "SitRep generation started" in r.content.decode()
    delay_mock.assert_called_once()


@pytest.mark.django_db
def test_sitrep_list_find_21_empty_state(commander_client, atlas_backend_project):
    r = commander_client.get(_list_url())
    body = r.content.decode()
    assert "No SitReps yet." in body
    assert "Gjallarhorn generates the first SitRep automatically when sync completes" in body
    assert 'data-testid="empty-state-cta"' in body


@pytest.mark.django_db
def test_sitrep_list_find_22_generate_button_accessible_label(commander_client, atlas_backend_project):
    r = commander_client.get(_list_url())
    body = r.content.decode()
    assert 'data-testid="generate-sitrep-btn"' in body
    assert 'aria-label="Generate SitRep"' in body
