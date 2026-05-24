"""execute_plan concurrency & celery_task_id — T-OR."""

import json
from unittest.mock import MagicMock, patch

import pytest
from django.contrib.auth import get_user_model

from gjallarhorn.agent.agent import GjallarhornAgent
from gjallarhorn.llm.base import LLMResponse
from gjallarhorn.models import Conversation, ExecutionPlan, PlanStep
from gjallarhorn.models.execution_plan import InvalidStateTransitionError
from gjallarhorn.tasks.plan_tasks import execute_plan
from ingestion.models import Project
from roe.models import RulesOfEngagement, RulesOfEngagementVersion

User = get_user_model()

_END_TURN = LLMResponse(content="done", stop_reason="end_turn", usage={}, tool_calls=[], model="test")
_NARRATIVE_JSON = json.dumps({"headline": "OK", "situation_assessment": "fine", "notable_activity": []})
_NARRATIVE_TURN = LLMResponse(content=_NARRATIVE_JSON, stop_reason="end_turn", usage={}, tool_calls=[], model="test")


@pytest.fixture
def plan_running(db):
    """A plan whose status has already been set to 'running' by another worker."""
    user = User.objects.create_user(email="conc-test@example.com", password="test")
    project = Project.objects.create(name="conc-proj", slug="conc-proj")
    conv = Conversation.objects.create(user=user, project=project, conversation_type="sitrep_generation")
    plan = ExecutionPlan.objects.create(conversation=conv, goal="test", progress_total=3)
    for i in range(1, 4):
        PlanStep.objects.create(plan=plan, order=i, action=f"Step {i}", reasoning_why_needed="r", expected_outcome="o")
    # Simulate another worker already grabbed this plan
    ExecutionPlan.objects.filter(plan_id=plan.plan_id).update(status="running")
    plan.refresh_from_db()
    return plan


@pytest.fixture
def project_with_roe_for_concurrency(db):
    user = User.objects.create_user(email="tid-test@example.com", password="test")
    project = Project.objects.create(name="tid-proj", slug="tid-proj", imported_by=user)
    roe = RulesOfEngagement.objects.create(slug="tid-roe", name="TID RoE")
    RulesOfEngagementVersion.objects.create(roe=roe, version_number=1, workflow_md="wf")
    project.assigned_roe = roe
    project.save()
    return project, user


@pytest.mark.django_db
class TestExecutePlanConcurrency:
    def test_concurrent_dispatch_only_one_executes(self, scripted_llm_factory, plan_running):
        """Second execute_plan call for a plan already 'running' is a clean no-op."""
        plan = plan_running
        llm = scripted_llm_factory([_END_TURN, _END_TURN, _END_TURN])
        tool_executor = MagicMock()
        tool_executor.execute.return_value = {"success": True, "result": None, "error": None}
        agent = GjallarhornAgent(llm=llm, tool_executor=tool_executor)

        with patch("gjallarhorn.tasks.plan_tasks._build_agent_for_plan", return_value=agent):
            execute_plan.delay(str(plan.plan_id))

        plan.refresh_from_db()
        # Plan should still be "running" — the second dispatch must not have taken over
        assert plan.status == "running"
        # No steps should have been executed by the second dispatch
        assert plan.steps.filter(status="pending").count() == 3
        # LLM was never called (no execution happened)
        assert len(llm.calls) == 0

    def test_mark_started_raises_when_already_running(self, db):
        """mark_started() on a plan already in 'running' state raises InvalidStateTransitionError."""
        user = User.objects.create_user(email="ms-test@example.com", password="test")
        project = Project.objects.create(name="ms-proj", slug="ms-proj")
        conv = Conversation.objects.create(user=user, project=project, conversation_type="sitrep_generation")
        plan = ExecutionPlan.objects.create(conversation=conv, goal="test", progress_total=1)

        plan.mark_started()  # first: pending → running

        with pytest.raises(InvalidStateTransitionError):
            plan.mark_started()  # second: must raise

    def test_celery_task_id_persisted(self, scripted_llm_factory, project_with_roe_for_concurrency):
        """generate_sitrep_for_project stores celery_task_id on the created plan."""
        from django.utils import timezone

        from gjallarhorn.tasks.sitrep_tasks import generate_sitrep_for_project

        project, user = project_with_roe_for_concurrency
        now = timezone.now()
        from_dt = now.replace(hour=8, minute=0, second=0, microsecond=0)
        to_dt = now.replace(hour=14, minute=0, second=0, microsecond=0)

        llm = scripted_llm_factory([_NARRATIVE_TURN] * 5)
        tool_executor = MagicMock()
        tool_executor.execute.return_value = {"success": True, "result": None, "error": None}
        agent = GjallarhornAgent(llm=llm, tool_executor=tool_executor)

        with patch("gjallarhorn.tasks.plan_tasks._build_agent_for_plan", return_value=agent):
            plan_id = generate_sitrep_for_project(
                project_id=project.pk,
                from_dt=from_dt.isoformat(),
                to_dt=to_dt.isoformat(),
                trigger="manual",
            )

        plan = ExecutionPlan.objects.get(plan_id=plan_id)
        assert plan.celery_task_id != "", "celery_task_id must be stored on the plan after dispatch"
