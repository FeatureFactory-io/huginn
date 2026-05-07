"""Authoring-time catalog: entities and registered slicers (MVP subset)."""

from __future__ import annotations

from playbooks.models import PlaybookTable


def slicers_for_entity(entity: str) -> frozenset[str]:
    """Return slicer names valid for the given entity value (PlaybookTable.Entity)."""
    registry: dict[str, frozenset[str]] = {
        PlaybookTable.Entity.INCREMENT: frozenset(
            {"last_14d", "this_week", "last_30d", "today", "mine"},
        ),
        PlaybookTable.Entity.UNIT_OF_WORK: frozenset(
            {"open", "closed", "mine", "stale_7d", "priority_high"},
        ),
        PlaybookTable.Entity.MILESTONE: frozenset({"active", "closed"}),
        PlaybookTable.Entity.SPRINT: frozenset({"current", "planned"}),
        PlaybookTable.Entity.CONTRIBUTOR: frozenset({"active", "recent"}),
    }
    return registry.get(entity, frozenset())


def validate_table_row(*, entity: str, slicer: str) -> str | None:
    """Return a single human-readable error or None when valid."""
    valid_entities = {c.value for c in PlaybookTable.Entity}
    if entity not in valid_entities:
        return f"Unknown entity '{entity}'."
    allowed = slicers_for_entity(entity)
    if slicer not in allowed:
        return f"Slicer '{slicer}' is not registered for entity '{entity}'."
    return None


def scan_version_for_drift(playbook_version) -> list[str]:
    """Return drift messages for PlaybookTable rows (diagnostic only)."""
    errors: list[str] = []
    for row in playbook_version.tables.order_by("sort_order"):
        msg = validate_table_row(entity=row.entity, slicer=row.slicer)
        if msg:
            errors.append(f"Tables row {row.sort_order + 1}: {msg}")
    return errors
