"""Unit tests for DataSourcesService."""

from unittest.mock import patch

import pytest

from ingestion.integrations.gitlab_client import GitlabClient
from ingestion.models import DataSource, Project
from tests.factories import DataSourceFactory, ProjectFactory
from ui.services.datasources_service import DataSourcesService


@pytest.mark.django_db
def test_soft_delete_orphans_active_projects() -> None:
    ds = DataSourceFactory()
    p1 = ProjectFactory(datasource=ds)
    p2 = ProjectFactory(datasource=ds)
    svc = DataSourcesService()
    svc.soft_delete_gitlab_source(ds.pk)
    p1.refresh_from_db()
    p2.refresh_from_db()
    assert not DataSource.objects.filter(pk=ds.pk).exists()
    assert p1.status == Project.Status.ORPHANED
    assert p2.status == Project.Status.ORPHANED
    assert p1.datasource_id is None
    assert p2.datasource_id is None


@pytest.mark.django_db
def test_soft_delete_without_projects() -> None:
    ds = DataSourceFactory()
    pk = ds.pk
    DataSourcesService().soft_delete_gitlab_source(pk)
    assert not DataSource.objects.filter(pk=pk).exists()


@pytest.mark.django_db
def test_create_gitlab_source_persists_connection_metadata() -> None:
    with (
        patch.object(GitlabClient, "verify_token", return_value={"username": "ada", "name": "Ada"}),
        patch.object(GitlabClient, "get_visible_project_count", return_value=21),
    ):
        svc = DataSourcesService()
        ds = svc.create_gitlab_source(
            name="ada-gitlab",
            base_url="https://gitlab.example.com/",
            token="glpat-secret",
            token_expires_at=None,
        )
    assert ds.connected_user == "ada"
    assert ds.visible_project_count == 21
    assert ds.status == DataSource.Status.CONNECTED


def test_test_gitlab_connection_merges_project_count() -> None:
    with (
        patch.object(GitlabClient, "verify_token", return_value={"username": "bob"}),
        patch.object(GitlabClient, "get_visible_project_count", return_value=3),
    ):
        out = DataSourcesService().test_gitlab_connection(
            base_url="https://gitlab.example.com",
            token="tok",
        )
    assert out["username"] == "bob"
    assert out["visible_project_count"] == 3


def test_test_gitlab_connection_swallows_project_count_errors() -> None:
    with (
        patch.object(GitlabClient, "verify_token", return_value={"username": "bob"}),
        patch.object(GitlabClient, "get_visible_project_count", side_effect=ConnectionError("nope")),
    ):
        out = DataSourcesService().test_gitlab_connection(
            base_url="https://gitlab.example.com",
            token="tok",
        )
    assert out["visible_project_count"] is None
