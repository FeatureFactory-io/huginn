"""Factory helpers for gjallarhorn services."""

from django.conf import settings

from gjallarhorn.agent.tool_executor import ToolExecutor
from gjallarhorn.mcp_tools import (
    get_active_roe,
    get_active_situational_awareness,
    get_contributor_activity,
    list_active_fragos,
    list_commits,
    list_issues,
    list_merge_requests,
    list_milestones,
)

PLANNING_MODEL = "claude-opus-4-5"
EXECUTION_MODEL = "claude-sonnet-4-6"


def create_agent(user=None, project=None, plan_id: str | None = None):
    """Construct a GjallarhornAgent backed by ClaudeLLM and the full tool executor.

    ClaudeLLM is lazy-imported to keep test setup free of ANTHROPIC_API_KEY.
    """
    import logging

    log = logging.getLogger(__name__)
    from gjallarhorn.agent.agent import GjallarhornAgent  # noqa: PLC0415
    from gjallarhorn.llm.claude import ClaudeLLM  # noqa: PLC0415

    log.debug("create_agent: constructing ClaudeLLM plan=%s key_set=%s", plan_id, bool(settings.ANTHROPIC_API_KEY))
    llm = ClaudeLLM(api_key=settings.ANTHROPIC_API_KEY)
    log.debug("create_agent: ClaudeLLM ready plan=%s", plan_id)
    tool_executor = build_executor(user=user, project=project, plan_id=plan_id)
    log.debug("create_agent: executor ready plan=%s", plan_id)
    agent = GjallarhornAgent(llm=llm, tool_executor=tool_executor)
    log.debug("create_agent: done plan=%s", plan_id)
    return agent


def build_executor(user, project, plan_id: str | None = None) -> ToolExecutor:
    """Instantiate ToolExecutor and register all narrative-phase read tools."""
    executor = ToolExecutor(user=user, project=project, plan_id=plan_id)
    executor.register("list_commits", list_commits)
    executor.register("get_contributor_activity", get_contributor_activity)
    executor.register("get_active_roe", get_active_roe)
    executor.register("get_active_situational_awareness", get_active_situational_awareness)
    executor.register("list_active_fragos", list_active_fragos)
    executor.register("list_issues", list_issues)
    executor.register("list_milestones", list_milestones)
    executor.register("list_merge_requests", list_merge_requests)
    return executor
