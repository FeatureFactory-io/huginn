"""Unit tests for SitRep model."""

import pytest

from tests.factories import SitRepFactory


@pytest.mark.django_db
def test_variables_snapshot_defaults_to_empty_list():
    """variables_snapshot should default to an empty list."""
    sitrep = SitRepFactory()
    assert sitrep.variables_snapshot == []


@pytest.mark.django_db
def test_variables_snapshot_accepts_datapoints_list():
    """variables_snapshot can store and retrieve a list of datapoint dicts."""
    datapoints = [
        {
            "variable_name": "Throughput",
            "abbrev": "Tp",
            "y_axis_label": "merged MRs",
            "value": "15",
            "color": "green",
        },
        {
            "variable_name": "Cycle Time",
            "abbrev": "CT",
            "y_axis_label": "days",
            "value": "3.2",
            "color": "orange",
        },
    ]

    sitrep = SitRepFactory(variables_snapshot=datapoints)
    assert sitrep.variables_snapshot == datapoints
    assert len(sitrep.variables_snapshot) == 2
    assert sitrep.variables_snapshot[0]["variable_name"] == "Throughput"
    assert sitrep.variables_snapshot[1]["y_axis_label"] == "days"

    sitrep.refresh_from_db()
    assert sitrep.variables_snapshot == datapoints
