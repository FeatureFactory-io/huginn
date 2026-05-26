"""execute_plan must not swallow SitRep persist failures."""

import json
from unittest.mock import MagicMock, patch

import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone

from gjallarhorn.agent.agent import GjallarhornAgent
from gjallarhorn.llm.base import LLMResponse
from gjallarhorn.models import Conversation, ExecutionPlan, PlanStep
from gjallarhorn.tasks.plan_tasks import execute_plan
from ingestion.models import Project

User = get_user_model()

_NARRATIVE_JSON = json.dumps(
    {
        "headline": "GREEN — ok",
        "situation_assessment": "All good.",
        "notable_activity": [],
    }
)
_END_TURN = LLMResponse(content=_NARRATIVE_JSON, stop_reason="end_turn", usage={}, tool_calls=[], model="test")


@pytest.fixture
def sitrep_plan(db):
    user = User.objects.create_user(email="persist-fail@example.com", password="test")
    project = Project.objects.create(name="pf-proj", slug="pf-proj", imported_by=user)
    now = timezone.now()
    conv = Conversation.objects.create(user=user, project=project, conversation_type="sitrep_generation")
    plan = ExecutionPlan.objects.create(
        conversation=conv,
        goal="generate sitrep",
        progress_total=1,
        sitrep_from_dt=now - timezone.timedelta(hours=8),
        sitrep_to_dt=now,
        sitrep_trigger="manual",
    )
    PlanStep.objects.create(
        plan=plan,
        order=1,
        action="Compose SitRep narrative",
        reasoning_why_needed="r",
        expected_outcome="o",
        status="pending",
        is_planning=True,
    )
    return plan


@pytest.mark.django_db
def test_execute_plan_marks_failed_when_sitrep_persist_raises(sitrep_plan):
    """Persist errors propagate: plan is failed, not left silently completed."""
    plan = sitrep_plan
    llm = MagicMock()
    llm.generate_with_tools.return_value = _END_TURN
    agent = GjallarhornAgent(llm=llm, tool_executor=MagicMock())

    with patch("gjallarhorn.tasks.plan_tasks._build_agent_for_plan", return_value=agent):
        with patch(
            "gjallarhorn.services.sitrep_service._persist_sitrep_from_plan",
            side_effect=RuntimeError("persist boom"),
        ):
            with pytest.raises(RuntimeError, match="persist boom"):
                execute_plan.delay(str(plan.plan_id))

    plan.refresh_from_db()
    assert plan.status == "failed"
    assert "persist boom" in plan.last_error
