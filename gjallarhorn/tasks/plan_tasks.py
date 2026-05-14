"""Celery tasks for ExecutionPlan execution."""

import logging

import anthropic
from celery import shared_task

from gjallarhorn.models import ExecutionPlan
from gjallarhorn.models.execution_plan import InvalidStateTransitionError

logger = logging.getLogger(__name__)


def _build_agent_for_plan(plan: ExecutionPlan):
    """Build a GjallarhornAgent for the given plan.

    Module-level helper so tests can monkey-patch it to inject a
    ScriptedLLM-backed agent without touching task logic.
    """
    from gjallarhorn.services.factory import create_agent  # noqa: PLC0415

    conversation = plan.conversation
    return create_agent(user=conversation.user, project=conversation.project)


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
        return  # already completed / failed — idempotent no-op

    try:
        step_number = plan.progress_current
        while (step := plan.get_next_pending_step()) is not None:
            agent.execute_single_step(plan, step)
            step_number += 1
            plan.update_progress(step_number, f"Completed: {step.action}")
            # TODO(chat-milestone): publish plan_step_update

        plan.mark_completed()
        # TODO(sitrep-generate): _persist_sitrep_from_plan(plan) — wired in #61
        # TODO(chat-milestone): _notify_ai_of_plan_success(plan)

    except (anthropic.RateLimitError, TimeoutError, OSError) as exc:
        plan.mark_paused_for_retry(exc)
        if plan.status == "failed":
            return  # max retries reached; plan already marked failed
        raise self.retry(exc=exc, countdown=_retry_countdown(plan))

    except Exception as exc:  # noqa: BLE001
        plan.mark_failed(exc)
        # TODO(chat-milestone): _notify_ai_of_plan_failure(plan, exc)
        raise
