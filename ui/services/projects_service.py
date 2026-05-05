"""Project lifecycle — import, configuration, archival (Act 2)."""

from __future__ import annotations

import uuid

from django.utils import timezone

from ingestion.integrations.gitlab_client import GitlabClient
from ingestion.models import DataSource, Project


class ProjectsService:
    """Domain entrypoints for Projects."""

    def load_remote_projects_snapshot(self, datasource_id: int) -> dict:
        ds = DataSource.objects.get(pk=datasource_id)
        token = ds.encrypted_token_ciphertext or ""
        meta: dict = {}
        try:
            meta = GitlabClient(ds.base_url, token).verify_token()
        except (ConnectionError, OSError, ValueError):
            pass

        stub_key = _catalog_key(ds)
        return {
            "datasource_id": datasource_id,
            "login": meta.get("username") or ds.name,
            "entries": [
                {"key": stub_key, "name": ds.name},
            ],
        }

    def persist_imported_project_selection(
        self,
        *,
        datasource_id: int,
        remote_keys: list[str],
    ) -> None:
        datasource = DataSource.objects.get(pk=datasource_id)
        for raw in remote_keys:
            key = raw.strip()
            if not key:
                continue
            slug_base = key.replace("/", "-").lower().replace("--", "-")
            slug_base = "".join(ch if ch.isalnum() or ch == "-" else "-" for ch in slug_base).strip("-")
            if not slug_base:
                slug_base = uuid.uuid4().hex[:8]
            name = key.split("/")[-1].strip() or slug_base

            slug = slug_base
            n = 0
            while Project.objects.filter(slug=slug).exists():
                n += 1
                slug = f"{slug_base}-{n}"

            Project.objects.create(
                datasource=datasource,
                name=name,
                slug=slug,
            )

    def enqueue_immediate_project_sync(self, project_id: int) -> None:
        Project.objects.filter(pk=project_id).update(last_sync_at=timezone.now())

    def update_project_configuration(self, project_id: int, **fields) -> None:
        qs = Project.objects.filter(pk=project_id)
        if "display_name" in fields:
            qs.update(display_name=(fields["display_name"] or "").strip())

    def archive_project(self, project_id: int) -> None:
        Project.objects.filter(pk=project_id).update(status=Project.Status.ARCHIVED)


def _catalog_key(ds: DataSource) -> str:
    return f"{ds.name}/imported-{ds.pk}"
