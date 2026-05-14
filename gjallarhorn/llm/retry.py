"""Retry decorator for LLM calls — handles Anthropic rate-limit errors."""

import functools
import time

import anthropic


def retry_on_rate_limit(max_retries: int = 3, base_delay: int = 30, status_callback=None):
    """Decorator factory that retries a function on anthropic.RateLimitError.

    Exponential backoff: base_delay * 2^(attempt-1), i.e. 30 → 60 → 120 s.
    Non-rate-limit exceptions propagate immediately without retrying.

    Args:
        max_retries: Maximum number of retry attempts (default 3).
        base_delay: Base delay in seconds for the first retry (default 30).
        status_callback: Optional callable(attempt: int, delay: int) called before each sleep.
    """

    def decorator(fn):
        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries + 1):
                try:
                    return fn(*args, **kwargs)
                except anthropic.RateLimitError:
                    if attempt == max_retries:
                        raise
                    delay = base_delay * (2**attempt)
                    if status_callback is not None:
                        status_callback(attempt + 1, delay)
                    time.sleep(delay)

        return wrapper

    return decorator
