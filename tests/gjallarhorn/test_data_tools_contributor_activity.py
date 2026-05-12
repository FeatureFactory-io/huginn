"""get_contributor_activity tool tests — T-65a."""

import pytest
from django.utils import timezone

from gjallarhorn.mcp_tools.data_tools import get_contributor_activity
from ingestion.models import Contributor, DataSource, Increment, Project


@pytest.mark.django_db
class TestGetContributorActivity:
    def test_aggregates_by_author_email(self):
        """alice (3 commits) before bob (1)."""
        project = Project.objects.create(name="test-proj", slug="test-proj")
        ds = DataSource.objects.create(name="test-ds", datasource_type="gitlab", base_url="https://gitlab.com")
        alice = Contributor.objects.create(datasource=ds, email="alice@example.com")
        bob = Contributor.objects.create(datasource=ds, email="bob@example.com")

        base_time = timezone.now()

        for i in range(3):
            Increment.objects.create(
                project=project,
                datasource=ds,
                kind="commit",
                external_id=f"alice-commit-{i}",
                occurred_at=base_time + timezone.timedelta(minutes=i),
                contributor=alice,
            )

        Increment.objects.create(
            project=project,
            datasource=ds,
            kind="commit",
            external_id="bob-commit",
            occurred_at=base_time,
            contributor=bob,
        )

        result = get_contributor_activity(
            project_id=project.id,
            from_dt=base_time - timezone.timedelta(hours=1),
            to_dt=base_time + timezone.timedelta(hours=1),
        )

        assert len(result) == 2
        assert result[0]["email"] == "alice@example.com"
        assert result[0]["commit_count"] == 3
        assert result[1]["email"] == "bob@example.com"
        assert result[1]["commit_count"] == 1

    def test_cross_project_excluded(self):
        """Other project's commits not aggregated."""
        project1 = Project.objects.create(name="proj1", slug="proj1")
        project2 = Project.objects.create(name="proj2", slug="proj2")
        ds = DataSource.objects.create(name="test-ds", datasource_type="gitlab", base_url="https://gitlab.com")
        alice = Contributor.objects.create(datasource=ds, email="alice@example.com")

        base_time = timezone.now()

        Increment.objects.create(
            project=project1,
            datasource=ds,
            kind="commit",
            external_id="proj1-commit",
            occurred_at=base_time,
            contributor=alice,
        )

        Increment.objects.create(
            project=project2,
            datasource=ds,
            kind="commit",
            external_id="proj2-commit",
            occurred_at=base_time,
            contributor=alice,
        )

        result = get_contributor_activity(
            project_id=project1.id,
            from_dt=base_time - timezone.timedelta(hours=1),
            to_dt=base_time + timezone.timedelta(hours=1),
        )

        assert len(result) == 1
        assert result[0]["commit_count"] == 1
