"""GitLab merge requests as UnitOfWork rows."""

from __future__ import annotations

from collections.abc import Iterator
from datetime import datetime

from ingestion.adapters import register_work_adapter
from ingestion.adapters.gitlab_common import (
    contributor_from_user,
    gitlab_client_for,
    parse_gitlab_datetime,
    since_aware,
)
from ingestion.adapters.since import is_at_or_before_cursor
from ingestion.adapters.work_base import WorkItemAdapter
from ingestion.domain.work import UnitOfWorkDTO
from ingestion.models import DataSource, Project, UnitOfWork


def _mr_to_dto(mr: dict) -> UnitOfWorkDTO:
    closed_raw = mr.get("merged_at") or mr.get("closed_at")
    return UnitOfWorkDTO(
        kind=UnitOfWork.Kind.MERGE_REQUEST,
        external_id=str(mr["id"]),
        iid=int(mr.get("iid") or 0),
        title=str(mr.get("title") or "")[:512],
        state=str(mr.get("state") or "opened"),
        contributor=contributor_from_user(mr.get("author")),
        labels=[str(label) for label in (mr.get("labels") or []) if label],
        created_at=parse_gitlab_datetime(mr.get("created_at")),
        updated_at=parse_gitlab_datetime(mr.get("updated_at")),
        closed_at=parse_gitlab_datetime(closed_raw) if closed_raw else None,
        payload={
            "web_url": str(mr.get("web_url") or ""),
            "source_branch": str(mr.get("source_branch") or ""),
            "target_branch": str(mr.get("target_branch") or ""),
        },
    )


class GitlabMergeRequestAdapter(WorkItemAdapter):
    def fetch_work_items(self, project: Project, *, since: datetime | None) -> Iterator[UnitOfWorkDTO]:
        client = gitlab_client_for(project)
        since_eff = since_aware(since)
        items = client.list_merge_requests(int(project.external_project_id), updated_after=since_eff)
        for item in items:
            if not item.get("id"):
                continue
            dto = _mr_to_dto(item)
            if is_at_or_before_cursor(dto.updated_at, since_eff):
                continue
            yield dto


register_work_adapter(DataSource.Type.GITLAB, GitlabMergeRequestAdapter)
