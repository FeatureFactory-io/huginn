"""Increment and contributor data transfer objects for ingestion adapters."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Protocol, runtime_checkable


class IncrementKind:
    """Discriminator stored on :class:`~ingestion.models.Increment`."""

    COMMIT = "commit"


@dataclass(frozen=True)
class ContributorDTO:
    """Author identity from a source system prior to ORM upsert."""

    source: str
    email: str
    name: str = ""
    handle: str | None = None


@runtime_checkable
class IncrementDTO(Protocol):
    """Structural type for adapter-produced increments (duck typing + isinstance checks)."""

    kind: str
    external_id: str
    occurred_at: datetime
    contributor: ContributorDTO
    summary: str
    payload: dict[str, Any]

    def stable_key(self) -> str:
        """Return a unique key for idempotent upsert (scoped by project + kind in the engine)."""


@dataclass(frozen=True)
class CommitIncrementDTO:
    """Git commit as an Increment."""

    external_id: str
    occurred_at: datetime
    contributor: ContributorDTO
    summary: str
    payload: dict[str, Any] = field(default_factory=dict)

    @property
    def kind(self) -> str:
        return IncrementKind.COMMIT

    def stable_key(self) -> str:
        return f"commit:{self.external_id}"


def assert_increment_dto(dto: IncrementDTO) -> IncrementDTO:
    """Narrow type for callers after isinstance(dto, IncrementDTO)."""
    return dto
