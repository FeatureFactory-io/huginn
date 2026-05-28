"""SyncEngine orchestration tests for work items and milestones."""

import pytest
from django.utils import timezone

from ingestion.adapters.base import DataSourceAdapter
from ingestion.adapters.work_base import MilestoneAdapter, WorkItemAdapter
from ingestion.domain.increments import CommitIncrementDTO, ContributorDTO
from ingestion.domain.work import MilestoneDTO, UnitOfWorkDTO
from ingestion.models import Milestone, UnitOfWork, UoWStateChange
from ingestion.services.sync_engine import SyncEngine
from tests.factories import DataSourceFactory, ProjectFactory


def _commit_dtos():
    now = timezone.now()
    return [
        CommitIncrementDTO(
            external_id="sha111",
            occurred_at=now,
            contributor=ContributorDTO("gitlab", "a@example.com", "Alice"),
            summary="one",
        ),
    ]


def _work_dtos(state: str = "opened"):
    now = timezone.now()
    return [
        UnitOfWorkDTO(
            kind="issue",
            external_id="101",
            iid=1,
            title="Bug",
            state=state,
            created_at=now,
            updated_at=now,
            contributor=ContributorDTO("gitlab", "dev@example.com", "Dev"),
            labels=["bug"],
        ),
    ]


def _milestone_dtos():
    now = timezone.now()
    return [
        MilestoneDTO(
            external_id="55",
            title="v1.0",
            state="active",
            updated_at=now,
        ),
    ]


def _engine(commit_dtos=None, work_dtos=None, milestone_dtos=None):
    commit_dtos = commit_dtos if commit_dtos is not None else _commit_dtos()
    work_dtos = work_dtos if work_dtos is not None else _work_dtos()
    milestone_dtos = milestone_dtos if milestone_dtos is not None else _milestone_dtos()

    class StubIncrementAdapter(DataSourceAdapter):
        def fetch_increments(self, project, *, since):
            for dto in commit_dtos:
                if since is not None and dto.occurred_at < since:
                    continue
                yield dto

    class StubWorkAdapter(WorkItemAdapter):
        def fetch_work_items(self, project, *, since):
            for dto in work_dtos:
                if since is not None and dto.updated_at < since:
                    continue
                yield dto

    class StubMilestoneAdapter(MilestoneAdapter):
        def fetch_milestones(self, project, *, since):
            for dto in milestone_dtos:
                if since is not None and dto.updated_at < since:
                    continue
                yield dto

    return SyncEngine(
        classes_for=lambda _t: [StubIncrementAdapter],
        work_classes_for=lambda _t: [StubWorkAdapter],
        milestone_classes_for=lambda _t: [StubMilestoneAdapter],
    )


@pytest.mark.django_db
def test_sync_engine_persists_work_items_and_milestones() -> None:
    ds = DataSourceFactory()
    project = ProjectFactory(datasource=ds, external_project_id=1)
    run = _engine().run_for_project(project.pk)
    assert run is not None
    assert run.work_items_ingested == 1
    assert run.milestones_ingested == 1
    assert UnitOfWork.objects.filter(project=project, kind="issue").count() == 1
    assert Milestone.objects.filter(project=project).count() == 1


@pytest.mark.django_db
def test_sync_engine_appends_state_change_on_reopen() -> None:
    ds = DataSourceFactory()
    project = ProjectFactory(datasource=ds, external_project_id=1)
    engine_closed = _engine(work_dtos=_work_dtos("closed"))
    engine_closed.run_for_project(project.pk)
    assert UoWStateChange.objects.filter(unit_of_work__project=project).count() == 0

    engine_open = _engine(work_dtos=_work_dtos("opened"))
    engine_open.run_for_project(project.pk)
    change = UoWStateChange.objects.get(unit_of_work__project=project)
    assert change.from_state == "closed"
    assert change.to_state == "opened"


@pytest.mark.django_db
def test_sync_engine_idempotent_work_resync_no_duplicate_state() -> None:
    ds = DataSourceFactory()
    project = ProjectFactory(datasource=ds, external_project_id=1)
    engine = _engine()
    engine.run_for_project(project.pk)
    engine.run_for_project(project.pk)
    assert UnitOfWork.objects.filter(project=project).count() == 1
    assert UoWStateChange.objects.filter(unit_of_work__project=project).count() == 0
