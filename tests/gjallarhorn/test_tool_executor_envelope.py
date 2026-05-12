"""ToolExecutor envelope contract tests — T-65a + T-65b."""

import pytest
from django.contrib.auth import get_user_model

from gjallarhorn.agent.tool_executor import ToolExecutor
from gjallarhorn.services.factory import build_executor
from ingestion.models import Project

User = get_user_model()


@pytest.mark.django_db
class TestToolExecutorEnvelope:
    def test_known_read_tool_returns_success_envelope(self):
        """Known read tool returns {success:True, result:..., error:None}."""
        user = User.objects.create_user(email="test@example.com", password="test")
        project = Project.objects.create(name="test-proj", slug="test-proj")

        executor = ToolExecutor(user=user, project=project)
        executor.register("test_tool", lambda **kwargs: {"data": "test"})

        result = executor.execute("test_tool", arg1="value1")

        assert result["success"] is True
        assert result["result"] == {"data": "test"}
        assert result["error"] is None

    def test_unknown_tool_returns_error_envelope(self):
        """Unknown tool returns {success:False, error contains 'Unknown tool'}."""
        user = User.objects.create_user(email="test@example.com", password="test")
        project = Project.objects.create(name="test-proj", slug="test-proj")

        executor = ToolExecutor(user=user, project=project)

        result = executor.execute("nonexistent_tool")

        assert result["success"] is False
        assert result["result"] is None
        assert "Unknown tool" in result["error"]

    def test_write_tool_blocked_in_narrative_phase(self):
        """Write tools return {success:False, error contains 'narrative phase'}."""
        user = User.objects.create_user(email="test@example.com", password="test")
        project = Project.objects.create(name="test-proj", slug="test-proj")

        executor = ToolExecutor(user=user, project=project)
        executor.register("create_frago", lambda **kwargs: {"created": True})

        result = executor.execute("create_frago", title="Test")

        assert result["success"] is False
        assert result["result"] is None
        assert "narrative phase" in result["error"].lower()

    def test_tool_exception_captured_in_envelope(self):
        """Raised exception → {success:False, error: str(exc)}."""
        user = User.objects.create_user(email="test@example.com", password="test")
        project = Project.objects.create(name="test-proj", slug="test-proj")

        def failing_tool(**kwargs):
            raise ValueError("Tool failed intentionally")

        executor = ToolExecutor(user=user, project=project)
        executor.register("failing_tool", failing_tool)

        result = executor.execute("failing_tool")

        assert result["success"] is False
        assert result["result"] is None
        assert "Tool failed intentionally" in result["error"]

    def test_build_executor_registers_five_tools(self):
        """build_executor returns ToolExecutor with 5 tools registered."""
        user = User.objects.create_user(email="test@example.com", password="test")
        project = Project.objects.create(name="test-proj", slug="test-proj")

        executor = build_executor(user=user, project=project)

        assert len(executor._registry) == 5
        assert "list_commits" in executor._registry
        assert "get_contributor_activity" in executor._registry
        assert "get_active_playbook" in executor._registry
        assert "get_active_situational_awareness" in executor._registry
        assert "list_active_fragos" in executor._registry
