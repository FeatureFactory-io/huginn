import pytest
from django.urls import reverse

from ingestion.models import DataSource, Project
from tests.factories import ProjectFactory, RulesOfEngagementFactory, RulesOfEngagementVersionFactory


def _csrf(client):
    return client.cookies["csrftoken"].value


@pytest.mark.django_db
def test_project_edit_screen_renders(commander_client):
    ds = DataSource.objects.create(
        name="gitlab-co",
        datasource_type=DataSource.Type.GITLAB,
        base_url="https://gitlab.example.com/",
    )
    p = ProjectFactory(
        datasource=ds,
        name="atlas-backend",
        slug="atlas-backend",
    )
    r = commander_client.get(reverse("projects-edit", args=[p.pk]))
    assert r.status_code == 200
    body = r.content.decode()
    assert "Edit Project" in body
    assert "atlas-backend" in body
    assert "projects-edit-sync-schedule" in body


@pytest.mark.django_db
def test_project_edit_post_updates_display_name(commander_client):
    ds = DataSource.objects.create(
        name="gitlab-co",
        datasource_type=DataSource.Type.GITLAB,
        base_url="https://gitlab.example.com/",
    )
    p = ProjectFactory(
        datasource=ds,
        name="atlas-backend",
        slug="atlas-backend",
    )
    commander_client.get(reverse("projects-edit", args=[p.pk]))
    r = commander_client.post(
        reverse("projects-edit", args=[p.pk]),
        {
            "csrfmiddlewaretoken": _csrf(commander_client),
            "display_name": "Atlas Backend (Core)",
            "sync_schedule": "daily",
            "assigned_roe": "",
            "pinned_roe_version": "",
        },
        follow=False,
    )
    assert r.status_code == 302
    p.refresh_from_db()
    assert p.display_name == "Atlas Backend (Core)"
    assert p.sync_schedule == Project.SyncSchedule.DAILY


@pytest.mark.django_db
def test_edit_03_schedule_defaults_hourly(commander_client):
    p = ProjectFactory(name="defh", slug="defh")
    r = commander_client.get(reverse("projects-edit", args=[p.pk]))
    body = r.content.decode()
    assert 'value="hourly" selected' in body


@pytest.mark.django_db
def test_edit_09_schedule_options(commander_client):
    p = ProjectFactory(name="opts", slug="opts")
    r = commander_client.get(reverse("projects-edit", args=[p.pk]))
    body = r.content.decode()
    assert "Every 6h" in body
    assert 'value="every_6h"' in body
    assert 'value="weekly"' in body
    assert 'value="manual"' in body
    assert "Weekly" in body
    assert "Manual" in body


@pytest.mark.django_db
def test_edit_11_empty_display_name_rejected(commander_client):
    p = ProjectFactory(name="keep-name", slug="keep-name", display_name="")
    commander_client.get(reverse("projects-edit", args=[p.pk]))
    r = commander_client.post(
        reverse("projects-edit", args=[p.pk]),
        {
            "csrfmiddlewaretoken": _csrf(commander_client),
            "display_name": "",
            "sync_schedule": "hourly",
            "assigned_roe": "",
            "pinned_roe_version": "",
        },
        follow=False,
    )
    assert r.status_code == 200
    p.refresh_from_db()
    assert p.display_name == ""
    assert "projects-edit-error" in r.content.decode() or "Display name is required" in r.content.decode()


@pytest.mark.django_db
def test_edit_12_cancel_link_goes_to_detail(commander_client):
    p = ProjectFactory(name="can", slug="can")
    r = commander_client.get(reverse("projects-edit", args=[p.pk]))
    body = r.content.decode()
    assert reverse("projects-detail", args=[p.pk]) in body


@pytest.mark.django_db
def test_edit_13_all_inputs_have_labels(commander_client):
    p = ProjectFactory(name="lbl", slug="lbl")
    r = commander_client.get(reverse("projects-edit", args=[p.pk]))
    body = r.content.decode()
    assert 'for="id_display_name"' in body
    assert 'for="id_sync_schedule"' in body
    assert 'for="id_assigned_roe"' in body
    assert 'for="id_pinned_version"' in body


@pytest.mark.django_db
def test_project_edit_post_assigns_roe_and_slug(commander_client):
    p = ProjectFactory(name="roe-assign", slug="roe-assign", roe_slug="")
    roe = RulesOfEngagementFactory(name="Roadmap RoE", slug="roadmap-roe")
    RulesOfEngagementVersionFactory(roe=roe, version_number=1)
    commander_client.get(reverse("projects-edit", args=[p.pk]))
    r = commander_client.post(
        reverse("projects-edit", args=[p.pk]),
        {
            "csrfmiddlewaretoken": _csrf(commander_client),
            "display_name": "RoE Assign",
            "sync_schedule": "hourly",
            "assigned_roe": str(roe.pk),
            "pinned_roe_version": "",
        },
        follow=False,
    )
    assert r.status_code == 302
    p.refresh_from_db()
    assert p.assigned_roe_id == roe.pk
    assert p.roe_slug == "roadmap-roe"
    assert p.pinned_roe_version_id is None


