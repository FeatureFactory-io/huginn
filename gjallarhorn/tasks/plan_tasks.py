"""Celery tasks for ExecutionPlan execution — stub (full impl in T-67)."""

from celery import shared_task

from gjallarhorn.models import ExecutionPlan


@shared_task(bind=True, max_retries=5)
def execute_plan(self, plan_id: str) -> None:
    """Execute an ExecutionPlan step-by-step.

    Stub implementation — marks the plan running.
    Full resilience loop implemented in T-67.
    """
    plan = ExecutionPlan.objects.get(plan_id=plan_id)
    plan.status = "running"
    plan.save(update_fields=["status"])
