"""list_issues, list_milestones, list_merge_requests tool tests."""

import json

import pytest
from django.utils import timezone

from gjallarhorn.mcp_tools.data_tools import list_issues, list_merge_requests, list_milestones
from ingestion.models import Contributor, Milestone, UnitOfWork
from tests.factories import MilestoneFactory, ProjectFactory, UnitOfWorkFactory


@pytest.mark.django_db
class TestListIssues:
    def test_issues_in_window_by_updated_at(self):
        project = ProjectFactory()
        ds = project.datasource
        base = timezone.now()
        window_start = base
        window_end = base + timezone.timedelta(hours=1)

        UnitOfWorkFactory(
            project=project,
            datasource=ds,
            kind=UnitOfWork.Kind.ISSUE,
            external_id="issue-in",
            title="In window",
            updated_at=base + timezone.timedelta(minutes=10),
        )
        UnitOfWorkFactory(
            project=project,
            datasource=ds,
            kind=UnitOfWork.Kind.ISSUE,
            external_id="issue-out",
            title="Out of window",
            updated_at=base + timezone.timedelta(hours=2),
        )

        result = list_issues(project.pk, window_start, window_end)
        assert len(result) == 1
        assert result[0]["external_id"] == "issue-in"
        assert result[0]["kind"] == "issue"

    def test_issues_in_window_by_closed_at(self):
        project = ProjectFactory()
        base = timezone.now()
        closed = base + timezone.timedelta(minutes=30)

        UnitOfWorkFactory(
            project=project,
            kind=UnitOfWork.Kind.ISSUE,
            external_id="issue-closed",
            updated_at=base - timezone.timedelta(days=1),
            closed_at=closed,
        )

        result = list_issues(
            project.pk,
            base,
            base + timezone.timedelta(hours=1),
        )
        assert len(result) == 1
        assert result[0]["external_id"] == "issue-closed"

    def test_excludes_merge_requests(self):
        project = ProjectFactory()
        base = timezone.now()
        UnitOfWorkFactory(
            project=project,
            kind=UnitOfWork.Kind.MERGE_REQUEST,
            external_id="mr-1",
            updated_at=base,
        )

        result = list_issues(project.pk, base - timezone.timedelta(hours=1), base + timezone.timedelta(hours=1))
        assert result == []

    def test_serialized_fields(self):
        project = ProjectFactory()
        ds = project.datasource
        contributor = Contributor.objects.create(datasource=ds, email="dev@example.com", name="Dev")
        milestone = MilestoneFactory(project=project, title="Sprint 1")
        base = timezone.now()

        UnitOfWorkFactory(
            project=project,
            datasource=ds,
            kind=UnitOfWork.Kind.ISSUE,
            external_id="42",
            iid=7,
            title="Fix auth",
            state="opened",
            milestone=milestone,
            assignee=contributor,
            labels=["bug", "auth"],
            updated_at=base,
            payload={"web_url": "https://gitlab.com/g/i/-/issues/7"},
        )

        result = list_issues(project.pk, base - timezone.timedelta(minutes=1), base + timezone.timedelta(minutes=1))
        assert len(result) == 1
        row = result[0]
        assert row["iid"] == 7
        assert row["title"] == "Fix auth"
        assert row["milestone_title"] == "Sprint 1"
        assert row["assignee_email"] == "dev@example.com"
        assert row["labels"] == ["bug", "auth"]
        assert row["web_url"] == "https://gitlab.com/g/i/-/issues/7"
        json.dumps(result)


@pytest.mark.django_db
class TestListMergeRequests:
    def test_merge_requests_in_window(self):
        project = ProjectFactory()
        base = timezone.now()

        UnitOfWorkFactory(
            project=project,
            kind=UnitOfWork.Kind.MERGE_REQUEST,
            external_id="mr-in",
            title="Feature MR",
            updated_at=base,
        )
        UnitOfWorkFactory(
            project=project,
            kind=UnitOfWork.Kind.ISSUE,
            external_id="issue-only",
            updated_at=base,
        )

        result = list_merge_requests(
            project.pk,
            base - timezone.timedelta(hours=1),
            base + timezone.timedelta(hours=1),
        )
        assert len(result) == 1
        assert result[0]["external_id"] == "mr-in"
        assert result[0]["kind"] == "merge_request"


@pytest.mark.django_db
class TestListMilestones:
    def test_returns_project_milestones(self):
        project = ProjectFactory()
        MilestoneFactory(project=project, external_id="ms-1", title="Alpha")
        MilestoneFactory(project=project, external_id="ms-2", title="Beta", state="closed")
        other = ProjectFactory()
        MilestoneFactory(project=other, external_id="ms-other", title="Other")

        result = list_milestones(project.pk)
        titles = {row["title"] for row in result}
        assert titles == {"Alpha", "Beta"}

    def test_at_dt_filters_updated_at(self):
        project = ProjectFactory()
        base = timezone.now()
        Milestone.objects.create(
            project=project,
            datasource=project.datasource,
            external_id="old",
            title="Old",
            state="closed",
            updated_at=base - timezone.timedelta(days=2),
        )
        Milestone.objects.create(
            project=project,
            datasource=project.datasource,
            external_id="new",
            title="New",
            state="active",
            updated_at=base,
        )

        result = list_milestones(project.pk, at_dt=base - timezone.timedelta(days=1))
        assert len(result) == 1
        assert result[0]["title"] == "Old"
