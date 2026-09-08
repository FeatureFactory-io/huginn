"""Shared dump-cursor comparisons for ingestion adapters."""

from datetime import datetime


def is_at_or_before_cursor(value: datetime | None, since: datetime | None) -> bool:
    """Return True when ``value`` is not strictly after the dump cursor.

    The previous successful run stores ``cursor_to`` as the latest ingested
    timestamp. The next run must treat that instant as already dumped, otherwise
    the same row is counted every hour and automatic SitRep keeps firing.

    :param value: Event timestamp as datetime. Example: 2026-08-28T21:09:32+00:00
    :param since: Exclusive cursor as datetime. Example: 2026-08-28T21:09:32+00:00
    :return: Whether the event should be skipped as bool. Example: True
    """
    if since is None or value is None:
        return False
    return value <= since
