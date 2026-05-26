"""Unit tests for RulesOfEngagementVariable model."""

import pytest

from tests.factories import RulesOfEngagementVariableFactory


@pytest.mark.django_db
def test_y_axis_label_defaults_blank():
    """y_axis_label should default to blank string."""
    variable = RulesOfEngagementVariableFactory(name="Test Variable")
    assert variable.y_axis_label == ""


@pytest.mark.django_db
def test_y_axis_label_stored_and_retrieved():
    """y_axis_label can be set and retrieved correctly."""
    variable = RulesOfEngagementVariableFactory(name="Throughput", y_axis_label="merged MRs")
    assert variable.y_axis_label == "merged MRs"

    variable.refresh_from_db()
    assert variable.y_axis_label == "merged MRs"
