"""GitLab client — connectivity check without bundling python-gitlab in MVP."""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


class GitlabClient:
    """Calls GitLab HTTP API for token validation."""

    def __init__(self, base_url: str, token: str) -> None:
        self.base_url = base_url.rstrip("/")
        self._token = token

    def verify_token(self) -> dict:
        """Return user metadata from ``/api/v4/user`` or raise on failure."""
        if not self._token.strip():
            raise ValueError("Token is blank")
        url = f"{self.base_url}/api/v4/user"
        req = Request(url, headers={"PRIVATE-TOKEN": self._token})
        try:
            with urlopen(req, timeout=10) as resp:  # noqa: S310 — runtime URL controlled by admins
                return json.loads(resp.read().decode())
        except HTTPError as exc:
            raise ConnectionError(f"GitLab responded with HTTP {exc.code}") from exc
        except URLError as exc:
            raise ConnectionError("Unable to reach GitLab.") from exc

    def get_visible_project_count(self) -> int:
        """Return total visible projects for this token (membership scope)."""
        url = f"{self.base_url}/api/v4/projects?membership=true&per_page=1"
        req = Request(url, headers={"PRIVATE-TOKEN": self._token})
        try:
            with urlopen(req, timeout=10) as resp:  # noqa: S310
                total = resp.headers.get("X-Total") or resp.headers.get("x-total")
                if total is None:
                    return 0
                return int(total)
        except HTTPError as exc:
            raise ConnectionError(f"GitLab responded with HTTP {exc.code}") from exc
        except URLError as exc:
            raise ConnectionError("Unable to reach GitLab.") from exc

    def list_visible_projects(self, *, per_page: int = 100, max_pages: int = 100) -> list[dict[str, Any]]:
        """Paginated ``GET /api/v4/projects`` with ``membership=true``.

        Stable identity for catalog rows is ``id`` (GitLab project id), exposed as
        string ``key`` by :class:`ProjectsService`.
        """
        if not self._token.strip():
            raise ValueError("Token is blank")

        results: list[dict[str, Any]] = []
        page = 1
        pages_read = 0

        while pages_read < max_pages:
            qs = urlencode({"membership": "true", "per_page": str(per_page), "page": str(page)})
            url = f"{self.base_url}/api/v4/projects?{qs}"
            req = Request(url, headers={"PRIVATE-TOKEN": self._token})
            try:
                with urlopen(req, timeout=30) as resp:  # noqa: S310
                    raw = resp.read().decode()
                    data = json.loads(raw)
                    next_page = resp.headers.get("X-Next-Page") or resp.headers.get("x-next-page") or ""
            except HTTPError as exc:
                raise ConnectionError(f"GitLab responded with HTTP {exc.code}") from exc
            except URLError as exc:
                raise ConnectionError("Unable to reach GitLab.") from exc

            if not isinstance(data, list) or not data:
                break

            for item in data:
                if not isinstance(item, dict):
                    continue
                pid = item.get("id")
                path = item.get("path_with_namespace") or ""
                if pid is None or not path:
                    continue
                desc = item.get("description") or ""
                if isinstance(desc, str) and len(desc) > 500:
                    desc = desc[:500] + "…"
                elif not isinstance(desc, str):
                    desc = str(desc) if desc is not None else ""
                results.append(
                    {
                        "id": int(pid),
                        "name": str(item.get("name") or path.rsplit("/", maxsplit=1)[-1]),
                        "path_with_namespace": path,
                        "description": desc,
                        "web_url": str(item.get("web_url") or ""),
                        "last_activity_at": item.get("last_activity_at"),
                    }
                )

            pages_read += 1
            if not next_page or next_page == "0":
                break
            try:
                page = int(next_page)
            except ValueError:
                page += 1
            if len(data) < per_page:
                break

        return results

    def get_project(self, project_id: int) -> dict[str, Any]:
        """Fetch ``GET /api/v4/projects/:id`` metadata (description, urls, names)."""
        if not self._token.strip():
            raise ValueError("Token is blank")

        pid = int(project_id)
        url = f"{self.base_url}/api/v4/projects/{pid}"
        req = Request(url, headers={"PRIVATE-TOKEN": self._token})
        try:
            with urlopen(req, timeout=30) as resp:  # noqa: S310 — admin-controlled GitLab URL
                raw_bytes = resp.read().decode()
                data = json.loads(raw_bytes)
        except HTTPError as exc:
            raise ConnectionError(f"GitLab responded with HTTP {exc.code}") from exc
        except URLError as exc:
            raise ConnectionError("Unable to reach GitLab.") from exc

        if not isinstance(data, dict):
            raise ConnectionError("GitLab returned unexpected project payload.")

        raw_desc = data.get("description")
        if isinstance(raw_desc, str) and len(raw_desc) > 500:
            norm_desc = raw_desc[:500] + "…"
        elif not isinstance(raw_desc, str):
            norm_desc = str(raw_desc) if raw_desc is not None else ""
        else:
            norm_desc = raw_desc or ""

        return {
            "id": int(data.get("id") or pid),
            "name": str(data.get("name") or ""),
            "description": norm_desc,
            "web_url": str(data.get("web_url") or ""),
            "path_with_namespace": str(data.get("path_with_namespace") or ""),
            "default_branch": str(data.get("default_branch") or ""),
        }

    def list_branch_names(
        self,
        project_id: int,
        *,
        per_page: int = 100,
        max_pages: int = 20,
    ) -> list[str]:
        """Return branch ``name`` values for ``GET .../repository/branches`` (paginated)."""
        if not self._token.strip():
            raise ValueError("Token is blank")
        names: list[str] = []
        page = 1
        pages_read = 0
        pid = int(project_id)
        while pages_read < max_pages:
            qs = urlencode({"per_page": str(per_page), "page": str(page)})
            url = f"{self.base_url}/api/v4/projects/{pid}/repository/branches?{qs}"
            req = Request(url, headers={"PRIVATE-TOKEN": self._token})
            try:
                with urlopen(req, timeout=30) as resp:  # noqa: S310
                    raw = resp.read().decode()
                    data = json.loads(raw)
                    next_page = resp.headers.get("X-Next-Page") or resp.headers.get("x-next-page") or ""
            except HTTPError as exc:
                raise ConnectionError(f"GitLab responded with HTTP {exc.code}") from exc
            except URLError as exc:
                raise ConnectionError("Unable to reach GitLab.") from exc

            if not isinstance(data, list) or not data:
                break

            for item in data:
                if isinstance(item, dict) and item.get("name"):
                    names.append(str(item["name"]))

            pages_read += 1
            if not next_page or next_page == "0":
                break
            try:
                page = int(next_page)
            except ValueError:
                page += 1
            if len(data) < per_page:
                break

        return names

    def list_commits(
        self,
        project_id: int,
        *,
        ref_name: str,
        since: datetime | None = None,
        per_page: int = 100,
        max_pages: int = 100,
    ) -> list[dict[str, Any]]:
        """Paginated ``GET .../repository/commits`` for one ``ref_name``."""
        if not self._token.strip():
            raise ValueError("Token is blank")

        params: dict[str, str] = {"ref_name": ref_name, "per_page": str(per_page)}
        if since is not None:
            params["since"] = since.replace(microsecond=0).isoformat().replace("+00:00", "Z")

        results: list[dict[str, Any]] = []
        page = 1
        pages_read = 0
        pid = int(project_id)

        while pages_read < max_pages:
            q = dict(params)
            q["page"] = str(page)
            qs = urlencode(q)
            url = f"{self.base_url}/api/v4/projects/{pid}/repository/commits?{qs}"
            req = Request(url, headers={"PRIVATE-TOKEN": self._token})
            try:
                with urlopen(req, timeout=60) as resp:  # noqa: S310
                    raw = resp.read().decode()
                    data = json.loads(raw)
                    next_page = resp.headers.get("X-Next-Page") or resp.headers.get("x-next-page") or ""
            except HTTPError as exc:
                raise ConnectionError(f"GitLab responded with HTTP {exc.code}") from exc
            except URLError as exc:
                raise ConnectionError("Unable to reach GitLab.") from exc

            if not isinstance(data, list) or not data:
                break

            for item in data:
                if isinstance(item, dict) and item.get("id"):
                    results.append(item)

            pages_read += 1
            if not next_page or next_page == "0":
                break
            try:
                page = int(next_page)
            except ValueError:
                page += 1
            if len(data) < per_page:
                break

        return results

    def _paginate(
        self,
        path: str,
        *,
        params: dict[str, str] | None = None,
        per_page: int = 100,
        max_pages: int = 100,
        timeout: int = 60,
    ) -> list[dict[str, Any]]:
        if not self._token.strip():
            raise ValueError("Token is blank")
        base_params = dict(params or {})
        base_params.setdefault("per_page", str(per_page))
        results: list[dict[str, Any]] = []
        page = 1
        pages_read = 0
        while pages_read < max_pages:
            q = dict(base_params)
            q["page"] = str(page)
            qs = urlencode(q)
            url = f"{self.base_url}{path}?{qs}"
            req = Request(url, headers={"PRIVATE-TOKEN": self._token})
            try:
                with urlopen(req, timeout=timeout) as resp:  # noqa: S310
                    raw = resp.read().decode()
                    data = json.loads(raw)
                    next_page = resp.headers.get("X-Next-Page") or resp.headers.get("x-next-page") or ""
            except HTTPError as exc:
                raise ConnectionError(f"GitLab responded with HTTP {exc.code}") from exc
            except URLError as exc:
                raise ConnectionError("Unable to reach GitLab.") from exc

            if not isinstance(data, list) or not data:
                break
            for item in data:
                if isinstance(item, dict):
                    results.append(item)
            pages_read += 1
            if not next_page or next_page == "0":
                break
            try:
                page = int(next_page)
            except ValueError:
                page += 1
            if len(data) < per_page:
                break
        return results

    def list_issues(
        self,
        project_id: int,
        *,
        updated_after: datetime | None = None,
        state: str | None = None,
    ) -> list[dict[str, Any]]:
        params: dict[str, str] = {}
        if updated_after is not None:
            params["updated_after"] = updated_after.replace(microsecond=0).isoformat().replace("+00:00", "Z")
        if state:
            params["state"] = state
        return self._paginate(f"/api/v4/projects/{int(project_id)}/issues", params=params)

    def list_milestones(
        self,
        project_id: int,
        *,
        updated_after: datetime | None = None,
    ) -> list[dict[str, Any]]:
        params: dict[str, str] = {}
        if updated_after is not None:
            params["updated_after"] = updated_after.replace(microsecond=0).isoformat().replace("+00:00", "Z")
        return self._paginate(f"/api/v4/projects/{int(project_id)}/milestones", params=params)

    def list_merge_requests(
        self,
        project_id: int,
        *,
        updated_after: datetime | None = None,
        state: str | None = None,
    ) -> list[dict[str, Any]]:
        params: dict[str, str] = {}
        if updated_after is not None:
            params["updated_after"] = updated_after.replace(microsecond=0).isoformat().replace("+00:00", "Z")
        if state:
            params["state"] = state
        return self._paginate(f"/api/v4/projects/{int(project_id)}/merge_requests", params=params)
