"""Unit tests for _persist_variable_datapoints."""

from unittest.mock import patch

import pytest
from django.utils import timezone

from gjallarhorn.services.sitrep_service import _persist_sitrep_from_plan, _persist_variable_datapoints
from sitrep.models import SitRep, VariableDatapoint
from tests.factories import (
    ProjectFactory,
    RulesOfEngagementFactory,
    RulesOfEngagementVariableFactory,
    RulesOfEngagementVersionFactory,
    SitRepFactory,
    UserFactory,
)


@pytest.mark.django_db
def test_persist_creates_one_datapoint_per_variable():
    """One VariableDatapoint row is created for each variable assessment step."""
    roe = RulesOfEngagementFactory()
    version = RulesOfEngagementVersionFactory(roe=roe)
    RulesOfEngagementVariableFactory(roe_version=version, name="Throughput", abbrev="Tp", y_axis_label="MRs")
    RulesOfEngagementVariableFactory(roe_version=version, name="Cycle Time", abbrev="CT", y_axis_label="days")

    project = ProjectFactory(assigned_roe=roe)
    user = UserFactory()

    from gjallarhorn.models import Conversation, ExecutionPlan, PlanStep

    conversation = Conversation.objects.create(user=user, project=project, conversation_type="sitrep")
    plan = ExecutionPlan.objects.create(conversation=conversation, goal="Test")

    PlanStep.objects.create(
        plan=plan,
        order=5,
        action="Assess Throughput (Tp)",
        reasoning_why_needed="Test",
        expected_outcome="{}",
        is_variable_assessment=True,
        result={"value": "15", "color": "green"},
    )
    PlanStep.objects.create(
        plan=plan,
        order=6,
        action="Assess Cycle Time (CT)",
        reasoning_why_needed="Test",
        expected_outcome="{}",
        is_variable_assessment=True,
        result={"value": "3.2", "color": "orange"},
    )

    now = timezone.now()
    sitrep = SitRepFactory(project=project, from_dt=now, to_dt=now, source_plan=plan)

    _persist_variable_datapoints(sitrep, plan)

    datapoints = VariableDatapoint.objects.filter(sitrep=sitrep)
    assert datapoints.count() == 2


@pytest.mark.django_db
def test_persist_sets_variables_snapshot_on_sitrep():
    """variables_snapshot JSONField is populated with datapoints list."""
    roe = RulesOfEngagementFactory()
    version = RulesOfEngagementVersionFactory(roe=roe)
    RulesOfEngagementVariableFactory(roe_version=version, name="Test", abbrev="T", y_axis_label="units")

    project = ProjectFactory(assigned_roe=roe)
    user = UserFactory()

    from gjallarhorn.models import Conversation, ExecutionPlan, PlanStep

    conversation = Conversation.objects.create(user=user, project=project, conversation_type="sitrep")
    plan = ExecutionPlan.objects.create(conversation=conversation, goal="Test")
    PlanStep.objects.create(
        plan=plan,
        order=5,
        action="Assess Test (T)",
        reasoning_why_needed="Test",
        expected_outcome="{}",
        is_variable_assessment=True,
        result={"value": "42", "color": "green"},
    )

    now = timezone.now()
    sitrep = SitRepFactory(project=project, from_dt=now, to_dt=now, source_plan=plan)

    _persist_variable_datapoints(sitrep, plan)

    sitrep.refresh_from_db()
    assert len(sitrep.variables_snapshot) == 1
    assert sitrep.variables_snapshot[0]["variable_name"] == "Test"
    assert sitrep.variables_snapshot[0]["value"] == "42"


@pytest.mark.django_db
def test_persist_idempotent_on_duplicate_plan_run():
    """Running persist twice does not create duplicate VariableDatapoint rows."""
    roe = RulesOfEngagementFactory()
    version = RulesOfEngagementVersionFactory(roe=roe)
    RulesOfEngagementVariableFactory(roe_version=version, name="Test", abbrev="T")

    project = ProjectFactory(assigned_roe=roe)
    user = UserFactory()

    from gjallarhorn.models import Conversation, ExecutionPlan, PlanStep

    conversation = Conversation.objects.create(user=user, project=project, conversation_type="sitrep")
    plan = ExecutionPlan.objects.create(conversation=conversation, goal="Test")
    PlanStep.objects.create(
        plan=plan,
        order=5,
        action="Assess Test (T)",
        reasoning_why_needed="Test",
        expected_outcome="{}",
        is_variable_assessment=True,
        result={"value": "10", "color": "green"},
    )

    now = timezone.now()
    sitrep = SitRepFactory(project=project, from_dt=now, to_dt=now, source_plan=plan)

    _persist_variable_datapoints(sitrep, plan)
    _persist_variable_datapoints(sitrep, plan)  # second call

    datapoints = VariableDatapoint.objects.filter(sitrep=sitrep)
    assert datapoints.count() == 1


@pytest.mark.django_db
def test_persist_grey_when_value_null():
    """Grey color and null value are persisted correctly."""
    roe = RulesOfEngagementFactory()
    version = RulesOfEngagementVersionFactory(roe=roe)
    RulesOfEngagementVariableFactory(roe_version=version, name="Test", abbrev="T")

    project = ProjectFactory(assigned_roe=roe)
    user = UserFactory()

    from gjallarhorn.models import Conversation, ExecutionPlan, PlanStep

    conversation = Conversation.objects.create(user=user, project=project, conversation_type="sitrep")
    plan = ExecutionPlan.objects.create(conversation=conversation, goal="Test")
    PlanStep.objects.create(
        plan=plan,
        order=5,
        action="Assess Test (T)",
        reasoning_why_needed="Test",
        expected_outcome="{}",
        is_variable_assessment=True,
        result={"value": None, "color": "grey"},
    )

    now = timezone.now()
    sitrep = SitRepFactory(project=project, from_dt=now, to_dt=now, source_plan=plan)

    _persist_variable_datapoints(sitrep, plan)

    datapoint = VariableDatapoint.objects.get(sitrep=sitrep)
    assert datapoint.value is None
    assert datapoint.color == "grey"


