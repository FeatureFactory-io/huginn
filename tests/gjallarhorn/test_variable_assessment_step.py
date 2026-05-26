"""Unit tests for variable assessment step execution."""

import pytest

# Placeholder - full implementation requires mocking LLM calls
# The integration test in test_variables_pipeline_e2e will cover the full flow


@pytest.mark.skip(reason="Requires LLM mocking infrastructure - covered by integration tests")
def test_variable_step_calls_execution_model():
    """Variable assessment step uses execution model (Sonnet), not planning model."""
    pass


@pytest.mark.skip(reason="Requires LLM mocking infrastructure - covered by integration tests")
def test_variable_step_result_has_value_and_color():
    """Variable step result contains value and color fields."""
    pass


@pytest.mark.skip(reason="Requires LLM mocking infrastructure - covered by integration tests")
def test_malformed_llm_response_defaults_to_grey():
    """On parse error, variable step defaults to value=None, color='grey'."""
    pass


@pytest.mark.skip(reason="Requires LLM mocking infrastructure - covered by integration tests")
def test_variable_step_does_not_use_planning_model():
    """Verify that variable assessment does not call _planning_model()."""
    pass
