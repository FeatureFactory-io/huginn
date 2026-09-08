"""GitHub milestones."""

from __future__ import annotations

from collections.abc import Iterator
from datetime import datetime

from ingestion.adapters import register_milestone_adapter
from ingestion.adapters.github_common import (
    github_client_for,
    github_repo_path_for,
    parse_github_date,
    parse_github_datetime,
    since_aware,
)
from ingestion.adapters.since import is_at_or_before_cursor
from ingestion.adapters.work_base import MilestoneAdapter
from ingestion.domain.work import MilestoneDTO
from ingestion.models import DataSource, Project


def _milestone_to_dto(item: dict) -> MilestoneDTO:
    state = str(item.get("state") or "open")
    if state == "open":
        state = "active"
    return MilestoneDTO(
        external_id=str(item["id"]),
        title=str(item.get("title") or "")[:512],
        state=state,
        due_date=parse_github_date(item.get("due_on")),
        start_date=None,
        updated_at=parse_github_datetime(item.get("updated_at") or item.get("created_at")),
        payload={"web_url": str(item.get("html_url") or "")},
    )


class GithubMilestoneAdapter(MilestoneAdapter):
    def fetch_milestones(self, project: Project, *, since: datetime | None) -> Iterator[MilestoneDTO]:
        owner, repo = github_repo_path_for(project)
        client = github_client_for(project)
        since_eff = since_aware(since)
        for item in client.list_milestones(owner, repo, since=since_eff):
            if not item.get("id"):
                continue
            dto = _milestone_to_dto(item)
            if is_at_or_before_cursor(dto.updated_at, since_eff):
                continue
            yield dto


register_milestone_adapter(DataSource.Type.GITHUB, GithubMilestoneAdapter)