@pytest.mark.django_db
def test_persist_links_source_plan_step():
    """VariableDatapoint.source_plan_step links to the PlanStep that produced it."""
    roe = RulesOfEngagementFactory()
    version = RulesOfEngagementVersionFactory(roe=roe)
    RulesOfEngagementVariableFactory(roe_version=version, name="Test", abbrev="T")

    project = ProjectFactory(assigned_roe=roe)
    user = UserFactory()

    from gjallarhorn.models import Conversation, ExecutionPlan, PlanStep

    conversation = Conversation.objects.create(user=user, project=project, conversation_type="sitrep")
    plan = ExecutionPlan.objects.create(conversation=conversation, goal="Test")
    step = PlanStep.objects.create(
        plan=plan,
        order=5,
        action="Assess Test (T)",
        reasoning_why_needed="Test",
        expected_outcome="{}",
        is_variable_assessment=True,
        result={"value": "100", "color": "green"},
    )

    now = timezone.now()
    sitrep = SitRepFactory(project=project, from_dt=now, to_dt=now, source_plan=plan)

    _persist_variable_datapoints(sitrep, plan)

    datapoint = VariableDatapoint.objects.get(sitrep=sitrep)
    assert datapoint.source_plan_step == step


@pytest.mark.django_db
def test_persist_truncates_long_values_to_64_chars():
    """LLM prose values are truncated to fit VariableDatapoint.value."""
    roe = RulesOfEngagementFactory()
    version = RulesOfEngagementVersionFactory(roe=roe)
    RulesOfEngagementVariableFactory(roe_version=version, name="Transparency", abbrev="T")

    project = ProjectFactory(assigned_roe=roe)
    user = UserFactory()

    from gjallarhorn.models import Conversation, ExecutionPlan, PlanStep

    conversation = Conversation.objects.create(user=user, project=project, conversation_type="sitrep")
    plan = ExecutionPlan.objects.create(conversation=conversation, goal="Test")
    long_value = "Last increment: 2026-05-25T01:30:51Z (~0 h ago — 2 commits ingested)"
    PlanStep.objects.create(
        plan=plan,
        order=5,
        action="Assess Transparency (T)",
        reasoning_why_needed="Test",
        expected_outcome="{}",
        is_variable_assessment=True,
        result={"value": long_value, "color": "green"},
    )

    now = timezone.now()
    sitrep = SitRepFactory(project=project, from_dt=now, to_dt=now, source_plan=plan)

    _persist_variable_datapoints(sitrep, plan)

    datapoint = VariableDatapoint.objects.get(sitrep=sitrep)
    assert len(datapoint.value) == 64
    assert datapoint.value == long_value[:64]
    sitrep.refresh_from_db()
    assert len(sitrep.variables_snapshot[0]["value"]) == 64


@pytest.mark.django_db
def test_persist_no_datapoints_when_no_variable_steps():
    """When plan has no variable assessment steps, no datapoints are created."""
    project = ProjectFactory()
    user = UserFactory()

    from gjallarhorn.models import Conversation, ExecutionPlan

    conversation = Conversation.objects.create(user=user, project=project, conversation_type="sitrep")
    plan = ExecutionPlan.objects.create(conversation=conversation, goal="Test")

    now = timezone.now()
    sitrep = SitRepFactory(project=project, from_dt=now, to_dt=now, source_plan=plan)

    _persist_variable_datapoints(sitrep, plan)

    datapoints = VariableDatapoint.objects.filter(sitrep=sitrep)
    assert datapoints.count() == 0
    sitrep.refresh_from_db()
    assert sitrep.variables_snapshot == []


@pytest.mark.django_db
def test_persist_rolls_back_sitrep_when_datapoint_write_fails():
    """SitRep row is not committed if variable datapoint persistence fails."""
    roe = RulesOfEngagementFactory()
    RulesOfEngagementVersionFactory(roe=roe)
    project = ProjectFactory(assigned_roe=roe)
    user = UserFactory()

    from gjallarhorn.models import Conversation, ExecutionPlan, PlanStep

    conversation = Conversation.objects.create(user=user, project=project, conversation_type="sitrep_generation")
    now = timezone.now()
    plan = ExecutionPlan.objects.create(
        conversation=conversation,
        goal="Test",
        sitrep_from_dt=now,
        sitrep_to_dt=now,
        sitrep_trigger="manual",
    )
    PlanStep.objects.create(
        plan=plan,
        order=1,
        action="Compose narrative",
        reasoning_why_needed="Test",
        expected_outcome="{}",
        status="completed",
        is_planning=True,
        result={
            "headline": "GREEN",
            "situation_assessment": "Ok",
            "notable_activity": [],
        },
    )
    before = SitRep.objects.count()

    with patch(
        "gjallarhorn.services.sitrep_service._persist_variable_datapoints",
        side_effect=RuntimeError("datapoint write failed"),
    ):
        with pytest.raises(RuntimeError, match="datapoint write failed"):
            _persist_sitrep_from_plan(plan)

    assert SitRep.objects.count() == before
