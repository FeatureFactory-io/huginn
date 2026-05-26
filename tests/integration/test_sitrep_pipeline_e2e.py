"""SitRep pipeline end-to-end integration tests.

Proves the full lifecycle:
  1. A SitRep can be requested via the Celery task.
  2. An ExecutionPlan with 5 PlanSteps is created.
  3. All 5 steps are executed in order and progress is tracked.
  4. A non-critical step failure does not crash the plan.
  5. The resulting SitRep is persisted and ready for display.
"""

import json
from datetime import timedelta
from unittest.mock import MagicMock, patch

import pytest
from django.utils import timezone

from gjallarhorn.agent.agent import GjallarhornAgent
from gjallarhorn.llm.base import LLMResponse
from gjallarhorn.models import Conversation, ExecutionPlan, PlanStep
from gjallarhorn.tasks.plan_tasks import execute_plan
from gjallarhorn.tasks.sitrep_tasks import generate_sitrep_for_project
from sitrep.models import SitRep
from tests.factories import (
    FragoFactory,
    ProjectFactory,
    RulesOfEngagementFactory,
    RulesOfEngagementVariableFactory,
    RulesOfEngagementVersionFactory,
    UserFactory,
)
from tests.gjallarhorn.conftest import ScriptedLLM

# ---------------------------------------------------------------------------
# Shared test doubles
# ---------------------------------------------------------------------------

_NARRATIVE = {
    "headline": "GREEN — sprint on track",
    "situation_assessment": "All 8 commits merged cleanly, no blockers.",
    "notable_activity": ["Alice: 5 commits", "Bob: 3 PRs merged"],
}
_NARRATIVE_JSON = json.dumps(_NARRATIVE)
_END_TURN = LLMResponse(
    content=_NARRATIVE_JSON,
    stop_reason="end_turn",
    usage={},
    tool_calls=[],
    model="test-model",
)


def _scripted_agent() -> GjallarhornAgent:
    """GjallarhornAgent backed by ScriptedLLM returning the canonical narrative JSON.

    The new architecture calls the LLM exactly once (the planning step).
    Data steps 1–4 call tools directly without touching the LLM.
    """
    llm = ScriptedLLM([_END_TURN])  # one response for the single planning step
    te = MagicMock()
    te.execute.return_value = {"success": True, "result": None, "error": None}
    return GjallarhornAgent(llm=llm, tool_executor=te)


def _agent_with_failing_step(fail_on_order: int) -> GjallarhornAgent:
    """Mocked agent whose execute_single_step raises RuntimeError for one specific step order.

    All other steps are completed normally with the canonical narrative JSON so
    that _persist_sitrep_from_plan can read the final step result.
    """
    agent = MagicMock(spec=GjallarhornAgent)

    def _side_effect(plan, step):
        if step.order == fail_on_order:
            raise RuntimeError(f"Simulated failure on step {step.order}")
        step.status = "completed"
        step.outcome_assessment = _NARRATIVE_JSON
        step.result = {"tool_results": [], "synthesis": _NARRATIVE_JSON}
        step.model_used = "test-model"
        step.save()

    agent.execute_single_step.side_effect = _side_effect
    return agent


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def project_ctx(db):
    """A fully configured project: user, roe v1, two FRAGOs, time window."""
    user = UserFactory()
    roe = RulesOfEngagementFactory()
    RulesOfEngagementVersionFactory(roe=roe, version_number=1)
    project = ProjectFactory(imported_by=user, assigned_roe=roe)
    FragoFactory(project=project, title="FRAGO Alpha")
    FragoFactory(project=project, title="FRAGO Bravo")
    now = timezone.now()
    return {
        "project": project,
        "user": user,
        "from_dt": now - timedelta(hours=8),
        "to_dt": now,
    }


