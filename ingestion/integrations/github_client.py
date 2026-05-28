"""GitHub.com REST client (MVP — fixed api.github.com base).

Auth/headers follow https://docs.github.com/en/rest/authentication/authenticating-to-the-rest-api
and https://docs.github.com/en/rest/using-the-rest-api/getting-started-with-the-rest-api
"""

from __future__ import annotations

import json
import re
from datetime import datetime
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

GITHUB_API_BASE = "https://api.github.com"
# Required on every REST request per GitHub docs (Getting started with the REST API).
GITHUB_API_VERSION = "2022-11-28"
GITHUB_USER_AGENT = "Huginn-GitHub-Integration"
# Classic PAT (legacy): ghp_ + 36-251 alnum chars — github.blog token formats.
_GHP_CLASSIC = re.compile(r"ghp_[A-Za-z0-9]{36,251}")
_UNICODE_JUNK = str.maketrans("", "", "\u2014\u2013\u2212—–\n\r\t")
_GHP_CLASSIC_MIN_LEN = 40  # ghp_ + 36


def normalize_github_token(raw: str) -> str:
    """Prepare a classic ``ghp_`` PAT for HTTP headers (latin-1 safe, ASCII only)."""
    token = (raw or "").strip().strip('"').strip("'")
    for prefix in ("Bearer ", "bearer ", "token ", "Token "):
        while token.startswith(prefix):
            token = token[len(prefix) :].strip()
    token = token.translate(_UNICODE_JUNK).strip()
    # Drop trailing notes after whitespace (e.g. "ghp_xxx save this token").
    if token.split():
        token = token.split()[0]
    match = _GHP_CLASSIC.search(token)
    if match:
        return match.group(0)
    if token.startswith("ghp_"):
        body = "".join(ch for ch in token[4:] if ch.isalnum())
        return f"ghp_{body}"
    return "".join(ch for ch in token if ch.isascii() and (ch.isalnum() or ch == "_"))


def validate_github_token(raw: str) -> str:
    """Normalize and reject classic PATs that are clearly truncated before calling GitHub."""
    token = normalize_github_token(raw)
    if not token:
        raise ValueError("Token is blank")
    if token.startswith("ghp_") and len(token) < _GHP_CLASSIC_MIN_LEN:
        raise ValueError(
            f"Token looks truncated ({len(token)} characters). "
            f"Classic ghp_ tokens are {_GHP_CLASSIC_MIN_LEN} characters — clear the field and paste again."
        )
    return token


