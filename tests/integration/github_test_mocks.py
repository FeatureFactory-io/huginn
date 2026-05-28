"""Shared urllib mocks for GitHub catalog integration tests."""

import json
import re
from unittest.mock import MagicMock
from urllib.parse import urlparse


def github_catalog_urlopen_side_effect(
    repo_rows: list[dict],
    *,
    single_repo_by_path: dict[str, dict] | None = None,
    commits: list[dict] | None = None,
    issues: list[dict] | None = None,
    pull_requests: list[dict] | None = None,
    milestones: list[dict] | None = None,
):
    """Callable for ``urlopen`` mock covering GitHub user/repos and sync endpoints."""

    user_bytes = b'{"login":"octocat","name":"Octocat"}'

    def side_effect(req, *args, **kwargs):
        url = getattr(req, "full_url", str(req))
        parsed = urlparse(url)
        path = parsed.path or ""
        cm = MagicMock()
        enter = cm.__enter__.return_value
        enter.headers = {"link": ""}

        if path.endswith("/user") or path.endswith("/user/"):
            enter.read.return_value = user_bytes
            return cm

        if "/user/repos" in path:
            enter.read.return_value = json.dumps(repo_rows).encode()
            return cm

        m_repo = re.fullmatch(r"/repos/([^/]+)/([^/]+)$", path)
        if single_repo_by_path is not None and m_repo:
            full = f"{m_repo.group(1)}/{m_repo.group(2)}"
            payload = single_repo_by_path.get(full)
            if payload is not None:
                enter.read.return_value = json.dumps(payload).encode()
                return cm

        if "/commits" in path:
            enter.read.return_value = json.dumps(commits or []).encode()
            return cm
        if "/issues" in path and "/pulls" not in path:
            enter.read.return_value = json.dumps(issues or []).encode()
            return cm
        if "/pulls" in path:
            enter.read.return_value = json.dumps(pull_requests or []).encode()
            return cm
        if "/milestones" in path:
            enter.read.return_value = json.dumps(milestones or []).encode()
            return cm

        raise AssertionError(f"Unexpected GitHub URL in mock: {url!r}")

    return side_effect
