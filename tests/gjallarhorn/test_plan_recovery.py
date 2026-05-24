"""recover_orphaned_plans task — RED tests for orphan recovery — T-OR."""

from unittest.mock import patch

import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone

from gjallarhorn.models import Conversation, ExecutionPlan, PlanStep
from ingestion.models import Project

User = get_user_model()


def _make_plan(db, slug, status="pending", steps=1):
    user = User.objects.create_user(email=f"{slug}@example.com", password="x")
    project = Project.objects.create(name=slug, slug=slug)
    conv = Conversation.objects.create(user=user, project=project, conversation_type="sitrep_generation")
    plan = ExecutionPlan.objects.create(conversation=conv, goal="test", progress_total=steps, status=status)
    for i in range(1, steps + 1):
        PlanStep.objects.create(plan=plan, order=i, action=f"Step {i}", reasoning_why_needed="r", expected_outcome="o")
    return plan


def _age_plan(plan, seconds):
    """Back-date plan.created_at to simulate it being old."""
    old_ts = timezone.now() - timezone.timedelta(seconds=seconds)
    ExecutionPlan.objects.filter(plan_id=plan.plan_id).update(created_at=old_ts)
    plan.refresh_from_db()


@pytest.mark.django_db
class TestRecoverOrphanedPlans:
    def test_pending_plan_beyond_threshold_requeued(self, settings):
        """A pending plan older than PLAN_ORPHAN_PENDING_SECONDS is re-dispatched."""
        from gjallarhorn.tasks.recovery_tasks import recover_orphaned_plans

        settings.PLAN_ORPHAN_PENDING_SECONDS = 60
        settings.PLAN_ORPHAN_RUNNING_SECONDS = 3600

        plan = _make_plan(None, "orphan-pending", status="pending")
        _age_plan(plan, seconds=120)  # 2× the threshold

        with patch("gjallarhorn.tasks.recovery_tasks.execute_plan") as mock_task:
            result = recover_orphaned_plans()

        mock_task.delay.assert_called_once_with(str(plan.plan_id))
        assert result["re_dispatched"] >= 1

    def test_running_plan_beyond_threshold_reset_and_requeued(self, settings):
        """A running plan older than PLAN_ORPHAN_RUNNING_SECONDS is reset to pending and re-dispatched."""
        from gjallarhorn.tasks.recovery_tasks import recover_orphaned_plans

        settings.PLAN_ORPHAN_PENDING_SECONDS = 3600
        settings.PLAN_ORPHAN_RUNNING_SECONDS = 60

        plan = _make_plan(None, "orphan-running", status="running")
        _age_plan(plan, seconds=120)

        with patch("gjallarhorn.tasks.recovery_tasks.execute_plan") as mock_task:
            recover_orphaned_plans()

        plan.refresh_from_db()
        assert plan.status == "pending"
        mock_task.delay.assert_called_once_with(str(plan.plan_id))

    def test_fresh_pending_plan_not_touched(self, settings):
        """A plan just created (within threshold) is not re-dispatched."""
        from gjallarhorn.tasks.recovery_tasks import recover_orphaned_plans

        settings.PLAN_ORPHAN_PENDING_SECONDS = 300
        settings.PLAN_ORPHAN_RUNNING_SECONDS = 1800

        plan = _make_plan(None, "fresh-pending", status="pending")
        # do NOT age — it's brand new

        with patch("gjallarhorn.tasks.recovery_tasks.execute_plan") as mock_task:
            result = recover_orphaned_plans()

        mock_task.delay.assert_not_called()
        plan.refresh_from_db()
        assert plan.status == "pending"
        assert result["re_dispatched"] == 0

    def test_terminal_plans_not_touched(self, settings):
        """Completed and failed plans are never re-dispatched."""
        from gjallarhorn.tasks.recovery_tasks import recover_orphaned_plans

        settings.PLAN_ORPHAN_PENDING_SECONDS = 1
        settings.PLAN_ORPHAN_RUNNING_SECONDS = 1

        completed = _make_plan(None, "terminal-completed", status="completed")
        failed = _make_plan(None, "terminal-failed", status="failed")
        _age_plan(completed, seconds=9999)
        _age_plan(failed, seconds=9999)

        with patch("gjallarhorn.tasks.recovery_tasks.execute_plan") as mock_task:
            result = recover_orphaned_plans()

        mock_task.delay.assert_not_called()
        assert result["re_dispatched"] == 0

    def test_recovery_returns_counts(self, settings):
        """Return dict includes re_dispatched count covering both pending and running orphans."""
        from gjallarhorn.tasks.recovery_tasks import recover_orphaned_plans

        settings.PLAN_ORPHAN_PENDING_SECONDS = 60
        settings.PLAN_ORPHAN_RUNNING_SECONDS = 60

        p1 = _make_plan(None, "count-pending-1", status="pending")
        p2 = _make_plan(None, "count-running-1", status="running")
        _age_plan(p1, seconds=120)
        _age_plan(p2, seconds=120)

        with patch("gjallarhorn.tasks.recovery_tasks.execute_plan") as mock_task:
            result = recover_orphaned_plans()

        assert result["re_dispatched"] == 2
        assert mock_task.delay.call_count == 2
