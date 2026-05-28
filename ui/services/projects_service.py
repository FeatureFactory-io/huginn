"""Project lifecycle — import, configuration, archival (Act 2)."""

from __future__ import annotations

from django.db import IntegrityError
from django.utils.text import slugify

from ingestion.integrations.gitlab_client import GitlabClient
from ingestion.models import DataSource, Project
from ingestion.tasks import sync_project
from roe.models import RulesOfEngagement, RulesOfEngagementVersion


def _parse_optional_hour(raw: object) -> int | None:
    if raw is None:
        return None
    text = str(raw).strip()
    if not text:
        return None
    if not text.isdigit():
        return None
    hour = int(text)
    if 0 <= hour <= 23:
        return hour
    return None


def _parse_optional_weekday(raw: object) -> int | None:
    if raw is None:
        return None
    text = str(raw).strip()
    if not text:
        return None
    if not text.isdigit():
        return None
    day = int(text)
    if 0 <= day <= 6:
        return day
    return None


class ProjectsService:
    """Domain entrypoints for Projects."""

    def load_remote_projects_snapshot(self, datasource_id: int) -> dict:
        ds = DataSource.objects.get(pk=datasource_id)
        snap: dict = {
            "datasource_id": datasource_id,
            "login": ds.connected_user or ds.name,
            "entries": [],
            "error": None,
        }

        if ds.datasource_type == DataSource.Type.GITLAB:
            return self._load_gitlab_snapshot(ds, snap)
        if ds.datasource_type == DataSource.Type.GITHUB:
            return self._load_github_snapshot(ds, snap)
        snap["error"] = "Project import is only available for GitLab or GitHub data sources."
        return snap

    def _load_gitlab_snapshot(self, ds: DataSource, snap: dict) -> dict:
        token = ds.encrypted_token_ciphertext or ""
        client = GitlabClient(ds.base_url, token)
        try:
            meta = client.verify_token()
            snap["login"] = meta.get("username") or meta.get("name") or meta.get("email") or snap["login"]
            raw_rows = client.list_visible_projects()
        except (ConnectionError, OSError, ValueError) as exc:
            snap["error"] = str(exc) or "Unable to load projects from GitLab."
            return snap

        existing_ids = set(
            Project.objects.filter(datasource=ds, external_project_id__isnull=False).values_list(
                "external_project_id",
                flat=True,
            )
        )

        parsed = 0
        for row in raw_rows:
            gid = row["id"]
            path = row["path_with_namespace"]
            key = str(gid)
            short_name = row["name"]
            label = f"{path} / {short_name}"
            snap["entries"].append(
                {
                    "key": key,
                    "name": label,
                    "short_name": short_name,
                    "path": path,
                    "description": row.get("description") or "",
                    "web_url": row.get("web_url") or "",
                    "last_activity_at": row.get("last_activity_at"),
                    "already_imported": gid in existing_ids,
                }
            )
            parsed += 1

        if not raw_rows:
            return snap
        if parsed == 0:
            snap["error"] = "GitLab returned data but no valid project rows were found."
            snap["entries"] = []
            return snap
        if snap["entries"] and all(e.get("already_imported") for e in snap["entries"]):
            snap["all_imported"] = True
        return snap

    def _load_github_snapshot(self, ds: DataSource, snap: dict) -> dict:
        from ingestion.integrations.github_client import GithubClient

        token = ds.encrypted_token_ciphertext or ""
        client = GithubClient(token)
        try:
            meta = client.verify_token()
            snap["login"] = meta.get("login") or meta.get("username") or snap["login"]
            raw_rows = client.list_visible_repos()
        except (ConnectionError, OSError, ValueError) as exc:
            snap["error"] = str(exc) or "Unable to load repositories from GitHub."
            return snap

        existing_ids = set(
            Project.objects.filter(datasource=ds, external_project_id__isnull=False).values_list(
                "external_project_id",
                flat=True,
            )
        )

        parsed = 0
        for row in raw_rows:
            rid = row["id"]
            path = row["full_name"]
            key = str(rid)
            short_name = row["name"]
            label = f"{path} / {short_name}"
            snap["entries"].append(
                {
                    "key": key,
                    "name": label,
                    "short_name": short_name,
                    "path": path,
                    "description": row.get("description") or "",
                    "web_url": row.get("html_url") or "",
                    "last_activity_at": row.get("updated_at"),
                    "already_imported": rid in existing_ids,
                }
            )
            parsed += 1

        if not raw_rows:
            return snap
        if parsed == 0:
            snap["error"] = "GitHub returned data but no valid repository rows were found."
            snap["entries"] = []
            return snap
        if snap["entries"] and all(e.get("already_imported") for e in snap["entries"]):
            snap["all_imported"] = True
        return snap

    def persist_imported_project_selection(
        self,
        *,
        datasource_id: int,
        remote_keys: list[str],
        catalog_entries: list[dict],
        imported_by_id: int | None = None,
    ) -> list[int]:
        datasource = DataSource.objects.get(pk=datasource_id)
        lookup = {str(e.get("key", "")).strip(): e for e in catalog_entries if e.get("key")}
        created: list[int] = []

        for raw in remote_keys:
            key = raw.strip()
            if not key or key not in lookup:
                continue
            entry = lookup[key]
            if entry.get("already_imported"):
                continue
            try:
                gid = int(key)
            except ValueError:
                continue

            if Project.objects.filter(datasource=datasource, external_project_id=gid).exists():
                continue

            path = str(entry.get("path") or "")
            short_name = str(entry.get("short_name") or path.rsplit("/", maxsplit=1)[-1] or "project")
            web_url = str(entry.get("web_url") or "")
            desc_raw = entry.get("description") or ""
            description = (str(desc_raw) if desc_raw is not None else "")[:500]
            slug_base = slugify(path.replace("/", "-")) or slugify(short_name) or "project"

            slug = slug_base
            n = 0
            while Project.objects.filter(slug=slug).exists():
                n += 1
                slug = f"{slug_base}-{n}"

            try:
                project = Project.objects.create(
                    datasource=datasource,
                    name=short_name,
                    slug=slug,
                    source_path=path,
                    source_url=web_url,
                    description=description,
                    external_project_id=gid,
                    sync_state=Project.SyncState.INITIAL_SYNC_QUEUED,
                    imported_by_id=imported_by_id,
                )
            except IntegrityError:
                continue

            created.append(project.pk)
            sync_project.delay(project.pk)

        return created

    def enqueue_immediate_project_sync(self, project_id: int) -> None:
        Project.objects.filter(pk=project_id).update(sync_state=Project.SyncState.SYNCING)
        sync_project.delay(project_id)

    def update_project_configuration(self, project_id: int, **fields) -> None:
        qs = Project.objects.filter(pk=project_id)
        updates: dict = {}
        if "display_name" in fields:
            updates["display_name"] = (fields["display_name"] or "").strip()
        schedule_val: str | None = None
        if "sync_schedule" in fields:
            val = (fields["sync_schedule"] or "").strip()
            choices = {c.value for c in Project.SyncSchedule}
            if val in choices:
                schedule_val = val
                updates["sync_schedule"] = val

        effective_schedule = schedule_val
        if effective_schedule is None and qs.exists():
            effective_schedule = qs.values_list("sync_schedule", flat=True).first()

        if effective_schedule == Project.SyncSchedule.DAILY:
            if "sync_daily_hour" in fields:
                updates["sync_daily_hour"] = _parse_optional_hour(fields.get("sync_daily_hour"))
        elif effective_schedule is not None:
            updates["sync_daily_hour"] = None

        if effective_schedule == Project.SyncSchedule.WEEKLY:
            weekly_day = _parse_optional_weekday(fields.get("sync_weekly_day"))
            weekly_hour = _parse_optional_hour(fields.get("sync_weekly_hour"))
            if schedule_val == Project.SyncSchedule.WEEKLY and (weekly_day is None or weekly_hour is None):
                updates.pop("sync_schedule", None)
            else:
                if "sync_weekly_day" in fields:
                    updates["sync_weekly_day"] = weekly_day
                if "sync_weekly_hour" in fields:
                    updates["sync_weekly_hour"] = weekly_hour
        elif effective_schedule is not None:
            updates["sync_weekly_day"] = None
            updates["sync_weekly_hour"] = None

        if {"assigned_roe", "pinned_roe_version"} & fields.keys():
            apb_raw = (fields.get("assigned_roe") or "").strip()
            pin_raw = (fields.get("pinned_roe_version") or "").strip()
            if not apb_raw:
                updates["assigned_roe_id"] = None
                updates["pinned_roe_version_id"] = None
                updates["roe_slug"] = ""
            elif apb_raw.isdigit():
                roe = RulesOfEngagement.objects.filter(pk=int(apb_raw)).first()
                if roe:
                    updates["assigned_roe_id"] = roe.pk
                    updates["roe_slug"] = roe.slug
                    pin_pk = None
                    if pin_raw.isdigit():
                        pv = RulesOfEngagementVersion.objects.filter(pk=int(pin_raw), roe_id=roe.pk).first()
                        if pv:
                            pin_pk = pv.pk
                    updates["pinned_roe_version_id"] = pin_pk

        if updates:
            qs.update(**updates)

    def archive_project(self, project_id: int) -> None:
        Project.objects.filter(pk=project_id).update(status=Project.Status.ARCHIVED)
