"""execute_plan max retries exhausted — plan marked failed — T-67."""

from unittest.mock import MagicMock, patch

import celery.exceptions
import pytest
from django.contrib.auth import get_user_model

from gjallarhorn.agent.agent import GjallarhornAgent
from gjallarhorn.models import Conversation, ExecutionPlan, PlanStep
from gjallarhorn.tasks.plan_tasks import execute_plan
from ingestion.models import Project

User = get_user_model()


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
def plan_1_step_max_retries_1(db):
    user = User.objects.create_user(email="mr-test@example.com", password="test")
    project = Project.objects.create(name="mr-proj", slug="mr-proj")
    conv = Conversation.objects.create(user=user, project=project, conversation_type="sitrep_generation")
    plan = ExecutionPlan.objects.create(conversation=conv, goal="test", progress_total=1, max_retries=1)
    PlanStep.objects.create(
        plan=plan, order=1, action="Step 1", reasoning_why_needed="r", expected_outcome="o", is_planning=True
    )
    return plan


@pytest.mark.django_db
class TestExecutePlanMaxRetriesExhausted:
    def test_execute_plan_max_retries_exhausted(self, plan_1_step_max_retries_1):
        plan = plan_1_step_max_retries_1
        llm = _ExceptionLLM(
            [
                TimeoutError("fail 1"),  # try 1 → waiting_retry (retry_count → 1)
                TimeoutError("fail 2"),  # try 2 → max_retries=1 reached → failed
            ]
        )
        tool_executor = MagicMock()
        tool_executor.execute.return_value = {"success": True, "result": None, "error": None}
        agent = GjallarhornAgent(llm=llm, tool_executor=tool_executor)

        with patch("gjallarhorn.tasks.plan_tasks._build_agent_for_plan", return_value=agent):
            # Try 1: retry_count=0 < max_retries=1 → waiting_retry + Retry raised
            with pytest.raises(celery.exceptions.Retry):
                execute_plan.delay(str(plan.plan_id))

            # Try 2: retry_count=1 >= max_retries=1 → plan marked failed, no Retry
            execute_plan.delay(str(plan.plan_id))

        plan.refresh_from_db()
        assert plan.status == "failed"
