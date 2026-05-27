"""GitLab milestones."""

from __future__ import annotations

from collections.abc import Iterator
from datetime import datetime

from ingestion.adapters import register_milestone_adapter
from ingestion.adapters.gitlab_common import gitlab_client_for, parse_gitlab_date, parse_gitlab_datetime, since_aware
from ingestion.adapters.work_base import MilestoneAdapter
from ingestion.domain.work import MilestoneDTO
from ingestion.models import DataSource, Project


def _milestone_to_dto(item: dict) -> MilestoneDTO:
    return MilestoneDTO(
        external_id=str(item["id"]),
        title=str(item.get("title") or "")[:512],
        state=str(item.get("state") or "active"),
        due_date=parse_gitlab_date(item.get("due_date")),
        start_date=parse_gitlab_date(item.get("start_date")),
        updated_at=parse_gitlab_datetime(item.get("updated_at") or item.get("created_at")),
        payload={"web_url": str(item.get("web_url") or "")},
    )


class GitlabMilestoneAdapter(MilestoneAdapter):
    def fetch_milestones(self, project: Project, *, since: datetime | None) -> Iterator[MilestoneDTO]:
        client = gitlab_client_for(project)
        since_eff = since_aware(since)
        items = client.list_milestones(int(project.gitlab_project_id), updated_after=since_eff)
        for item in items:
            if not item.get("id"):
                continue
            dto = _milestone_to_dto(item)
            if since_eff is not None and dto.updated_at < since_eff:
                continue
            yield dto


register_milestone_adapter(DataSource.Type.GITLAB, GitlabMilestoneAdapter)
