"""Abstract bases for work-item and milestone ingestion adapters."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Iterable
from datetime import datetime

from ingestion.domain.work import MilestoneDTO, UnitOfWorkDTO
from ingestion.models import DataSource, Project


class WorkItemAdapter(ABC):
    """Pulls normalized UnitOfWork rows from an external system."""

    def __init__(self, datasource: DataSource) -> None:
        self.datasource = datasource

    @abstractmethod
    def fetch_work_items(self, project: Project, *, since: datetime | None) -> Iterable[UnitOfWorkDTO]:
        """Yield work items with ``updated_at >= since`` when ``since`` is set."""


class MilestoneAdapter(ABC):
    """Pulls normalized Milestone rows from an external system."""

    def __init__(self, datasource: DataSource) -> None:
        self.datasource = datasource

    @abstractmethod
    def fetch_milestones(self, project: Project, *, since: datetime | None) -> Iterable[MilestoneDTO]:
        """Yield milestones updated on or after ``since`` when set."""
