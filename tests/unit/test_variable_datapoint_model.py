"""Unit tests for VariableDatapoint model."""

import pytest
from django.db import IntegrityError
from django.utils import timezone

from tests.factories import (
    RulesOfEngagementVariableFactory,
    SitRepFactory,
    VariableDatapointFactory,
)


@pytest.mark.django_db
def test_create_minimal():
    """Minimal VariableDatapoint can be created with required fields."""
    sitrep = SitRepFactory()
    now = timezone.now()

    datapoint = VariableDatapointFactory(
        sitrep=sitrep,
        variable_name="Test Variable",
        color="green",
        from_dt=now,
        to_dt=now,
        roe_variable=None,
    )

    assert datapoint.sitrep == sitrep
    assert datapoint.variable_name == "Test Variable"
    assert datapoint.color == "green"
    assert datapoint.from_dt == now
    assert datapoint.to_dt == now


@pytest.mark.django_db
def test_color_choices():
    """Only green, orange, red, grey colors are accepted."""
    valid_colors = ["green", "orange", "red", "grey"]

    for color in valid_colors:
        datapoint = VariableDatapointFactory(color=color)
        assert datapoint.color == color
        datapoint.full_clean()


@pytest.mark.django_db
def test_value_nullable():
    """value=None is valid for grey color (no data)."""
    datapoint = VariableDatapointFactory(value=None, color="grey")
    assert datapoint.value is None
    assert datapoint.color == "grey"

    datapoint.refresh_from_db()
    assert datapoint.value is None


@pytest.mark.django_db
def test_unique_sitrep_roe_variable():
    """Duplicate (sitrep, roe_variable) should raise IntegrityError."""
    sitrep = SitRepFactory()
    roe_var = RulesOfEngagementVariableFactory()

    VariableDatapointFactory(sitrep=sitrep, roe_variable=roe_var)

    with pytest.raises(IntegrityError):
        VariableDatapointFactory(sitrep=sitrep, roe_variable=roe_var)


@pytest.mark.django_db
def test_ordering_by_sort_order():
    """Datapoints are ordered by sitrep, then roe_variable__sort_order."""
    sitrep = SitRepFactory()
    var1 = RulesOfEngagementVariableFactory(sort_order=2)
    var2 = RulesOfEngagementVariableFactory(roe_version=var1.roe_version, sort_order=1)

    dp1 = VariableDatapointFactory(sitrep=sitrep, roe_variable=var1)
    dp2 = VariableDatapointFactory(sitrep=sitrep, roe_variable=var2)

    from sitrep.models import VariableDatapoint

    datapoints = list(VariableDatapoint.objects.filter(sitrep=sitrep))

    assert len(datapoints) == 2
    assert datapoints[0] == dp2
    assert datapoints[1] == dp1
