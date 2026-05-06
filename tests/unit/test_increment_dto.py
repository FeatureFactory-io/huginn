"""DTO contract for ingestion."""

from datetime import UTC, datetime

import pytest

from ingestion.domain.increments import CommitIncrementDTO, ContributorDTO, IncrementDTO, IncrementKind
from tests.factories import ContributorDTOFactory


def test_commit_increment_stable_key() -> None:
    dto = CommitIncrementDTO(
        external_id="deadbeef",
        occurred_at=datetime.now(UTC),
        contributor=ContributorDTOFactory.build(),
        summary="fix: thing",
    )
    assert dto.stable_key() == "commit:deadbeef"
    assert dto.kind == IncrementKind.COMMIT


def test_commit_increment_is_increment_dto_protocol() -> None:
    dto = CommitIncrementDTO(
        external_id="a1",
        occurred_at=datetime.now(UTC),
        contributor=ContributorDTO("gitlab", "a@b.com", "A"),
        summary="x",
    )
    assert isinstance(dto, IncrementDTO)


def test_contributor_dto_frozen() -> None:
    c = ContributorDTO("gitlab", "e@e.com", "E")
    with pytest.raises(AttributeError):
        c.email = "other@e.com"  # type: ignore[misc]
