"""sync_project_completed signal and full pipeline — GEN-06–08."""

import json
from unittest.mock import MagicMock, patch

import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone

from gjallarhorn.agent.agent import GjallarhornAgent
from gjallarhorn.llm.base import LLMResponse
from gjallarhorn.tasks.sitrep_tasks import on_sync_project_completed
from ingestion.models import Increment, Project
from ingestion.signals import sync_project_completed
from roe.models import RulesOfEngagement, RulesOfEngagementVersion
from sitrep.models import SitRep

User = get_user_model()

_NARRATIVE_JSON = json.dumps(
    {
        "headline": "GREEN — all good",
        "situation_assessment": "12 commits, healthy.",
        "notable_activity": [],
    }
)
_END_TURN = LLMResponse(content=_NARRATIVE_JSON, stop_reason="end_turn", usage={}, tool_calls=[], model="test")


@pytest.fixture
def project_with_commit(db):
    user = User.objects.create_user(email="sig-test@example.com", password="test")
    project = Project.objects.create(name="atlas-backend", slug="atlas-backend", imported_by=user)
    roe = RulesOfEngagement.objects.create(slug="default-roe", name="Default RoE")
    RulesOfEngagementVersion.objects.create(roe=roe, version_number=1, workflow_md="workflow")
    project.assigned_roe = roe
    project.save()
    now = timezone.now()
    Increment.objects.create(project=project, kind="commit", external_id="sha1", occurred_at=now)
    return project, user, now


@pytest.mark.django_db
class TestSitRepSignal:
    def test_signal_auto_trigger(self, scripted_llm_factory, project_with_commit):
        project, user, now = project_with_commit
        llm = scripted_llm_factory([_END_TURN] * 5)
        tool_executor = MagicMock()
        tool_executor.execute.return_value = {"success": True, "result": None, "error": None}
        agent = GjallarhornAgent(llm=llm, tool_executor=tool_executor)

        with patch("gjallarhorn.tasks.plan_tasks._build_agent_for_plan", return_value=agent):
            sync_project_completed.send(sender=None, project=project, to_dt=now)

        assert SitRep.objects.filter(project=project).count() == 1

    def test_signal_receiver_no_propagate(self, db):
        project = Project.objects.create(name="err-proj", slug="err-proj")
        now = timezone.now()
        with patch(
            "gjallarhorn.tasks.sitrep_tasks.generate_sitrep_for_project.delay",
            side_effect=RuntimeError("boom"),
        ):
            on_sync_project_completed(sender=None, project=project, to_dt=now)

    def test_flow_a_full_pipeline(self, scripted_llm_factory, project_with_commit):
        project, user, now = project_with_commit
        llm = scripted_llm_factory([_END_TURN] * 5)
        tool_executor = MagicMock()
        tool_executor.execute.return_value = {"success": True, "result": None, "error": None}
        agent = GjallarhornAgent(llm=llm, tool_executor=tool_executor)

        with patch("gjallarhorn.tasks.plan_tasks._build_agent_for_plan", return_value=agent):
            from ingestion.services.sync_engine import SyncEngine

            engine = SyncEngine()
            engine.sync_project_completed_send = lambda **kw: sync_project_completed.send(
                sender=SyncEngine, project=project, to_dt=now
            )
            engine.sync_project_completed_send()

        sitrep = SitRep.objects.filter(project=project).first()
        assert sitrep is not None
        assert sitrep.source_plan.steps.filter(status="completed").count() == 8
