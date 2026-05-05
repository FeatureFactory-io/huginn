import pytest

from ingestion.models import DataSource, Project


@pytest.mark.django_db
def test_project_archive_confirm_renders(commander_client):
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
    r = commander_client.get(f"/projects/{p.pk}/archive/")
    assert r.status_code == 200
    assert "atlas-backend" in r.content.decode()


@pytest.mark.django_db
def test_project_archive_post_archives(commander_client):
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
    r = commander_client.post(f"/projects/{p.pk}/archive/", {}, follow=False)
    assert r.status_code == 302
    p.refresh_from_db()
    assert p.status == Project.Status.ARCHIVED
