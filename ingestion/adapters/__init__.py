"""Register ingestion adapter implementations by DataSource type."""

from __future__ import annotations

from collections import defaultdict

from ingestion.adapters.base import DataSourceAdapter
from ingestion.adapters.work_base import MilestoneAdapter, WorkItemAdapter

ADAPTER_REGISTRY: dict[str, list[type[DataSourceAdapter]]] = defaultdict(list)
WORK_ADAPTER_REGISTRY: dict[str, list[type[WorkItemAdapter]]] = defaultdict(list)
MILESTONE_ADAPTER_REGISTRY: dict[str, list[type[MilestoneAdapter]]] = defaultdict(list)


def register_adapter(datasource_type: str, cls: type[DataSourceAdapter]) -> None:
    ADAPTER_REGISTRY[datasource_type].append(cls)


def register_work_adapter(datasource_type: str, cls: type[WorkItemAdapter]) -> None:
    WORK_ADAPTER_REGISTRY[datasource_type].append(cls)


def register_milestone_adapter(datasource_type: str, cls: type[MilestoneAdapter]) -> None:
    MILESTONE_ADAPTER_REGISTRY[datasource_type].append(cls)


def adapter_classes_for(datasource_type: str) -> list[type[DataSourceAdapter]]:
    return list(ADAPTER_REGISTRY.get(datasource_type, []))


def work_adapter_classes_for(datasource_type: str) -> list[type[WorkItemAdapter]]:
    return list(WORK_ADAPTER_REGISTRY.get(datasource_type, []))


def milestone_adapter_classes_for(datasource_type: str) -> list[type[MilestoneAdapter]]:
    return list(MILESTONE_ADAPTER_REGISTRY.get(datasource_type, []))
