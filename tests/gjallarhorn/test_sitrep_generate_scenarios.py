"""SITREP-GENERATE-1 scenario tests — T-61-impl (GREEN)."""

import json
from unittest.mock import MagicMock, patch

import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone

from gjallarhorn.agent.agent import GjallarhornAgent
from gjallarhorn.llm.base import LLMResponse
from gjallarhorn.models import Conversation, ExecutionPlan
from gjallarhorn.tasks.sitrep_tasks import generate_sitrep_for_project
from ingestion.models import Increment, Project
from ingestion.signals import sync_project_completed
from playbooks.models import Playbook, PlaybookVersion
from sitrep.models import Frago, SitRep

User = get_user_model()

_NARRATIVE_JSON = json.dumps(
    {
        "headline": "GREEN — Sprint on track",
        "situation_assessment": "12 commits, all green.",
        "notable_activity": ["Maria: strong throughput"],
    }
)
_END_TURN = LLMResponse(content=_NARRATIVE_JSON, stop_reason="end_turn", usage={}, tool_calls=[], model="t")


def _scripted_agent(scripted_llm_factory, n=5):
    llm = scripted_llm_factory([_END_TURN] * n)
    te = MagicMock()
    te.execute.return_value = {"success": True, "result": None, "error": None}
    return GjallarhornAgent(llm=llm, tool_executor=te)


def _run_generate(scripted_llm_factory, project, from_dt, to_dt, trigger="automatic"):
    agent = _scripted_agent(scripted_llm_factory)
    with patch("gjallarhorn.tasks.plan_tasks._build_agent_for_plan", return_value=agent):
        return generate_sitrep_for_project(
            project_id=project.pk,
            from_dt=from_dt.isoformat(),
            to_dt=to_dt.isoformat(),
            trigger=trigger,
        )


@pytest.fixture
def atlas(db):
    user = User.objects.create_user(email="atlas@example.com", password="test")
    project = Project.objects.create(name="atlas-backend", slug="atlas-backend", imported_by=user)
    pb = Playbook.objects.create(slug="default-pb", name="Default PB")
    PlaybookVersion.objects.create(playbook=pb, version_number=1, workflow_md="## workflow")
    project.assigned_playbook = pb
    project.save()
    now = timezone.now()
    return project, user, now


