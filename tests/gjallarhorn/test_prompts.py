"""System prompt tests — T-64."""

from gjallarhorn.agent.prompts import SITREP_NARRATIVE_SYSTEM_PROMPT


def test_system_prompt_non_empty():
    """SITREP_NARRATIVE_SYSTEM_PROMPT is a non-empty string."""
    assert isinstance(SITREP_NARRATIVE_SYSTEM_PROMPT, str)
    assert len(SITREP_NARRATIVE_SYSTEM_PROMPT) > 100


def test_system_prompt_no_variable_compute_language():
    """Prompt does not reference VariableDatapoint (narrative phase only)."""
    assert "VariableDatapoint" not in SITREP_NARRATIVE_SYSTEM_PROMPT
    assert "variable" not in SITREP_NARRATIVE_SYSTEM_PROMPT.lower() or "Variable" in SITREP_NARRATIVE_SYSTEM_PROMPT