# ---------------------------------------------------------------------------
# 1. Sitrep can be requested
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_sitrep_can_be_requested(project_ctx):
    """generate_sitrep_for_project returns a plan_id and creates a DB record."""
    project = project_ctx["project"]
    from_dt = project_ctx["from_dt"]
    to_dt = project_ctx["to_dt"]

    agent = _scripted_agent()
    with patch("gjallarhorn.tasks.plan_tasks._build_agent_for_plan", return_value=agent):
        plan_id = generate_sitrep_for_project(
            project_id=project.pk,
            from_dt=from_dt.isoformat(),
            to_dt=to_dt.isoformat(),
            trigger="manual",
        )

    assert plan_id is not None, "task must return a plan_id"
    assert ExecutionPlan.objects.filter(plan_id=plan_id).exists(), "ExecutionPlan must be persisted"


@pytest.mark.django_db
def test_sitrep_not_requested_without_roe(db):
    """generate_sitrep_for_project returns None when project has no roe."""
    user = UserFactory()
    project = ProjectFactory(imported_by=user, assigned_roe=None)
    now = timezone.now()

    plan_id = generate_sitrep_for_project(
        project_id=project.pk,
        from_dt=(now - timedelta(hours=1)).isoformat(),
        to_dt=now.isoformat(),
    )

    assert plan_id is None
    assert not ExecutionPlan.objects.filter(conversation__project=project).exists()


# ---------------------------------------------------------------------------
# 2. Plan is created with correct structure
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_plan_created_with_5_steps(project_ctx):
    """ExecutionPlan is created with exactly 5 PlanSteps in the correct order."""
    project = project_ctx["project"]
    from_dt = project_ctx["from_dt"]
    to_dt = project_ctx["to_dt"]

    agent = _scripted_agent()
    with patch("gjallarhorn.tasks.plan_tasks._build_agent_for_plan", return_value=agent):
        plan_id = generate_sitrep_for_project(
            project_id=project.pk,
            from_dt=from_dt.isoformat(),
            to_dt=to_dt.isoformat(),
            trigger="manual",
        )

    plan = ExecutionPlan.objects.get(plan_id=plan_id)
    assert plan.progress_total == 5

    steps = list(plan.steps.order_by("order"))
    assert len(steps) == 5
    assert [s.order for s in steps] == [1, 2, 3, 4, 5]

    # Final step is the narrative composition step
    assert steps[-1].is_planning is True

    # Plan is linked to the correct project via conversation
    assert plan.conversation.project == project
    assert plan.conversation.conversation_type == "sitrep_generation"


# ---------------------------------------------------------------------------
# 3. Steps are executed in order with progress tracking
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_all_steps_executed_with_progress(project_ctx):
    """All 5 steps run to completion and progress_current reaches 5."""
    project = project_ctx["project"]
    from_dt = project_ctx["from_dt"]
    to_dt = project_ctx["to_dt"]

    agent = _scripted_agent()
    with patch("gjallarhorn.tasks.plan_tasks._build_agent_for_plan", return_value=agent):
        plan_id = generate_sitrep_for_project(
            project_id=project.pk,
            from_dt=from_dt.isoformat(),
            to_dt=to_dt.isoformat(),
            trigger="manual",
        )

    plan = ExecutionPlan.objects.get(plan_id=plan_id)
    assert plan.status == "completed"
    assert plan.progress_current == 5
    assert plan.steps.filter(status="completed").count() == 5
    assert plan.steps.filter(status="pending").count() == 0

    # Data steps call tools directly — the LLM is invoked exactly once (planning step)
    assert len(agent.llm.calls) == 1

    # The single LLM call contains the "Compose SitRep narrative" goal
    assert "Compose SitRep narrative" in agent.llm.calls[0]["messages"][0]["content"]


# ---------------------------------------------------------------------------
# 4. Non-critical step failure does not crash the plan
# ---------------------------------------------------------------------------


