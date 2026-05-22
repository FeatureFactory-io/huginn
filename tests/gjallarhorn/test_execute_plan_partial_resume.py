"""execute_plan partial resume — pre-completed steps not re-run — T-67."""

from unittest.mock import MagicMock, patch

import pytest
from django.contrib.auth import get_user_model

from gjallarhorn.agent.agent import GjallarhornAgent
from gjallarhorn.llm.base import LLMResponse
from gjallarhorn.models import Conversation, ExecutionPlan, PlanStep
from gjallarhorn.tasks.plan_tasks import execute_plan
from ingestion.models import Project

User = get_user_model()

_END_TURN = LLMResponse(content="done", stop_reason="end_turn", usage={}, tool_calls=[], model="test")


@pytest.fixture
def plan_5_steps_two_done(db):
    user = User.objects.create_user(email="pr-test@example.com", password="test")
    project = Project.objects.create(name="pr-proj", slug="pr-proj")
    conv = Conversation.objects.create(user=user, project=project, conversation_type="sitrep_generation")
    plan = ExecutionPlan.objects.create(conversation=conv, goal="test", progress_total=5, status="waiting_retry")
    for i in range(1, 6):
        status = "completed" if i <= 2 else "pending"
        result = {"content": f"result {i}"} if i <= 2 else None
        PlanStep.objects.create(
            plan=plan,
            order=i,
            action=f"Step {i}",
            reasoning_why_needed="r",
            expected_outcome="o",
            status=status,
            result=result,
            is_planning=True,
        )
    return plan


@pytest.mark.django_db
class TestExecutePlanPartialResume:
    def test_execute_plan_partial_resume(self, scripted_llm_factory, plan_5_steps_two_done):
        plan = plan_5_steps_two_done
        llm = scripted_llm_factory([_END_TURN, _END_TURN, _END_TURN])
        tool_executor = MagicMock()
        tool_executor.execute.return_value = {"success": True, "result": None, "error": None}
        agent = GjallarhornAgent(llm=llm, tool_executor=tool_executor)

        with patch("gjallarhorn.tasks.plan_tasks._build_agent_for_plan", return_value=agent):
            execute_plan.delay(str(plan.plan_id))

        plan.refresh_from_db()
        assert plan.status == "completed"
        assert len(llm.calls) == 3
