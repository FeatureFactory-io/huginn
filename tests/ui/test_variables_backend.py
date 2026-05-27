"""Unit tests for Variables UI backend."""

import pytest
from django.urls import reverse
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


@pytest.mark.django_db
def test_projects_detail_informer_bar_reflects_latest_datapoints(client):
    """Informer bar dots on Vitals tab show latest variable colors."""
    user = UserFactory()
    roe = RulesOfEngagementFactory()
    version = RulesOfEngagementVersionFactory(roe=roe)
    var1 = RulesOfEngagementVariableFactory(roe_version=version, sort_order=1, name="Var1", abbrev="V1")
    var2 = RulesOfEngagementVariableFactory(roe_version=version, sort_order=2, name="Var2", abbrev="V2")

    project = ProjectFactory(assigned_roe=roe)

    now = timezone.now()

    from gjallarhorn.models import Conversation, ExecutionPlan

    conversation = Conversation.objects.create(user=user, project=project, conversation_type="sitrep")
    plan = ExecutionPlan.objects.create(conversation=conversation, goal="Test")

    sitrep = SitRepFactory(project=project, from_dt=now, to_dt=now, source_plan=plan)
    VariableDatapointFactory(sitrep=sitrep, roe_variable=var1, variable_name="Var1", value="10", color="green")
    VariableDatapointFactory(sitrep=sitrep, roe_variable=var2, variable_name="Var2", value="5", color="red")

    client.force_login(user)
    url = reverse("projects-detail", args=[project.pk])
    response = client.get(url)

    assert response.status_code == 200
    context = response.context
    informer_bar_dots = context["informer_bar_dots"]

    assert len(informer_bar_dots) == 2
    assert informer_bar_dots[0]["abbrev"] == "V1"
    assert informer_bar_dots[0]["color"] == "green"
    assert informer_bar_dots[0]["value"] == "10"
    assert informer_bar_dots[1]["abbrev"] == "V2"
    assert informer_bar_dots[1]["color"] == "red"
    assert informer_bar_dots[1]["value"] == "5"


@pytest.mark.django_db
def test_projects_detail_variables_tab_shows_datapoints_for_period(client):
    """Variables tab shows datapoints within the selected time window."""
    user = UserFactory()
    roe = RulesOfEngagementFactory()
    version = RulesOfEngagementVersionFactory(roe=roe)
    var = RulesOfEngagementVariableFactory(roe_version=version, name="Test", abbrev="T")

    project = ProjectFactory(assigned_roe=roe)

    base = timezone.now()
    t1 = base - timezone.timedelta(hours=2)
    t2 = base - timezone.timedelta(hours=1)

    from gjallarhorn.models import Conversation, ExecutionPlan

    conversation = Conversation.objects.create(user=user, project=project, conversation_type="sitrep")
    plan1 = ExecutionPlan.objects.create(conversation=conversation, goal="P1")
    plan2 = ExecutionPlan.objects.create(conversation=conversation, goal="P2")

    sitrep1 = SitRepFactory(project=project, from_dt=t1, to_dt=t1, source_plan=plan1)
    sitrep2 = SitRepFactory(project=project, from_dt=t2, to_dt=t2, source_plan=plan2)

    VariableDatapointFactory(sitrep=sitrep1, roe_variable=var, variable_name="Test", value="A")
    VariableDatapointFactory(sitrep=sitrep2, roe_variable=var, variable_name="Test", value="B")

    client.force_login(user)
    url = reverse("projects-detail", args=[project.pk]) + "?tab=variables&period=today"
    response = client.get(url)

    assert response.status_code == 200
    context = response.context
    variables_datapoints = context["variables_datapoints"]

    # Should include both datapoints from today
    assert len(variables_datapoints) >= 2


@pytest.mark.django_db
def test_project_variables_echarts_api_returns_json(client):
    """ECharts API endpoint returns proper JSON structure."""
    user = UserFactory()
    roe = RulesOfEngagementFactory()
    version = RulesOfEngagementVersionFactory(roe=roe)
    var = RulesOfEngagementVariableFactory(roe_version=version, name="TestVar", abbrev="TV")

    project = ProjectFactory(assigned_roe=roe)

    now = timezone.now()

    from gjallarhorn.models import Conversation, ExecutionPlan

    conversation = Conversation.objects.create(user=user, project=project, conversation_type="sitrep")
    plan = ExecutionPlan.objects.create(conversation=conversation, goal="Test")

    sitrep = SitRepFactory(project=project, from_dt=now, to_dt=now, source_plan=plan)
    VariableDatapointFactory(sitrep=sitrep, roe_variable=var, variable_name="TestVar", value="42", color="green")

    client.force_login(user)
    url = reverse("project-variables-echarts", args=[project.pk])
    response = client.get(url)

    assert response.status_code == 200
    data = response.json()

    assert "xAxis" in data
    assert "series" in data
    assert len(data["series"]) == 1
    assert data["series"][0]["name"] == "TestVar"
    assert len(data["series"][0]["data"]) == 1
    assert data["series"][0]["data"][0]["value"][1] == 42.0
    assert data["series"][0]["data"][0]["display_value"] == "42"
    assert data["series"][0]["data"][0]["plot_y"] == 42.0
    assert data["series"][0]["data"][0]["itemStyle"]["color"] == "#4CAF50"


