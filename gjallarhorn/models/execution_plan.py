"""ExecutionPlan model — fields only (state-machine helpers in T-67)."""

import uuid

from django.db import models


class ExecutionPlan(models.Model):
    """Async execution plan for multi-step AI tasks."""

    plan_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    conversation = models.ForeignKey(
        "gjallarhorn.Conversation",
        on_delete=models.CASCADE,
        related_name="plans",
    )
    goal = models.TextField()
    status = models.CharField(max_length=16, default="pending")
    retry_count = models.IntegerField(default=0)
    max_retries = models.IntegerField(default=5)
    celery_task_id = models.CharField(max_length=255, blank=True)
    paused_at = models.DateTimeField(null=True, blank=True)
    last_error = models.TextField(blank=True)
    last_error_type = models.CharField(max_length=255, blank=True)
    retry_after = models.DateTimeField(null=True, blank=True)
    progress_current = models.IntegerField(default=0)
    progress_total = models.IntegerField(default=0)
    progress_message = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"ExecutionPlan {self.plan_id} — {self.status}"
