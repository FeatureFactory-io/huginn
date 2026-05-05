import pytest


@pytest.mark.django_db
def test_project_edit_screen_renders(commander_client):
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
    r = commander_client.get(f"/projects/{p.pk}/edit/")
    assert r.status_code == 200
    body = r.content.decode()
    assert "Edit project" in body
    assert "atlas-backend" in body


@pytest.mark.django_db
def test_project_edit_post_updates_display_name(commander_client):
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
    r = commander_client.post(
        f"/projects/{p.pk}/edit/",
        {"display_name": "Atlas Backend (Core)"},
        follow=False,
    )
    assert r.status_code == 302
    p.refresh_from_db()
    assert p.display_name == "Atlas Backend (Core)"
