from datetime import timedelta

import pytest
from django.urls import reverse
from django.utils import timezone

from ingestion.models import DataSource, Project
from tests.factories import IncrementFactory, ProjectFactory


def _csrf(client):
    return client.cookies["csrftoken"].value


@pytest.mark.django_db
def test_transparency_widget_marker_on_project_detail(commander_client):
    """PROJECTS-VIEW_VITALS: Transparency card is rendered on Vitals tab."""
    p = ProjectFactory(sync_state=Project.SyncState.ACTIVE)
    r = commander_client.get(reverse("projects-detail", args=[p.pk]))
    assert r.status_code == 200
    assert 'data-testid="project-widget-transparency"' in r.content.decode()


@pytest.mark.django_db
def test_vitals_transparency_last_sync_humanized(commander_client):
    p = ProjectFactory(
        sync_state=Project.SyncState.ACTIVE,
        last_sync_at=timezone.now() - timedelta(hours=2),
    )
    body = commander_client.get(reverse("projects-detail", args=[p.pk])).content.decode()
    assert 'data-testid="project-transparency-last-sync"' in body
    assert "hours ago" in body


@pytest.mark.django_db
def test_vitals_transparency_last_commits_humanized(commander_client):
    p = ProjectFactory(sync_state=Project.SyncState.ACTIVE)
    IncrementFactory(project=p, occurred_at=timezone.now() - timedelta(hours=5))
    body = commander_client.get(reverse("projects-detail", args=[p.pk])).content.decode()
    assert 'data-testid="project-transparency-last-commits"' in body
    assert "hours ago" in body


@pytest.mark.django_db
def test_vitals_04_never_synced_shows_never(commander_client):
    p = ProjectFactory(last_sync_at=None, sync_state=Project.SyncState.ACTIVE)
    body = commander_client.get(reverse("projects-detail", args=[p.pk])).content.decode()
    assert 'data-testid="project-transparency-last-sync"' in body
    assert "Never" in body


@pytest.mark.django_db
def test_vitals_05_no_commits_shows_empty_copy(commander_client):
    p = ProjectFactory(sync_state=Project.SyncState.ACTIVE)
    body = commander_client.get(reverse("projects-detail", args=[p.pk])).content.decode()
    assert 'data-testid="project-transparency-last-commits"' in body
    assert "No commits yet" in body


@pytest.mark.django_db
def test_vitals_01_tab_labels_and_testids(commander_client):
    p = ProjectFactory(sync_state=Project.SyncState.ACTIVE)
    body = commander_client.get(reverse("projects-detail", args=[p.pk])).content.decode()
    assert 'data-testid="project-tab-vitals"' in body
    assert 'data-testid="project-tab-variables"' in body
    assert 'data-testid="project-tab-increments"' in body
    assert "Vitals</a>" in body
    assert "Increments" in body


@pytest.mark.django_db
def test_vitals_02_deeplink_tab_vitals_active(commander_client):
    p = ProjectFactory(sync_state=Project.SyncState.ACTIVE)
    body = commander_client.get(reverse("projects-detail", args=[p.pk]) + "?tab=vitals").content.decode()
    assert 'id="project-pane-vitals"' in body
    nav_at = body.index('data-testid="project-tab-vitals"')
    nav_snippet = body[nav_at - 200 : nav_at + 80]
    assert "nav-link" in nav_snippet
    assert "active" in nav_snippet
    assert 'aria-selected="true"' in nav_snippet


@pytest.mark.django_db
def test_vitals_06_vitals_coexistence_no_increments_table(commander_client):
    p = ProjectFactory(sync_state=Project.SyncState.ACTIVE, source_path="group/widget")
    body = commander_client.get(reverse("projects-detail", args=[p.pk])).content.decode()
    for tid in (
        "project-widget-transparency",
        "project-widget-variables",
        "project-informer-bar",
        "project-source-path",
    ):
        assert f'data-testid="{tid}"' in body
    assert 'data-testid="increments-table"' not in body


@pytest.mark.django_db
def test_vitals_header_shows_source_path(commander_client):
    p = ProjectFactory(sync_state=Project.SyncState.ACTIVE, source_path="group/acme")
    body = commander_client.get(reverse("projects-detail", args=[p.pk])).content.decode()
    assert 'data-testid="project-source-path"' in body
    assert "group/acme" in body


