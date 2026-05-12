"""Retry decorator for rate-limit handling."""

import time
from collections.abc import Callable
from functools import wraps

import anthropic


def retry_on_rate_limit(
    max_retries: int = 3,
    base_delay: int = 30,
    status_callback: Callable[[int, int], None] | None = None,
):
    """Decorator that retries on anthropic.RateLimitError with exponential backoff.

    Args:
        max_retries: Maximum number of retry attempts
        base_delay: Base delay in seconds (doubled each retry)
        status_callback: Optional callback(attempt, delay) called before each retry
    """

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except anthropic.RateLimitError:
                    if attempt >= max_retries:
                        raise
                    delay = base_delay * (2**attempt)
                    if status_callback:
                        status_callback(attempt + 1, delay)
                    time.sleep(delay)
            return None

        return wrapper

    return decorator
