"""retry_on_rate_limit decorator tests — T-64."""

from unittest.mock import Mock, patch

import anthropic
import pytest

from gjallarhorn.llm.retry import retry_on_rate_limit


def test_no_retry_on_success():
    """No retry when function succeeds first time."""
    mock_fn = Mock(return_value="success")
    decorated = retry_on_rate_limit(max_retries=3, base_delay=30)(mock_fn)

    with patch("time.sleep") as mock_sleep:
        result = decorated()

    assert result == "success"
    assert mock_fn.call_count == 1
    mock_sleep.assert_not_called()


def test_retries_on_rate_limit_error():
    """Retries on anthropic.RateLimitError."""
    mock_fn = Mock(
        side_effect=[
            anthropic.RateLimitError("Rate limit", response=Mock(status_code=429), body={}),
            anthropic.RateLimitError("Rate limit", response=Mock(status_code=429), body={}),
            "success",
        ]
    )
    decorated = retry_on_rate_limit(max_retries=3, base_delay=30)(mock_fn)

    with patch("time.sleep"):
        result = decorated()

    assert result == "success"
    assert mock_fn.call_count == 3


def test_propagates_after_max_retries():
    """Raises RateLimitError after max_retries exhausted."""
    mock_fn = Mock(
        side_effect=anthropic.RateLimitError(
            "Rate limit",
            response=Mock(status_code=429),
            body={},
        )
    )
    decorated = retry_on_rate_limit(max_retries=2, base_delay=10)(mock_fn)

    with patch("time.sleep"):
        with pytest.raises(anthropic.RateLimitError):
            decorated()

    assert mock_fn.call_count == 3


def test_non_rate_limit_error_bypasses_retry():
    """Non-RateLimitError exceptions propagate immediately."""
    mock_fn = Mock(side_effect=ValueError("Not a rate limit error"))
    decorated = retry_on_rate_limit(max_retries=3, base_delay=30)(mock_fn)

    with pytest.raises(ValueError, match="Not a rate limit error"):
        decorated()

    assert mock_fn.call_count == 1


def test_status_callback_called_per_retry():
    """status_callback invoked on each retry."""
    callback_calls = []

    def status_cb(attempt, delay):
        callback_calls.append((attempt, delay))

    mock_fn = Mock(
        side_effect=[
            anthropic.RateLimitError("Rate limit", response=Mock(status_code=429), body={}),
            anthropic.RateLimitError("Rate limit", response=Mock(status_code=429), body={}),
            "success",
        ]
    )
    decorated = retry_on_rate_limit(max_retries=3, base_delay=30, status_callback=status_cb)(mock_fn)

    with patch("time.sleep"):
        decorated()

    assert len(callback_calls) == 2
    assert callback_calls[0] == (1, 30)
    assert callback_calls[1] == (2, 60)


def test_exponential_backoff_delays():
    """Delays follow exponential backoff: base_delay * 2^(attempt-1)."""
    mock_fn = Mock(
        side_effect=[
            anthropic.RateLimitError("Rate limit", response=Mock(status_code=429), body={}),
            anthropic.RateLimitError("Rate limit", response=Mock(status_code=429), body={}),
            anthropic.RateLimitError("Rate limit", response=Mock(status_code=429), body={}),
            "success",
        ]
    )
    decorated = retry_on_rate_limit(max_retries=5, base_delay=30)(mock_fn)

    with patch("time.sleep") as mock_sleep:
        decorated()

    assert mock_sleep.call_count == 3
    assert mock_sleep.call_args_list[0][0][0] == 30
    assert mock_sleep.call_args_list[1][0][0] == 60
    assert mock_sleep.call_args_list[2][0][0] == 120
