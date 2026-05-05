"""Ingestion ORM models."""

from django.db import models


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


class Project(models.Model):
    """Imported engineering project bound to a DataSource."""

    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        ARCHIVED = "archived", "Archived"
        ORPHANED = "orphaned", "Orphaned"

    datasource = models.ForeignKey(
        DataSource,
        on_delete=models.CASCADE,
        related_name="projects",
    )
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True)
    display_name = models.CharField(max_length=255, blank=True)
    source_path = models.CharField(max_length=512, blank=True)
    playbook_slug = models.CharField(max_length=255, blank=True)
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

    def __str__(self) -> str:
        return self.name
