"""GitLab issues as UnitOfWork rows."""

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
from ingestion.adapters.work_base import WorkItemAdapter
from ingestion.domain.work import UnitOfWorkDTO
from ingestion.models import DataSource, Project, UnitOfWork


def _issue_to_dto(issue: dict) -> UnitOfWorkDTO:
    milestone = issue.get("milestone")
    milestone_id = None
    if isinstance(milestone, dict) and milestone.get("id") is not None:
        milestone_id = str(milestone["id"])
    labels = [str(label) for label in (issue.get("labels") or []) if label]
    return UnitOfWorkDTO(
        kind=UnitOfWork.Kind.ISSUE,
        external_id=str(issue["id"]),
        iid=int(issue.get("iid") or 0),
        title=str(issue.get("title") or "")[:512],
        state=str(issue.get("state") or "opened"),
        milestone_external_id=milestone_id,
        contributor=contributor_from_user(issue.get("assignee")) or contributor_from_user(issue.get("author")),
        labels=labels,
        created_at=parse_gitlab_datetime(issue.get("created_at")),
        updated_at=parse_gitlab_datetime(issue.get("updated_at")),
        closed_at=parse_gitlab_datetime(issue.get("closed_at")) if issue.get("closed_at") else None,
        payload={
            "web_url": str(issue.get("web_url") or ""),
            "description": str(issue.get("description") or "")[:500],
        },
    )


class GitlabIssueAdapter(WorkItemAdapter):
    def fetch_work_items(self, project: Project, *, since: datetime | None) -> Iterator[UnitOfWorkDTO]:
        client = gitlab_client_for(project)
        since_eff = since_aware(since)
        issues = client.list_issues(int(project.gitlab_project_id), updated_after=since_eff)
        for issue in issues:
            if not issue.get("id"):
                continue
            dto = _issue_to_dto(issue)
            if since_eff is not None and dto.updated_at < since_eff:
                continue
            yield dto


register_work_adapter(DataSource.Type.GITLAB, GitlabIssueAdapter)
