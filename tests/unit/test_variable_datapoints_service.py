"""Unit tests for VariableDatapointService."""

import pytest
from django.utils import timezone

from tests.factories import (
    ProjectFactory,
    RulesOfEngagementFactory,
    RulesOfEngagementVariableFactory,
    RulesOfEngagementVersionFactory,
    SitRepFactory,
    UserFactory,
    VariableDatapointFactory,
)
from ui.services.variable_datapoints_service import (
    get_datapoints_for_period,
    get_latest_datapoints,
    get_sitrep_variables_snapshot,
)


@pytest.mark.django_db
def test_get_latest_datapoints_returns_latest_for_each_variable():
    """get_latest_datapoints returns the most recent datapoint per variable."""
    roe = RulesOfEngagementFactory()
    version = RulesOfEngagementVersionFactory(roe=roe)
    var1 = RulesOfEngagementVariableFactory(roe_version=version, sort_order=1, name="Var1", abbrev="V1")
    var2 = RulesOfEngagementVariableFactory(roe_version=version, sort_order=2, name="Var2", abbrev="V2")

    project = ProjectFactory(assigned_roe=roe)
    user = UserFactory()

    now = timezone.now()
    older = now - timezone.timedelta(days=7)

    from gjallarhorn.models import Conversation, ExecutionPlan

    conversation = Conversation.objects.create(user=user, project=project, conversation_type="sitrep")
    plan1 = ExecutionPlan.objects.create(conversation=conversation, goal="Older")
    plan2 = ExecutionPlan.objects.create(conversation=conversation, goal="Latest")

    sitrep1 = SitRepFactory(project=project, from_dt=older, to_dt=older, source_plan=plan1)
    sitrep2 = SitRepFactory(project=project, from_dt=now, to_dt=now, source_plan=plan2)

    # Older datapoints
    VariableDatapointFactory(sitrep=sitrep1, roe_variable=var1, variable_name="Var1", value="10", color="green")
    VariableDatapointFactory(sitrep=sitrep1, roe_variable=var2, variable_name="Var2", value="5", color="orange")

    # Latest datapoints
    VariableDatapointFactory(sitrep=sitrep2, roe_variable=var1, variable_name="Var1", value="20", color="green")
    VariableDatapointFactory(sitrep=sitrep2, roe_variable=var2, variable_name="Var2", value="8", color="red")

    result = get_latest_datapoints(project.pk)

    assert len(result) == 2
    assert result[0]["variable_name"] == "Var1"
    assert result[0]["value"] == "20"
    assert result[0]["color"] == "green"
    assert result[1]["variable_name"] == "Var2"
    assert result[1]["value"] == "8"
    assert result[1]["color"] == "red"


@pytest.mark.django_db
def test_get_latest_datapoints_returns_grey_for_missing_variable():
    """When a variable has no datapoint yet, return grey placeholder."""
    roe = RulesOfEngagementFactory()
    version = RulesOfEngagementVersionFactory(roe=roe)
    RulesOfEngagementVariableFactory(roe_version=version, name="NewVar", abbrev="NV")

    project = ProjectFactory(assigned_roe=roe)

    result = get_latest_datapoints(project.pk)

    assert len(result) == 1
    assert result[0]["variable_name"] == "NewVar"
    assert result[0]["abbrev"] == "NV"
    assert result[0]["value"] is None
    assert result[0]["color"] == "grey"
    assert result[0]["to_dt"] is None


@pytest.mark.django_db
def test_get_latest_datapoints_returns_empty_when_no_roe():
    """When project has no RoE, return empty list."""
    project = ProjectFactory(assigned_roe=None)

    result = get_latest_datapoints(project.pk)

    assert result == []


@pytest.mark.django_db
def test_get_latest_datapoints_nonexistent_project():
    """When project ID does not exist, return empty list."""
    result = get_latest_datapoints(99999)

    assert result == []


@pytest.mark.django_db
def test_get_datapoints_for_period_filters_by_time_window():
    """get_datapoints_for_period returns only datapoints within [from_dt, to_dt]."""
    roe = RulesOfEngagementFactory()
    version = RulesOfEngagementVersionFactory(roe=roe)
    var = RulesOfEngagementVariableFactory(roe_version=version, name="Test", abbrev="T")

    project = ProjectFactory(assigned_roe=roe)
    user = UserFactory()

    base = timezone.now()
    before = base - timezone.timedelta(days=10)
    inside1 = base - timezone.timedelta(days=5)
    inside2 = base - timezone.timedelta(days=2)
    after = base + timezone.timedelta(days=1)

    from gjallarhorn.models import Conversation, ExecutionPlan

    conversation = Conversation.objects.create(user=user, project=project, conversation_type="sitrep")
    plan_before = ExecutionPlan.objects.create(conversation=conversation, goal="Before")
    plan_inside1 = ExecutionPlan.objects.create(conversation=conversation, goal="Inside1")
    plan_inside2 = ExecutionPlan.objects.create(conversation=conversation, goal="Inside2")
    plan_after = ExecutionPlan.objects.create(conversation=conversation, goal="After")

    sitrep_before = SitRepFactory(project=project, from_dt=before, to_dt=before, source_plan=plan_before)
    sitrep_inside1 = SitRepFactory(project=project, from_dt=inside1, to_dt=inside1, source_plan=plan_inside1)
    sitrep_inside2 = SitRepFactory(project=project, from_dt=inside2, to_dt=inside2, source_plan=plan_inside2)
    sitrep_after = SitRepFactory(project=project, from_dt=after, to_dt=after, source_plan=plan_after)

    VariableDatapointFactory(sitrep=sitrep_before, roe_variable=var, variable_name="Test", value="1")
    VariableDatapointFactory(sitrep=sitrep_inside1, roe_variable=var, variable_name="Test", value="2")
    VariableDatapointFactory(sitrep=sitrep_inside2, roe_variable=var, variable_name="Test", value="3")
    VariableDatapointFactory(sitrep=sitrep_after, roe_variable=var, variable_name="Test", value="4")

    from_dt = inside1 - timezone.timedelta(hours=1)
    to_dt = inside2 + timezone.timedelta(hours=1)

    result = get_datapoints_for_period(project.pk, from_dt, to_dt)

    assert len(result) == 2
    assert result[0]["value"] == "2"
    assert result[1]["value"] == "3"


