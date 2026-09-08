"""GitHub pull requests as UnitOfWork merge_request rows."""

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
from ingestion.adapters.since import is_at_or_before_cursor
from ingestion.adapters.work_base import WorkItemAdapter
from ingestion.domain.work import UnitOfWorkDTO
from ingestion.models import DataSource, Project, UnitOfWork


def _pr_state(item: dict) -> str:
    if item.get("merged_at"):
        return "merged"
    return str(item.get("state") or "open")


def _pr_to_dto(item: dict) -> UnitOfWorkDTO:
    closed_raw = item.get("merged_at") or item.get("closed_at")
    return UnitOfWorkDTO(
        kind=UnitOfWork.Kind.MERGE_REQUEST,
        external_id=str(item["id"]),
        iid=int(item.get("number") or 0),
        title=str(item.get("title") or "")[:512],
        state=_pr_state(item),
        contributor=contributor_from_github_user(item.get("user")),
        labels=[str(label.get("name") or label) for label in (item.get("labels") or []) if label],
        created_at=parse_github_datetime(item.get("created_at")),
        updated_at=parse_github_datetime(item.get("updated_at")),
        closed_at=parse_github_datetime(closed_raw) if closed_raw else None,
        payload={
            "web_url": str(item.get("html_url") or ""),
            "head_ref": str(item.get("head", {}).get("ref") or ""),
            "base_ref": str(item.get("base", {}).get("ref") or ""),
        },
    )


class GithubPullRequestAdapter(WorkItemAdapter):
    def fetch_work_items(self, project: Project, *, since: datetime | None) -> Iterator[UnitOfWorkDTO]:
        owner, repo = github_repo_path_for(project)
        client = github_client_for(project)
        since_eff = since_aware(since)
        for item in client.list_pull_requests(owner, repo, since=since_eff):
            if not item.get("id"):
                continue
            dto = _pr_to_dto(item)
            if is_at_or_before_cursor(dto.updated_at, since_eff):
                continue
            yield dto


register_work_adapter(DataSource.Type.GITHUB, GithubPullRequestAdapter)
