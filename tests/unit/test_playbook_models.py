"""Playbook domain models."""

import pytest
from django.db import IntegrityError

from playbooks.models import PlaybookVariable
from tests.factories import (
    PlaybookFactory,
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


def test_playbook_variable_has_no_dimensions_field() -> None:
    assert not hasattr(PlaybookVariable, "dimensions")


def test_playbook_table_does_not_exist() -> None:
    import playbooks.models as pm

    assert not hasattr(pm, "PlaybookTable")
