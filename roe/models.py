"""Versioned Rules of Engagement — metadata, workflow markdown, and variables."""

from django.conf import settings
from django.db import models


class RulesOfEngagement(models.Model):
    """Logical RoE; mutable shell pointing at immutable version snapshots."""

    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True)
    description = models.CharField(max_length=512, blank=True, default="")
    is_system_seed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="roe_authored",
    )

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


class RulesOfEngagementVersion(models.Model):
    """Immutable snapshot (workflow + structured rows) under one RoE."""

    roe = models.ForeignKey(RulesOfEngagement, on_delete=models.CASCADE, related_name="versions")
    version_number = models.PositiveIntegerField()
    workflow_md = models.TextField(blank=True, default="")
    change_summary = models.CharField(max_length=512, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="playbook_versions_created",
    )

    class Meta:
        ordering = ["-version_number"]
        constraints = [
            models.UniqueConstraint(
                fields=("roe", "version_number"),
                name="roe_rulesofengagementversion_unique_version_per_roe",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.roe.slug} v{self.version_number}"


class RulesOfEngagementVariable(models.Model):
    """Structured variable row attached to a RulesOfEngagementVersion."""

    roe_version = models.ForeignKey(
        RulesOfEngagementVersion,
        on_delete=models.CASCADE,
        related_name="variables",
    )
    sort_order = models.PositiveSmallIntegerField()
    name = models.CharField(max_length=255)
    abbrev = models.CharField(max_length=64)
    calculating = models.TextField(blank=True, default="")
    interpreting = models.TextField(blank=True, default="")
    hover = models.TextField(blank=True, default="")
    y_axis_label = models.CharField(max_length=128, blank=True, default="")

    class Meta:
        ordering = ["sort_order"]

    def __str__(self) -> str:
        return self.name