class GithubClient:
    """Calls GitHub REST API for token validation and repository sync."""

    def __init__(self, token: str, *, base_url: str = GITHUB_API_BASE) -> None:
        self.base_url = base_url.rstrip("/")
        self._token = validate_github_token(token)

    def _headers(self) -> dict[str, str]:
        auth = f"Bearer {self._token}"
        if not auth.isascii():
            raise ValueError("Token contains invalid characters; paste the ghp_ token only.")
        return {
            "Authorization": auth,
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": GITHUB_API_VERSION,
            "User-Agent": GITHUB_USER_AGENT,
        }

    def _request(self, url: str, *, timeout: int = 30) -> tuple[bytes, dict[str, str]]:
        if not self._token:
            raise ValueError("Token is blank")
        req = Request(url, headers=self._headers())
        try:
            with urlopen(req, timeout=timeout) as resp:  # noqa: S310
                raw = resp.read()
                hdrs = {k.lower(): v for k, v in resp.headers.items()}
                return raw, hdrs
        except HTTPError as exc:
            detail = ""
            try:
                body = json.loads(exc.read().decode())
                if isinstance(body, dict) and body.get("message"):
                    detail = f": {body['message']}"
            except (OSError, ValueError, json.JSONDecodeError):
                pass
            raise ConnectionError(f"GitHub responded with HTTP {exc.code}{detail}") from exc
        except URLError as exc:
            reason = getattr(exc, "reason", exc)
            raise ConnectionError(f"Unable to reach GitHub ({reason}).") from exc

    @staticmethod
    def _link_next(link_header: str | None) -> str | None:
        if not link_header:
            return None
        for part in link_header.split(","):
            if 'rel="next"' in part:
                return part.split(";")[0].strip().strip("<>")
        return None

    def verify_token(self) -> dict[str, Any]:
        raw, _ = self._request(f"{self.base_url}/user")
        data = json.loads(raw.decode())
        if not isinstance(data, dict):
            raise ConnectionError("GitHub returned unexpected user payload.")
        login = str(data.get("login") or "")
        return {
            "login": login,
            "username": login,
            "name": str(data.get("name") or login),
            "email": str(data.get("email") or ""),
        }

    def get_visible_repo_count(self, *, max_pages: int = 20, per_page: int = 100) -> int:
        count = 0
        url: str | None = f"{self.base_url}/user/repos?" + urlencode(
            {"affiliation": "owner,collaborator", "per_page": str(per_page), "page": "1"}
        )
        pages = 0
        while url and pages < max_pages:
            raw, hdrs = self._request(url)
            data = json.loads(raw.decode())
            if not isinstance(data, list):
                break
            count += len(data)
            pages += 1
            url = self._link_next(hdrs.get("link"))
            if len(data) < per_page:
                break
        return count

    def list_visible_repos(self, *, per_page: int = 100, max_pages: int = 100) -> list[dict[str, Any]]:
        results: list[dict[str, Any]] = []
        url: str | None = f"{self.base_url}/user/repos?" + urlencode(
            {
                "affiliation": "owner,collaborator",
                "sort": "updated",
                "direction": "desc",
                "per_page": str(per_page),
                "page": "1",
            }
        )
        pages = 0
        while url and pages < max_pages:
            raw, hdrs = self._request(url, timeout=60)
            data = json.loads(raw.decode())
            if not isinstance(data, list) or not data:
                break
            for item in data:
                if not isinstance(item, dict):
                    continue
                rid = item.get("id")
                full_name = item.get("full_name") or ""
                if rid is None or not full_name:
                    continue
                desc = item.get("description") or ""
                if isinstance(desc, str) and len(desc) > 500:
                    desc = desc[:500] + "…"
                elif not isinstance(desc, str):
                    desc = str(desc) if desc is not None else ""
                results.append(
                    {
                        "id": int(rid),
                        "name": str(item.get("name") or full_name.rsplit("/", maxsplit=1)[-1]),
                        "full_name": str(full_name),
                        "description": desc,
                        "html_url": str(item.get("html_url") or ""),
                        "updated_at": item.get("updated_at") or item.get("pushed_at"),
                    }
                )
            pages += 1
            url = self._link_next(hdrs.get("link"))
            if len(data) < per_page:
                break
        return results

    @staticmethod
    def split_repo_path(full_name: str) -> tuple[str, str]:
        owner, _, repo = full_name.partition("/")
        if not owner or not repo:
            raise ValueError(f"Invalid repository path: {full_name!r}")
        return owner, repo

    def get_repo(self, owner: str, repo: str) -> dict[str, Any]:
        raw, _ = self._request(f"{self.base_url}/repos/{owner}/{repo}")
        data = json.loads(raw.decode())
        if not isinstance(data, dict):
            raise ConnectionError("GitHub returned unexpected repository payload.")
        raw_desc = data.get("description")
        if isinstance(raw_desc, str) and len(raw_desc) > 500:
            norm_desc = raw_desc[:500] + "…"
        elif not isinstance(raw_desc, str):
            norm_desc = str(raw_desc) if raw_desc is not None else ""
        else:
            norm_desc = raw_desc or ""
        return {
            "id": int(data.get("id") or 0),
            "name": str(data.get("name") or repo),
            "description": norm_desc,
            "html_url": str(data.get("html_url") or ""),
            "full_name": str(data.get("full_name") or f"{owner}/{repo}"),
        }

    def _paginate_repo(
        self,
        owner: str,
        repo: str,
        path: str,
        *,
        params: dict[str, str] | None = None,
        per_page: int = 100,
        max_pages: int = 100,
    ) -> list[dict[str, Any]]:
        base_params = dict(params or {})
        base_params.setdefault("per_page", str(per_page))
        results: list[dict[str, Any]] = []
        url: str | None = f"{self.base_url}/repos/{owner}/{repo}/{path}?{urlencode({**base_params, 'page': '1'})}"
        pages = 0
        while url and pages < max_pages:
            raw, hdrs = self._request(url, timeout=60)
            data = json.loads(raw.decode())
            if not isinstance(data, list) or not data:
                break
            for item in data:
                if isinstance(item, dict):
                    results.append(item)
            pages += 1
            url = self._link_next(hdrs.get("link"))
            if len(data) < per_page:
                break
        return results

    def list_commits(
        self,
        owner: str,
        repo: str,
        *,
        since: datetime | None = None,
    ) -> list[dict[str, Any]]:
        params: dict[str, str] = {}
        if since is not None:
            params["since"] = since.replace(microsecond=0).isoformat().replace("+00:00", "Z")
        return self._paginate_repo(owner, repo, "commits", params=params)

    def list_issues(
        self,
        owner: str,
        repo: str,
        *,
        since: datetime | None = None,
        state: str = "all",
    ) -> list[dict[str, Any]]:
        params: dict[str, str] = {"state": state}
        items = self._paginate_repo(owner, repo, "issues", params=params)
        if since is None:
            return [i for i in items if not i.get("pull_request")]
        out: list[dict[str, Any]] = []
        for item in items:
            if item.get("pull_request"):
                continue
            updated = item.get("updated_at") or item.get("created_at")
            if updated and since is not None:
                try:
                    dt = datetime.fromisoformat(str(updated).replace("Z", "+00:00"))
                    if dt < since:
                        continue
                except ValueError:
                    pass
            out.append(item)
        return out

    def list_pull_requests(
        self,
        owner: str,
        repo: str,
        *,
        since: datetime | None = None,
        state: str = "all",
    ) -> list[dict[str, Any]]:
        params: dict[str, str] = {"state": state, "sort": "updated", "direction": "desc"}
        items = self._paginate_repo(owner, repo, "pulls", params=params)
        if since is None:
            return items
        out: list[dict[str, Any]] = []
        for item in items:
            updated = item.get("updated_at") or item.get("created_at")
            if updated:
                try:
                    dt = datetime.fromisoformat(str(updated).replace("Z", "+00:00"))
                    if dt < since:
                        continue
                except ValueError:
                    pass
            out.append(item)
        return out

    def list_milestones(
        self,
        owner: str,
        repo: str,
        *,
        since: datetime | None = None,
        state: str = "all",
    ) -> list[dict[str, Any]]:
        params: dict[str, str] = {"state": state}
        items = self._paginate_repo(owner, repo, "milestones", params=params)
        if since is None:
            return items
        out: list[dict[str, Any]] = []
        for item in items:
            updated = item.get("updated_at") or item.get("created_at")
            if updated:
                try:
                    dt = datetime.fromisoformat(str(updated).replace("Z", "+00:00"))
                    if dt < since:
                        continue
                except ValueError:
                    pass
            out.append(item)
        return out
