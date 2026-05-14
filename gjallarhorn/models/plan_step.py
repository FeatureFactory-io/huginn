"""PlanStep model."""

import uuid

from django.db import models


class PlanStep(models.Model):
    """Single step in an ExecutionPlan."""

    step_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    plan = models.ForeignKey(
        "gjallarhorn.ExecutionPlan",
        on_delete=models.CASCADE,
        related_name="steps",
    )
    order = models.IntegerField()
    action = models.TextField()
    reasoning_why_needed = models.TextField()
    expected_outcome = models.TextField()
    status = models.CharField(max_length=16, default="pending")
    result = models.JSONField(null=True, blank=True)
    outcome_assessment = models.TextField(blank=True)
    is_critical = models.BooleanField(default=True)
    is_planning = models.BooleanField(default=False)
    model_used = models.CharField(max_length=64, blank=True, default="")

    class Meta:
        ordering = ["order"]
        constraints = [
            models.UniqueConstraint(
                fields=["plan", "order"],
                name="uq_plan_step_order",
            ),
        ]

    def __str__(self):
        return f"PlanStep {self.step_id} — order {self.order} ({self.status})"
