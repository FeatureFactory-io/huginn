import pytest
from django.urls import reverse

from ingestion.models import Project
from ingestion.tasks import sync_project_placeholder
from tests.factories import ProjectFactory


def _csrf(client):
    return client.cookies["csrftoken"].value


@pytest.mark.django_db
def test_project_archive_confirm_renders(commander_client):
    p = ProjectFactory(
        name="atlas-backend",
        slug="atlas-backend",
    )
    r = commander_client.get(reverse("projects-archive", args=[p.pk]))
    assert r.status_code == 200
    body = r.content.decode()
    assert "atlas-backend" in body
    assert "projects-archive-modal" in body


@pytest.mark.django_db
def test_project_archive_post_archives(commander_client):
    p = ProjectFactory(
        name="atlas-backend",
        slug="atlas-backend",
    )
    commander_client.get(reverse("projects-archive", args=[p.pk]))
    r = commander_client.post(
        reverse("projects-archive", args=[p.pk]),
        {"csrfmiddlewaretoken": _csrf(commander_client)},
        follow=False,
    )
    assert r.status_code == 302
    p.refresh_from_db()
    assert p.status == Project.Status.ARCHIVED


@pytest.mark.django_db
def test_archive_02_modal_copy(commander_client):
    p = ProjectFactory(name="atlas-backend", slug="atlas-backend")
    r = commander_client.get(reverse("projects-archive", args=[p.pk]))
    body = r.content.decode()
    assert "Syncs will stop. Ingested history is retained" in body
    assert "Project will not appear on the Tactical Plot." in body
    assert "btn-warning" in body
    assert "projects-archive-cancel" in body


@pytest.mark.django_db
def test_archive_04_archived_project_not_synced(commander_client):
    p = ProjectFactory(
        name="arc-sync",
        slug="arc-sync",
        status=Project.Status.ARCHIVED,
        sync_state=Project.SyncState.ERROR,
    )
    sync_project_placeholder(p.pk)
    p.refresh_from_db()
    assert p.sync_state == Project.SyncState.ERROR


@pytest.mark.django_db
def test_archive_06_archived_appears_in_filtered_list(commander_client):
    p = ProjectFactory(name="gone-arch", slug="gone-arch")
    commander_client.get(reverse("projects-archive", args=[p.pk]))
    commander_client.post(
        reverse("projects-archive", args=[p.pk]),
        {"csrfmiddlewaretoken": _csrf(commander_client)},
        follow=False,
    )
    r = commander_client.get(reverse("projects-list"), {"status": "archived"})
    assert "gone-arch" in r.content.decode()


@pytest.mark.django_db
def test_archive_08_cancel_does_not_archive(commander_client):
    p = ProjectFactory(name="stay-active", slug="stay-active")
    r_arch = commander_client.get(reverse("projects-archive", args=[p.pk]))
    body = r_arch.content.decode()
    assert reverse("projects-detail", args=[p.pk]) in body
    commander_client.get(reverse("projects-detail", args=[p.pk]))
    p.refresh_from_db()
    assert p.status == Project.Status.ACTIVE


@pytest.mark.django_db
def test_archive_10_button_accessible_label(commander_client):
    p = ProjectFactory(name="atlas-backend", slug="atlas-backend")
    commander_client.get(reverse("projects-archive", args=[p.pk]))
    r = commander_client.get(reverse("projects-archive", args=[p.pk]))
    body = r.content.decode()
    assert 'data-testid="confirm-archive-project"' in body
    assert "Archive atlas-backend" in body


@pytest.mark.skip(reason="PROJECTS-ARCHIVE_PROJECT-05 blocked until DASHBOARD-PROJECTS-1 exists")
@pytest.mark.django_db
def test_project_archive_removes_from_dashboard_when_configured():
    """Reserved for dashboard policy once DASHBOARD-PROJECTS-1 is defined."""
