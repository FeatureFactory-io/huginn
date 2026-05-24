"""RulesOfEngagement domain models."""

import pytest
from django.db import IntegrityError

from roe.models import RulesOfEngagementVariable
from tests.factories import (
    RulesOfEngagementFactory,
    RulesOfEngagementVariableFactory,
    RulesOfEngagementVersionFactory,
)


@pytest.mark.django_db
def test_roe_version_unique_per_roe() -> None:
    roe = RulesOfEngagementFactory()
    RulesOfEngagementVersionFactory(roe=roe, version_number=1)
    with pytest.raises(IntegrityError):
        RulesOfEngagementVersionFactory(roe=roe, version_number=1)


@pytest.mark.django_db
def test_variables_respect_sort_order() -> None:
    roe = RulesOfEngagementFactory()
    ver = RulesOfEngagementVersionFactory(roe=roe, version_number=1)
    RulesOfEngagementVariableFactory(roe_version=ver, sort_order=1, name="Second")
    RulesOfEngagementVariableFactory(roe_version=ver, sort_order=0, name="First")
    assert [v.name for v in ver.variables.all()] == ["First", "Second"]


def test_roe_variable_has_no_dimensions_field() -> None:
    assert not hasattr(RulesOfEngagementVariable, "dimensions")


def test_roe_table_does_not_exist() -> None:
    import roe.models as rm

    assert not hasattr(rm, "RulesOfEngagementTable")
