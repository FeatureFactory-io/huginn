import pytest


@pytest.mark.django_db
def test_edit_get(commander_client, db):
    from ingestion.models import DataSource

    ds = DataSource.objects.create(
        name="gitlab-x",
        datasource_type=DataSource.Type.GITLAB,
        base_url="https://gitlab.example.com/",
    )
    r = commander_client.get(f"/datasources/{ds.pk}/edit/")
    assert r.status_code == 200


@pytest.mark.django_db
def test_edit_post_redirects(commander_client, db):
    from ingestion.models import DataSource

    ds = DataSource.objects.create(
        name="gitlab-x",
        datasource_type=DataSource.Type.GITLAB,
        base_url="https://gitlab.example.com/",
    )
    r = commander_client.post(
        f"/datasources/{ds.pk}/edit/",
        {"name": "gitlab-x", "base_url": "https://gitlab-edited.example.com/"},
        follow=False,
    )
    assert r.status_code == 302
    ds.refresh_from_db()
    assert "gitlab-edited" in ds.base_url
