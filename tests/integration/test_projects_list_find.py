import pytest
from django.urls import reverse

from ingestion.models import DataSource, Project
from tests.factories import PlaybookFactory, ProjectFactory


@pytest.mark.django_db
def test_projects_list(commander_client, db):
    r = commander_client.get(reverse("projects-list"))
    assert r.status_code == 200
    assert "Projects" in r.content.decode()


@pytest.mark.django_db
def test_list_02_table_has_required_columns(commander_client, db):
    ProjectFactory(name="sole", slug="sole")
    r = commander_client.get(reverse("projects-list"))
    assert r.status_code == 200
    body = r.content.decode()
    for label in ("Name", "Data source", "Playbook", "Last sync", "Last SitRep", "Last SitRep generated", "Status"):
        assert label in body


@pytest.mark.django_db
def test_list_04_no_playbook_shows_not_assigned(commander_client, db):
    ProjectFactory(name="nopb", slug="nopb", playbook_slug="")
    r = commander_client.get(reverse("projects-list"))
    assert "Not assigned" in r.content.decode()


@pytest.mark.django_db
def test_list_05_newly_imported_shows_initial_sync_queued(commander_client, db):
    ProjectFactory(
        name="queued",
        slug="queued",
        sync_state=Project.SyncState.INITIAL_SYNC_QUEUED,
    )
    r = commander_client.get(reverse("projects-list"))
    assert "Initial sync queued" in r.content.decode()


@pytest.mark.django_db
def test_list_06_view_action_link_present(commander_client, db):
    p = ProjectFactory(name="v", slug="v")
    r = commander_client.get(reverse("projects-list"))
    body = r.content.decode()
    assert f'data-testid="projects-row-name-{p.pk}"' in body
    assert reverse("projects-detail", args=[p.pk]) in body


@pytest.mark.django_db
def test_list_07_edit_action_link_present(commander_client, db):
    p = ProjectFactory(name="e", slug="e")
    r = commander_client.get(reverse("projects-list"))
    body = r.content.decode()
    assert f'data-testid="projects-row-edit-{p.pk}"' in body
    assert f"/projects/{p.pk}/edit/" in body


@pytest.mark.django_db
def test_list_08_archive_action_link_present(commander_client, db):
    p = ProjectFactory(name="a", slug="a")
    r = commander_client.get(reverse("projects-list"))
    body = r.content.decode()
    assert f'data-testid="projects-row-archive-{p.pk}"' in body
    assert f"/projects/{p.pk}/archive/" in body


@pytest.mark.django_db
def test_list_11_filter_status_active(commander_client, db):
    ProjectFactory(name="only-active-proj", slug="only-active-proj", status=Project.Status.ACTIVE)
    ProjectFactory(name="only-archived-proj", slug="only-archived-proj", status=Project.Status.ARCHIVED)
    r = commander_client.get(reverse("projects-list"), {"status": "active"})
    body = r.content.decode()
    assert "only-active-proj" in body
    assert "only-archived-proj" not in body


@pytest.mark.django_db
def test_list_12_filter_status_archived(commander_client, db):
    ProjectFactory(name="list12-active", slug="list12-active", status=Project.Status.ACTIVE)
    ProjectFactory(name="list12-archived", slug="list12-archived", status=Project.Status.ARCHIVED)
    r = commander_client.get(reverse("projects-list"), {"status": "archived"})
    body = r.content.decode()
    assert "list12-archived" in body
    assert "list12-active" not in body


@pytest.mark.django_db
def test_list_13_filter_status_orphaned(commander_client, db):
    ProjectFactory(name="orph", slug="orph", status=Project.Status.ORPHANED)
    ProjectFactory(name="norm", slug="norm", status=Project.Status.ACTIVE)
    r = commander_client.get(reverse("projects-list"), {"status": "orphaned"})
    body = r.content.decode()
    assert "orph" in body
    assert "norm" not in body


@pytest.mark.django_db
def test_list_17_nav_projects_active(commander_client):
    r = commander_client.get(reverse("projects-list"))
    body = r.content.decode()
    assert 'data-testid="nav-projects"' in body
    assert "nav-link active" in body


@pytest.mark.django_db
def test_projects_list_shows_imported_rows(commander_client, db):
    ds = DataSource.objects.create(
        name="co-gl",
        datasource_type=DataSource.Type.GITLAB,
        base_url="https://gitlab.example.com/",
    )
    ProjectFactory(
        datasource=ds,
        name="atlas",
        slug="atlas",
        sync_state=Project.SyncState.ACTIVE,
    )
    r = commander_client.get(reverse("projects-list"))
    assert r.status_code == 200
    body = r.content.decode()
    assert "Projects" in body
    assert "atlas" in body
    assert "projects-list-table" in body


@pytest.mark.django_db
def test_projects_list_filter_by_datasource(commander_client, db):
    ds_a = DataSource.objects.create(
        name="gl-a",
        datasource_type=DataSource.Type.GITLAB,
        base_url="https://a.example.com/",
    )
    ds_b = DataSource.objects.create(
        name="gl-b",
        datasource_type=DataSource.Type.GITLAB,
        base_url="https://b.example.com/",
    )
    ProjectFactory(datasource=ds_a, name="only-a", slug="only-a")
    ProjectFactory(datasource=ds_b, name="only-b", slug="only-b")

    r = commander_client.get(reverse("projects-list"), {"datasource": str(ds_a.pk)})
    body = r.content.decode()
    assert "only-a" in body
    assert "only-b" not in body


@pytest.mark.django_db
def test_projects_list_import_banner_query(commander_client):
    r = commander_client.get(reverse("projects-list"), {"imported": "1"})
    body = r.content.decode()
    assert "projects-list-import-banner" in body


@pytest.mark.django_db
def test_projects_list_filter_playbook_matches_assigned_fk(commander_client, db):
    pb = PlaybookFactory(name="Zebra Analytics", slug="zebra-analytics")
    ProjectFactory(name="with-pb", slug="with-pb", assigned_playbook=pb, playbook_slug=pb.slug)
    ProjectFactory(name="no-pb", slug="no-pb", playbook_slug="")

    r = commander_client.get(reverse("projects-list"), {"playbook": "Zebra"})
    body = r.content.decode()
    assert "with-pb" in body
    assert "no-pb" not in body


@pytest.mark.django_db
def test_projects_list_empty_state_cta(commander_client):
    r = commander_client.get(reverse("projects-list"), {"playbook": "no-such-slug-xyz"})
    body = r.content.decode()
    assert "projects-empty-state" in body
    assert "projects-empty-cta-import" in body