@pytest.mark.django_db
def test_project_edit_post_pins_version_when_valid(commander_client):
    p = ProjectFactory(name="roe-pin", slug="roe-pin")
    roe = RulesOfEngagementFactory(slug="pin-roe")
    v1 = RulesOfEngagementVersionFactory(roe=roe, version_number=1)
    commander_client.get(reverse("projects-edit", args=[p.pk]))
    r = commander_client.post(
        reverse("projects-edit", args=[p.pk]),
        {
            "csrfmiddlewaretoken": _csrf(commander_client),
            "display_name": "RoE Pin",
            "sync_schedule": "hourly",
            "assigned_roe": str(roe.pk),
            "pinned_roe_version": str(v1.pk),
        },
        follow=False,
    )
    assert r.status_code == 302
    p.refresh_from_db()
    assert p.pinned_roe_version_id == v1.pk


@pytest.mark.django_db
def test_project_edit_post_every_6h(commander_client):
    p = ProjectFactory(name="six", slug="six")
    commander_client.get(reverse("projects-edit", args=[p.pk]))
    r = commander_client.post(
        reverse("projects-edit", args=[p.pk]),
        {
            "csrfmiddlewaretoken": _csrf(commander_client),
            "display_name": "Six hour",
            "sync_schedule": "every_6h",
            "assigned_roe": "",
            "pinned_roe_version": "",
        },
        follow=False,
    )
    assert r.status_code == 302
    p.refresh_from_db()
    assert p.sync_schedule == Project.SyncSchedule.EVERY_6H


@pytest.mark.django_db
def test_edit_manual_schedule_saves(commander_client):
    p = ProjectFactory(name="manual", slug="manual")
    commander_client.get(reverse("projects-edit", args=[p.pk]))
    r = commander_client.post(
        reverse("projects-edit", args=[p.pk]),
        {
            "csrfmiddlewaretoken": _csrf(commander_client),
            "display_name": "Manual Project",
            "sync_schedule": "manual",
            "assigned_roe": "",
            "pinned_roe_version": "",
        },
        follow=False,
    )
    assert r.status_code == 302
    p.refresh_from_db()
    assert p.sync_schedule == Project.SyncSchedule.MANUAL


@pytest.mark.django_db
def test_edit_weekly_schedule_saves_day_and_hour(commander_client):
    p = ProjectFactory(name="weekly", slug="weekly")
    commander_client.get(reverse("projects-edit", args=[p.pk]))
    r = commander_client.post(
        reverse("projects-edit", args=[p.pk]),
        {
            "csrfmiddlewaretoken": _csrf(commander_client),
            "display_name": "Weekly Project",
            "sync_schedule": "weekly",
            "sync_weekly_day": "3",
            "sync_weekly_hour": "9",
            "assigned_roe": "",
            "pinned_roe_version": "",
        },
        follow=False,
    )
    assert r.status_code == 302
    p.refresh_from_db()
    assert p.sync_schedule == Project.SyncSchedule.WEEKLY
    assert p.sync_weekly_day == 3
    assert p.sync_weekly_hour == 9


@pytest.mark.django_db
def test_edit_daily_with_hour_saves(commander_client):
    p = ProjectFactory(name="daily-hour", slug="daily-hour")
    commander_client.get(reverse("projects-edit", args=[p.pk]))
    r = commander_client.post(
        reverse("projects-edit", args=[p.pk]),
        {
            "csrfmiddlewaretoken": _csrf(commander_client),
            "display_name": "Daily Hour Project",
            "sync_schedule": "daily",
            "sync_daily_hour": "8",
            "assigned_roe": "",
            "pinned_roe_version": "",
        },
        follow=False,
    )
    assert r.status_code == 302
    p.refresh_from_db()
    assert p.sync_schedule == Project.SyncSchedule.DAILY
    assert p.sync_daily_hour == 8


@pytest.mark.django_db
def test_edit_weekly_renders_existing_values(commander_client):
    p = ProjectFactory(
        name="weekly-render",
        slug="weekly-render",
        sync_schedule=Project.SyncSchedule.WEEKLY,
        sync_weekly_day=3,
        sync_weekly_hour=9,
    )
    r = commander_client.get(reverse("projects-edit", args=[p.pk]))
    body = r.content.decode()
    assert 'value="weekly" selected' in body
    assert 'value="3" selected' in body
    assert 'value="9" selected' in body
    assert "projects-edit-sync-weekly-day" in body
    assert "projects-edit-sync-weekly-hour" in body


@pytest.mark.django_db
def test_edit_switching_from_weekly_clears_fields(commander_client):
    p = ProjectFactory(
        name="weekly-clear",
        slug="weekly-clear",
        sync_schedule=Project.SyncSchedule.WEEKLY,
        sync_weekly_day=3,
        sync_weekly_hour=9,
    )
    commander_client.get(reverse("projects-edit", args=[p.pk]))
    r = commander_client.post(
        reverse("projects-edit", args=[p.pk]),
        {
            "csrfmiddlewaretoken": _csrf(commander_client),
            "display_name": "Weekly Clear",
            "sync_schedule": "hourly",
            "assigned_roe": "",
            "pinned_roe_version": "",
        },
        follow=False,
    )
    assert r.status_code == 302
    p.refresh_from_db()
    assert p.sync_schedule == Project.SyncSchedule.HOURLY
    assert p.sync_weekly_day is None
    assert p.sync_weekly_hour is None
