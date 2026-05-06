import pytest
from django.urls import reverse

from ingestion.models import DataSource, Project
from tests.factories import ProjectFactory


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
    assert "Manual only" not in body


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
        },
        follow=False,
    )
    assert r.status_code == 302
    p.refresh_from_db()
    assert p.sync_schedule == Project.SyncSchedule.EVERY_6H
