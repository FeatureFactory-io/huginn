"""Refresh denormalized project fields from upstream data sources."""

from __future__ import annotations

import logging

from ingestion.integrations.gitlab_client import GitlabClient
from ingestion.models import DataSource, Project

logger = logging.getLogger(__name__)


def refresh_project_metadata(project: Project) -> None:
    """Best-effort metadata refresh before a sync-related user action.

    Upstream failures (network, HTTP) are swallowed and logged so sync can proceed.
    """
    row = Project.objects.select_related("datasource").filter(pk=project.pk).first()
    if row is None or row.datasource is None:
        return
    ds_type = row.datasource.datasource_type
    try:
        if ds_type == DataSource.Type.GITLAB:
            _refresh_gitlab_metadata(row)
        elif ds_type == DataSource.Type.GITHUB:
            _refresh_github_metadata(row)
    except ConnectionError as exc:
        logger.warning(
            "project metadata refresh skipped (%s): project_id=%s reason=%s",
            ds_type,
            project.pk,
            exc,
        )


def _refresh_gitlab_metadata(row: Project) -> None:
    ds = row.datasource
    if ds is None or ds.datasource_type != DataSource.Type.GITLAB:
        return
    if row.external_project_id is None:
        return

    token = (ds.encrypted_token_ciphertext or "").strip()
    if not token:
        logger.warning("skip metadata refresh: empty token datasource_id=%s", ds.pk)
        return

    client = GitlabClient(ds.base_url, token)
    data = client.get_project(int(row.external_project_id))

    updates: dict[str, str] = {"description": data["description"]}
    if data.get("name"):
        updates["name"] = str(data["name"])[:255]
    web_url = (data.get("web_url") or "").strip()
    if web_url:
        updates["source_url"] = web_url[:1024]

    path = (data.get("path_with_namespace") or "").strip()
    if path:
        updates["source_path"] = path[:512]

    Project.objects.filter(pk=row.pk).update(**updates)


def _refresh_github_metadata(row: Project) -> None:
    from ingestion.integrations.github_client import GithubClient

    ds = row.datasource
    if ds is None or ds.datasource_type != DataSource.Type.GITHUB:
        return
    path = (row.source_path or "").strip()
    if not path or "/" not in path:
        return

    token = (ds.encrypted_token_ciphertext or "").strip()
    if not token:
        logger.warning("skip metadata refresh: empty token datasource_id=%s", ds.pk)
        return

    owner, repo = GithubClient.split_repo_path(path)
    client = GithubClient(token)
    data = client.get_repo(owner, repo)

    updates: dict[str, str] = {"description": data["description"]}
    if data.get("name"):
        updates["name"] = str(data["name"])[:255]
    web_url = (data.get("html_url") or "").strip()
    if web_url:
        updates["source_url"] = web_url[:1024]

    full_name = (data.get("full_name") or path).strip()
    if full_name:
        updates["source_path"] = full_name[:512]

    Project.objects.filter(pk=row.pk).update(**updates)