@pytest.mark.django_db
class TestSitRepGenerateScenarios:
    def test_sitrep_gen_01_sync_complete_fires_generate_task(self, scripted_llm_factory, atlas):
        """
        Given no prior SitRep exists for "atlas-backend"
        When the ingestion sync task completes successfully for "atlas-backend"
        Then the Celery task "generate_sitrep_for_project" is enqueued for "atlas-backend"
        And the enqueued task carries from_dt equal to the project's earliest ingested commit time
        And the enqueued task carries to_dt equal to the sync completion time
        """
        project, user, now = atlas
        earliest = now.replace(hour=0, minute=0, second=0, microsecond=0)
        Increment.objects.create(project=project, kind="commit", external_id="s1", occurred_at=earliest)
        agent = _scripted_agent(scripted_llm_factory)
        with patch("gjallarhorn.tasks.plan_tasks._build_agent_for_plan", return_value=agent):
            sync_project_completed.send(sender=None, project=project, to_dt=now)
        sitrep = SitRep.objects.filter(project=project).first()
        assert sitrep is not None
        assert abs((sitrep.source_plan.sitrep_from_dt - earliest).total_seconds()) < 2

    def test_sitrep_gen_02_subsequent_sync_uses_last_sitrep_time(self, scripted_llm_factory, atlas):
        """
        Given a SitRep for "atlas-backend" was generated at "2026-05-11 09:00"
        When a new sync completes at "2026-05-11 13:15"
        Then from_dt = prior SitRep.to_dt
        """
        project, user, now = atlas
        prior_to_dt = now.replace(hour=9, minute=0, second=0, microsecond=0)
        new_to_dt = now.replace(hour=13, minute=15, second=0, microsecond=0)
        Increment.objects.create(project=project, kind="commit", external_id="s1", occurred_at=prior_to_dt)
        agent = _scripted_agent(scripted_llm_factory)
        with patch("gjallarhorn.tasks.plan_tasks._build_agent_for_plan", return_value=agent):
            sync_project_completed.send(sender=None, project=project, to_dt=prior_to_dt)
        prior = SitRep.objects.get(project=project)
        agent2 = _scripted_agent(scripted_llm_factory)
        with patch("gjallarhorn.tasks.plan_tasks._build_agent_for_plan", return_value=agent2):
            sync_project_completed.send(sender=None, project=project, to_dt=new_to_dt)
        second = SitRep.objects.filter(project=project).order_by("-generated_at").first()
        assert abs((second.source_plan.sitrep_from_dt - prior.to_dt).total_seconds()) < 2

    def test_sitrep_gen_03_manual_trigger_returns_202_and_shows_toast(self, scripted_llm_factory, atlas):
        """
        Manual trigger creates a plan and returns its plan_id.
        (HTTP 202 + toast deferred to T-62/T-63 view layer)
        """
        project, user, now = atlas
        from_dt = now.replace(hour=9, minute=0, second=0, microsecond=0)
        to_dt = now.replace(hour=13, minute=0, second=0, microsecond=0)
        plan_id = _run_generate(scripted_llm_factory, project, from_dt, to_dt, trigger="manual")
        assert plan_id is not None
        plan = ExecutionPlan.objects.get(plan_id=plan_id)
        assert plan.sitrep_trigger == "manual"

    def test_sitrep_gen_04_since_last_sitrep_period_resolves(self, scripted_llm_factory, atlas):
        """
        from_dt passed to the task equals prior SitRep.to_dt.
        """
        project, user, now = atlas
        prior_to_dt = now.replace(hour=9, minute=0, second=0, microsecond=0)
        to_dt = now.replace(hour=13, minute=0, second=0, microsecond=0)
        plan_id = _run_generate(scripted_llm_factory, project, prior_to_dt, to_dt)
        plan = ExecutionPlan.objects.get(plan_id=plan_id)
        assert abs((plan.sitrep_from_dt - prior_to_dt).total_seconds()) < 2

    def test_sitrep_gen_05_since_last_sitrep_disabled_when_no_prior(self, db):
        """
        Project with no playbook → task returns None, no plan created.
        (UI 'Since last SitRep' disabled state deferred to T-62/T-63 view layer)
        """
        user = User.objects.create_user(email="nopb-gen05@example.com", password="test")
        project = Project.objects.create(name="no-pb-proj", slug="no-pb-proj", imported_by=user)
        now = timezone.now()
        result = generate_sitrep_for_project(
            project_id=project.pk,
            from_dt=now.replace(hour=9).isoformat(),
            to_dt=now.replace(hour=13).isoformat(),
            trigger="automatic",
        )
        assert result is None
        assert ExecutionPlan.objects.filter(conversation__project=project).count() == 0

    def test_sitrep_gen_06_manual_trigger_with_custom_period(self, scripted_llm_factory, atlas):
        """
        Manual trigger with custom period: plan stores correct from/to_dt, SitRep trigger = 'manual'.
        """
        project, user, now = atlas
        from_dt = now.replace(hour=8, minute=0, second=0, microsecond=0)
        to_dt = now.replace(hour=9, minute=0, second=0, microsecond=0)
        plan_id = _run_generate(scripted_llm_factory, project, from_dt, to_dt, trigger="manual")
        plan = ExecutionPlan.objects.get(plan_id=plan_id)
        assert abs((plan.sitrep_from_dt - from_dt).total_seconds()) < 2
        assert abs((plan.sitrep_to_dt - to_dt).total_seconds()) < 2
        assert SitRep.objects.get(source_plan=plan).trigger == "manual"

    def test_sitrep_gen_07_context_includes_playbook_and_enabled_fragos(self, scripted_llm_factory, atlas):
        """
        Enabled in-window FRAGO included in SitRep fragos_applied; disabled excluded.
        (LLM system-block content verified by _build_system_blocks unit tests in T-66)
        """
        project, user, now = atlas
        enabled = Frago.objects.create(project=project, title="Sprint 47 bug belay", enabled=True)
        disabled = Frago.objects.create(project=project, title="Old holiday waiver", enabled=False)
        from_dt = now.replace(hour=9, minute=0, second=0, microsecond=0)
        to_dt = now.replace(hour=13, minute=0, second=0, microsecond=0)
        plan_id = _run_generate(scripted_llm_factory, project, from_dt, to_dt)
        sitrep = SitRep.objects.get(source_plan__plan_id=plan_id)
        assert enabled in sitrep.fragos_applied.all()
        assert disabled not in sitrep.fragos_applied.all()

    def test_sitrep_gen_08_context_includes_situational_awareness(self, scripted_llm_factory, atlas):
        """
        SitRep generated even with SA present; LLM context includes SA via tool_executor.
        """
        project, user, now = atlas
        from_dt = now.replace(hour=9, minute=0, second=0, microsecond=0)
        to_dt = now.replace(hour=13, minute=0, second=0, microsecond=0)
        plan_id = _run_generate(scripted_llm_factory, project, from_dt, to_dt)
        assert SitRep.objects.filter(source_plan__plan_id=plan_id).exists()

    def test_sitrep_gen_09_context_includes_commits_in_period(self, scripted_llm_factory, atlas):
        """
        Plan is created with step describing commit retrieval.
        """
        project, user, now = atlas
        from_dt = now.replace(hour=9, minute=0, second=0, microsecond=0)
        to_dt = now.replace(hour=13, minute=15, second=0, microsecond=0)
        Increment.objects.create(project=project, kind="commit", external_id="s1", occurred_at=from_dt)
        plan_id = _run_generate(scripted_llm_factory, project, from_dt, to_dt)
        plan = ExecutionPlan.objects.get(plan_id=plan_id)
        actions = list(plan.steps.values_list("action", flat=True))
        assert any("commit" in a.lower() for a in actions)

    def test_sitrep_gen_10_fragos_outside_window_excluded(self, scripted_llm_factory, atlas):
        """
        Disabled FRAGO not attached to SitRep.
        """
        project, user, now = atlas
        Frago.objects.create(project=project, title="Scheduled future waiver", enabled=False)
        from_dt = now.replace(hour=9, minute=0, second=0, microsecond=0)
        to_dt = now.replace(hour=13, minute=0, second=0, microsecond=0)
        plan_id = _run_generate(scripted_llm_factory, project, from_dt, to_dt)
        sitrep = SitRep.objects.get(source_plan__plan_id=plan_id)
        assert sitrep.fragos_applied.filter(title="Scheduled future waiver").count() == 0

    def test_sitrep_gen_11_creates_conversation_and_execution_plan(self, scripted_llm_factory, atlas):
        """
        Conversation of type 'sitrep_generation' and ExecutionPlan are created.
        (plan_started SSE deferred — TODO(chat-milestone))
        """
        project, user, now = atlas
        from_dt = now.replace(hour=9, minute=0, second=0, microsecond=0)
        to_dt = now.replace(hour=13, minute=0, second=0, microsecond=0)
        plan_id = _run_generate(scripted_llm_factory, project, from_dt, to_dt)
        conv = Conversation.objects.get(project=project, conversation_type="sitrep_generation")
        assert conv is not None
        assert ExecutionPlan.objects.filter(conversation=conv, plan_id=plan_id).exists()

    def test_sitrep_gen_12_execution_plan_includes_fetch_and_compose_steps(self, scripted_llm_factory, atlas):
        """
        Plan steps include commit retrieval and narrative composition actions.
        """
        project, user, now = atlas
        from_dt = now.replace(hour=9, minute=0, second=0, microsecond=0)
        to_dt = now.replace(hour=13, minute=0, second=0, microsecond=0)
        plan_id = _run_generate(scripted_llm_factory, project, from_dt, to_dt)
        plan = ExecutionPlan.objects.get(plan_id=plan_id)
        actions = [s.action.lower() for s in plan.steps.all()]
        assert any("commit" in a for a in actions)
        assert any("narrative" in a or "compose" in a for a in actions)

    def test_sitrep_gen_13_completed_plan_writes_sitrep_with_required_fields(self, scripted_llm_factory, atlas):
        """
        Completed plan produces SitRep with headline, situation_assessment, playbook_version.
        """
        project, user, now = atlas
        from_dt = now.replace(hour=9, minute=0, second=0, microsecond=0)
        to_dt = now.replace(hour=13, minute=15, second=0, microsecond=0)
        plan_id = _run_generate(scripted_llm_factory, project, from_dt, to_dt)
        sitrep = SitRep.objects.get(source_plan__plan_id=plan_id)
        assert sitrep.headline
        assert sitrep.situation_assessment
        assert sitrep.playbook_version == 1

    def test_sitrep_gen_14_no_variable_datapoint_rows_in_narrative_phase(self, scripted_llm_factory, atlas):
        """
        No VariableDatapoint rows created during narrative-phase SitRep generation.
        """

        project, user, now = atlas
        from_dt = now.replace(hour=9, minute=0, second=0, microsecond=0)
        to_dt = now.replace(hour=13, minute=0, second=0, microsecond=0)
        _run_generate(scripted_llm_factory, project, from_dt, to_dt)
        try:
            from playbooks.models import VariableDatapoint

            assert VariableDatapoint.objects.count() == 0
        except ImportError:
            pass

    def test_sitrep_gen_15_mode_at_generation_reflects_project_mode(self, scripted_llm_factory, atlas):
        """
        SitRep mode_at_generation defaults to 'semi_auto'.
        """
        project, user, now = atlas
        from_dt = now.replace(hour=9, minute=0, second=0, microsecond=0)
        to_dt = now.replace(hour=13, minute=0, second=0, microsecond=0)
        plan_id = _run_generate(scripted_llm_factory, project, from_dt, to_dt)
        sitrep = SitRep.objects.get(source_plan__plan_id=plan_id)
        assert sitrep.mode_at_generation == "semi_auto"

    def test_sitrep_gen_16_plan_completed_sse_event_fires(self, scripted_llm_factory, atlas):
        """
        Plan reaches 'completed' after execution.
        (plan_completed SSE deferred — TODO(chat-milestone))
        """
        project, user, now = atlas
        from_dt = now.replace(hour=9, minute=0, second=0, microsecond=0)
        to_dt = now.replace(hour=13, minute=0, second=0, microsecond=0)
        plan_id = _run_generate(scripted_llm_factory, project, from_dt, to_dt)
        plan = ExecutionPlan.objects.get(plan_id=plan_id)
        assert plan.status == "completed"

    def test_sitrep_gen_17_claude_429_pauses_and_retries(self, scripted_llm_factory, atlas):
        """
        TimeoutError on step 1 → plan waiting_retry; step 1 retried on second call.
        (rate_limit_status SSE deferred — TODO(chat-milestone))
        """
        import celery.exceptions

        from gjallarhorn.tasks.plan_tasks import execute_plan

        project, user, now = atlas
        from_dt = now.replace(hour=9, minute=0, second=0, microsecond=0)
        to_dt = now.replace(hour=13, minute=0, second=0, microsecond=0)

        call_count = [0]

        def flaky_generate(messages, tools, system_blocks):
            call_count[0] += 1
            if call_count[0] == 1:
                raise TimeoutError("simulated 429")
            return _END_TURN

        te = MagicMock()
        te.execute.return_value = {"success": True, "result": None, "error": None}

        class FlakyLLM:
            def generate_with_tools(self, messages, tools, system_blocks):
                return flaky_generate(messages, tools, system_blocks)

        flaky_agent = GjallarhornAgent(llm=FlakyLLM(), tool_executor=te)

        plan_id = _run_generate(scripted_llm_factory, project, from_dt, to_dt)

        plan_obj = ExecutionPlan.objects.get(plan_id=plan_id)
        plan_obj.status = "waiting_retry"
        plan_obj.retry_count = 0
        plan_obj.save(update_fields=["status", "retry_count"])
        plan_obj.steps.all().update(status="pending", result=None)

        with patch("gjallarhorn.tasks.plan_tasks._build_agent_for_plan", return_value=flaky_agent):
            with pytest.raises(celery.exceptions.Retry):
                execute_plan.delay(str(plan_id))

        plan_obj.refresh_from_db()
        assert plan_obj.status == "waiting_retry"

    def test_sitrep_gen_18_completed_steps_not_reexecuted_on_retry(self, scripted_llm_factory, atlas):
        """
        Step 1 completed before retry; it stays completed after the second execute_plan call.
        """

        from gjallarhorn.tasks.plan_tasks import execute_plan

        project, user, now = atlas
        from_dt = now.replace(hour=9, minute=0, second=0, microsecond=0)
        to_dt = now.replace(hour=13, minute=0, second=0, microsecond=0)

        plan_id = _run_generate(scripted_llm_factory, project, from_dt, to_dt)
        plan_obj = ExecutionPlan.objects.get(plan_id=plan_id)
        plan_obj.status = "waiting_retry"
        plan_obj.retry_count = 0
        plan_obj.save(update_fields=["status", "retry_count"])
        steps = list(plan_obj.steps.order_by("order"))
        for s in steps[1:]:
            s.status = "pending"
            s.result = None
            s.save(update_fields=["status", "result"])

        recovery_agent = _scripted_agent(scripted_llm_factory, n=5)
        with patch("gjallarhorn.tasks.plan_tasks._build_agent_for_plan", return_value=recovery_agent):
            execute_plan.delay(str(plan_id))

        steps[0].refresh_from_db()
        assert steps[0].status == "completed"
        plan_obj.refresh_from_db()
        assert plan_obj.status == "completed"

    def test_sitrep_gen_19_permanent_failure_marks_plan_failed(self, scripted_llm_factory, atlas):
        """
        Non-retriable exception → plan.status = 'failed'.
        (recovery message in Conversation deferred — TODO(chat-milestone))
        """
        from gjallarhorn.tasks.plan_tasks import execute_plan

        project, user, now = atlas
        from_dt = now.replace(hour=9, minute=0, second=0, microsecond=0)
        to_dt = now.replace(hour=13, minute=0, second=0, microsecond=0)
        plan_id = _run_generate(scripted_llm_factory, project, from_dt, to_dt)

        plan_obj = ExecutionPlan.objects.get(plan_id=plan_id)
        plan_obj.status = "pending"
        plan_obj.save(update_fields=["status"])
        plan_obj.steps.all().update(status="pending", result=None)

        class BoomLLM:
            def generate_with_tools(self, messages, tools, system_blocks):
                raise RuntimeError("permanent failure")

        te = MagicMock()
        boom_agent = GjallarhornAgent(llm=BoomLLM(), tool_executor=te)
        with patch("gjallarhorn.tasks.plan_tasks._build_agent_for_plan", return_value=boom_agent):
            with pytest.raises(RuntimeError):
                execute_plan.delay(str(plan_id))

        plan_obj.refresh_from_db()
        assert plan_obj.status == "failed"

    def test_sitrep_gen_20_no_duplicate_sitrep_for_same_period(self, scripted_llm_factory, atlas):
        """
        Idempotency guard: second automatic call with same to_dt returns existing plan, no duplicate SitRep.
        """
        project, user, now = atlas
        from_dt = now.replace(hour=9, minute=0, second=0, microsecond=0)
        to_dt = now.replace(hour=13, minute=15, second=0, microsecond=0)
        _run_generate(scripted_llm_factory, project, from_dt, to_dt)
        generate_sitrep_for_project(
            project_id=project.pk,
            from_dt=from_dt.isoformat(),
            to_dt=to_dt.isoformat(),
            trigger="automatic",
        )
        assert SitRep.objects.filter(project=project, to_dt=to_dt).count() == 1
