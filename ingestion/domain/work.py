"""Canonical work-item DTOs for ingestion adapters (no Django imports)."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Any

from ingestion.domain.increments import ContributorDTO


@dataclass(frozen=True)
class MilestoneDTO:
    external_id: str
    title: str
    state: str
    updated_at: datetime
    due_date: date | None = None
    start_date: date | None = None
    payload: dict[str, Any] = field(default_factory=dict)

    def stable_key(self) -> str:
        return f"milestone:{self.external_id}"


@dataclass(frozen=True)
class UnitOfWorkDTO:
    kind: str
    external_id: str
    iid: int
    title: str
    state: str
    created_at: datetime
    updated_at: datetime
    milestone_external_id: str | None = None
    contributor: ContributorDTO | None = None
    labels: list[str] = field(default_factory=list)
    closed_at: datetime | None = None
    payload: dict[str, Any] = field(default_factory=dict)

    def stable_key(self) -> str:
        return f"{self.kind}:{self.external_id}"
