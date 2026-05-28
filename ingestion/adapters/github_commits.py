"""GitHub repository commits as Increments."""

from __future__ import annotations

from collections.abc import Iterator
from datetime import datetime
from typing import Any

from ingestion.adapters import register_adapter
from ingestion.adapters.base import DataSourceAdapter
from ingestion.adapters.github_common import (
    contributor_from_github_user,
    github_client_for,
    github_repo_path_for,
    parse_github_datetime,
    since_aware,
)
from ingestion.domain.increments import CommitIncrementDTO, ContributorDTO
from ingestion.models import DataSource, Project


def _commit_author(commit: dict[str, Any]) -> ContributorDTO:
    nested = commit.get("commit") or {}
    author_block = nested.get("author") or {}
    email = str(author_block.get("email") or "").strip()
    name = str(author_block.get("name") or "").strip()
    if email:
        return ContributorDTO(source="github", email=email, name=name)
    for key in ("author", "committer"):
        user = commit.get(key)
        dto = contributor_from_github_user(user, source="github")
        if dto:
            return dto
    email = "unknown@users.noreply.github.com"
    return ContributorDTO(source="github", email=email, name=name)


def _committed_at(commit: dict[str, Any]) -> datetime:
    nested = commit.get("commit") or {}
    author = nested.get("author") or {}
    return parse_github_datetime(author.get("date"))


def _commit_to_dto(commit: dict[str, Any]) -> CommitIncrementDTO:
    nested = commit.get("commit") or {}
    message = str(nested.get("message") or commit.get("message") or "")
    title = message.split("\n", 1)[0][:512]
    return CommitIncrementDTO(
        external_id=str(commit["sha"]),
        occurred_at=_committed_at(commit),
        contributor=_commit_author(commit),
        summary=title,
        payload={
            "web_url": str(commit.get("html_url") or ""),
            "short_id": str(commit.get("sha") or "")[:12],
        },
    )


class GithubCommitAdapter(DataSourceAdapter):
    def fetch_increments(self, project: Project, *, since: datetime | None) -> Iterator[CommitIncrementDTO]:
        owner, repo = github_repo_path_for(project)
        client = github_client_for(project)
        since_eff = since_aware(since)
        commits = client.list_commits(owner, repo, since=since_eff)
        seen: set[str] = set()
        for raw in commits:
            sha = str(raw.get("sha") or "")
            if not sha or sha in seen:
                continue
            seen.add(sha)
            yield _commit_to_dto(raw)


register_adapter(DataSource.Type.GITHUB, GithubCommitAdapter)
