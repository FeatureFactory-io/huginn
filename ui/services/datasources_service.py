"""Datasource lifecycle — delegates to ingestion integrations."""

from datetime import datetime
from datetime import time as time_of_day
from urllib.error import URLError

from django.utils import timezone
from django.utils.dateparse import parse_date

from ingestion.integrations.gitlab_client import GitlabClient
from ingestion.models import DataSource, Project


def _coerce_token_expires_at(raw) -> object | None:
    if raw is None:
        return None
    if not str(raw).strip():
        return None
    if hasattr(raw, "year"):
        return raw
    d = parse_date(str(raw).strip())
    if not d:
        return None
    return timezone.make_aware(datetime.combine(d, time_of_day.min))


class DataSourcesService:
    """Persist and validate datasource rows."""

    def test_gitlab_connection(self, *, base_url: str, token: str) -> dict:
        try:
            client = GitlabClient(base_url.strip(), token)
            meta = dict(client.verify_token())
            try:
                meta["visible_project_count"] = client.get_visible_project_count()
            except (ConnectionError, OSError, ValueError, URLError):
                meta["visible_project_count"] = None
            return meta
        except ConnectionError:
            raise
        except ValueError:
            raise
        except URLError as exc:
            raise ConnectionError("Unable to verify GitLab connection.") from exc

    def create_gitlab_source(
        self,
        *,
        name: str,
        base_url: str,
        token: str,
        token_expires_at,
    ) -> DataSource:
        expires = _coerce_token_expires_at(token_expires_at)
        connected_user = ""
        visible_count = None
        try:
            meta = self.test_gitlab_connection(base_url=base_url, token=token)
            status = DataSource.Status.CONNECTED
            err = ""
            connected_user = (meta.get("username") or meta.get("name") or "")[:255]
            visible_count = meta.get("visible_project_count")
        except (ConnectionError, OSError, ValueError):
            status = DataSource.Status.CONNECTION_ERROR
            err = "Could not validate token with GitLab; saved for editing later."

        return DataSource.objects.create(
            name=name.strip(),
            datasource_type=DataSource.Type.GITLAB,
            base_url=base_url.strip(),
            encrypted_token_ciphertext=token,
            token_expires_at=expires,
            connected_user=connected_user,
            visible_project_count=visible_count,
            status=status,
            last_error_message=err,
        )

    def update_gitlab_source(self, datasource_id: int, **fields) -> DataSource:
        ds = DataSource.objects.get(pk=datasource_id)
        new_token = fields.pop("new_token", None)
        if "token_expires_at" in fields:
            ds.token_expires_at = _coerce_token_expires_at(fields.pop("token_expires_at"))
        if "name" in fields and fields["name"]:
            ds.name = fields["name"].strip()
        if "base_url" in fields and fields["base_url"]:
            ds.base_url = fields["base_url"].strip()
        if new_token:
            try:
                meta = self.test_gitlab_connection(base_url=ds.base_url, token=new_token)
            except (ConnectionError, ValueError, OSError) as exc:
                raise ValueError("Unable to validate new token with GitLab.") from exc
            ds.encrypted_token_ciphertext = new_token
            ds.connected_user = (meta.get("username") or meta.get("name") or "")[:255]
            ds.visible_project_count = meta.get("visible_project_count")
            ds.status = DataSource.Status.CONNECTED
            ds.last_error_message = ""
        ds.save()
        return ds

    def soft_delete_gitlab_source(self, datasource_id: int) -> None:
        ds = DataSource.objects.get(pk=datasource_id)
        ds.projects.update(status=Project.Status.ORPHANED)
        ds.delete()
