import pytest


@pytest.mark.django_db
def test_datasource_detail(commander_client, db):
    from ingestion.models import DataSource

    ds = DataSource.objects.create(
        name="co-gitlab",
        datasource_type=DataSource.Type.GITLAB,
        base_url="https://gitlab.example.com/",
    )
    r = commander_client.get(f"/datasources/{ds.pk}/")
    assert r.status_code == 200
    assert "co-gitlab" in r.content.decode()
