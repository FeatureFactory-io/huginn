"""GitHub issues as UnitOfWork rows."""

from __future__ import annotations

from collections.abc import Iterator
from datetime import datetime

from ingestion.adapters import register_work_adapter
from ingestion.adapters.github_common import (
    contributor_from_github_user,
    github_client_for,
    github_repo_path_for,
    parse_github_datetime,
    since_aware,
)
from ingestion.adapters.work_base import WorkItemAdapter
from ingestion.domain.work import UnitOfWorkDTO
from ingestion.models import DataSource, Project, UnitOfWork


def _normalize_state(state: str) -> str:
    if state == "open":
        return "opened"
    return state


def _issue_to_dto(issue: dict) -> UnitOfWorkDTO:
    milestone = issue.get("milestone")
    milestone_id = None
    if isinstance(milestone, dict) and milestone.get("id") is not None:
        milestone_id = str(milestone["id"])
    labels = [str(label.get("name") or label) for label in (issue.get("labels") or []) if label]
    return UnitOfWorkDTO(
        kind=UnitOfWork.Kind.ISSUE,
        external_id=str(issue["id"]),
        iid=int(issue.get("number") or 0),
        title=str(issue.get("title") or "")[:512],
        state=_normalize_state(str(issue.get("state") or "open")),
        milestone_external_id=milestone_id,
        contributor=contributor_from_github_user(issue.get("assignee"))
        or contributor_from_github_user(issue.get("user")),
        labels=labels,
        created_at=parse_github_datetime(issue.get("created_at")),
        updated_at=parse_github_datetime(issue.get("updated_at")),
        closed_at=parse_github_datetime(issue.get("closed_at")) if issue.get("closed_at") else None,
        payload={
            "web_url": str(issue.get("html_url") or ""),
            "body": str(issue.get("body") or "")[:500],
        },
    )


class GithubIssueAdapter(WorkItemAdapter):
    def fetch_work_items(self, project: Project, *, since: datetime | None) -> Iterator[UnitOfWorkDTO]:
        owner, repo = github_repo_path_for(project)
        client = github_client_for(project)
        since_eff = since_aware(since)
        for issue in client.list_issues(owner, repo, since=since_eff):
            if not issue.get("id"):
                continue
            dto = _issue_to_dto(issue)
            if since_eff is not None and dto.updated_at < since_eff:
                continue
            yield dto


register_work_adapter(DataSource.Type.GITHUB, GithubIssueAdapter)
