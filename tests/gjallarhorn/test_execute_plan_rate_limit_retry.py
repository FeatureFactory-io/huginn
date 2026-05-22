"""execute_plan rate-limit retry — completed steps not re-run — T-67."""

from unittest.mock import MagicMock, patch

import celery.exceptions
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
    """Minimal LLM test double that raises exceptions from the response list."""

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
def plan_3_steps(db):
    user = User.objects.create_user(email="rl-test@example.com", password="test")
    project = Project.objects.create(name="rl-proj", slug="rl-proj")
    conv = Conversation.objects.create(user=user, project=project, conversation_type="sitrep_generation")
    plan = ExecutionPlan.objects.create(conversation=conv, goal="test", progress_total=3)
    for i in range(1, 4):
        PlanStep.objects.create(
            plan=plan, order=i, action=f"Step {i}", reasoning_why_needed="r", expected_outcome="o", is_planning=True
        )
    return plan


@pytest.mark.django_db
class TestExecutePlanRateLimitRetry:
    def test_execute_plan_rate_limit_retry(self, plan_3_steps):
        plan = plan_3_steps
        llm = _ExceptionLLM(
            [
                _END_TURN,  # step 1 — first run
                _END_TURN,  # step 2 — first run
                TimeoutError("simulated rate limit"),  # step 3 — first run → retry
                _END_TURN,  # step 3 — second run (retry)
            ]
        )
        tool_executor = MagicMock()
        tool_executor.execute.return_value = {"success": True, "result": None, "error": None}
        agent = GjallarhornAgent(llm=llm, tool_executor=tool_executor)

        with patch("gjallarhorn.tasks.plan_tasks._build_agent_for_plan", return_value=agent):
            # First run: steps 1-2 complete, step 3 fails → waiting_retry + Retry raised
            with pytest.raises(celery.exceptions.Retry):
                execute_plan.delay(str(plan.plan_id))

            plan.refresh_from_db()
            assert plan.status == "waiting_retry"
            assert plan.steps.filter(status="completed").count() == 2

            # Second run: resumes from step 3 only (steps 1-2 already done)
            execute_plan.delay(str(plan.plan_id))

        plan.refresh_from_db()
        assert plan.status == "completed"
        assert len(llm.calls) == 4  # step1, step2, step3-fail, step3-success
        assert plan.steps.filter(status="completed").count() == 3
