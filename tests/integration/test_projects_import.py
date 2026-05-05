import pytest

from ingestion.models import DataSource, Project


@pytest.mark.django_db
def test_projects_import_screen_renders(commander_client):
    r = commander_client.get("/projects/import/")
    assert r.status_code == 200
    assert "Import projects" in r.content.decode()


@pytest.mark.django_db
def test_projects_import_refresh_then_import(commander_client, db):
    ds = DataSource.objects.create(
        name="gitlab-a",
        datasource_type=DataSource.Type.GITLAB,
        base_url="https://gitlab.example.com/",
    )
    refresh = commander_client.post(
        "/projects/import/",
        {"action": "refresh-catalog", "datasource_id": str(ds.pk)},
        follow=False,
    )
    assert refresh.status_code == 302

    catalog_key = f"{ds.name}/imported-{ds.pk}"
    imp = commander_client.post(
        "/projects/import/",
        {"action": "import", "datasource_id": str(ds.pk), "remote_keys": catalog_key},
        follow=False,
    )
    assert imp.status_code == 302
    assert Project.objects.filter(datasource=ds).exists()


@pytest.mark.django_db
def test_projects_list_links_to_import(commander_client):
    r = commander_client.get("/projects/")
    assert r.status_code == 200
    body = r.content.decode()
    assert "/projects/import/" in body
