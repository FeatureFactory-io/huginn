"""Refresh denormalized project fields from upstream data sources."""

from __future__ import annotations

import logging

from ingestion.integrations.gitlab_client import GitlabClient
from ingestion.models import DataSource, Project

logger = logging.getLogger(__name__)


def refresh_project_metadata(project: Project) -> None:
    """Best-effort metadata refresh before a sync-related user action.

    GitLab failures (network, HTTP) are swallowed and logged so sync can proceed.

    :param project: In-memory ``Project``; re-fetches from DB for ``select_related``.
    """
    try:
        _refresh_gitlab_metadata(project.pk)
    except ConnectionError as exc:
        logger.warning(
            "project metadata refresh skipped (gitlab): project_id=%s reason=%s",
            project.pk,
            exc,
        )


def _refresh_gitlab_metadata(project_pk: int) -> None:
    row = Project.objects.select_related("datasource").filter(pk=project_pk).first()
    if row is None or row.datasource is None:
        return

    ds = row.datasource
    if ds.datasource_type != DataSource.Type.GITLAB:
        logger.warning(
            "skip metadata refresh: datasource %s type=%s is not GitLab",
            ds.pk,
            ds.datasource_type,
        )
        return
    if row.gitlab_project_id is None:
        return

    token = (ds.encrypted_token_ciphertext or "").strip()
    if not token:
        logger.warning("skip metadata refresh: empty token datasource_id=%s", ds.pk)
        return

    client = GitlabClient(ds.base_url, ds.encrypted_token_ciphertext or "")
    data = client.get_project(int(row.gitlab_project_id))

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
