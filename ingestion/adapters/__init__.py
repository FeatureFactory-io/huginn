"""Register :class:`DataSourceAdapter` implementations by :class:`~ingestion.models.DataSource.Type`."""

from __future__ import annotations

from collections import defaultdict

from ingestion.adapters.base import DataSourceAdapter

ADAPTER_REGISTRY: dict[str, list[type[DataSourceAdapter]]] = defaultdict(list)


def register_adapter(datasource_type: str, cls: type[DataSourceAdapter]) -> None:
    """Append an adapter class for a :class:`~ingestion.models.DataSource.Type` value (e.g. ``\"gitlab\"``)."""
    ADAPTER_REGISTRY[datasource_type].append(cls)


def adapter_classes_for(datasource_type: str) -> list[type[DataSourceAdapter]]:
    return list(ADAPTER_REGISTRY.get(datasource_type, []))
