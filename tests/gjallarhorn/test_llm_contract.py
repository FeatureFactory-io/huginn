"""LLM ABC and LLMResponse contract tests — T-64."""

import dataclasses

import pytest

from gjallarhorn.llm.base import LLM, LLMResponse


def test_scripted_llm_satisfies_abc(scripted_llm_factory):
    """ScriptedLLM is a valid LLM implementation."""
    responses = [
        LLMResponse(
            content="Test response",
            stop_reason="end_turn",
            usage={"input_tokens": 10, "output_tokens": 5},
            tool_calls=[],
            model="scripted",
        )
    ]
    llm = scripted_llm_factory(responses)
    assert isinstance(llm, LLM)


def test_llm_response_all_fields():
    """LLMResponse dataclass has all required fields."""
    resp = LLMResponse(
        content="Test",
        stop_reason="end_turn",
        usage={"input_tokens": 10, "output_tokens": 5, "cache_read_input_tokens": 0},
        tool_calls=[{"name": "test_tool", "input": {}}],
        model="claude-sonnet-4-6",
    )
    as_dict = dataclasses.asdict(resp)
    assert as_dict["content"] == "Test"
    assert as_dict["stop_reason"] == "end_turn"
    assert as_dict["usage"]["input_tokens"] == 10
    assert as_dict["tool_calls"][0]["name"] == "test_tool"
    assert as_dict["model"] == "claude-sonnet-4-6"


def test_llm_response_tool_calls_default_empty():
    """tool_calls defaults to empty list."""
    resp = LLMResponse(
        content="Test",
        stop_reason="end_turn",
        usage={},
        model="test",
    )
    assert resp.tool_calls == []


def test_scripted_llm_records_calls(scripted_llm_factory):
    """ScriptedLLM records all calls in .calls list."""
    responses = [
        LLMResponse(
            content="Response 1",
            stop_reason="end_turn",
            usage={},
            tool_calls=[],
            model="scripted",
        )
    ]
    llm = scripted_llm_factory(responses)

    llm.generate_with_tools(
        messages=[{"role": "user", "content": "Test"}],
        tools=[],
        system_blocks=[],
    )

    assert len(llm.calls) == 1
    assert llm.calls[0]["messages"][0]["content"] == "Test"


def test_scripted_llm_exhaustion(scripted_llm_factory):
    """ScriptedLLM raises StopIteration when responses exhausted."""
    responses = [
        LLMResponse(
            content="Only response",
            stop_reason="end_turn",
            usage={},
            tool_calls=[],
            model="scripted",
        )
    ]
    llm = scripted_llm_factory(responses)

    llm.generate_with_tools(messages=[], tools=[], system_blocks=[])

    with pytest.raises(StopIteration):
        llm.generate_with_tools(messages=[], tools=[], system_blocks=[])
