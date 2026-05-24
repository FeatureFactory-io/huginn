"""Celery tasks for ExecutionPlan orphan recovery."""

import logging

from celery import shared_task
from django.conf import settings
from django.utils import timezone

from gjallarhorn.models import ExecutionPlan
from gjallarhorn.tasks.plan_tasks import execute_plan

logger = logging.getLogger(__name__)


@shared_task(name="gjallarhorn.recover_orphaned_plans")
def recover_orphaned_plans() -> dict:
    """Re-dispatch ExecutionPlans that are stuck in 'pending' or 'running'.

    Plans stuck in 'pending' longer than ``PLAN_ORPHAN_PENDING_SECONDS`` were
    enqueued but never picked up (worker was down when the message arrived and
    Redis dropped it because ``acks_late`` was not set, or it was set but the
    worker restarted before ACK).

    Plans stuck in 'running' longer than ``PLAN_ORPHAN_RUNNING_SECONDS`` had
    their worker die mid-execution without the task being retried.  They are
    reset to 'pending' before re-dispatch so ``mark_started()`` can transition
    them cleanly.

    Returns ``{"re_dispatched": N}`` for observability / CloudWatch metrics.
    """
    pending_secs = int(getattr(settings, "PLAN_ORPHAN_PENDING_SECONDS", 300))
    running_secs = int(getattr(settings, "PLAN_ORPHAN_RUNNING_SECONDS", 1800))

    now = timezone.now()
    cutoff_pending = now - timezone.timedelta(seconds=pending_secs)
    cutoff_running = now - timezone.timedelta(seconds=running_secs)

    orphaned_running = list(
        ExecutionPlan.objects.filter(
            status="running",
            created_at__lt=cutoff_running,
        )
    )
    for plan in orphaned_running:
        age_s = int((now - plan.created_at).total_seconds())
        logger.warning(
            "recover_orphaned_plans: plan=%s stuck in 'running' (%ds) — resetting to pending",
            plan.plan_id,
            age_s,
        )
        updated = ExecutionPlan.objects.filter(plan_id=plan.plan_id, status="running").update(status="pending")
        if updated:
            plan.status = "pending"

    orphaned_pending = list(
        ExecutionPlan.objects.filter(
            status="pending",
            created_at__lt=cutoff_pending,
        )
    )

    to_dispatch = {p.plan_id: p for p in orphaned_running + orphaned_pending}

    count = 0
    for plan in to_dispatch.values():
        age_s = int((now - plan.created_at).total_seconds())
        logger.warning(
            "recover_orphaned_plans: re-dispatching plan=%s (status=%s, age=%ds)",
            plan.plan_id,
            plan.status,
            age_s,
        )
        execute_plan.delay(str(plan.plan_id))
        count += 1

    if count:
        logger.info("recover_orphaned_plans: re-dispatched %d plan(s)", count)
    else:
        logger.debug("recover_orphaned_plans: no orphaned plans found")

    return {"re_dispatched": count}
