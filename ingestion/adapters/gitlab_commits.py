"""GitLab repository commits as Increments."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterator
from datetime import datetime
from typing import Any

from django.utils import timezone
from django.utils.dateparse import parse_datetime

from ingestion.adapters import register_adapter
from ingestion.adapters.base import DataSourceAdapter
from ingestion.domain.increments import CommitIncrementDTO, ContributorDTO
from ingestion.integrations.gitlab_client import GitlabClient
from ingestion.models import DataSource, Project


def _committed_at(commit: dict[str, Any]) -> datetime:
    raw = commit.get("committed_date") or commit.get("created_at")
    if not raw:
        return timezone.now()
    dt = parse_datetime(str(raw))
    if dt is None:
        return timezone.now()
    if timezone.is_naive(dt):
        return timezone.make_aware(dt, timezone=timezone.utc)
    return dt


def _commit_to_dto(commit: dict[str, Any], branches: list[str]) -> CommitIncrementDTO:
    author_name = ""
    email = ""
    if isinstance(commit.get("author"), dict):
        a = commit["author"]
        author_name = str(a.get("name") or "")
        email = str(a.get("email") or "")
    if not email:
        email = "unknown@gitlab.local"
    title = str(commit.get("title") or commit.get("message") or "").split("\n", 1)[0][:512]
    return CommitIncrementDTO(
        external_id=str(commit["id"]),
        occurred_at=_committed_at(commit),
        contributor=ContributorDTO(source="gitlab", email=email, name=author_name),
        summary=title,
        payload={
            "web_url": str(commit.get("web_url") or ""),
            "branches": branches,
            "short_id": commit.get("short_id"),
        },
    )


class GitlabCommitAdapter(DataSourceAdapter):
    """Fetches git commits across all branches visible to the token."""

    def fetch_increments(self, project: Project, *, since: datetime | None) -> Iterator[CommitIncrementDTO]:
        if not project.gitlab_project_id or not project.datasource:
            return
        token = (project.datasource.encrypted_token_ciphertext or "").strip()
        if not token:
            return

        client = GitlabClient(project.datasource.base_url, token)
        gid = int(project.gitlab_project_id)
        try:
            branches = client.list_branch_names(gid)
        except (ConnectionError, OSError, ValueError):
            raise
        if not branches:
            return

        since_eff = since
        if since_eff is not None and timezone.is_naive(since_eff):
            since_eff = timezone.make_aware(since_eff, timezone=timezone.utc)

        by_sha: dict[str, dict[str, Any]] = {}
        branch_by_sha: dict[str, set[str]] = defaultdict(set)

        for ref in branches:
            commits = client.list_commits(gid, ref_name=ref, since=since_eff)
            for c in commits:
                sha = str(c.get("id") or "")
                if not sha:
                    continue
                by_sha.setdefault(sha, c)
                branch_by_sha[sha].add(ref)

        for _sha, raw in sorted(by_sha.items(), key=lambda kv: _committed_at(kv[1]), reverse=True):
            yield _commit_to_dto(raw, sorted(branch_by_sha[_sha]))


register_adapter(DataSource.Type.GITLAB, GitlabCommitAdapter)