@pytest.mark.django_db
def test_project_detail_renders(commander_client):
    ds = DataSource.objects.create(
        name="gitlab-co",
        datasource_type=DataSource.Type.GITLAB,
        base_url="https://gitlab.example.com/",
    )
    p = ProjectFactory(
        datasource=ds,
        name="atlas-backend",
        slug="atlas-backend",
        sync_state=Project.SyncState.ACTIVE,
        source_path="co/atlas-backend",
    )
    r = commander_client.get(reverse("projects-detail", args=[p.pk]))
    assert r.status_code == 200
    body = r.content.decode()
    assert "atlas-backend" in body
    assert "gitlab-co" in body
    assert "project-sync-state" in body
    assert "project-open-sitreps" in body
    assert "project-widget-variables" in body
    assert "project-tab-vitals" in body
    assert "project-tab-variables" in body
    assert "project-tab-increments" in body
    assert "projects-placeholder-activity" not in body


@pytest.mark.django_db
def test_view_02_import_metadata_preserved_detail_loads(commander_client, commander_user):
    ds = DataSource.objects.create(
        name="gitlab-co",
        datasource_type=DataSource.Type.GITLAB,
        base_url="https://gitlab.example.com/",
    )
    p = ProjectFactory(
        datasource=ds,
        name="imp",
        slug="imp",
        imported_by=commander_user,
        sync_state=Project.SyncState.ACTIVE,
    )
    r = commander_client.get(reverse("projects-detail", args=[p.pk]))
    assert r.status_code == 200
    body = r.content.decode()
    assert 'data-testid="project-detail-name"' in body
    assert "imp" in body
    p.refresh_from_db()
    assert p.imported_by_id == commander_user.pk


@pytest.mark.django_db
def test_view_03_no_playbook_shows_informer_empty(commander_client):
    p = ProjectFactory(name="npb", slug="npb", playbook_slug="", sync_state=Project.SyncState.ACTIVE)
    body = commander_client.get(reverse("projects-detail", args=[p.pk])).content.decode()
    assert 'data-testid="informer-bar-empty"' in body
    assert "No Playbook assigned" in body


@pytest.mark.django_db
def test_view_05_edit_form_shows_sync_schedule(commander_client):
    p = ProjectFactory(
        name="sched",
        slug="sched",
        sync_schedule=Project.SyncSchedule.DAILY,
        sync_state=Project.SyncState.ACTIVE,
    )
    r = commander_client.get(reverse("projects-edit", args=[p.pk]))
    body = r.content.decode()
    assert 'data-testid="projects-edit-sync-schedule"' in body
    assert "Daily" in body


@pytest.mark.django_db
def test_view_06_active_status_shown(commander_client):
    p = ProjectFactory(name="actv", slug="actv", sync_state=Project.SyncState.ACTIVE)
    r = commander_client.get(reverse("projects-detail", args=[p.pk]))
    body = r.content.decode()
    assert 'data-testid="project-sync-state"' in body
    assert "Active" in body


@pytest.mark.django_db
def test_view_07_error_status_shown(commander_client):
    p = ProjectFactory(name="err", slug="err", sync_state=Project.SyncState.ERROR)
    r = commander_client.get(reverse("projects-detail", args=[p.pk]))
    assert "Error" in r.content.decode()


@pytest.mark.django_db
def test_view_13_action_buttons_accessible(commander_client):
    p = ProjectFactory(name="btns", slug="btns", sync_state=Project.SyncState.ACTIVE)
    r = commander_client.get(reverse("projects-detail", args=[p.pk]))
    body = r.content.decode()
    assert ">Edit<" in body or "Edit</a>" in body
    assert "Sync now" in body
    assert "Archive" in body


@pytest.mark.django_db
def test_project_sync_now_post_redirects(commander_client):
    ds = DataSource.objects.create(
        name="gitlab-co",
        datasource_type=DataSource.Type.GITLAB,
        base_url="https://gitlab.example.com/",
    )
    p = ProjectFactory(
        datasource=ds,
        name="atlas-backend",
        slug="atlas-backend",
        sync_state=Project.SyncState.ACTIVE,
    )
    commander_client.get(reverse("projects-detail", args=[p.pk]))
    r = commander_client.post(
        reverse("projects-sync-now", args=[p.pk]),
        {"csrfmiddlewaretoken": _csrf(commander_client), "tab": "vitals"},
        follow=False,
    )
    assert r.status_code == 302
    p.refresh_from_db()
    assert p.sync_state == Project.SyncState.ACTIVE
    assert "tab=vitals" in (r.get("Location") or "")
