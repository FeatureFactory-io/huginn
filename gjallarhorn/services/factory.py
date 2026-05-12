"""Factory functions for Gjallarhorn services."""

from gjallarhorn.agent.tool_executor import ToolExecutor
from gjallarhorn.mcp_tools.data_tools import get_contributor_activity, list_commits
from gjallarhorn.mcp_tools.playbook_tools import get_active_playbook
from gjallarhorn.mcp_tools.sitrep_tools import (
    get_active_situational_awareness,
    list_active_fragos,
)


def build_executor(user, project) -> ToolExecutor:
    """Build a ToolExecutor with all narrative-phase read tools registered.

    Args:
        user: User instance for permission checks
        project: Project instance for scoping

    Returns:
        ToolExecutor with 5 tools registered
    """
    executor = ToolExecutor(user=user, project=project)

    # Data tools
    executor.register("list_commits", list_commits)
    executor.register("get_contributor_activity", get_contributor_activity)

    # Playbook tools
    executor.register("get_active_playbook", get_active_playbook)

    # SitRep tools
    executor.register("get_active_situational_awareness", get_active_situational_awareness)
    executor.register("list_active_fragos", list_active_fragos)

    return executor
