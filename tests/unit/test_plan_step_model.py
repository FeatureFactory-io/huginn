"""Unit tests for PlanStep model."""

import pytest

from gjallarhorn.models import Conversation, ExecutionPlan, PlanStep
from tests.factories import ProjectFactory, UserFactory


@pytest.mark.django_db
def test_is_variable_assessment_defaults_false(settings):
    """is_variable_assessment should default to False."""
    settings.ANTHROPIC_API_KEY = "test-key"

    user = UserFactory()
    project = ProjectFactory()
    conversation = Conversation.objects.create(
        user=user,
        project=project,
        conversation_type="sitrep",
    )
    plan = ExecutionPlan.objects.create(
        conversation=conversation,
        goal="Test goal",
    )

    step = PlanStep.objects.create(
        plan=plan,
        order=1,
        action="Test action",
        reasoning_why_needed="Test reasoning",
        expected_outcome="Test outcome",
    )

    assert step.is_variable_assessment is False


@pytest.mark.django_db
def test_step_type_exclusivity(settings):
    """A step should not have both is_planning=True and is_variable_assessment=True."""
    settings.ANTHROPIC_API_KEY = "test-key"

    user = UserFactory()
    project = ProjectFactory()
    conversation = Conversation.objects.create(
        user=user,
        project=project,
        conversation_type="sitrep",
    )
    plan = ExecutionPlan.objects.create(
        conversation=conversation,
        goal="Test goal",
    )

    planning_step = PlanStep.objects.create(
        plan=plan,
        order=1,
        action="Planning action",
        reasoning_why_needed="Planning reasoning",
        expected_outcome="Planning outcome",
        is_planning=True,
        is_variable_assessment=False,
    )
    assert planning_step.is_planning is True
    assert planning_step.is_variable_assessment is False

    variable_step = PlanStep.objects.create(
        plan=plan,
        order=2,
        action="Variable assessment action",
        reasoning_why_needed="Variable reasoning",
        expected_outcome="Variable outcome",
        is_planning=False,
        is_variable_assessment=True,
    )
    assert variable_step.is_planning is False
    assert variable_step.is_variable_assessment is True
