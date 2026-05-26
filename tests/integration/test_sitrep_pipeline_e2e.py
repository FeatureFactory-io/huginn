"""SitRep pipeline end-to-end integration tests.

Proves the full lifecycle through the real task → execute_plan → create_agent path.
Only the Anthropic client is stubbed (ScriptedLLM via patch_claude_llm); ToolExecutor
and MCP tools run for real against the test database.

  1. A SitRep can be requested via the Celery task.
  2. An ExecutionPlan with the correct PlanSteps is created.
  3. All steps are executed in order and progress is tracked.
  4. The resulting SitRep is persisted and ready for display.
  5. Variables pipeline: assessment steps, datapoints, variables_snapshot.
"""

import json
from datetime import timedelta

import pytest
from django.utils import timezone

from gjallarhorn.llm.base import LLMResponse
from gjallarhorn.models import ExecutionPlan
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

# ---------------------------------------------------------------------------
# Shared scripted LLM responses
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


# ---------------------------------------------------------------------------
# 1. Sitrep can be requested
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_sitrep_can_be_requested(project_ctx, patch_claude_llm):
    """generate_sitrep_for_project returns a plan_id and creates a DB record."""
    patch_claude_llm([_END_TURN])
    project = project_ctx["project"]
    from_dt = project_ctx["from_dt"]
    to_dt = project_ctx["to_dt"]

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
def test_plan_created_with_5_steps(project_ctx, patch_claude_llm):
    """ExecutionPlan is created with exactly 5 PlanSteps in the correct order."""
    patch_claude_llm([_END_TURN])
    project = project_ctx["project"]
    from_dt = project_ctx["from_dt"]
    to_dt = project_ctx["to_dt"]

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

    assert steps[-1].is_planning is True
    assert plan.conversation.project == project
    assert plan.conversation.conversation_type == "sitrep_generation"


# ---------------------------------------------------------------------------
# 3. Steps are executed in order with progress tracking
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_all_steps_executed_with_progress(project_ctx, patch_claude_llm):
    """All 5 steps run to completion and progress_current reaches 5."""
    llm_holder = patch_claude_llm([_END_TURN])
    project = project_ctx["project"]
    from_dt = project_ctx["from_dt"]
    to_dt = project_ctx["to_dt"]

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

    assert len(llm_holder["llm"].calls) == 1
    assert "Compose SitRep narrative" in llm_holder["llm"].calls[0]["messages"][0]["content"]


# ---------------------------------------------------------------------------
# 4. SitRep result is persisted and ready to display
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_sitrep_persisted_with_correct_content(project_ctx, patch_claude_llm):
    """A SitRep row is created with the correct fields and linked to the plan."""
    patch_claude_llm([_END_TURN])
    project = project_ctx["project"]
    from_dt = project_ctx["from_dt"]
    to_dt = project_ctx["to_dt"]

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
    assert sitrep.fragos_applied.count() == 2


# ---------------------------------------------------------------------------
# 5. Variables pipeline: assessment steps, LLM calls, datapoints, snapshot
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_plan_with_variables_has_correct_step_count(project_ctx_with_vars, patch_claude_llm):
    """Plan for a project with 2 variables has 4 data + 2 var + 1 narrative = 7 steps."""
    var_response = LLMResponse(
        content='{"value": "12", "color": "green"}',
        stop_reason="end_turn",
        usage={},
        tool_calls=[],
        model="test-model",
    )
    patch_claude_llm([var_response, var_response, _END_TURN])
    project = project_ctx_with_vars["project"]
    from_dt = project_ctx_with_vars["from_dt"]
    to_dt = project_ctx_with_vars["to_dt"]

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
def test_variables_pipeline_full_e2e(project_ctx_with_vars, patch_claude_llm):
    """Full pipeline: generate_sitrep_for_project → variable steps executed → datapoints persisted."""
    from sitrep.models import VariableDatapoint

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
    llm_holder = patch_claude_llm([tp_response, ct_response, _END_TURN])
    project = project_ctx_with_vars["project"]
    from_dt = project_ctx_with_vars["from_dt"]
    to_dt = project_ctx_with_vars["to_dt"]

    plan_id = generate_sitrep_for_project(
        project_id=project.pk,
        from_dt=from_dt.isoformat(),
        to_dt=to_dt.isoformat(),
        trigger="manual",
    )

    plan = ExecutionPlan.objects.get(plan_id=plan_id)
    assert plan.status == "completed"
    assert plan.steps.filter(status="completed").count() == 7

    assert len(llm_holder["llm"].calls) == 3
    assert "Throughput" in llm_holder["llm"].calls[0]["messages"][0]["content"]
    assert "Cycle Time" in llm_holder["llm"].calls[1]["messages"][0]["content"]

    sitrep = SitRep.objects.filter(project=project).first()
    assert sitrep is not None
    assert sitrep.headline == _NARRATIVE["headline"]

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

    assert len(sitrep.variables_snapshot) == 2
    snap = {v["variable_name"]: v for v in sitrep.variables_snapshot}
    assert snap["Throughput"]["value"] == "15"
    assert snap["Throughput"]["color"] == "green"
    assert snap["Throughput"]["abbrev"] == "Tp"
    assert snap["Cycle Time"]["value"] == "3.2"
    assert snap["Cycle Time"]["color"] == "green"


@pytest.mark.django_db
def test_sitrep_idempotent_on_duplicate_request(project_ctx, patch_claude_llm):
    """A second automatic request for the same to_dt does not create a duplicate SitRep."""
    patch_claude_llm([_END_TURN])
    project = project_ctx["project"]
    from_dt = project_ctx["from_dt"]
    to_dt = project_ctx["to_dt"]

    plan_id_1 = generate_sitrep_for_project(
        project_id=project.pk,
        from_dt=from_dt.isoformat(),
        to_dt=to_dt.isoformat(),
        trigger="automatic",
    )
    plan_id_2 = generate_sitrep_for_project(
        project_id=project.pk,
        from_dt=from_dt.isoformat(),
        to_dt=to_dt.isoformat(),
        trigger="automatic",
    )

    assert SitRep.objects.filter(project=project).count() == 1, "only one SitRep must exist"
    assert plan_id_1 == plan_id_2, "idempotent call must return the same plan_id"
