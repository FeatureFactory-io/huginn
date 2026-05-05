import pytest


@pytest.mark.django_db
def test_project_detail_renders(commander_client):
    from ingestion.models import DataSource, Project

    ds = DataSource.objects.create(
        name="gitlab-co",
        datasource_type=DataSource.Type.GITLAB,
        base_url="https://gitlab.example.com/",
    )
    p = Project.objects.create(
        datasource=ds,
        name="atlas-backend",
        slug="atlas-backend",
    )
    r = commander_client.get(f"/projects/{p.pk}/")
    assert r.status_code == 200
    body = r.content.decode()
    assert "atlas-backend" in body
    assert "gitlab-co" in body


@pytest.mark.django_db
def test_project_sync_now_post_redirects(commander_client):
    from ingestion.models import DataSource, Project

    ds = DataSource.objects.create(
        name="gitlab-co",
        datasource_type=DataSource.Type.GITLAB,
        base_url="https://gitlab.example.com/",
    )
    p = Project.objects.create(
        datasource=ds,
        name="atlas-backend",
        slug="atlas-backend",
    )
    r = commander_client.post(f"/projects/{p.pk}/sync/", {}, follow=False)
    assert r.status_code == 302
