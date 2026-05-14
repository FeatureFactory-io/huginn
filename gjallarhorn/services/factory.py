"""Factory helpers for gjallarhorn services."""

from django.conf import settings

from gjallarhorn.agent.tool_executor import ToolExecutor
from gjallarhorn.mcp_tools import (
    get_active_playbook,
    get_active_situational_awareness,
    get_contributor_activity,
    list_active_fragos,
    list_commits,
)


def create_agent(user=None, project=None):
    """Construct a GjallarhornAgent backed by ClaudeLLM and the full tool executor.

    ClaudeLLM is lazy-imported to keep test setup free of ANTHROPIC_API_KEY.
    """
    from gjallarhorn.agent.agent import GjallarhornAgent  # noqa: PLC0415
    from gjallarhorn.llm.claude import ClaudeLLM  # noqa: PLC0415

    llm = ClaudeLLM(api_key=settings.ANTHROPIC_API_KEY)
    tool_executor = build_executor(user=user, project=project)
    return GjallarhornAgent(llm=llm, tool_executor=tool_executor)


def build_executor(user, project) -> ToolExecutor:
    """Instantiate ToolExecutor and register all narrative-phase read tools."""
    executor = ToolExecutor(user=user, project=project)
    executor.register("list_commits", list_commits)
    executor.register("get_contributor_activity", get_contributor_activity)
    executor.register("get_active_playbook", get_active_playbook)
    executor.register("get_active_situational_awareness", get_active_situational_awareness)
    executor.register("list_active_fragos", list_active_fragos)
    return executor
