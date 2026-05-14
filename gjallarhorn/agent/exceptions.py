"""Gjallarhorn agent exceptions."""


class ToolExecutionError(Exception):
    """Raised when a tool call returns success=False."""

    def __init__(self, tool_name: str, error_message: str):
        self.tool_name = tool_name
        super().__init__(f"Tool '{tool_name}' failed: {error_message}")
