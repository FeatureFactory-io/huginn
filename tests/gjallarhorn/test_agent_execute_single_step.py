"""GjallarhornAgent.execute_single_step tests — T-66."""

from unittest.mock import MagicMock, patch

import pytest
from django.contrib.auth import get_user_model

from gjallarhorn.agent.agent import GjallarhornAgent
from gjallarhorn.agent.exceptions import ToolExecutionError
from gjallarhorn.llm.base import LLMResponse
from gjallarhorn.models import Conversation, ExecutionPlan, PlanStep
from ingestion.models import Project

User = get_user_model()


@pytest.fixture
def project_and_conv(db):
    user = User.objects.create_user(email="es-test@example.com", password="test")
    project = Project.objects.create(name="es-proj", slug="es-proj")
    conv = Conversation.objects.create(user=user, project=project, conversation_type="sitrep_generation")
    return project, conv


@pytest.fixture
def plan_with_steps(project_and_conv):
    _, conv = project_and_conv
    plan = ExecutionPlan.objects.create(conversation=conv, goal="test", progress_total=2)
    step1 = PlanStep.objects.create(
        plan=plan,
        order=1,
        action="Fetch commits",
        reasoning_why_needed="Need data",
        expected_outcome="Commit list",
    )
    step2 = PlanStep.objects.create(
        plan=plan,
        order=2,
        action="Compose narrative",
        reasoning_why_needed="Produce output",
        expected_outcome="Narrative text",
    )
    return plan, step1, step2


def make_agent(llm, tool_executor=None):
    if tool_executor is None:
        tool_executor = MagicMock()
        tool_executor.execute.return_value = {"success": True, "result": None, "error": None}
    return GjallarhornAgent(llm=llm, tool_executor=tool_executor)


@pytest.mark.django_db
class TestExecuteSingleStep:
    def test_step_marked_completed(self, scripted_llm_factory, plan_with_steps):
        plan, step1, _ = plan_with_steps
        llm = scripted_llm_factory(
            [LLMResponse(content="Analysis done.", stop_reason="end_turn", usage={}, tool_calls=[], model="test")]
        )
        agent = make_agent(llm)
        agent.execute_single_step(plan, step1)
        step1.refresh_from_db()
        assert step1.status == "completed"

    def test_previous_step_results_in_prompt(self, scripted_llm_factory, plan_with_steps):
        plan, step1, step2 = plan_with_steps
        step1.status = "completed"
        step1.result = {"content": "12 commits found"}
        step1.outcome_assessment = "12 commits found"
        step1.save()

        captured_messages = []
        llm = scripted_llm_factory(
            [LLMResponse(content="Narrative.", stop_reason="end_turn", usage={}, tool_calls=[], model="test")]
        )
        original_gen = llm.generate_with_tools

        def capture(messages, tools, system_blocks):
            captured_messages.extend(messages)
            return original_gen(messages, tools, system_blocks)

        with patch.object(llm, "generate_with_tools", side_effect=capture):
            agent = make_agent(llm)
            agent.execute_single_step(plan, step2)

        all_content = " ".join(str(m.get("content", "")) for m in captured_messages)
        assert "12 commits found" in all_content

    def test_tool_call_dispatched(self, scripted_llm_factory, plan_with_steps):
        plan, step1, _ = plan_with_steps
        llm = scripted_llm_factory(
            [
                LLMResponse(
                    content="",
                    stop_reason="tool_use",
                    usage={},
                    tool_calls=[{"name": "list_commits", "input": {"project_id": 1}}],
                    model="test",
                )
            ]
        )
        tool_executor = MagicMock()
        tool_executor.execute.return_value = {"success": True, "result": [], "error": None}
        agent = make_agent(llm, tool_executor)
        agent.execute_single_step(plan, step1)
        tool_executor.execute.assert_any_call("list_commits", project_id=1)

    def test_tool_failure_raises_tool_execution_error(self, scripted_llm_factory, plan_with_steps):
        plan, step1, _ = plan_with_steps
        llm = scripted_llm_factory(
            [
                LLMResponse(
                    content="",
                    stop_reason="tool_use",
                    usage={},
                    tool_calls=[{"name": "list_commits", "input": {}}],
                    model="test",
                )
            ]
        )
        tool_executor = MagicMock()
        tool_executor.execute.return_value = {"success": False, "result": None, "error": "Tool failed"}
        agent = make_agent(llm, tool_executor)
        with pytest.raises(ToolExecutionError):
            agent.execute_single_step(plan, step1)

    def test_system_blocks_four_entries(self, scripted_llm_factory, plan_with_steps):
        plan, step1, _ = plan_with_steps
        llm = scripted_llm_factory(
            [LLMResponse(content="done", stop_reason="end_turn", usage={}, tool_calls=[], model="test")]
        )
        tool_executor = MagicMock()
        tool_executor.execute.return_value = {"success": True, "result": None, "error": None}
        agent = make_agent(llm, tool_executor)
        blocks = agent._build_system_blocks(plan)
        assert len(blocks) == 4
