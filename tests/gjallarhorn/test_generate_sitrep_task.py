"""generate_sitrep_for_project task tests — GEN-01–05."""

import json
from contextlib import contextmanager
from unittest.mock import MagicMock, patch

import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone

from gjallarhorn.agent.agent import GjallarhornAgent
from gjallarhorn.llm.base import LLMResponse
from gjallarhorn.models import ExecutionPlan
from gjallarhorn.tasks.sitrep_tasks import generate_sitrep_for_project
from ingestion.models import Increment, Project
from playbooks.models import Playbook, PlaybookVersion
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


def _make_agent(scripted_llm_factory, n_steps=5):
    llm = scripted_llm_factory([_END_TURN] * n_steps)
    tool_executor = MagicMock()
    tool_executor.execute.return_value = {"success": True, "result": None, "error": None}
    return GjallarhornAgent(llm=llm, tool_executor=tool_executor)


@contextmanager
def _agent_patches(agent):
    with patch("gjallarhorn.tasks.plan_tasks._build_agent_for_plan", return_value=agent):
        yield


@pytest.fixture
def project_with_playbook(db):
    user = User.objects.create_user(email="gen-test@example.com", password="test")
    project = Project.objects.create(name="atlas-backend", slug="atlas-backend", imported_by=user)
    pb = Playbook.objects.create(slug="default-pb", name="Default PB")
    PlaybookVersion.objects.create(playbook=pb, version_number=1, workflow_md="workflow")
    project.assigned_playbook = pb
    project.save()
    return project, user


@pytest.mark.django_db
class TestGenerateSitRepTask:
    def test_generate_from_dt_no_prior(self, scripted_llm_factory, project_with_playbook):
        project, user = project_with_playbook
        now = timezone.now()
        earliest = now.replace(hour=0, minute=0, second=0, microsecond=0)
        Increment.objects.create(
            project=project,
            kind="commit",
            external_id="sha1",
            occurred_at=earliest,
        )
        agent = _make_agent(scripted_llm_factory)
        with _agent_patches(agent):
            plan_id = generate_sitrep_for_project(
                project_id=project.pk,
                from_dt=earliest.isoformat(),
                to_dt=now.isoformat(),
                trigger="automatic",
            )
        assert plan_id is not None
        plan = ExecutionPlan.objects.get(plan_id=plan_id)
        assert abs((plan.sitrep_from_dt - earliest).total_seconds()) < 2

    def test_generate_from_dt_prior_exists(self, scripted_llm_factory, project_with_playbook):
        project, user = project_with_playbook
        now = timezone.now()
        prior_to_dt = now.replace(hour=9, minute=0, second=0, microsecond=0)
        to_dt = now.replace(hour=13, minute=15, second=0, microsecond=0)

        agent = _make_agent(scripted_llm_factory)
        with _agent_patches(agent):
            plan_id = generate_sitrep_for_project(
                project_id=project.pk,
                from_dt=prior_to_dt.isoformat(),
                to_dt=to_dt.isoformat(),
                trigger="automatic",
            )
        plan = ExecutionPlan.objects.get(plan_id=plan_id)
        assert abs((plan.sitrep_from_dt - prior_to_dt).total_seconds()) < 2

    def test_generate_idempotency(self, scripted_llm_factory, project_with_playbook):
        project, user = project_with_playbook
        now = timezone.now()
        from_dt = now.replace(hour=9, minute=0, second=0, microsecond=0)
        to_dt = now.replace(hour=13, minute=0, second=0, microsecond=0)

        agent = _make_agent(scripted_llm_factory)
        with _agent_patches(agent):
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

        assert SitRep.objects.filter(project=project, to_dt=to_dt).count() == 1
        assert str(plan_id_1) == str(plan_id_2)

    def test_generate_no_playbook(self, db):
        user = User.objects.create_user(email="nopb@example.com", password="test")
        project = Project.objects.create(name="no-pb", slug="no-pb", imported_by=user)
        now = timezone.now()
        result = generate_sitrep_for_project(
            project_id=project.pk,
            from_dt=now.replace(hour=9).isoformat(),
            to_dt=now.replace(hour=13).isoformat(),
            trigger="automatic",
        )
        assert result is None
        assert ExecutionPlan.objects.filter(conversation__project=project).count() == 0

    def test_generate_manual_trigger(self, scripted_llm_factory, project_with_playbook):
        project, user = project_with_playbook
        now = timezone.now()
        from_dt = now.replace(hour=8, minute=0, second=0, microsecond=0)
        to_dt_auto = now.replace(hour=14, minute=0, second=0, microsecond=0)
        to_dt_manual = now.replace(hour=16, minute=0, second=0, microsecond=0)

        agent_first = _make_agent(scripted_llm_factory)
        with _agent_patches(agent_first):
            plan_id_auto = generate_sitrep_for_project(
                project_id=project.pk,
                from_dt=from_dt.isoformat(),
                to_dt=to_dt_auto.isoformat(),
                trigger="automatic",
            )

        repeat = generate_sitrep_for_project(
            project_id=project.pk,
            from_dt=from_dt.isoformat(),
            to_dt=to_dt_auto.isoformat(),
            trigger="automatic",
        )
        assert repeat == plan_id_auto

        agent_manual = _make_agent(scripted_llm_factory)
        with _agent_patches(agent_manual):
            plan_id_manual = generate_sitrep_for_project(
                project_id=project.pk,
                from_dt=from_dt.isoformat(),
                to_dt=to_dt_manual.isoformat(),
                trigger="manual",
            )

        assert plan_id_manual is not None
        assert plan_id_manual != plan_id_auto
        assert SitRep.objects.filter(project=project).count() == 2
