"""ExecutionPlan, PlanStep, Conversation, Message model tests — T-60."""

import pytest
from django.contrib.auth import get_user_model
from django.db import IntegrityError

from gjallarhorn.models import Conversation, ExecutionPlan, Message, PlanStep
from ingestion.models import Project

User = get_user_model()


@pytest.mark.django_db
class TestExecutionPlanModel:
    def test_plan_step_order_unique(self):
        """Duplicate (plan, order) raises IntegrityError."""
        user = User.objects.create_user(email="test@example.com", password="testpass")
        project = Project.objects.create(name="test-proj", slug="test-proj")
        conv = Conversation.objects.create(
            user=user,
            project=project,
            agent_identity="gjallarhorn",
            conversation_type="sitrep_generation",
        )
        plan = ExecutionPlan.objects.create(conversation=conv, goal="Test goal")

        PlanStep.objects.create(
            plan=plan,
            order=1,
            action="Step 1",
            reasoning_why_needed="Test",
            expected_outcome="Test",
            status="pending",
        )

        with pytest.raises(IntegrityError):
            PlanStep.objects.create(
                plan=plan,
                order=1,
                action="Duplicate order",
                reasoning_why_needed="Test",
                expected_outcome="Test",
                status="pending",
            )

    def test_plan_step_ordering_by_order(self):
        """plan.steps.all() returns steps in order ascending."""
        user = User.objects.create_user(email="test@example.com", password="testpass")
        project = Project.objects.create(name="test-proj", slug="test-proj")
        conv = Conversation.objects.create(
            user=user,
            project=project,
            agent_identity="gjallarhorn",
            conversation_type="sitrep_generation",
        )
        plan = ExecutionPlan.objects.create(conversation=conv, goal="Test goal")

        step3 = PlanStep.objects.create(
            plan=plan,
            order=3,
            action="Step 3",
            reasoning_why_needed="Test",
            expected_outcome="Test",
            status="pending",
        )
        step1 = PlanStep.objects.create(
            plan=plan,
            order=1,
            action="Step 1",
            reasoning_why_needed="Test",
            expected_outcome="Test",
            status="pending",
        )
        step2 = PlanStep.objects.create(
            plan=plan,
            order=2,
            action="Step 2",
            reasoning_why_needed="Test",
            expected_outcome="Test",
            status="pending",
        )

        steps = list(plan.steps.all())
        assert steps == [step1, step2, step3]

    def test_plan_default_status_pending(self):
        """New ExecutionPlan defaults to status='pending'."""
        user = User.objects.create_user(email="test@example.com", password="testpass")
        project = Project.objects.create(name="test-proj", slug="test-proj")
        conv = Conversation.objects.create(
            user=user,
            project=project,
            agent_identity="gjallarhorn",
            conversation_type="sitrep_generation",
        )
        plan = ExecutionPlan.objects.create(conversation=conv, goal="Test goal")

        assert plan.status == "pending"

    def test_conversation_unique_per_user_project(self):
        """Duplicate (user, project) Conversation raises IntegrityError."""
        user = User.objects.create_user(email="test@example.com", password="testpass")
        project = Project.objects.create(name="test-proj", slug="test-proj")

        Conversation.objects.create(
            user=user,
            project=project,
            agent_identity="gjallarhorn",
            conversation_type="ad_hoc",
        )

        with pytest.raises(IntegrityError):
            Conversation.objects.create(
                user=user,
                project=project,
                agent_identity="gjallarhorn",
                conversation_type="sitrep_generation",
            )

    def test_message_ordering(self):
        """messages ordered by created_at ASC."""
        user = User.objects.create_user(email="test@example.com", password="testpass")
        project = Project.objects.create(name="test-proj", slug="test-proj")
        conv = Conversation.objects.create(
            user=user,
            project=project,
            agent_identity="gjallarhorn",
            conversation_type="ad_hoc",
        )

        msg1 = Message.objects.create(conversation=conv, role="user", content="First")
        msg2 = Message.objects.create(conversation=conv, role="assistant", content="Second")
        msg3 = Message.objects.create(conversation=conv, role="user", content="Third")

        messages = list(conv.messages.all())
        assert messages == [msg1, msg2, msg3]
