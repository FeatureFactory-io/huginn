"""GitHub SitRep plan steps use ingested canonical rows."""

import pytest
from django.utils import timezone

from gjallarhorn.mcp_tools.data_tools import list_issues
from gjallarhorn.services.sitrep_service import build_narrative_plan_steps
from ingestion.models import DataSource, UnitOfWork
from tests.factories import DataSourceFactory, ProjectFactory, RulesOfEngagementFactory, RulesOfEngagementVersionFactory


@pytest.mark.django_db
def test_github_project_plan_has_seven_data_steps() -> None:
    ds = DataSourceFactory(datasource_type=DataSource.Type.GITHUB)
    roe = RulesOfEngagementFactory()
    RulesOfEngagementVersionFactory(roe=roe, version_number=1)
    project = ProjectFactory(datasource=ds, assigned_roe=roe, source_path="acme/widget")
    now = timezone.now()
    steps = build_narrative_plan_steps(project, now - timezone.timedelta(hours=1), now)
    tools = [s["tool"] for s in steps if s.get("tool")]
    assert tools[:7] == [
        "list_commits",
        "get_contributor_activity",
        "list_active_fragos",
        "get_active_situational_awareness",
        "list_issues",
        "list_milestones",
        "list_merge_requests",
    ]


@pytest.mark.django_db
def test_list_issues_returns_github_ingested_rows() -> None:
    ds = DataSourceFactory(datasource_type=DataSource.Type.GITHUB)
    project = ProjectFactory(datasource=ds)
    now = timezone.now()
    UnitOfWork.objects.create(
        project=project,
        datasource=ds,
        kind=UnitOfWork.Kind.ISSUE,
        external_id="101",
        iid=7,
        title="Bug",
        state="opened",
        created_at=now,
        updated_at=now,
    )
    rows = list_issues(project.pk, now - timezone.timedelta(hours=1), now + timezone.timedelta(hours=1))
    assert len(rows) == 1
    assert rows[0]["title"] == "Bug"
