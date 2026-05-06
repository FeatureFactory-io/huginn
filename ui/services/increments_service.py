"""Time-window queries for Project Increments (Act 2)."""

from __future__ import annotations

from datetime import UTC, date, datetime, time, timedelta

from django.db.models import QuerySet
from django.utils import timezone

from ingestion.models import Increment

VALID_RANGE_KEYS: frozenset[str] = frozenset({"today", "yesterday", "this_week", "last_week", "last_14d"})

RANGE_LABELS: dict[str, str] = {
    "today": "Today",
    "yesterday": "Yesterday",
    "this_week": "This week",
    "last_week": "Last week",
    "last_14d": "Last 14 days",
}


def normalize_range_key(raw: str | None) -> str:
    """Return a supported range key, defaulting to ``last_14d``."""
    key = (raw or "").strip().lower()
    return key if key in VALID_RANGE_KEYS else "last_14d"


def _day_start(d: date, *, tz) -> datetime:
    naive = datetime.combine(d, time.min)
    if tz is None:
        return naive.replace(tzinfo=UTC)
    return timezone.make_aware(naive, tz)


def time_window_bounds(
    range_key: str,
    *,
    now: datetime | None = None,
) -> tuple[datetime, datetime | None]:
    """Return ``(start, end_exclusive)`` for filtering ``occurred_at``.

    ``end_exclusive`` is ``None`` when the upper bound is "now" (rolling window).
    """
    range_key = normalize_range_key(range_key)
    now = now or timezone.now()
    if timezone.is_naive(now):
        now = timezone.make_aware(now, UTC)

    tz = timezone.get_current_timezone()
    local_date = timezone.localtime(now, tz).date()

    if range_key == "today":
        start = _day_start(local_date, tz=tz)
        return start, start + timedelta(days=1)
    if range_key == "yesterday":
        y = local_date - timedelta(days=1)
        start = _day_start(y, tz=tz)
        return start, start + timedelta(days=1)
    if range_key == "this_week":
        monday = local_date - timedelta(days=local_date.weekday())
        start = _day_start(monday, tz=tz)
        return start, start + timedelta(days=7)
    if range_key == "last_week":
        monday_this = local_date - timedelta(days=local_date.weekday())
        this_week_start = _day_start(monday_this, tz=tz)
        last_week_start = this_week_start - timedelta(days=7)
        return last_week_start, this_week_start
    if range_key == "last_14d":
        start = now - timedelta(days=14)
        return start, None
    msg = f"unexpected range key {range_key!r}"
    raise AssertionError(msg)


class IncrementsService:
    """Read models for the Increments tab."""

    def increments_for_project(self, project_id: int, range_key: str) -> QuerySet[Increment]:
        range_key = normalize_range_key(range_key)
        start, end_excl = time_window_bounds(range_key)
        qs = (
            Increment.objects.filter(project_id=project_id)
            .select_related("contributor", "project")
            .order_by("-occurred_at", "-id")
        )
        qs = qs.filter(occurred_at__gte=start)
        if end_excl is not None:
            qs = qs.filter(occurred_at__lt=end_excl)
        else:
            qs = qs.filter(occurred_at__lte=timezone.now())
        return qs
