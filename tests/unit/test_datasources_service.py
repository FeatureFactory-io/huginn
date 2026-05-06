"""Unit tests for DataSourcesService."""

import pytest

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
