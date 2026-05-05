"""GitLab client — connectivity check without bundling python-gitlab in MVP."""


class GitlabClient:
    """Calls GitLab HTTP API for token validation."""

    def __init__(self, base_url: str, token: str) -> None:
        self.base_url = base_url.rstrip("/")
        self._token = token

    def verify_token(self) -> dict:
        """Return user metadata from ``/api/v4/user`` or raise on failure."""
        from urllib.error import HTTPError, URLError
        from urllib.request import Request, urlopen

        if not self._token.strip():
            raise ValueError("Token is blank")
        url = f"{self.base_url}/api/v4/user"
        req = Request(url, headers={"PRIVATE-TOKEN": self._token})
        try:
            with urlopen(req, timeout=10) as resp:  # noqa: S310 — runtime URL controlled by admins
                import json

                return json.loads(resp.read().decode())
        except HTTPError as exc:
            raise ConnectionError(f"GitLab responded with HTTP {exc.code}") from exc
        except URLError as exc:
            raise ConnectionError("Unable to reach GitLab.") from exc