@pytest.mark.django_db
def test_get_datapoints_for_period_includes_incremental_sitrep_by_to_dt():
    """Incremental SitReps are included when to_dt falls in the period, even if from_dt is older."""
    from ui.services.increments_service import time_window_bounds

    roe = RulesOfEngagementFactory()
    version = RulesOfEngagementVersionFactory(roe=roe)
    var = RulesOfEngagementVariableFactory(roe_version=version, name="Complexity", abbrev="CX")

    project = ProjectFactory(assigned_roe=roe)
    user = UserFactory()

    now = timezone.now()
    week_ago = now - timezone.timedelta(days=7)

    from gjallarhorn.models import Conversation, ExecutionPlan

    conversation = Conversation.objects.create(user=user, project=project, conversation_type="sitrep")
    plan = ExecutionPlan.objects.create(conversation=conversation, goal="Incremental")
    sitrep = SitRepFactory(project=project, from_dt=week_ago, to_dt=now, source_plan=plan)
    VariableDatapointFactory(
        sitrep=sitrep,
        roe_variable=var,
        variable_name="Complexity",
        value="~18 files/MR (2 MRs, est.)",
    )

    start, end_exclusive = time_window_bounds("today")
    result = get_datapoints_for_period(project.pk, start, end_exclusive)

    assert len(result) == 1
    assert result[0]["value"] == "~18 files/MR (2 MRs, est.)"


@pytest.mark.django_db
def test_get_datapoints_for_period_empty_when_no_data():
    """When no datapoints exist in range, return empty list."""
    project = ProjectFactory()
    now = timezone.now()

    result = get_datapoints_for_period(project.pk, now, now)

    assert result == []


@pytest.mark.django_db
def test_get_datapoints_for_period_ordered_by_to_dt():
    """Datapoints are returned in chronological order (sitrep__to_dt ascending)."""
    roe = RulesOfEngagementFactory()
    version = RulesOfEngagementVersionFactory(roe=roe)
    var = RulesOfEngagementVariableFactory(roe_version=version, name="Test", abbrev="T")

    project = ProjectFactory(assigned_roe=roe)
    user = UserFactory()

    base = timezone.now()
    t1 = base - timezone.timedelta(days=3)
    t2 = base - timezone.timedelta(days=1)

    from gjallarhorn.models import Conversation, ExecutionPlan

    conversation = Conversation.objects.create(user=user, project=project, conversation_type="sitrep")
    plan1 = ExecutionPlan.objects.create(conversation=conversation, goal="P1")
    plan2 = ExecutionPlan.objects.create(conversation=conversation, goal="P2")

    sitrep2 = SitRepFactory(project=project, from_dt=t2, to_dt=t2, source_plan=plan2)
    sitrep1 = SitRepFactory(project=project, from_dt=t1, to_dt=t1, source_plan=plan1)

    # Create in reverse order, but should be returned in chronological order
    VariableDatapointFactory(sitrep=sitrep2, roe_variable=var, variable_name="Test", value="B")
    VariableDatapointFactory(sitrep=sitrep1, roe_variable=var, variable_name="Test", value="A")

    result = get_datapoints_for_period(project.pk, t1 - timezone.timedelta(hours=1), t2 + timezone.timedelta(hours=1))

    assert len(result) == 2
    assert result[0]["value"] == "A"
    assert result[1]["value"] == "B"


@pytest.mark.django_db
def test_get_sitrep_variables_snapshot_returns_snapshot():
    """get_sitrep_variables_snapshot returns the SitRep.variables_snapshot list."""
    project = ProjectFactory()
    sitrep = SitRepFactory(
        project=project,
        variables_snapshot=[
            {"variable_name": "V1", "abbrev": "V1", "y_axis_label": "units", "value": "10", "color": "green"},
            {"variable_name": "V2", "abbrev": "V2", "y_axis_label": "units", "value": "5", "color": "red"},
        ],
    )

    result = get_sitrep_variables_snapshot(sitrep.pk)

    assert len(result) == 2
    assert result[0]["variable_name"] == "V1"
    assert result[0]["value"] == "10"
    assert result[1]["variable_name"] == "V2"
    assert result[1]["value"] == "5"


@pytest.mark.django_db
def test_get_sitrep_variables_snapshot_returns_empty_when_no_snapshot():
    """When SitRep has no variables_snapshot, return empty list."""
    project = ProjectFactory()
    sitrep = SitRepFactory(project=project, variables_snapshot=[])

    result = get_sitrep_variables_snapshot(sitrep.pk)

    assert result == []


@pytest.mark.django_db
def test_get_sitrep_variables_snapshot_nonexistent_sitrep():
    """When SitRep ID does not exist, return empty list."""
    result = get_sitrep_variables_snapshot(99999)

    assert result == []