@pytest.fixture()
def plan_with_non_critical_step_2(db):
    """A 5-step plan where step 2 is marked non-critical."""
    user = UserFactory()
    roe = RulesOfEngagementFactory()
    RulesOfEngagementVersionFactory(roe=roe, version_number=1)
    project = ProjectFactory(imported_by=user, assigned_roe=roe)
    now = timezone.now()

    conv = Conversation.objects.create(
        user=user,
        project=project,
        conversation_type="sitrep_generation",
    )
    plan = ExecutionPlan.objects.create(
        conversation=conv,
        goal="Generate SitRep (non-critical step test)",
        status="pending",
        progress_total=5,
        sitrep_from_dt=now - timedelta(hours=8),
        sitrep_to_dt=now,
        sitrep_trigger="manual",
    )
    for i in range(1, 6):
        PlanStep.objects.create(
            plan=plan,
            order=i,
            action=f"Step {i}",
            reasoning_why_needed="reason",
            expected_outcome="outcome",
            status="pending",
            is_critical=(i != 2),  # step 2 is non-critical
            is_planning=(i == 5),
        )
    return plan


@pytest.mark.django_db
def test_non_critical_step_failure_does_not_crash_plan(plan_with_non_critical_step_2):
    """A non-critical step failure is recorded but the plan still completes."""
    plan = plan_with_non_critical_step_2
    agent = _agent_with_failing_step(fail_on_order=2)

    with patch("gjallarhorn.tasks.plan_tasks._build_agent_for_plan", return_value=agent):
        execute_plan.delay(str(plan.plan_id))

    plan.refresh_from_db()
    assert plan.status == "completed", "plan must complete despite non-critical step failure"
    assert plan.progress_current == 5, "all 5 steps must be counted toward progress"

    steps = {s.order: s for s in plan.steps.all()}
    assert steps[1].status == "completed"
    assert steps[2].status == "failed"
    assert steps[3].status == "completed"
    assert steps[4].status == "completed"
    assert steps[5].status == "completed"

    # The error is recorded on the failed step
    assert "RuntimeError" in steps[2].outcome_assessment
    assert "Simulated failure" in steps[2].outcome_assessment


@pytest.mark.django_db
def test_critical_step_failure_marks_plan_failed(db):
    """A critical step failure marks the plan as failed (not completed)."""
    user = UserFactory()
    project = ProjectFactory(imported_by=user)
    conv = Conversation.objects.create(user=user, project=project, conversation_type="sitrep_generation")
    plan = ExecutionPlan.objects.create(
        conversation=conv,
        goal="test",
        status="pending",
        progress_total=3,
    )
    for i in range(1, 4):
        PlanStep.objects.create(
            plan=plan,
            order=i,
            action=f"Step {i}",
            reasoning_why_needed="reason",
            expected_outcome="outcome",
            status="pending",
            is_critical=True,
        )

    agent = _agent_with_failing_step(fail_on_order=2)

    with patch("gjallarhorn.tasks.plan_tasks._build_agent_for_plan", return_value=agent):
        with pytest.raises(RuntimeError, match="Simulated failure"):
            execute_plan.delay(str(plan.plan_id))

    plan.refresh_from_db()
    assert plan.status == "failed"
    assert "Simulated failure" in plan.last_error

    # Step 1 completed, step 2 raised before save so it stays pending
    steps = {s.order: s for s in plan.steps.all()}
    assert steps[1].status == "completed"
    assert steps[2].status == "pending"  # execute_single_step raised before saving
    # Step 3 was never reached
    assert steps[3].status == "pending"


