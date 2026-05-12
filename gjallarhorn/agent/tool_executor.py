"""ToolExecutor — permission-aware envelope dispatcher."""

from collections.abc import Callable


class ToolExecutor:
    """Executes tools with permission checks and standardized error handling."""

    WRITE_TOOLS = frozenset(
        {
            "create_frago",
            "extend_sitawareness",
            "create_jira_issue",
            "approve_decision",
        }
    )

    def __init__(self, user, project):
        self.user = user
        self.project = project
        self._registry: dict[str, Callable] = {}

    def register(self, name: str, fn: Callable) -> None:
        """Register a tool function."""
        self._registry[name] = fn

    def execute(self, tool_name: str, **kwargs) -> dict:
        """Execute a tool and return standardized envelope.

        Returns:
            {"success": bool, "result": Any | None, "error": str | None}
        """
        # Check if tool exists
        if tool_name not in self._registry:
            return {
                "success": False,
                "result": None,
                "error": f"Unknown tool: {tool_name}",
            }

        # Block write tools in narrative phase
        if tool_name in self.WRITE_TOOLS:
            return {
                "success": False,
                "result": None,
                "error": f"Write tool '{tool_name}' is not available in narrative phase",
            }

        # Execute tool and wrap exceptions
        try:
            result = self._registry[tool_name](**kwargs)
            return {"success": True, "result": result, "error": None}
        except Exception as exc:
            return {"success": False, "result": None, "error": str(exc)}
