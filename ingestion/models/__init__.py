"""Ingestion ORM models."""

from datetime import timedelta

from django.conf import settings
from django.db import models
from django.utils import timezone

from ingestion.domain.increments import IncrementKind


class DataSource(models.Model):
    """Connected external system; token storage is ciphertext placeholder in MVP."""

    class Type(models.TextChoices):
        GITLAB = "gitlab", "GitLab"
        JIRA = "jira", "Jira"

    class Status(models.TextChoices):
        CONNECTED = "connected", "Connected"
        TOKEN_EXPIRING = "token_expiring", "Token expiring"
        TOKEN_EXPIRED = "token_expired", "Token expired"
        CONNECTION_ERROR = "connection_error", "Connection error"

    name = models.SlugField(max_length=255, unique=True)
    datasource_type = models.CharField(
        max_length=16,
        choices=Type.choices,
        default=Type.GITLAB,
        db_index=True,
    )
    base_url = models.URLField(max_length=512)
    encrypted_token_ciphertext = models.TextField(blank=True)
    token_expires_at = models.DateTimeField(null=True, blank=True)
    connected_user = models.CharField(max_length=255, blank=True)
    visible_project_count = models.IntegerField(null=True, blank=True)
    status = models.CharField(
        max_length=32,
        choices=Status.choices,
        default=Status.CONNECTED,
        db_index=True,
    )
    last_activity_at = models.DateTimeField(null=True, blank=True)
    last_error_message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name

    @property
    def computed_status(self) -> str:
        """Derive UI status from expiry window when applicable."""
        if self.token_expires_at:
            now = timezone.now()
            if self.token_expires_at < now:
                return self.Status.TOKEN_EXPIRED
            if self.token_expires_at <= now + timedelta(days=30):
                return self.Status.TOKEN_EXPIRING
        return self.status

    @property
    def token_expires_in_days(self) -> int | None:
        if self.token_expires_at:
            delta = self.token_expires_at - timezone.now()
            return max(0, delta.days)
        return None

    @property
    def masked_token(self) -> str:
        raw = self.encrypted_token_ciphertext
        if not raw:
            return "—"
        if len(raw) <= 4:
            return "••••"
        return "••••••••" + raw[-4:]


class Contributor(models.Model):
    """Developer identity keyed by DataSource + email (MVP reconciliation)."""

    datasource = models.ForeignKey(
        DataSource,
        on_delete=models.CASCADE,
        related_name="contributors",
    )
    email = models.EmailField(max_length=254)
    name = models.CharField(max_length=255, blank=True)
    handle = models.CharField(max_length=255, blank=True)
    first_seen_at = models.DateTimeField(auto_now_add=True)
    last_seen_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["datasource_id", "email"]
        constraints = [
            models.UniqueConstraint(fields=["datasource", "email"], name="ingestion_contributor_ds_email_uniq"),
        ]

    def __str__(self) -> str:
        return f"{self.email} @ {self.datasource_id}"


class Project(models.Model):
    """Imported engineering project bound to a DataSource."""

    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        ARCHIVED = "archived", "Archived"
        ORPHANED = "orphaned", "Orphaned"

    class SyncState(models.TextChoices):
        INITIAL_SYNC_QUEUED = "initial_sync_queued", "Initial sync queued"
        SYNCING = "syncing", "Syncing"
        ACTIVE = "active", "Active"
        ERROR = "error", "Error"

    class SyncSchedule(models.TextChoices):
        HOURLY = "hourly", "Hourly"
        EVERY_6H = "every_6h", "Every 6h"
        DAILY = "daily", "Daily"
        WEEKLY = "weekly", "Weekly"
        MANUAL = "manual", "Manual"

    datasource = models.ForeignKey(
        DataSource,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="projects",
    )
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True)
    display_name = models.CharField(max_length=255, blank=True)
    source_path = models.CharField(max_length=512, blank=True)
    roe_slug = models.CharField(max_length=255, blank=True)
    assigned_roe = models.ForeignKey(
        "roe.RulesOfEngagement",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assigned_projects",
    )
    pinned_roe_version = models.ForeignKey(
        "roe.RulesOfEngagementVersion",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="pinned_projects",
    )
    gitlab_project_id = models.BigIntegerField(null=True, blank=True, db_index=True)
    source_url = models.URLField(max_length=1024, blank=True)
    description = models.TextField(blank=True, default="")
    sync_state = models.CharField(
        max_length=32,
        choices=SyncState.choices,
        default=SyncState.INITIAL_SYNC_QUEUED,
        db_index=True,
    )
    sync_schedule = models.CharField(
        max_length=16,
        choices=SyncSchedule.choices,
        default=SyncSchedule.HOURLY,
    )
    sync_daily_hour = models.IntegerField(null=True, blank=True)
    sync_weekly_day = models.IntegerField(null=True, blank=True)
    sync_weekly_hour = models.IntegerField(null=True, blank=True)
    imported_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="imported_projects",
    )
    status = models.CharField(
        max_length=32,
        choices=Status.choices,
        default=Status.ACTIVE,
        db_index=True,
    )
    last_sync_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]
        constraints = [
            models.UniqueConstraint(
                fields=["datasource", "gitlab_project_id"],
                condition=models.Q(gitlab_project_id__isnull=False),
                name="ingestion_project_ds_gitlab_id_uniq",
            ),
        ]

    def __str__(self) -> str:
        return self.name


class Increment(models.Model):
    """Ingested discrete contribution (commit; post-MVP kinds register here)."""

    class Kind(models.TextChoices):
        COMMIT = IncrementKind.COMMIT, "Commit"

    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="increments",
    )
    datasource = models.ForeignKey(
        DataSource,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="increments_records",
    )
    kind = models.CharField(max_length=32, choices=Kind.choices, db_index=True)
    external_id = models.CharField(max_length=128, db_index=True)
    occurred_at = models.DateTimeField(db_index=True)
    contributor = models.ForeignKey(
        Contributor,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="increments",
    )
    summary = models.CharField(max_length=512, blank=True)
    payload = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-occurred_at", "id"]
        constraints = [
            models.UniqueConstraint(
                fields=["project", "kind", "external_id"],
                name="ingestion_increment_proj_kind_ext_uniq",
            ),
        ]
        indexes = [
            models.Index(fields=["project", "occurred_at"]),
            models.Index(fields=["project", "kind", "occurred_at"]),
        ]

    def __str__(self) -> str:
        return f"{self.kind}:{self.external_id[:12]}"


class IngestionRun(models.Model):
    """One execution of sync for a project."""

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        RUNNING = "running", "Running"
        SUCCESS = "success", "Success"
        ERROR = "error", "Error"

    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="ingestion_runs",
    )
    datasource = models.ForeignKey(
        DataSource,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="ingestion_runs_records",
    )
    started_at = models.DateTimeField(auto_now_add=True)
    finished_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.PENDING, db_index=True)
    cursor_to = models.DateTimeField(null=True, blank=True)
    increments_ingested = models.IntegerField(default=0)
    contributors_touched = models.IntegerField(default=0)
    error_message = models.TextField(blank=True)

    class Meta:
        ordering = ["-started_at", "id"]

    def __str__(self) -> str:
        return f"run #{self.pk} project={self.project_id} {self.status}"
