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
        tool="list_commits",
        reasoning_why_needed="Need data",
        expected_outcome="Commit list",
        is_planning=False,
    )
    step2 = PlanStep.objects.create(
        plan=plan,
        order=2,
        action="Compose narrative",
        tool="",
        reasoning_why_needed="Produce output",
        expected_outcome="Narrative text",
        is_planning=True,
    )
    return plan, step1, step2


def make_agent(llm, tool_executor=None):
    if tool_executor is None:
        tool_executor = MagicMock()
        tool_executor.execute.return_value = {"success": True, "result": None, "error": None}
    return GjallarhornAgent(llm=llm, tool_executor=tool_executor)


@pytest.mark.django_db
class TestExecuteSingleStep:
    def test_data_step_calls_tool_directly(self, scripted_llm_factory, plan_with_steps):
        """A data step (is_planning=False) calls the tool executor without touching the LLM."""
        plan, step1, _ = plan_with_steps
        llm = scripted_llm_factory([])  # no responses — LLM must not be called
        tool_executor = MagicMock()
        tool_executor.execute.return_value = {"success": True, "result": [{"sha": "abc"}], "error": None}
        agent = make_agent(llm, tool_executor)

        agent.execute_single_step(plan, step1)

        step1.refresh_from_db()
        assert step1.status == "completed"
        assert len(llm.calls) == 0  # no LLM call for data steps
        tool_executor.execute.assert_called_with("list_commits", from_dt=None, to_dt=None)

    def test_data_step_stores_tool_result(self, scripted_llm_factory, plan_with_steps):
        """Data step result contains the raw tool output."""
        plan, step1, _ = plan_with_steps
        llm = scripted_llm_factory([])
        tool_executor = MagicMock()
        tool_executor.execute.return_value = {"success": True, "result": ["commit-1"], "error": None}
        agent = make_agent(llm, tool_executor)

        agent.execute_single_step(plan, step1)

        step1.refresh_from_db()
        assert step1.result["result"] == ["commit-1"]

    def test_data_step_critical_failure_raises(self, scripted_llm_factory, plan_with_steps):
        """A critical data step raises ToolExecutionError when the tool fails."""
        plan, step1, _ = plan_with_steps
        llm = scripted_llm_factory([])
        tool_executor = MagicMock()
        tool_executor.execute.return_value = {"success": False, "result": None, "error": "DB error"}
        agent = make_agent(llm, tool_executor)

        with pytest.raises(ToolExecutionError):
            agent.execute_single_step(plan, step1)

    def test_planning_step_calls_llm_with_collected_data(self, scripted_llm_factory, plan_with_steps):
        """Planning step (is_planning=True) passes prior step results into the LLM prompt."""
        plan, step1, step2 = plan_with_steps
        # Simulate step1 already completed with data
        step1.status = "completed"
        step1.result = {"success": True, "result": [{"sha": "abc", "message": "feat: new thing"}], "error": None}
        step1.outcome_assessment = "ok"
        step1.is_planning = False
        step1.save()

        captured_messages = []
        llm = scripted_llm_factory(
            [
                LLMResponse(
                    content='{"headline":"x","situation_assessment":"y"}',
                    stop_reason="end_turn",
                    usage={},
                    tool_calls=[],
                    model="test",
                )
            ]
        )
        original_gen = llm.generate_with_tools

        def capture(messages, tools, system_blocks):
            captured_messages.extend(messages)
            return original_gen(messages, tools, system_blocks)

        tool_executor = MagicMock()
        tool_executor.execute.return_value = {"success": True, "result": None, "error": None}

        with patch.object(llm, "generate_with_tools", side_effect=capture):
            agent = make_agent(llm, tool_executor)
            agent.execute_single_step(plan, step2)

        all_content = " ".join(str(m.get("content", "")) for m in captured_messages)
        # The collected data from step1 must appear in the planning step prompt
        assert "feat: new thing" in all_content

    def test_planning_step_marked_completed(self, scripted_llm_factory, plan_with_steps):
        """Planning step is marked completed after LLM responds."""
        plan, _, step2 = plan_with_steps
        llm = scripted_llm_factory(
            [LLMResponse(content="Narrative done.", stop_reason="end_turn", usage={}, tool_calls=[], model="test")]
        )
        tool_executor = MagicMock()
        tool_executor.execute.return_value = {"success": True, "result": None, "error": None}
        agent = make_agent(llm, tool_executor)
        agent.execute_single_step(plan, step2)
        step2.refresh_from_db()
        assert step2.status == "completed"
        assert step2.model_used == "test"

    def test_planning_step_llm_tool_call_dispatched(self, scripted_llm_factory, plan_with_steps):
        """If the LLM returns a tool_call during the planning step, the executor is invoked."""
        plan, _, step2 = plan_with_steps
        llm = scripted_llm_factory(
            [
                LLMResponse(
                    content="",
                    stop_reason="tool_use",
                    usage={},
                    tool_calls=[{"name": "get_active_roe", "input": {}}],
                    model="test",
                )
            ]
        )
        tool_executor = MagicMock()
        tool_executor.execute.return_value = {"success": True, "result": {"workflow_md": "..."}, "error": None}
        agent = make_agent(llm, tool_executor)
        agent.execute_single_step(plan, step2)
        tool_executor.execute.assert_any_call("get_active_roe")

    def test_planning_step_llm_tool_failure_raises(self, scripted_llm_factory, plan_with_steps):
        """If a tool call during the planning step fails, ToolExecutionError is raised."""
        plan, _, step2 = plan_with_steps
        llm = scripted_llm_factory(
            [
                LLMResponse(
                    content="",
                    stop_reason="tool_use",
                    usage={},
                    tool_calls=[{"name": "get_active_roe", "input": {}}],
                    model="test",
                )
            ]
        )
        tool_executor = MagicMock()
        # First call (system block) succeeds; second call (LLM tool_call) fails
        tool_executor.execute.side_effect = [
            {"success": True, "result": None, "error": None},  # get_active_roe (system block)
            {"success": True, "result": None, "error": None},  # list_active_fragos (system block)
            {"success": True, "result": None, "error": None},  # get_active_situational_awareness (system block)
            {"success": False, "result": None, "error": "Tool failed"},  # LLM tool_call
        ]
        agent = make_agent(llm, tool_executor)
        with pytest.raises(ToolExecutionError):
            agent.execute_single_step(plan, step2)

    def test_system_blocks_four_entries(self, scripted_llm_factory, plan_with_steps):
        """_build_system_blocks always returns exactly 4 blocks (system prompt + 3 static)."""
        plan, _, _ = plan_with_steps
        tool_executor = MagicMock()
        tool_executor.execute.return_value = {"success": True, "result": None, "error": None}
        llm = scripted_llm_factory([])
        agent = make_agent(llm, tool_executor)
        blocks = agent._build_system_blocks(plan)
        assert len(blocks) == 4
