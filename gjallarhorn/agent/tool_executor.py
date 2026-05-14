"""Permission-aware tool dispatcher for the narrative phase."""


class ToolExecutor:
    """Wraps every tool call in the standard envelope; blocks write tools."""

    WRITE_TOOLS = frozenset({"create_frago", "extend_sitawareness", "create_jira_issue", "approve_decision"})

    def __init__(self, user, project):
        self.user = user
        self.project = project
        self._registry: dict[str, callable] = {}

    def register(self, name: str, fn: callable) -> None:
        self._registry[name] = fn

    def execute(self, tool_name: str, **kwargs) -> dict:
        """Returns {success, result, error}. Never raises."""
        if tool_name in self.WRITE_TOOLS:
            return {
                "success": False,
                "result": None,
                "error": f"Write tool '{tool_name}' not enabled in narrative phase",
            }
        fn = self._registry.get(tool_name)
        if fn is None:
            return {"success": False, "result": None, "error": f"Unknown tool: {tool_name}"}
        try:
            result = fn(project_id=self.project.pk, **kwargs)
            return {"success": True, "result": result, "error": None}
        except Exception as exc:  # noqa: BLE001
            return {"success": False, "result": None, "error": str(exc)}
