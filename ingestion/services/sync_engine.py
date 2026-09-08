"""Orchestrate ingestion runs for a single :class:`~ingestion.models.Project`."""

from __future__ import annotations

import logging
from collections.abc import Callable
from datetime import timedelta
from typing import TYPE_CHECKING

from django.db import transaction
from django.utils import timezone

from ingestion.adapters import (
    adapter_classes_for,
    milestone_adapter_classes_for,
    work_adapter_classes_for,
)
from ingestion.domain.increments import IncrementDTO
from ingestion.domain.work import MilestoneDTO, UnitOfWorkDTO
from ingestion.models import (
    Contributor,
    DataSource,
    Increment,
    IngestionRun,
    Milestone,
    Project,
    UnitOfWork,
    UoWStateChange,
)
from ingestion.signals import sync_project_completed

if TYPE_CHECKING:
    from ingestion.adapters.base import DataSourceAdapter
    from ingestion.adapters.work_base import MilestoneAdapter, WorkItemAdapter

logger = logging.getLogger("ingestion.sync")

SYNC_LOOKBACK_DAYS = 90


class SyncEngine:
    """Runs registered adapter classes for one project."""

    def __init__(
        self,
        classes_for: Callable[[str], list[type[DataSourceAdapter]]] | None = None,
        work_classes_for: Callable[[str], list[type[WorkItemAdapter]]] | None = None,
        milestone_classes_for: Callable[[str], list[type[MilestoneAdapter]]] | None = None,
    ) -> None:
        self._classes_for = classes_for or adapter_classes_for
        self._work_classes_for = work_classes_for or work_adapter_classes_for
        self._milestone_classes_for = milestone_classes_for or milestone_adapter_classes_for

    def run_for_project(self, project_id: int) -> IngestionRun | None:
        logger.info("sync start project_id=%s", project_id)
        try:
            project = Project.objects.select_related("datasource").get(pk=project_id)
        except Project.DoesNotExist:
            logger.warning("sync skipped project_id=%s reason=missing", project_id)
            return None

        if project.status == Project.Status.ARCHIVED:
            logger.info("sync skipped project_id=%s reason=archived", project_id)
            return None

        if IngestionRun.objects.filter(
            project=project,
            status=IngestionRun.Status.RUNNING,
            finished_at__isnull=True,
        ).exists():
            logger.info("sync skipped project_id=%s reason=run_in_progress", project_id)
            return None

        run = IngestionRun.objects.create(
            project=project,
            datasource=project.datasource,
            status=IngestionRun.Status.RUNNING,
        )
        logger.info(
            "sync run opened run_id=%s project_id=%s datasource_id=%s datasource_type=%s external_project_id=%s",
            run.pk,
            project_id,
            project.datasource_id,
            project.datasource.datasource_type if project.datasource else None,
            project.external_project_id,
        )

        try:
            self._execute_run(project, run)
        except Exception as exc:  # noqa: BLE001
            logger.exception(
                "sync failed project_id=%s run_id=%s error=%s",
                project_id,
                run.pk,
                exc,
            )
            run.status = IngestionRun.Status.ERROR
            run.finished_at = timezone.now()
            run.error_message = str(exc)[:2000]
            run.save(update_fields=["status", "finished_at", "error_message"])
            Project.objects.filter(pk=project.pk).update(
                sync_state=Project.SyncState.ERROR,
                last_sync_at=timezone.now(),
            )
            return run

        run.status = IngestionRun.Status.SUCCESS
        run.finished_at = timezone.now()
        run.save(
            update_fields=[
                "status",
                "finished_at",
                "cursor_to",
                "increments_ingested",
                "work_items_ingested",
                "milestones_ingested",
                "contributors_touched",
            ]
        )
        sync_completed_at = timezone.now()
        Project.objects.filter(pk=project.pk).update(
            sync_state=Project.SyncState.ACTIVE,
            last_sync_at=sync_completed_at,
        )
        logger.info(
            "sync success project_id=%s run_id=%s increments=%s work_items=%s milestones=%s "
            "contributors=%s cursor_to=%s",
            project_id,
            run.pk,
            run.increments_ingested,
            run.work_items_ingested,
            run.milestones_ingested,
            run.contributors_touched,
            run.cursor_to,
        )
        self._emit_sitrep_signal_if_dump_had_data(project, run, sync_completed_at)
        return run

    def _emit_sitrep_signal_if_dump_had_data(self, project: Project, run: IngestionRun, to_dt) -> None:
        ingested = run.increments_ingested + run.work_items_ingested + run.milestones_ingested
        if ingested == 0:
            logger.info(
                "sync skip sitrep project_id=%s run_id=%s reason=empty dump increments=%s work_items=%s milestones=%s",
                project.pk,
                run.pk,
                run.increments_ingested,
                run.work_items_ingested,
                run.milestones_ingested,
            )
            return
        logger.info(
            "sync emit sitrep signal project_id=%s run_id=%s ingested=%s to_dt=%s",
            project.pk,
            run.pk,
            ingested,
            to_dt,
        )
        sync_project_completed.send(
            sender=self.__class__,
            project=project,
            to_dt=to_dt,
        )

    def _execute_run(self, project: Project, run: IngestionRun) -> None:
        if not project.datasource:
            run.cursor_to = timezone.now()
            run.save(update_fields=["cursor_to"])
            raise RuntimeError("Project has no DataSource — cannot ingest.")

        since = self._compute_since(project)
        ds_type = project.datasource.datasource_type
        logger.info(
            "sync execute run_id=%s project_id=%s datasource_type=%s since=%s lookback_days=%s",
            run.pk,
            project.pk,
            ds_type,
            since,
            SYNC_LOOKBACK_DAYS,
        )
        max_occurred = None
        increments_count = 0
        work_items_count = 0
        milestones_count = 0
        contributors_seen: set[tuple[int, str]] = set()

        for adapter_cls in self._milestone_classes_for(ds_type):
            adapter = adapter_cls(project.datasource)
            adapter_count = 0
            for dto in adapter.fetch_milestones(project, since=since):
                if not isinstance(dto, MilestoneDTO):
                    continue
                self._persist_milestone_dto(project, dto)
                milestones_count += 1
                adapter_count += 1
                max_occurred = dto.updated_at if max_occurred is None else max(max_occurred, dto.updated_at)
            logger.info(
                "sync adapter done run_id=%s adapter=%s phase=milestones fetched=%s total_milestones=%s",
                run.pk,
                adapter_cls.__name__,
                adapter_count,
                milestones_count,
            )

        for adapter_cls in self._classes_for(ds_type):
            adapter = self._instantiate_adapter(adapter_cls, project.datasource)
            adapter_count = 0
            for dto in adapter.fetch_increments(project, since=since):
                if not isinstance(dto, IncrementDTO):
                    continue
                self._persist_dto(project, dto)
                increments_count += 1
                adapter_count += 1
                max_occurred = dto.occurred_at if max_occurred is None else max(max_occurred, dto.occurred_at)
                contributors_seen.add((project.datasource_id, dto.contributor.email))
            logger.info(
                "sync adapter done run_id=%s adapter=%s phase=increments fetched=%s total_increments=%s",
                run.pk,
                adapter_cls.__name__,
                adapter_count,
                increments_count,
            )

        for adapter_cls in self._work_classes_for(ds_type):
            adapter = adapter_cls(project.datasource)
            adapter_count = 0
            for dto in adapter.fetch_work_items(project, since=since):
                if not isinstance(dto, UnitOfWorkDTO):
                    continue
                self._persist_work_dto(project, dto)
                work_items_count += 1
                adapter_count += 1
                max_occurred = dto.updated_at if max_occurred is None else max(max_occurred, dto.updated_at)
                if dto.contributor and dto.contributor.email:
                    contributors_seen.add((project.datasource_id, dto.contributor.email))
            logger.info(
                "sync adapter done run_id=%s adapter=%s phase=work_items fetched=%s total_work_items=%s",
                run.pk,
                adapter_cls.__name__,
                adapter_count,
                work_items_count,
            )

        run.increments_ingested = increments_count
        run.work_items_ingested = work_items_count
        run.milestones_ingested = milestones_count
        run.contributors_touched = len(contributors_seen)
        run.cursor_to = max_occurred or timezone.now()
        if increments_count == 0 and work_items_count == 0 and milestones_count == 0:
            logger.warning(
                "sync empty run_id=%s project_id=%s external_project_id=%s since=%s — "
                "no milestones, increments, or work items ingested",
                run.pk,
                project.pk,
                project.external_project_id,
                since,
            )

    def _compute_since(self, project: Project):
        last_ok = (
            IngestionRun.objects.filter(project=project, status=IngestionRun.Status.SUCCESS)
            .order_by("-finished_at")
            .first()
        )
        floor = timezone.now() - timedelta(days=SYNC_LOOKBACK_DAYS)
        if last_ok and last_ok.cursor_to:
            return max(last_ok.cursor_to, floor)
        return floor

    def _instantiate_adapter(self, cls: type[DataSourceAdapter], datasource: DataSource):
        return cls(datasource)

    @staticmethod
    def _persist_dto(project: Project, dto: IncrementDTO) -> None:
        if not project.datasource:
            return
        with transaction.atomic():
            contributor, _ = Contributor.objects.update_or_create(
                datasource=project.datasource,
                email=dto.contributor.email,
                defaults={
                    "name": (dto.contributor.name or "")[:255],
                    "handle": (dto.contributor.handle or "")[:255],
                },
            )
            Increment.objects.update_or_create(
                project=project,
                kind=dto.kind,
                external_id=dto.external_id[:128],
                defaults={
                    "datasource": project.datasource,
                    "occurred_at": dto.occurred_at,
                    "contributor": contributor,
                    "summary": (dto.summary or "")[:512],
                    "payload": dto.payload or {},
                },
            )

    @staticmethod
    def _persist_milestone_dto(project: Project, dto: MilestoneDTO) -> None:
        if not project.datasource:
            return
        Milestone.objects.update_or_create(
            project=project,
            external_id=dto.external_id[:128],
            defaults={
                "datasource": project.datasource,
                "title": (dto.title or "")[:512],
                "state": (dto.state or "")[:32],
                "due_date": dto.due_date,
                "start_date": dto.start_date,
                "updated_at": dto.updated_at,
                "payload": dto.payload or {},
            },
        )

    @staticmethod
    def _persist_work_dto(project: Project, dto: UnitOfWorkDTO) -> None:
        if not project.datasource:
            return
        with transaction.atomic():
            assignee = None
            if dto.contributor and dto.contributor.email:
                assignee, _ = Contributor.objects.update_or_create(
                    datasource=project.datasource,
                    email=dto.contributor.email,
                    defaults={
                        "name": (dto.contributor.name or "")[:255],
                        "handle": (dto.contributor.handle or "")[:255],
                    },
                )

            milestone = None
            if dto.milestone_external_id:
                milestone = Milestone.objects.filter(
                    project=project,
                    external_id=str(dto.milestone_external_id)[:128],
                ).first()

            existing = UnitOfWork.objects.filter(
                project=project,
                kind=dto.kind,
                external_id=dto.external_id[:128],
            ).first()
            prior_state = existing.state if existing else None

            uow, _created = UnitOfWork.objects.update_or_create(
                project=project,
                kind=dto.kind,
                external_id=dto.external_id[:128],
                defaults={
                    "datasource": project.datasource,
                    "iid": dto.iid,
                    "title": (dto.title or "")[:512],
                    "state": (dto.state or "")[:32],
                    "milestone": milestone,
                    "assignee": assignee,
                    "labels": dto.labels or [],
                    "created_at": dto.created_at,
                    "updated_at": dto.updated_at,
                    "closed_at": dto.closed_at,
                    "payload": dto.payload or {},
                },
            )

            if prior_state is not None and prior_state != dto.state:
                UoWStateChange.objects.create(
                    unit_of_work=uow,
                    from_state=prior_state[:32],
                    to_state=(dto.state or "")[:32],
                    recorded_at=timezone.now(),
                    source=str(project.datasource.datasource_type) if project.datasource else "unknown",
                )