# ---------------------------------------------------------------------------
# 5. SitRep result is persisted and ready to display
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_sitrep_persisted_with_correct_content(project_ctx):
    """A SitRep row is created with the correct fields and linked to the plan."""
    project = project_ctx["project"]
    from_dt = project_ctx["from_dt"]
    to_dt = project_ctx["to_dt"]

    agent = _scripted_agent()
    with patch("gjallarhorn.tasks.plan_tasks._build_agent_for_plan", return_value=agent):
        plan_id = generate_sitrep_for_project(
            project_id=project.pk,
            from_dt=from_dt.isoformat(),
            to_dt=to_dt.isoformat(),
            trigger="manual",
        )

    sitrep = SitRep.objects.filter(project=project).first()
    assert sitrep is not None, "SitRep must be persisted after plan completes"

    assert sitrep.headline == _NARRATIVE["headline"]
    assert sitrep.situation_assessment == _NARRATIVE["situation_assessment"]
    assert sitrep.notable_activity == _NARRATIVE["notable_activity"]
    assert sitrep.trigger == "manual"
    assert str(sitrep.source_plan_id) == plan_id

    # FRAGOs attached at generation time are linked
    assert sitrep.fragos_applied.count() == 2


# ---------------------------------------------------------------------------
# 6. Variables pipeline: assessment steps, LLM calls, datapoints, snapshot
# ---------------------------------------------------------------------------


@pytest.fixture()
def project_ctx_with_vars(db):
    """Project with RoE and 2 defined variables — proves the variables pipeline."""
    user = UserFactory()
    roe = RulesOfEngagementFactory()
    version = RulesOfEngagementVersionFactory(roe=roe, version_number=1)
    RulesOfEngagementVariableFactory(
        roe_version=version,
        sort_order=1,
        name="Throughput",
        abbrev="Tp",
        y_axis_label="MRs",
        calculating="Count merged MRs in period",
        interpreting="Green if > 10",
    )
    RulesOfEngagementVariableFactory(
        roe_version=version,
        sort_order=2,
        name="Cycle Time",
        abbrev="CT",
        y_axis_label="days",
        calculating="Median days from first commit to merge",
        interpreting="Green if < 5 days",
    )
    project = ProjectFactory(imported_by=user, assigned_roe=roe)
    now = timezone.now()
    return {
        "project": project,
        "user": user,
        "from_dt": now - timedelta(hours=8),
        "to_dt": now,
        "version": version,
    }


@pytest.mark.django_db
def test_plan_with_variables_has_correct_step_count(project_ctx_with_vars):
    """Plan for a project with 2 variables has 4 data + 2 var + 1 narrative = 7 steps."""
    project = project_ctx_with_vars["project"]
    from_dt = project_ctx_with_vars["from_dt"]
    to_dt = project_ctx_with_vars["to_dt"]

    # 2 variable steps need LLM responses; 1 narrative step needs 1 more
    var_response = LLMResponse(
        content='{"value": "12", "color": "green"}',
        stop_reason="end_turn",
        usage={},
        tool_calls=[],
        model="test-model",
    )
    responses = [var_response, var_response, _END_TURN]  # 2 vars + 1 narrative
    llm = ScriptedLLM(responses)
    te = MagicMock()
    te.execute.return_value = {"success": True, "result": None, "error": None}
    agent = GjallarhornAgent(llm=llm, tool_executor=te)

    with patch("gjallarhorn.tasks.plan_tasks._build_agent_for_plan", return_value=agent):
        plan_id = generate_sitrep_for_project(
            project_id=project.pk,
            from_dt=from_dt.isoformat(),
            to_dt=to_dt.isoformat(),
            trigger="manual",
        )

    plan = ExecutionPlan.objects.get(plan_id=plan_id)
    assert plan.progress_total == 7, "4 data + 2 variable + 1 narrative"

    steps = list(plan.steps.order_by("order"))
    assert len(steps) == 7

    var_steps = [s for s in steps if s.is_variable_assessment]
    assert len(var_steps) == 2
    assert var_steps[0].action == "Assess Throughput (Tp)"
    assert var_steps[1].action == "Assess Cycle Time (CT)"

    assert steps[-1].is_planning is True


