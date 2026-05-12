"""_persist_sitrep_from_plan tests — SREP-01–04."""

import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone

from gjallarhorn.models import Conversation, ExecutionPlan, PlanStep
from gjallarhorn.services.sitrep_service import _persist_sitrep_from_plan
from ingestion.models import Project
from sitrep.models import Frago, SitRep

User = get_user_model()

_FINAL_RESULT = {
    "headline": "GREEN — Sprint on track",
    "situation_assessment": "12 commits this week. All green.",
    "notable_activity": ["Maria: strong throughput"],
}


@pytest.fixture
def plan_with_final_step(db):
    now = timezone.now()
    user = User.objects.create_user(email="srep-test@example.com", password="test")
    project = Project.objects.create(name="atlas-backend", slug="atlas-backend", imported_by=user)
    conv = Conversation.objects.create(user=user, project=project, conversation_type="sitrep_generation")
    plan = ExecutionPlan.objects.create(
        conversation=conv,
        goal="generate sitrep",
        progress_total=5,
        status="completed",
        sitrep_from_dt=now - timezone.timedelta(days=7),
        sitrep_to_dt=now,
        sitrep_trigger="automatic",
    )
    for i in range(1, 5):
        PlanStep.objects.create(
            plan=plan,
            order=i,
            action=f"Step {i}",
            reasoning_why_needed="r",
            expected_outcome="o",
            status="completed",
            result={"content": f"Result {i}"},
        )
    PlanStep.objects.create(
        plan=plan,
        order=5,
        action="Compose narrative",
        reasoning_why_needed="r",
        expected_outcome="o",
        status="completed",
        result=_FINAL_RESULT,
    )
    return plan


@pytest.mark.django_db
class TestPersistSitRepFromPlan:
    def test_persist_sitrep_from_plan(self, plan_with_final_step):
        plan = plan_with_final_step
        sitrep = _persist_sitrep_from_plan(plan)
        assert SitRep.objects.filter(source_plan=plan).count() == 1
        assert sitrep.headline == "GREEN — Sprint on track"
        assert sitrep.situation_assessment == "12 commits this week. All green."

    def test_persist_sitrep_fragos_m2m(self, plan_with_final_step):
        plan = plan_with_final_step
        project = plan.conversation.project
        enabled_frago = Frago.objects.create(project=project, title="Sprint 47 bug belay", enabled=True)
        disabled_frago = Frago.objects.create(project=project, title="Old waiver", enabled=False)
        sitrep = _persist_sitrep_from_plan(plan)
        assert enabled_frago in sitrep.fragos_applied.all()
        assert disabled_frago not in sitrep.fragos_applied.all()

    def test_persist_sitrep_notable_activity(self, plan_with_final_step):
        plan = plan_with_final_step
        sitrep = _persist_sitrep_from_plan(plan)
        assert sitrep.notable_activity == ["Maria: strong throughput"]

    def test_persist_sitrep_bad_step_result(self, plan_with_final_step):
        plan = plan_with_final_step
        last_step = plan.steps.order_by("-order").first()
        last_step.result = {"content": "no headline here"}
        last_step.save()
        with pytest.raises(ValueError, match="headline"):
            _persist_sitrep_from_plan(plan)
        plan.refresh_from_db()
        assert plan.status == "failed"
