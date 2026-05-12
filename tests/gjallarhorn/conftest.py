"""Gjallarhorn test fixtures — T-64."""

import pytest

from gjallarhorn.llm.base import LLM, LLMResponse


class ScriptedLLM(LLM):
    """Test double for LLM — returns pre-scripted responses."""

    def __init__(self, responses: list[LLMResponse]):
        self._responses = iter(responses)
        self.calls: list[dict] = []

    def generate_with_tools(
        self,
        messages: list[dict],
        tools: list[dict],
        system_blocks: list[dict],
    ) -> LLMResponse:
        self.calls.append(
            {
                "messages": messages,
                "tools": tools,
                "system_blocks": system_blocks,
            }
        )
        return next(self._responses)


@pytest.fixture
def scripted_llm_factory():
    """Factory fixture for creating ScriptedLLM instances."""

    def _factory(responses: list[LLMResponse]) -> ScriptedLLM:
        return ScriptedLLM(responses)

    return _factory
