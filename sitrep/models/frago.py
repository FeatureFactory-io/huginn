"""FRAGO (fragmentary order) rows — project-scoped doctrine overrides."""

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models


class Frago(models.Model):
    """Human-authored FRAGO; persisted under sitrep per SAO."""

    project = models.ForeignKey(
        "ingestion.Project",
        on_delete=models.CASCADE,
        related_name="fragos",
    )
    title = models.CharField(max_length=255)
    body_md = models.TextField(blank=True, default="")
    affected_variable = models.ForeignKey(
        "roe.RulesOfEngagementVariable",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="fragos",
    )
    effective_from = models.DateField(null=True, blank=True)
    effective_to = models.DateField(null=True, blank=True)
    enabled = models.BooleanField(default=True)
    revoked_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="fragos_created",
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="fragos_updated",
    )

    class Meta:
        ordering = ["-updated_at", "-pk"]

    def __str__(self) -> str:
        return self.title

    def clean(self) -> None:
        super().clean()
        if self.revoked_at is not None and self.enabled:
            raise ValidationError("A revoked FRAGO cannot remain enabled.")


class FragoAuditEvent(models.Model):
    """Append-only audit trail for FRAGO mutations (explicit writes at mutation sites)."""

    class Kind(models.TextChoices):
        CREATED = "created", "Created"
        UPDATED = "updated", "Updated"
        ENABLED_TOGGLED = "enabled_toggled", "Enable/disable toggled"
        REVOKED = "revoked", "Revoked"
        BULK_ACTIVATED = "bulk_activated", "Bulk activated"
        BULK_DEACTIVATED = "bulk_deactivated", "Bulk deactivated"
        BULK_REVOKED = "bulk_revoked", "Bulk revoked"

    frago = models.ForeignKey(
        Frago,
        on_delete=models.CASCADE,
        related_name="audit_events",
    )
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="frago_audit_events",
    )
    kind = models.CharField(max_length=32, choices=Kind.choices)
    message = models.CharField(max_length=512)

    class Meta:
        ordering = ["-created_at", "-pk"]

    def __str__(self) -> str:
        return f"{self.frago_id}:{self.kind}:{self.message[:40]}"
