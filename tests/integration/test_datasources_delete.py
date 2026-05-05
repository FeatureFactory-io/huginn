import pytest


@pytest.mark.django_db
def test_delete_confirm_get(commander_client, db):
    from ingestion.models import DataSource

    ds = DataSource.objects.create(
        name="gitlab-z",
        datasource_type=DataSource.Type.GITLAB,
        base_url="https://gitlab.example.com/",
    )
    r = commander_client.get(f"/datasources/{ds.pk}/delete/")
    assert r.status_code == 200


@pytest.mark.django_db
def test_delete_post_removes_row(commander_client, db):
    from ingestion.models import DataSource

    ds = DataSource.objects.create(
        name="gitlab-z",
        datasource_type=DataSource.Type.GITLAB,
        base_url="https://gitlab.example.com/",
    )
    r = commander_client.post(f"/datasources/{ds.pk}/delete/", {}, follow=False)
    assert r.status_code == 302
    assert not DataSource.objects.filter(pk=ds.pk).exists()
