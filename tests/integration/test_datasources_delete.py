"""Integrations for DATASOURCES-DELETE_DATASOURCE-1 — disconnect flow."""

import pytest

from ingestion.models import DataSource, Project
from tests.factories import DataSourceFactory, ProjectFactory


@pytest.mark.django_db
def test_delete_modal_shows_datasource_name(commander_client: object) -> None:
    ds = DataSourceFactory(name="company-gitlab")
    r = commander_client.get(f"/datasources/{ds.pk}/delete/")
    assert r.status_code == 200
    body = r.content.decode()
    assert "company-gitlab" in body
    assert "Disconnect" in body


@pytest.mark.django_db
def test_delete_modal_shows_project_count_zero(commander_client: object) -> None:
    ds = DataSourceFactory()
    r = commander_client.get(f"/datasources/{ds.pk}/delete/")
    assert r.status_code == 200
    body = r.content.decode()
    assert "Project(s)" in body
    assert "0</strong>" in body or ">0<" in body


@pytest.mark.django_db
def test_delete_modal_shows_project_count_three(commander_client: object) -> None:
    ds = DataSourceFactory()
    for i in range(3):
        ProjectFactory(datasource=ds, name=f"p{i}", slug=f"p{i}-slug-{ds.pk}")
    r = commander_client.get(f"/datasources/{ds.pk}/delete/")
    assert r.status_code == 200
    assert "3" in r.content.decode()


@pytest.mark.django_db
def test_disconnect_post_removes_datasource(commander_client: object) -> None:
    ds = DataSourceFactory()
    pk = ds.pk
    r = commander_client.post(f"/datasources/{pk}/delete/", {}, follow=False)
    assert r.status_code == 302
    assert not DataSource.objects.filter(pk=pk).exists()


@pytest.mark.django_db
def test_disconnect_redirects_to_list(commander_client: object) -> None:
    ds = DataSourceFactory()
    r = commander_client.post(f"/datasources/{ds.pk}/delete/", {}, follow=False)
    assert r.status_code == 302
    assert r.headers.get("Location", "").endswith("/datasources/")


@pytest.mark.django_db
def test_disconnect_orphans_projects(commander_client: object) -> None:
    ds = DataSourceFactory()
    p1 = ProjectFactory(datasource=ds, name="a1", slug=f"or-a1-{ds.pk}")
    p2 = ProjectFactory(datasource=ds, name="a2", slug=f"or-a2-{ds.pk}")
    r = commander_client.post(f"/datasources/{ds.pk}/delete/", {}, follow=False)
    assert r.status_code == 302
    p1.refresh_from_db()
    p2.refresh_from_db()
    assert p1.status == Project.Status.ORPHANED
    assert p2.status == Project.Status.ORPHANED
    assert p1.datasource_id is None


@pytest.mark.django_db
def test_cancel_link_points_to_detail(commander_client: object) -> None:
    ds = DataSourceFactory()
    r = commander_client.get(f"/datasources/{ds.pk}/delete/")
    assert r.status_code == 200
    assert (
        f'href="/datasources/{ds.pk}/"' in r.content.decode() or f'href="/datasources/{ds.pk}/"' in r.content.decode()
    )
