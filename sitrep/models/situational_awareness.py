"""Situational Awareness document — one per Project, versioned snapshots."""

from django.conf import settings
from django.db import models


class SituationalAwareness(models.Model):
    """Single SA capsule bound to a project."""

    project = models.OneToOneField(
        "ingestion.Project",
        on_delete=models.CASCADE,
        related_name="situational_awareness",
    )

    class Meta:
        verbose_name_plural = "Situational awareness records"

    def __str__(self) -> str:
        return f"SA(project={self.project_id})"


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