@pytest.mark.django_db
def test_project_variables_echarts_api_empty_when_no_datapoints(client):
    """ECharts API returns empty series when no datapoints exist."""
    user = UserFactory()
    project = ProjectFactory()

    client.force_login(user)
    url = reverse("project-variables-echarts", args=[project.pk])
    response = client.get(url)

    assert response.status_code == 200
    data = response.json()

    assert data["series"] == []


@pytest.mark.django_db
def test_project_variables_echarts_api_filters_by_period(client):
    """ECharts API filters datapoints by the provided period parameter."""
    user = UserFactory()
    roe = RulesOfEngagementFactory()
    version = RulesOfEngagementVersionFactory(roe=roe)
    var = RulesOfEngagementVariableFactory(roe_version=version, name="Test", abbrev="T")

    project = ProjectFactory(assigned_roe=roe)

    base = timezone.now()
    old = base - timezone.timedelta(days=30)
    recent = base - timezone.timedelta(days=1)

    from gjallarhorn.models import Conversation, ExecutionPlan

    conversation = Conversation.objects.create(user=user, project=project, conversation_type="sitrep")
    plan_old = ExecutionPlan.objects.create(conversation=conversation, goal="Old")
    plan_recent = ExecutionPlan.objects.create(conversation=conversation, goal="Recent")

    sitrep_old = SitRepFactory(project=project, from_dt=old, to_dt=old, source_plan=plan_old)
    sitrep_recent = SitRepFactory(project=project, from_dt=recent, to_dt=recent, source_plan=plan_recent)

    VariableDatapointFactory(sitrep=sitrep_old, roe_variable=var, variable_name="Test", value="Old")
    VariableDatapointFactory(sitrep=sitrep_recent, roe_variable=var, variable_name="Test", value="Recent")

    client.force_login(user)
    url = reverse("project-variables-echarts", args=[project.pk]) + "?period=this_week"
    response = client.get(url)

    assert response.status_code == 200
    data = response.json()

    # Should only include recent datapoint from this week
    assert len(data["series"][0]["data"]) == 1
    assert data["series"][0]["data"][0]["display_value"] == "Recent"


@pytest.mark.django_db
def test_project_variables_echarts_api_includes_incremental_sitrep_for_today(client):
    """ECharts API includes incremental SitReps when to_dt is today but from_dt is older."""
    user = UserFactory()
    roe = RulesOfEngagementFactory()
    version = RulesOfEngagementVersionFactory(roe=roe)
    var = RulesOfEngagementVariableFactory(roe_version=version, name="Complexity", abbrev="CX")

    project = ProjectFactory(assigned_roe=roe)

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
        color="green",
    )

    client.force_login(user)
    url = reverse("project-variables-echarts", args=[project.pk]) + "?period=today"
    response = client.get(url)

    assert response.status_code == 200
    data = response.json()

    assert len(data["series"]) == 1
    assert len(data["series"][0]["data"]) == 1
    assert data["series"][0]["data"][0]["display_value"] == "~18 files/MR (2 MRs, est.)"
    assert data["series"][0]["data"][0]["plot_y"] == 18.0
    assert data["series"][0]["data"][0]["itemStyle"]["color"] == "#4CAF50"


@pytest.mark.django_db
def test_project_variables_echarts_api_null_plot_y_not_zero(client):
    """Non-numeric/null values must not be coerced to y=0 (avoids false drop-to-zero lines)."""
    user = UserFactory()
    roe = RulesOfEngagementFactory()
    version = RulesOfEngagementVersionFactory(roe=roe)
    var = RulesOfEngagementVariableFactory(roe_version=version, name="Cycle & Lead Time", abbrev="CLT")

    project = ProjectFactory(assigned_roe=roe)

    base = timezone.now()
    t1 = base - timezone.timedelta(hours=6)
    t2 = base - timezone.timedelta(hours=2)

    from gjallarhorn.models import Conversation, ExecutionPlan

    conversation = Conversation.objects.create(user=user, project=project, conversation_type="sitrep")
    plan1 = ExecutionPlan.objects.create(conversation=conversation, goal="P1")
    plan2 = ExecutionPlan.objects.create(conversation=conversation, goal="P2")

    sitrep1 = SitRepFactory(project=project, from_dt=t1, to_dt=t1, source_plan=plan1)
    sitrep2 = SitRepFactory(project=project, from_dt=t2, to_dt=t2, source_plan=plan2)

    VariableDatapointFactory(sitrep=sitrep1, roe_variable=var, variable_name="Cycle & Lead Time", value="10 commits")
    VariableDatapointFactory(
        sitrep=sitrep2, roe_variable=var, variable_name="Cycle & Lead Time", value=None, color="grey"
    )

    client.force_login(user)
    url = reverse("project-variables-echarts", args=[project.pk]) + "?period=today"
    response = client.get(url)

    assert response.status_code == 200
    data = response.json()
    points = data["series"][0]["data"]

    assert len(points) == 2
    assert points[0]["plot_y"] == 10.0
    assert points[1]["plot_y"] is None
    assert points[1]["value"][1] is None
