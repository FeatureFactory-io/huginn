"""list_commits tool tests — T-65a."""

import pytest
from django.utils import timezone

from gjallarhorn.mcp_tools.data_tools import list_commits
from ingestion.models import Contributor, DataSource, Increment, Project


@pytest.mark.django_db
class TestListCommits:
    def test_commits_in_window(self):
        """Only commits in [from_dt, to_dt) returned."""
        project = Project.objects.create(name="test-proj", slug="test-proj")
        ds = DataSource.objects.create(name="test-ds", datasource_type="gitlab", base_url="https://gitlab.com")
        contributor = Contributor.objects.create(datasource=ds, email="alice@example.com")

        base_time = timezone.now()

        # Before window
        Increment.objects.create(
            project=project,
            datasource=ds,
            kind="commit",
            external_id="commit-before",
            occurred_at=base_time - timezone.timedelta(hours=2),
            contributor=contributor,
        )

        # In window
        Increment.objects.create(
            project=project,
            datasource=ds,
            kind="commit",
            external_id="commit-in-window",
            occurred_at=base_time,
            contributor=contributor,
        )

        # After window
        Increment.objects.create(
            project=project,
            datasource=ds,
            kind="commit",
            external_id="commit-after",
            occurred_at=base_time + timezone.timedelta(hours=2),
            contributor=contributor,
        )

        result = list_commits(
            project_id=project.id,
            from_dt=base_time,
            to_dt=base_time + timezone.timedelta(hours=1),
        )

        assert len(result) == 1
        assert result[0]["external_id"] == "commit-in-window"

    def test_commits_excluded_other_project(self):
        """Other project's commits absent."""
        project1 = Project.objects.create(name="proj1", slug="proj1")
        project2 = Project.objects.create(name="proj2", slug="proj2")
        ds = DataSource.objects.create(name="test-ds", datasource_type="gitlab", base_url="https://gitlab.com")
        contributor = Contributor.objects.create(datasource=ds, email="alice@example.com")

        base_time = timezone.now()

        Increment.objects.create(
            project=project1,
            datasource=ds,
            kind="commit",
            external_id="commit-proj1",
            occurred_at=base_time,
            contributor=contributor,
        )

        Increment.objects.create(
            project=project2,
            datasource=ds,
            kind="commit",
            external_id="commit-proj2",
            occurred_at=base_time,
            contributor=contributor,
        )

        result = list_commits(
            project_id=project1.id,
            from_dt=base_time - timezone.timedelta(hours=1),
            to_dt=base_time + timezone.timedelta(hours=1),
        )

        assert len(result) == 1
        assert result[0]["external_id"] == "commit-proj1"

    def test_commits_limit_respected(self):
        """limit=3 returns exactly 3."""
        project = Project.objects.create(name="test-proj", slug="test-proj")
        ds = DataSource.objects.create(name="test-ds", datasource_type="gitlab", base_url="https://gitlab.com")
        contributor = Contributor.objects.create(datasource=ds, email="alice@example.com")

        base_time = timezone.now()

        for i in range(5):
            Increment.objects.create(
                project=project,
                datasource=ds,
                kind="commit",
                external_id=f"commit-{i}",
                occurred_at=base_time + timezone.timedelta(minutes=i),
                contributor=contributor,
            )

        result = list_commits(
            project_id=project.id,
            from_dt=base_time - timezone.timedelta(hours=1),
            to_dt=base_time + timezone.timedelta(hours=1),
            limit=3,
        )

        assert len(result) == 3

    def test_empty_window(self):
        """No commits → [] not error."""
        project = Project.objects.create(name="test-proj", slug="test-proj")

        base_time = timezone.now()

        result = list_commits(
            project_id=project.id,
            from_dt=base_time,
            to_dt=base_time + timezone.timedelta(hours=1),
        )

        assert result == []
