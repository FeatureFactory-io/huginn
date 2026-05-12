"""GjallarhornAgent.create_plan tests — T-66."""

from unittest.mock import MagicMock, patch

import pytest
from django.contrib.auth import get_user_model

from gjallarhorn.agent.agent import GjallarhornAgent
from gjallarhorn.models import Conversation, ExecutionPlan, PlanStep
from ingestion.models import Project

User = get_user_model()


def make_step_dicts(count=5):
    return [
        {
            "order": i,
            "action": f"Action {i}",
            "reasoning_why_needed": f"Reason {i}",
            "expected_outcome": f"Outcome {i}",
        }
        for i in range(1, count + 1)
    ]


@pytest.fixture
def conversation(db):
    user = User.objects.create_user(email="cp-test@example.com", password="test")
    project = Project.objects.create(name="cp-proj", slug="cp-proj")
    return Conversation.objects.create(user=user, project=project, conversation_type="sitrep_generation")


@pytest.fixture
def agent(scripted_llm_factory):
    llm = scripted_llm_factory([])
    executor = MagicMock()
    executor.execute.return_value = {"success": True, "result": None, "error": None}
    return GjallarhornAgent(llm=llm, tool_executor=executor)


@pytest.mark.django_db
class TestCreatePlan:
    def test_creates_execution_plan_and_steps(self, agent, conversation):
        steps = make_step_dicts(5)
        with patch("gjallarhorn.tasks.plan_tasks.execute_plan.delay"):
            plan = agent.create_plan(conversation, "Generate SitRep", steps)
        assert ExecutionPlan.objects.filter(plan_id=plan.plan_id).exists()
        assert PlanStep.objects.filter(plan=plan).count() == 5

    def test_enqueues_execute_plan(self, agent, conversation):
        steps = make_step_dicts(5)
        plan = agent.create_plan(conversation, "Generate SitRep", steps)
        plan.refresh_from_db()
        assert plan.status != "pending"

    def test_atomic_rollback(self, agent, conversation):
        steps = make_step_dicts(5)
        call_count = 0
        original_create = PlanStep.objects.create

        def failing_create(**kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 3:
                raise ValueError("Simulated failure on step 3")
            return original_create(**kwargs)

        with patch.object(PlanStep.objects, "create", side_effect=failing_create):
            with pytest.raises(ValueError):
                with patch("gjallarhorn.tasks.plan_tasks.execute_plan.delay"):
                    agent.create_plan(conversation, "Generate SitRep", steps)

        assert ExecutionPlan.objects.count() == 0
        assert PlanStep.objects.count() == 0

    def test_returns_execution_plan(self, agent, conversation):
        steps = make_step_dicts(5)
        with patch("gjallarhorn.tasks.plan_tasks.execute_plan.delay"):
            plan = agent.create_plan(conversation, "Generate SitRep", steps)
        assert isinstance(plan, ExecutionPlan)

    def test_progress_total_set(self, agent, conversation):
        steps = make_step_dicts(5)
        with patch("gjallarhorn.tasks.plan_tasks.execute_plan.delay"):
            plan = agent.create_plan(conversation, "Generate SitRep", steps)
        assert plan.progress_total == 5
