"""LLM abstraction layer — ABC and response dataclass."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class LLMResponse:
    """Response from an LLM generate call."""

    content: str
    stop_reason: str
    usage: dict
    tool_calls: list[dict] = field(default_factory=list)
    model: str = ""


class LLM(ABC):
    """Abstract base class for LLM implementations."""

    @abstractmethod
    def generate_with_tools(
        self,
        messages: list[dict],
        tools: list[dict],
        system_blocks: list[dict],
    ) -> LLMResponse:
        """Generate a response with tool-calling capability.

        Args:
            messages: Conversation history in Anthropic format
            tools: Tool definitions in Anthropic format
            system_blocks: System prompt blocks with cache_control markers

        Returns:
            LLMResponse with content, stop_reason, usage, and optional tool_calls
        """
