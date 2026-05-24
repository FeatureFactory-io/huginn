"""get_active_roe tool tests — T-65b."""

import pytest

from gjallarhorn.mcp_tools.roe_tools import get_active_roe
from ingestion.models import Project
from roe.models import RulesOfEngagement, RulesOfEngagementVersion


@pytest.mark.django_db
class TestGetActiveRoe:
    def test_returns_workflow_markdown(self):
        """Project with RoE → correct markdown + version."""
        roe = RulesOfEngagement.objects.create(name="Test RoE", slug="test-roe")
        RulesOfEngagementVersion.objects.create(
            roe=roe,
            version_number=5,
            workflow_md="# Test Workflow\n\nThis is the workflow.",
        )
        project = Project.objects.create(
            name="test-proj",
            slug="test-proj",
            assigned_roe=roe,
        )

        result = get_active_roe(project_id=project.id)

        assert result["workflow_md"] == "# Test Workflow\n\nThis is the workflow."
        assert result["version_number"] == 5
        assert result["roe_name"] == "Test RoE"

    def test_no_roe_returns_none(self):
        """No RoE → None (ToolExecutor wraps to {success:False})."""
        project = Project.objects.create(name="test-proj", slug="test-proj")

        result = get_active_roe(project_id=project.id)

        assert result is None
