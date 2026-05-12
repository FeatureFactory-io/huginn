"""ClaudeLLM implementation."""

import anthropic
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

from gjallarhorn.llm.base import LLM, LLMResponse
from gjallarhorn.llm.retry import retry_on_rate_limit


class ClaudeLLM(LLM):
    """Claude Sonnet 4.6 with extended thinking and prompt caching."""

    def __init__(self):
        api_key = getattr(settings, "ANTHROPIC_API_KEY", None)
        if not api_key:
            raise ImproperlyConfigured("ANTHROPIC_API_KEY must be set in settings or .env")
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = "claude-sonnet-4-6"

    @retry_on_rate_limit(max_retries=3, base_delay=30)
    def generate_with_tools(
        self,
        messages: list[dict],
        tools: list[dict],
        system_blocks: list[dict],
    ) -> LLMResponse:
        """Generate response with extended thinking and prompt caching."""
        response = self.client.messages.create(
            model=self.model,
            max_tokens=4096,
            thinking={"type": "enabled", "budget_tokens": 8000},
            system=system_blocks,
            messages=messages,
            tools=tools if tools else anthropic.NOT_GIVEN,
        )

        tool_calls = []
        content_text = ""

        for block in response.content:
            if block.type == "text":
                content_text += block.text
            elif block.type == "tool_use":
                tool_calls.append(
                    {
                        "id": block.id,
                        "name": block.name,
                        "input": block.input,
                    }
                )

        return LLMResponse(
            content=content_text,
            stop_reason=response.stop_reason,
            usage={
                "input_tokens": response.usage.input_tokens,
                "output_tokens": response.usage.output_tokens,
                "cache_read_input_tokens": getattr(response.usage, "cache_read_input_tokens", 0),
            },
            tool_calls=tool_calls,
            model=self.model,
        )
