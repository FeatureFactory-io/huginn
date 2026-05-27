"""SyncEngine orchestration."""

import pytest
from django.utils import timezone

from ingestion.adapters.base import DataSourceAdapter
from ingestion.domain.increments import CommitIncrementDTO, ContributorDTO
from ingestion.models import Increment, IngestionRun, Project
from ingestion.services.sync_engine import SyncEngine
from tests.factories import DataSourceFactory, ProjectFactory


def _dtos():
    now = timezone.now()
    return [
        CommitIncrementDTO(
            external_id="sha111",
            occurred_at=now,
            contributor=ContributorDTO("gitlab", "a@example.com", "Alice"),
            summary="one",
        ),
    ]


def _stub_classes(dtos: list):
    class StubAdapter(DataSourceAdapter):
        def fetch_increments(self, project, *, since):
            for d in dtos:
                if since is not None and d.occurred_at < since:
                    continue
                yield d

    return [StubAdapter]


@pytest.mark.django_db
def test_sync_engine_success_inserts_increment() -> None:
    ds = DataSourceFactory()
    p = ProjectFactory(datasource=ds, gitlab_project_id=1)
    engine = SyncEngine(
        classes_for=lambda _t: _stub_classes(_dtos()),
        work_classes_for=lambda _t: [],
        milestone_classes_for=lambda _t: [],
    )
    run = engine.run_for_project(p.pk)
    assert run is not None
    assert run.status == IngestionRun.Status.SUCCESS
    p.refresh_from_db()
    assert p.sync_state == Project.SyncState.ACTIVE
    assert Increment.objects.filter(project=p, external_id="sha111").count() == 1


@pytest.mark.django_db
def test_sync_engine_idempotent_second_run() -> None:
    ds = DataSourceFactory()
    p = ProjectFactory(datasource=ds, gitlab_project_id=1)
    dtos = _dtos()
    engine = SyncEngine(
        classes_for=lambda _t: _stub_classes(dtos),
        work_classes_for=lambda _t: [],
        milestone_classes_for=lambda _t: [],
    )
    engine.run_for_project(p.pk)
    engine.run_for_project(p.pk)
    assert Increment.objects.filter(project=p).count() == 1


@pytest.mark.django_db
def test_sync_engine_skips_archived() -> None:
    p = ProjectFactory(status=Project.Status.ARCHIVED)
    engine = SyncEngine(
        classes_for=lambda _t: _stub_classes(_dtos()),
        work_classes_for=lambda _t: [],
        milestone_classes_for=lambda _t: [],
    )
    assert engine.run_for_project(p.pk) is None


@pytest.mark.django_db
def test_sync_engine_skips_when_run_in_progress() -> None:
    ds = DataSourceFactory()
    p = ProjectFactory(datasource=ds, gitlab_project_id=1)
    IngestionRun.objects.create(project=p, datasource=ds, status=IngestionRun.Status.RUNNING)
    engine = SyncEngine(
        classes_for=lambda _t: _stub_classes(_dtos()),
        work_classes_for=lambda _t: [],
        milestone_classes_for=lambda _t: [],
    )
    assert engine.run_for_project(p.pk) is None


@pytest.mark.django_db
def test_sync_engine_error_no_datasource() -> None:
    p = ProjectFactory(datasource=None)
    engine = SyncEngine(
        classes_for=lambda _t: _stub_classes(_dtos()),
        work_classes_for=lambda _t: [],
        milestone_classes_for=lambda _t: [],
    )
    run = engine.run_for_project(p.pk)
    assert run is not None
    assert run.status == IngestionRun.Status.ERROR
    p.refresh_from_db()
    assert p.sync_state == Project.SyncState.ERROR
