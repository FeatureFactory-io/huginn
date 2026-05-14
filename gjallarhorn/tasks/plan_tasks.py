"""Celery tasks for ExecutionPlan execution.

# TODO(T-EXEC): replace with full resilience matrix per SAO §17.5
"""

import logging

from celery import shared_task

from gjallarhorn.models import ExecutionPlan

logger = logging.getLogger(__name__)


def _build_agent_for_plan(plan: ExecutionPlan):
    """Build a GjallarhornAgent for the given plan.

    Extracted as a named helper so T-EXEC can swap in the full agent
    with LLM + executor wired from plan context without touching task logic.
    """
    from gjallarhorn.agent.agent import GjallarhornAgent  # noqa: PLC0415
    from gjallarhorn.llm.claude import ClaudeLLM  # noqa: PLC0415
    from gjallarhorn.services.factory import build_executor  # noqa: PLC0415

    conversation = plan.conversation
    llm = ClaudeLLM()
    executor = build_executor(user=conversation.user, project=conversation.project)
    return GjallarhornAgent(llm=llm, tool_executor=executor)


@shared_task(bind=True, name="gjallarhorn.execute_plan")
def execute_plan(self, plan_id: str) -> None:
    """Execute all pending steps of an ExecutionPlan.

    # TODO(T-EXEC): replace with full resilience matrix per SAO §17.5
    """
    plan = ExecutionPlan.objects.get(plan_id=plan_id)
    plan.mark_started()

    agent = _build_agent_for_plan(plan)

    step_number = 0
    try:
        while True:
            step = plan.get_next_pending_step()
            if step is None:
                break
            agent.execute_single_step(plan, step)
            step_number += 1
            plan.update_progress(step_number)
    except Exception as exc:
        plan.mark_failed(exc)
        raise

    plan.mark_completed()
