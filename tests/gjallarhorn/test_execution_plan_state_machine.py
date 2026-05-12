"""ExecutionPlan state-machine helpers — T-67."""

import pytest
from django.contrib.auth import get_user_model

from gjallarhorn.models import Conversation, ExecutionPlan, PlanStep
from gjallarhorn.models.execution_plan import InvalidStateTransitionError
from ingestion.models import Project

User = get_user_model()


@pytest.fixture
def plan(db):
    user = User.objects.create_user(email="sm-test@example.com", password="test")
    project = Project.objects.create(name="sm-proj", slug="sm-proj")
    conv = Conversation.objects.create(user=user, project=project, conversation_type="sitrep_generation")
    return ExecutionPlan.objects.create(conversation=conv, goal="test goal", progress_total=3)


def add_step(plan, order, status="pending"):
    return PlanStep.objects.create(
        plan=plan,
        order=order,
        action=f"Step {order}",
        reasoning_why_needed="reason",
        expected_outcome="outcome",
        status=status,
    )


@pytest.mark.django_db
class TestStateMachine:
    def test_mark_started_pending(self, plan):
        plan.mark_started()
        plan.refresh_from_db()
        assert plan.status == "running"

    def test_mark_started_waiting_retry(self, plan):
        plan.status = "waiting_retry"
        plan.save()
        plan.mark_started()
        plan.refresh_from_db()
        assert plan.status == "running"

    def test_mark_started_completed_raises(self, plan):
        plan.status = "completed"
        plan.save()
        with pytest.raises(InvalidStateTransitionError):
            plan.mark_started()

    def test_mark_completed(self, plan):
        plan.mark_started()
        plan.mark_completed()
        plan.refresh_from_db()
        assert plan.status == "completed"

    def test_mark_failed_stores_error(self, plan):
        exc = ValueError("something broke")
        plan.mark_failed(exc)
        plan.refresh_from_db()
        assert plan.status == "failed"
        assert "something broke" in plan.last_error
        assert plan.last_error_type == "ValueError"

    def test_mark_paused_increments_retry_count(self, plan):
        exc = TimeoutError("timeout")
        plan.mark_paused_for_retry(exc)
        plan.refresh_from_db()
        assert plan.status == "waiting_retry"
        assert plan.retry_count == 1

    def test_mark_paused_at_max_retries_marks_failed(self, plan):
        plan.retry_count = plan.max_retries
        plan.save()
        plan.mark_paused_for_retry(TimeoutError("timeout"))
        plan.refresh_from_db()
        assert plan.status == "failed"

    def test_get_next_pending_step_skips_completed(self, plan):
        add_step(plan, 1, status="completed")
        step2 = add_step(plan, 2, status="pending")
        add_step(plan, 3, status="pending")
        assert plan.get_next_pending_step() == step2

    def test_get_next_pending_step_returns_none_when_all_done(self, plan):
        add_step(plan, 1, status="completed")
        add_step(plan, 2, status="completed")
        assert plan.get_next_pending_step() is None

    def test_update_progress_persists(self, plan):
        plan.update_progress(3, "halfway")
        plan.refresh_from_db()
        assert plan.progress_current == 3
        assert plan.progress_message == "halfway"
