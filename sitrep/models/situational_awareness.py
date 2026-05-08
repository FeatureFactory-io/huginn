"""Situational Awareness document — one capsule per workspace, versioned snapshots."""

from django.conf import settings
from django.db import models


class SituationalAwareness(models.Model):
    """Single SA capsule for the whole workspace (singleton row)."""

    class Meta:
        verbose_name_plural = "Situational awareness records"

    def __str__(self) -> str:
        return "SA (workspace)"


class SituationalAwarenessVersion(models.Model):
    """Immutable prose snapshot under one SA."""

    awareness = models.ForeignKey(
        SituationalAwareness,
        on_delete=models.CASCADE,
        related_name="versions",
    )
    version_number = models.PositiveIntegerField()
    standing_md = models.TextField(blank=True, default="")
    active_md = models.TextField(blank=True, default="")
    change_summary = models.CharField(max_length=512, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="situational_awareness_versions_created",
    )

    class Meta:
        ordering = ["-version_number"]
        constraints = [
            models.UniqueConstraint(
                fields=("awareness", "version_number"),
                name="sitrep_situationalawarenessversion_unique_version_per_awareness",
            ),
        ]

    def __str__(self) -> str:
        return f"v{self.version_number}"


class SituationalAwarenessEntry(models.Model):
    """Structured row under one SA version (standing vs active situations)."""

    class Section(models.TextChoices):
        STANDING = "standing", "Standing"
        ACTIVE = "active", "Active"

    version = models.ForeignKey(
        SituationalAwarenessVersion,
        on_delete=models.CASCADE,
        related_name="entries",
    )
    section = models.CharField(max_length=16, choices=Section.choices)
    sort_order = models.PositiveSmallIntegerField(default=0)
    title = models.CharField(max_length=255, default="Content")
    body_md = models.TextField(blank=True, default="")
    decision_label = models.CharField(max_length=128, blank=True, default="")
    decision_href = models.URLField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="situational_awareness_entries_created",
    )

    class Meta:
        ordering = ["section", "sort_order", "pk"]

    def __str__(self) -> str:
        return f"{self.section}:{self.title[:32]}"
