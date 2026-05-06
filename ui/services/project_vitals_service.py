"""Read models for Project Vitals (Act 2) — freshness / transparency."""

from __future__ import annotations

from datetime import datetime

from django.db.models import Max

from ingestion.models import Increment


class ProjectVitalsService:
    """Thin ORM read-model for Vitals tab."""

    def latest_increment_occurred_at(self, project_id: int) -> datetime | None:
        """Most recent ``Increment.occurred_at`` for the project, or ``None``."""
        return Increment.objects.filter(project_id=project_id).aggregate(latest=Max("occurred_at"))["latest"]
