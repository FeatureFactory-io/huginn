"""Playbook domain models."""

import pytest
from django.db import IntegrityError

from playbooks.models import PlaybookTable
from tests.factories import (
    PlaybookFactory,
    PlaybookTableFactory,
    PlaybookVariableFactory,
    PlaybookVersionFactory,
)


@pytest.mark.django_db
def test_playbook_version_unique_per_playbook() -> None:
    pb = PlaybookFactory()
    PlaybookVersionFactory(playbook=pb, version_number=1)
    with pytest.raises(IntegrityError):
        PlaybookVersionFactory(playbook=pb, version_number=1)


@pytest.mark.django_db
def test_variables_respect_sort_order() -> None:
    pb = PlaybookFactory()
    ver = PlaybookVersionFactory(playbook=pb, version_number=1)
    PlaybookVariableFactory(playbook_version=ver, sort_order=1, name="Second")
    PlaybookVariableFactory(playbook_version=ver, sort_order=0, name="First")
    assert [v.name for v in ver.variables.all()] == ["First", "Second"]


@pytest.mark.django_db
def test_tables_use_entity_choices() -> None:
    ver = PlaybookVersionFactory()
    row = PlaybookTableFactory(
        playbook_version=ver,
        sort_order=0,
        entity=PlaybookTable.Entity.INCREMENT,
        slicer="open",
    )
    row.refresh_from_db()
    assert row.entity == PlaybookTable.Entity.INCREMENT
