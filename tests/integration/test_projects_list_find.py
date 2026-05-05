import pytest


@pytest.mark.django_db
def test_projects_list(commander_client, db):
    r = commander_client.get("/projects/")
    assert r.status_code == 200
    assert "Projects" in r.content.decode()


@pytest.mark.django_db
def test_projects_list_shows_imported_rows(commander_client, db):
    from ingestion.models import DataSource, Project

    ds = DataSource.objects.create(
        name="co-gl",
        datasource_type=DataSource.Type.GITLAB,
        base_url="https://gitlab.example.com/",
    )
    Project.objects.create(
        datasource=ds,
        name="atlas",
        slug="atlas",
    )
    r = commander_client.get("/projects/")
    assert r.status_code == 200
    body = r.content.decode()
    assert "Projects" in body
    assert "atlas" in body
