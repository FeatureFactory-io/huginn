"""execute_plan permanent failure — plan failed, later steps never started — T-67."""

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


class _ExceptionLLM:
    def __init__(self, responses):
        self._responses = iter(responses)
        self.calls = []

    def generate_with_tools(self, messages, tools, system_blocks):
        self.calls.append(True)
        resp = next(self._responses)
        if isinstance(resp, BaseException):
            raise resp
        return resp


@pytest.fixture
def plan_5_steps(db):
    user = User.objects.create_user(email="pf-test@example.com", password="test")
    project = Project.objects.create(name="pf-proj", slug="pf-proj")
    conv = Conversation.objects.create(user=user, project=project, conversation_type="sitrep_generation")
    plan = ExecutionPlan.objects.create(conversation=conv, goal="test", progress_total=5)
    for i in range(1, 6):
        PlanStep.objects.create(
            plan=plan, order=i, action=f"Step {i}", reasoning_why_needed="r", expected_outcome="o", is_planning=True
        )
    return plan


@pytest.mark.django_db
class TestExecutePlanPermanentFailure:
    def test_execute_plan_permanent_failure(self, plan_5_steps):
        plan = plan_5_steps
        llm = _ExceptionLLM(
            [
                _END_TURN,  # step 1
                _END_TURN,  # step 2
                RuntimeError("permanent error"),  # step 3 — non-retriable
            ]
        )
        tool_executor = MagicMock()
        tool_executor.execute.return_value = {"success": True, "result": None, "error": None}
        agent = GjallarhornAgent(llm=llm, tool_executor=tool_executor)

        with patch("gjallarhorn.tasks.plan_tasks._build_agent_for_plan", return_value=agent):
            with pytest.raises(RuntimeError):
                execute_plan.delay(str(plan.plan_id))

        plan.refresh_from_db()
        assert plan.status == "failed"
        assert "permanent error" in plan.last_error
        assert plan.steps.filter(status="pending").count() == 3
