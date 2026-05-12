"""ExecutionPlan model with state-machine helpers."""

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
    sitrep_from_dt = models.DateTimeField(null=True, blank=True)
    sitrep_to_dt = models.DateTimeField(null=True, blank=True)
    sitrep_trigger = models.CharField(max_length=16, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    def mark_started(self) -> None:
        """Transition to 'running'. Valid from 'pending' or 'waiting_retry' only."""
        if self.status in ("completed", "failed"):
            raise InvalidStateTransitionError(f"Cannot start a plan with status '{self.status}'")
        self.status = "running"
        self.save(update_fields=["status"])

    def mark_completed(self, result=None) -> None:
        self.status = "completed"
        self.save(update_fields=["status"])

    def mark_failed(self, exc: BaseException) -> None:
        self.status = "failed"
        self.last_error = str(exc)
        self.last_error_type = type(exc).__name__
        self.save(update_fields=["status", "last_error", "last_error_type"])

    def mark_paused_for_retry(self, exc: BaseException) -> None:
        """Mark waiting_retry and increment counter; mark failed if max retries reached."""
        if self.retry_count >= self.max_retries:
            self.mark_failed(exc)
            return
        self.status = "waiting_retry"
        self.retry_count += 1
        self.last_error = str(exc)
        self.last_error_type = type(exc).__name__
        self.save(update_fields=["status", "retry_count", "last_error", "last_error_type"])

    def update_progress(self, current: int, message: str = "") -> None:
        self.progress_current = current
        self.progress_message = message
        self.save(update_fields=["progress_current", "progress_message"])

    def get_next_pending_step(self):
        """Return the lowest-order pending step, or None if all are done."""
        return self.steps.filter(status="pending").order_by("order").first()

    def __str__(self):
        return f"ExecutionPlan {self.plan_id} — {self.status}"


class InvalidStateTransitionError(Exception):
    """Raised when an invalid ExecutionPlan state transition is attempted."""
