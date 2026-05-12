"""Celery tasks for ExecutionPlan execution."""

from celery import shared_task

from gjallarhorn.models import ExecutionPlan


def _build_agent_for_plan(plan):
    """Build a GjallarhornAgent scoped to the plan's project. Patched in tests."""
    from gjallarhorn.services.factory import create_agent

    return create_agent(plan)


def _retry_countdown(retry_count: int) -> int:
    """Exponential backoff: 30s → 60s → 120s → 240s → 480s."""
    return 30 * (2 ** (retry_count - 1))


@shared_task(bind=True, max_retries=5)
def execute_plan(self, plan_id: str) -> None:
    """Execute all pending PlanSteps for the given ExecutionPlan.

    Resilience:
    - TimeoutError / OSError → mark_paused_for_retry + Celery retry (up to max_retries)
    - Other exceptions → mark_failed + re-raise
    - Already-completed steps are never re-run (get_next_pending_step skips them)
    """
    plan = ExecutionPlan.objects.select_related("conversation__project").get(plan_id=plan_id)
    plan.mark_started()

    agent = _build_agent_for_plan(plan)

    try:
        while True:
            step = plan.get_next_pending_step()
            if step is None:
                break
            agent.execute_single_step(plan, step)
            plan.update_progress(plan.steps.filter(status="completed").count())

        plan.mark_completed()
        # TODO(chat-milestone): _notify_ai_of_plan_success(plan)
        # TODO(sitrep-generate): _persist_sitrep_from_plan(plan)

    except (TimeoutError, OSError) as exc:
        plan.refresh_from_db()
        plan.mark_paused_for_retry(exc)
        plan.refresh_from_db()
        if plan.status == "waiting_retry":
            raise self.retry(exc=exc, countdown=_retry_countdown(plan.retry_count))
        # max retries exhausted — plan is already marked failed, return cleanly

    except Exception as exc:
        plan.mark_failed(exc)
        # TODO(chat-milestone): _notify_ai_of_plan_failure(plan, exc)
        raise
