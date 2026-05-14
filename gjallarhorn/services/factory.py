"""Factory helpers for gjallarhorn services."""

from gjallarhorn.agent.tool_executor import ToolExecutor
from gjallarhorn.mcp_tools import (
    get_active_playbook,
    get_active_situational_awareness,
    get_contributor_activity,
    list_active_fragos,
    list_commits,
)


def build_executor(user, project) -> ToolExecutor:
    """Instantiate ToolExecutor and register all narrative-phase read tools."""
    executor = ToolExecutor(user=user, project=project)
    executor.register("list_commits", list_commits)
    executor.register("get_contributor_activity", get_contributor_activity)
    executor.register("get_active_playbook", get_active_playbook)
    executor.register("get_active_situational_awareness", get_active_situational_awareness)
    executor.register("list_active_fragos", list_active_fragos)
    return executor