@pytest.mark.django_db
def test_variables_pipeline_full_e2e(project_ctx_with_vars):
    """Full pipeline: generate_sitrep_for_project → variable steps executed → datapoints persisted."""
    from sitrep.models import VariableDatapoint

    project = project_ctx_with_vars["project"]
    from_dt = project_ctx_with_vars["from_dt"]
    to_dt = project_ctx_with_vars["to_dt"]

    tp_response = LLMResponse(
        content='{"value": "15", "color": "green"}',
        stop_reason="end_turn",
        usage={},
        tool_calls=[],
        model="test-model",
    )
    ct_response = LLMResponse(
        content='{"value": "3.2", "color": "green"}',
        stop_reason="end_turn",
        usage={},
        tool_calls=[],
        model="test-model",
    )
    responses = [tp_response, ct_response, _END_TURN]  # 2 var assessments + narrative
    llm = ScriptedLLM(responses)
    te = MagicMock()
    te.execute.return_value = {"success": True, "result": None, "error": None}
    agent = GjallarhornAgent(llm=llm, tool_executor=te)

    with patch("gjallarhorn.tasks.plan_tasks._build_agent_for_plan", return_value=agent):
        plan_id = generate_sitrep_for_project(
            project_id=project.pk,
            from_dt=from_dt.isoformat(),
            to_dt=to_dt.isoformat(),
            trigger="manual",
        )

    # Plan completed with all 7 steps
    plan = ExecutionPlan.objects.get(plan_id=plan_id)
    assert plan.status == "completed"
    assert plan.steps.filter(status="completed").count() == 7

    # LLM called 3 times: 2 variable assessments + 1 narrative
    assert len(llm.calls) == 3

    # Variable assessment LLM calls contain the variable name
    assert "Throughput" in llm.calls[0]["messages"][0]["content"]
    assert "Cycle Time" in llm.calls[1]["messages"][0]["content"]

    # SitRep was persisted
    sitrep = SitRep.objects.filter(project=project).first()
    assert sitrep is not None
    assert sitrep.headline == _NARRATIVE["headline"]

    # VariableDatapoints were created
    dps = list(VariableDatapoint.objects.filter(sitrep=sitrep).order_by("roe_variable__sort_order"))
    assert len(dps) == 2

    assert dps[0].variable_name == "Throughput"
    assert dps[0].value == "15"
    assert dps[0].color == "green"
    assert dps[0].y_axis_label == "MRs"

    assert dps[1].variable_name == "Cycle Time"
    assert dps[1].value == "3.2"
    assert dps[1].color == "green"
    assert dps[1].y_axis_label == "days"

    # variables_snapshot is populated on the SitRep
    assert len(sitrep.variables_snapshot) == 2
    snap = {v["variable_name"]: v for v in sitrep.variables_snapshot}
    assert snap["Throughput"]["value"] == "15"
    assert snap["Throughput"]["color"] == "green"
    assert snap["Throughput"]["abbrev"] == "Tp"
    assert snap["Cycle Time"]["value"] == "3.2"
    assert snap["Cycle Time"]["color"] == "green"


@pytest.mark.django_db
def test_sitrep_idempotent_on_duplicate_request(project_ctx):
    """A second automatic request for the same to_dt does not create a duplicate SitRep."""
    project = project_ctx["project"]
    from_dt = project_ctx["from_dt"]
    to_dt = project_ctx["to_dt"]

    agent = _scripted_agent()
    with patch("gjallarhorn.tasks.plan_tasks._build_agent_for_plan", return_value=agent):
        plan_id_1 = generate_sitrep_for_project(
            project_id=project.pk,
            from_dt=from_dt.isoformat(),
            to_dt=to_dt.isoformat(),
            trigger="automatic",
        )
        # Second call with same to_dt — should reuse existing sitrep
        plan_id_2 = generate_sitrep_for_project(
            project_id=project.pk,
            from_dt=from_dt.isoformat(),
            to_dt=to_dt.isoformat(),
            trigger="automatic",
        )

    assert SitRep.objects.filter(project=project).count() == 1, "only one SitRep must exist"
    assert plan_id_1 == plan_id_2, "idempotent call must return the same plan_id"
