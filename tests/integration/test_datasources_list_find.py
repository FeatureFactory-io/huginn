import pytest


@pytest.mark.django_db
def test_datasources_list_renders(commander_client):
    response = commander_client.get("/datasources/")
    assert response.status_code == 200
    body = response.content.decode()
    assert "Data Sources" in body


@pytest.mark.django_db
def test_datasources_list_includes_db_rows(commander_client, db):
    """List shell renders; rows come from MIT wiring — not skeleton ORM listing."""
    from ingestion.models import DataSource

    DataSource.objects.create(
        name="company-gitlab",
        datasource_type=DataSource.Type.GITLAB,
        base_url="https://gitlab.example.com/",
    )
    response = commander_client.get("/datasources/")
    assert response.status_code == 200
    body = response.content.decode()
    assert "Data Sources" in body
    assert "company-gitlab" in body
