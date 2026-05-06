"""Unit tests for Project model defaults and constraints."""

import pytest
from django.db import IntegrityError, transaction

from ingestion.models import Project
from tests.factories import DataSourceFactory, ProjectFactory


@pytest.mark.django_db
def test_project_default_sync_state_is_initial_sync_queued() -> None:
    ds = DataSourceFactory()
    p = Project(datasource=ds, name="n", slug="n")
    assert p.sync_state == Project.SyncState.INITIAL_SYNC_QUEUED


@pytest.mark.django_db
def test_project_default_sync_schedule_is_hourly() -> None:
    ds = DataSourceFactory()
    p = Project(datasource=ds, name="n", slug="n")
    assert p.sync_schedule == Project.SyncSchedule.HOURLY


@pytest.mark.django_db
def test_project_has_description_field_default_empty() -> None:
    ds = DataSourceFactory()
    p = Project(datasource=ds, name="n", slug="n")
    assert p.description == ""

    persisted = Project.objects.create(datasource=ds, name="d", slug="slug-desc-test")
    assert persisted.description == ""


@pytest.mark.django_db
def test_project_imported_by_nullable() -> None:
    ds = DataSourceFactory()
    p = Project.objects.create(datasource=ds, name="n", slug="proj-nullable")
    assert p.imported_by_id is None


@pytest.mark.django_db
def test_project_gitlab_id_uniqueness_constraint_per_datasource() -> None:
    ds1 = DataSourceFactory()
    ds2 = DataSourceFactory(name="other-gl")
    gid = 42
    Project.objects.create(
        datasource=ds1,
        name="a",
        slug="proj-a",
        gitlab_project_id=gid,
    )
    with transaction.atomic():
        with pytest.raises(IntegrityError):
            Project.objects.create(
                datasource=ds1,
                name="b",
                slug="proj-b",
                gitlab_project_id=gid,
            )

    Project.objects.create(
        datasource=ds2,
        name="c",
        slug="proj-c",
        gitlab_project_id=gid,
    )
    assert Project.objects.filter(gitlab_project_id=gid).count() == 2


@pytest.mark.django_db
def test_project_factory_sets_sane_defaults() -> None:
    p = ProjectFactory()
    assert p.pk is not None
    assert p.sync_state == Project.SyncState.ACTIVE


@pytest.mark.django_db
def test_project_factory_default_sync_schedule_hourly() -> None:
    p = ProjectFactory()
    assert p.sync_schedule == Project.SyncSchedule.HOURLY


def test_sync_schedule_textchoices_values() -> None:
    values = {c.value for c in Project.SyncSchedule}
    assert values == {"hourly", "every_6h", "daily"}
