"""Datasource lifecycle — delegates to ingestion integrations."""

from urllib.error import URLError

from ingestion.integrations.gitlab_client import GitlabClient
from ingestion.models import DataSource, Project


class DataSourcesService:
    """Persist and validate datasource rows."""

    def test_gitlab_connection(self, *, base_url: str, token: str) -> dict:
        try:
            return GitlabClient(base_url.strip(), token).verify_token()
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
        # Validate token against GitLab when network available; persists even if unreachable in dev.
        try:
            GitlabClient(base_url.strip(), token).verify_token()
            status = DataSource.Status.CONNECTED
            err = ""
        except (ConnectionError, OSError):
            status = DataSource.Status.CONNECTION_ERROR
            err = "Could not validate token with GitLab; saved for editing later."

        return DataSource.objects.create(
            name=name.strip(),
            datasource_type=DataSource.Type.GITLAB,
            base_url=base_url.strip(),
            encrypted_token_ciphertext=token,
            token_expires_at=token_expires_at,
            status=status,
            last_error_message=err,
        )

    def update_gitlab_source(self, datasource_id: int, **fields) -> DataSource:
        ds = DataSource.objects.get(pk=datasource_id)
        if "name" in fields and fields["name"]:
            ds.name = fields["name"].strip()
        if "base_url" in fields and fields["base_url"]:
            ds.base_url = fields["base_url"].strip()
        ds.save()
        return ds

    def soft_delete_gitlab_source(self, datasource_id: int) -> None:
        ds = DataSource.objects.get(pk=datasource_id)
        ds.projects.update(status=Project.Status.ORPHANED)
        ds.delete()
