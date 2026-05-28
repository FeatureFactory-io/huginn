"""Shared GitHub adapter helpers."""

from __future__ import annotations

from datetime import date, datetime
from typing import Any

from django.utils import timezone
from django.utils.dateparse import parse_date, parse_datetime

from ingestion.domain.increments import ContributorDTO
from ingestion.integrations.github_client import GithubClient
from ingestion.models import DataSource, Project


def parse_github_datetime(raw: Any) -> datetime:
    if not raw:
        return timezone.now()
    text = str(raw).replace("Z", "+00:00")
    dt = parse_datetime(text)
    if dt is None:
        return timezone.now()
    if timezone.is_naive(dt):
        return timezone.make_aware(dt, timezone=timezone.utc)
    return dt


def parse_github_date(raw: Any) -> date | None:
    if not raw:
        return None
    return parse_date(str(raw))


def contributor_from_github_user(user: Any, *, source: str = "github") -> ContributorDTO | None:
    if not isinstance(user, dict):
        return None
    email = str(user.get("email") or "").strip()
    name = str(user.get("name") or user.get("login") or "").strip()
    handle = str(user.get("login") or "")[:255] or None
    if not email and not name:
        return None
    if not email:
        email = f"{handle or 'unknown'}@users.noreply.github.com"
    return ContributorDTO(source=source, email=email, name=name, handle=handle)


def github_repo_path_for(project: Project) -> tuple[str, str]:
    if not project.external_project_id or not project.datasource:
        raise RuntimeError(f"Project {project.pk} has no external_project_id configured — cannot ingest.")
    path = (project.source_path or "").strip()
    if not path or "/" not in path:
        raise RuntimeError(f"Project {project.pk} has no owner/repo source_path — cannot ingest.")
    owner, repo = GithubClient.split_repo_path(path)
    return owner, repo


def github_client_for(project: Project) -> GithubClient:
    if project.datasource is None:
        raise RuntimeError(f"Project {project.pk} has no datasource — cannot ingest.")
    token = (project.datasource.encrypted_token_ciphertext or "").strip()
    if not token:
        raise RuntimeError(f"DataSource {project.datasource_id} has no access token configured — cannot ingest.")
    return GithubClient(token)


def since_aware(since: datetime | None) -> datetime | None:
    if since is None:
        return None
    if timezone.is_naive(since):
        return timezone.make_aware(since, timezone=timezone.utc)
    return since


def datasource_source(project: Project) -> str:
    if project.datasource is None:
        return DataSource.Type.GITHUB
    return str(project.datasource.datasource_type)
