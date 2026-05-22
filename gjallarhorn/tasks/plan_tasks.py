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


@shared_task(bind=True, max_retries=5, name="gjallarhorn.execute_plan")
def execute_plan(self, plan_id: str) -> None:
    """Execute all pending steps of an ExecutionPlan with full resilience matrix."""
    plan = ExecutionPlan.objects.get(plan_id=plan_id)
    agent = _build_agent_for_plan(plan)

    try:
        plan.mark_started()
    except InvalidStateTransitionError:
        logger.info("plan=%s already in terminal state (%s) — skipping", plan.plan_id, plan.status)
        return  # already completed / failed — idempotent no-op

    logger.info("plan=%s started (progress_total=%s)", plan.plan_id, plan.progress_total)

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
            "plan=%s transient error (retry %s/%s): %s", plan.plan_id, plan.retry_count, plan.max_retries, exc
        )
        plan.mark_paused_for_retry(exc)
        if plan.status == "failed":
            logger.error("plan=%s max retries exhausted — marked failed", plan.plan_id)
            return  # max retries reached; plan already marked failed
        raise self.retry(exc=exc, countdown=_retry_countdown(plan))

    except Exception as exc:  # noqa: BLE001
        logger.exception("plan=%s failed with unhandled exception: %s", plan.plan_id, exc)
        plan.mark_failed(exc)
        # TODO(chat-milestone): _notify_ai_of_plan_failure(plan, exc)
        raise
