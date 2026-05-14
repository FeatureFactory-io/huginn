"""ClaudeLLM — Anthropic Claude implementation of the LLM ABC."""

import anthropic
from django.core.exceptions import ImproperlyConfigured

from gjallarhorn.llm.base import LLM, LLMResponse
from gjallarhorn.llm.retry import retry_on_rate_limit


class ClaudeLLM(LLM):
    """LLM implementation backed by Anthropic Claude with extended thinking."""

    MODEL = "claude-sonnet-4-6"
    THINKING_BUDGET = 8000

    def __init__(self, api_key: str, status_callback=None):
        if not api_key:
            raise ImproperlyConfigured("ANTHROPIC_API_KEY is required but was not provided or is empty.")
        self._client = anthropic.Anthropic(api_key=api_key)
        self._status_callback = status_callback
        self._generate_with_retry = retry_on_rate_limit(
            max_retries=3,
            base_delay=30,
            status_callback=status_callback,
        )(self._call_api)

    def generate_with_tools(
        self,
        messages: list[dict],
        tools: list[dict],
        system_blocks: list[dict],
    ) -> LLMResponse:
        return self._generate_with_retry(
            messages=messages,
            tools=tools,
            system_blocks=system_blocks,
        )

    def _call_api(
        self,
        messages: list[dict],
        tools: list[dict],
        system_blocks: list[dict],
    ) -> LLMResponse:
        response = self._client.messages.create(
            model=self.MODEL,
            max_tokens=16000,
            thinking={"type": "enabled", "budget_tokens": self.THINKING_BUDGET},
            system=system_blocks,
            tools=tools,
            messages=messages,
        )

        content_text = ""
        tool_calls: list[dict] = []
        for block in response.content:
            if block.type == "text":
                content_text = block.text
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
            model=response.model,
        )
