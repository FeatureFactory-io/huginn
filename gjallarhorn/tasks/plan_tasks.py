"""Celery tasks for ExecutionPlan execution."""

import logging

import anthropic
from celery import shared_task

from gjallarhorn.models import ExecutionPlan
from gjallarhorn.models.execution_plan import InvalidStateTransitionError

logger = logging.getLogger(__name__)


def _handle_non_critical_step_failure(step, exc: Exception) -> None:
    """Mark a non-critical step as failed and persist the error without raising."""
    logger.warning(
        "plan=%s step %s (%s) failed [non-critical, continuing]: %s: %s",
        step.plan_id,
        step.order,
        step.action,
        type(exc).__name__,
        exc,
    )
    step.status = "failed"
    step.outcome_assessment = f"{type(exc).__name__}: {exc}"
    step.save(update_fields=["status", "outcome_assessment"])


def _build_agent_for_plan(plan: ExecutionPlan):
    """Build a GjallarhornAgent for the given plan.

    Module-level helper so tests can monkey-patch it to inject a
    ScriptedLLM-backed agent without touching task logic.
    """
    from gjallarhorn.services.factory import create_agent  # noqa: PLC0415

    conversation = plan.conversation
    return create_agent(
        user=conversation.user,
        project=conversation.project,
        plan_id=str(plan.plan_id),
    )


def _retry_countdown(plan: ExecutionPlan) -> int:
    """Exponential back-off in seconds, capped at 120."""
    return min(30 * 2 ** (plan.retry_count - 1), 120)


@shared_task(bind=True, max_retries=5, name="gjallarhorn.execute_plan", acks_late=True)
def execute_plan(self, plan_id: str) -> None:
    """Execute all pending steps of an ExecutionPlan with full resilience matrix.

    ``acks_late=True``: the broker message is ACK'd only after the task returns
    (or raises a non-retried exception).  If the worker process dies mid-run the
    broker re-queues the task automatically, so plans are never silently lost.
    Requires ``CELERY_BROKER_TRANSPORT_OPTIONS = {"visibility_timeout": <seconds>}``
    set to at least the worst-case task duration (see settings).
    """
    celery_task_id = self.request.id or ""
    logger.info(
        "execute_plan started: plan=%s celery_task=%s",
        plan_id,
        celery_task_id,
    )
    plan = ExecutionPlan.objects.get(plan_id=plan_id)
    agent = _build_agent_for_plan(plan)

    try:
        plan.mark_started()
    except InvalidStateTransitionError as exc:
        logger.info(
            "execute_plan skipped (idempotent no-op): plan=%s celery_task=%s reason=%s",
            plan_id,
            celery_task_id,
            exc,
        )
        return  # another worker already owns this plan — safe no-op

    logger.info(
        "execute_plan running: plan=%s celery_task=%s progress_total=%s",
        plan.plan_id,
        celery_task_id,
        plan.progress_total,
    )

    try:
        step_number = plan.progress_current
        while (step := plan.get_next_pending_step()) is not None:
            logger.info(
                "plan=%s executing step %s/%s: %s",
                plan.plan_id,
                step.order,
                plan.progress_total,
                step.action,
            )
            step_failed = False
            try:
                agent.execute_single_step(plan, step)
            except Exception as exc:
                if step.is_critical:
                    raise
                _handle_non_critical_step_failure(step, exc)
                step_failed = True

            step_number += 1
            msg = f"{'Failed' if step_failed else 'Completed'}: {step.action}"
            plan.update_progress(step_number, msg)
            logger.info("plan=%s progress %s/%s — %s", plan.plan_id, step_number, plan.progress_total, msg)
            # TODO(chat-milestone): publish plan_step_update

        plan.mark_completed()
        logger.info("plan=%s completed", plan.plan_id)
        # TODO(chat-milestone): publish plan_completed to Redis
        if plan.conversation.conversation_type == "sitrep_generation" and plan.sitrep_to_dt is not None:
            from gjallarhorn.services.sitrep_service import _persist_sitrep_from_plan  # noqa: PLC0415

            try:
                _persist_sitrep_from_plan(plan)
            except Exception:  # noqa: BLE001
                pass  # plan already marked failed by _persist_sitrep_from_plan

    except (anthropic.RateLimitError, TimeoutError, OSError) as exc:
        logger.warning(
            "execute_plan transient error: plan=%s celery_task=%s retry=%s/%s error=%s: %s",
            plan.plan_id,
            celery_task_id,
            plan.retry_count,
            plan.max_retries,
            type(exc).__name__,
            exc,
        )
        plan.mark_paused_for_retry(exc)
        if plan.status == "failed":
            logger.error(
                "execute_plan max retries exhausted: plan=%s celery_task=%s",
                plan.plan_id,
                celery_task_id,
            )
            return  # max retries reached; plan already marked failed
        raise self.retry(exc=exc, countdown=_retry_countdown(plan))

    except Exception as exc:  # noqa: BLE001
        logger.exception(
            "execute_plan unhandled failure: plan=%s celery_task=%s error=%s: %s",
            plan.plan_id,
            celery_task_id,
            type(exc).__name__,
            exc,
        )
        plan.mark_failed(exc)
        # TODO(chat-milestone): _notify_ai_of_plan_failure(plan, exc)
        raise
