"""Shared urllib mocks for GitLab catalog integration tests."""

import json
import re
from unittest.mock import MagicMock
from urllib.parse import urlparse


def gitlab_catalog_urlopen_side_effect(
    project_rows: list[dict],
    *,
    single_project_by_id: dict[int, dict] | None = None,
    milestones: list[dict] | None = None,
    issues: list[dict] | None = None,
    merge_requests: list[dict] | None = None,
):
    """Callable for ``urlopen`` mock: catalog endpoints + empty sync (no branches/commits).

    Import persists fire :func:`ingestion.tasks.sync_project`, which calls
    ``GET .../repository/branches``. Without this, a fixed two-response
    ``side_effect`` list exhausts and sync marks the project ``error``.

    When ``single_project_by_id`` is set, ``GET /api/v4/projects/<id>`` (numeric id)
    returns the corresponding JSON object (for metadata refresh tests).
    """

    user_bytes = b'{"username":"catalog-user"}'
    milestones_payload = milestones or []
    issues_payload = issues or []
    merge_requests_payload = merge_requests or []

    def side_effect(req, *args, **kwargs):
        url = getattr(req, "full_url", str(req))
        parsed = urlparse(url)
        path_only = parsed.path or ""
        cm = MagicMock()
        enter = cm.__enter__.return_value
        enter.headers = {"X-Next-Page": ""}

        if "/api/v4/user" in url:
            enter.read.return_value = user_bytes
            return cm
        m_single = re.fullmatch(r"/api/v4/projects/(\d+)", path_only.rstrip("/") or path_only)
        if single_project_by_id is not None and m_single is not None and "/repository/" not in path_only:
            gid = int(m_single.group(1))
            payload = single_project_by_id.get(gid)
            if payload is not None:
                enter.read.return_value = json.dumps(payload).encode()
                return cm

        if "/api/v4/projects" in url and "membership=true" in url:
            enter.read.return_value = json.dumps(project_rows).encode()
            return cm
        if "/repository/branches" in url:
            enter.read.return_value = b"[]"
            return cm
        if "/repository/commits" in url:
            enter.read.return_value = b"[]"
            return cm
        if "/milestones" in url:
            enter.read.return_value = json.dumps(milestones_payload).encode()
            return cm
        if "/issues" in url:
            enter.read.return_value = json.dumps(issues_payload).encode()
            return cm
        if "/merge_requests" in url:
            enter.read.return_value = json.dumps(merge_requests_payload).encode()
            return cm
        msg = f"Unexpected GitLab URL in mock: {url!r}"
        raise AssertionError(msg)

    return side_effect


def gitlab_work_items_sync_urlopen_side_effect(
    *,
    milestones: list[dict] | None = None,
    issues: list[dict] | None = None,
    merge_requests: list[dict] | None = None,
):
    """``urlopen`` side_effect for SyncEngine work-item ingestion tests."""
    return gitlab_catalog_urlopen_side_effect(
        [],
        milestones=milestones or [],
        issues=issues or [],
        merge_requests=merge_requests or [],
    )


def gitlab_catalog_mocks(project_rows: list[dict], **kwargs):
    """Return ``urlopen`` side_effect (callable) for catalog + empty-branch sync."""
    return gitlab_catalog_urlopen_side_effect(project_rows, **kwargs)
