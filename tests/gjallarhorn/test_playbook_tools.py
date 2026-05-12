"""get_active_playbook tool tests — T-65b."""

import pytest

from gjallarhorn.mcp_tools.playbook_tools import get_active_playbook
from ingestion.models import Project
from playbooks.models import Playbook, PlaybookVersion


@pytest.mark.django_db
class TestGetActivePlaybook:
    def test_returns_workflow_markdown(self):
        """Project with Playbook → correct markdown + version."""
        playbook = Playbook.objects.create(name="Test Playbook", slug="test-playbook")
        PlaybookVersion.objects.create(
            playbook=playbook,
            version_number=5,
            workflow_md="# Test Workflow\n\nThis is the workflow.",
        )
        project = Project.objects.create(
            name="test-proj",
            slug="test-proj",
            assigned_playbook=playbook,
        )

        result = get_active_playbook(project_id=project.id)

        assert result["workflow_md"] == "# Test Workflow\n\nThis is the workflow."
        assert result["version_number"] == 5
        assert result["playbook_name"] == "Test Playbook"

    def test_no_playbook_returns_none(self):
        """No Playbook → None (ToolExecutor wraps to {success:False})."""
        project = Project.objects.create(name="test-proj", slug="test-proj")

        result = get_active_playbook(project_id=project.id)

        assert result is None
