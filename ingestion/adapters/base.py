"""Abstract base for per-DataSource ingestion adapters."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Iterable
from datetime import datetime

from ingestion.domain.increments import IncrementDTO
from ingestion.models import DataSource, Project


class DataSourceAdapter(ABC):
    """Pulls normalized Increments from an external system for one Project."""

    def __init__(self, datasource: DataSource) -> None:
        self.datasource = datasource

    @abstractmethod
    def fetch_increments(self, project: Project, *, since: datetime | None) -> Iterable[IncrementDTO]:
        """Yield :class:`IncrementDTO` instances with ``occurred_at >= since`` when ``since`` is set."""
