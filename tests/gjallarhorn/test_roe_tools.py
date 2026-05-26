"""Unit tests for get_roe_variables MCP tool."""

import pytest

from gjallarhorn.mcp_tools.roe_tools import get_roe_variables
from tests.factories import (
    ProjectFactory,
    RulesOfEngagementFactory,
    RulesOfEngagementVariableFactory,
    RulesOfEngagementVersionFactory,
)


@pytest.mark.django_db
def test_returns_variables_in_sort_order():
    """get_roe_variables returns variables ordered by sort_order."""
    roe = RulesOfEngagementFactory()
    version = RulesOfEngagementVersionFactory(roe=roe, version_number=1)
    RulesOfEngagementVariableFactory(roe_version=version, sort_order=2, name="Second", abbrev="S2")
    RulesOfEngagementVariableFactory(roe_version=version, sort_order=1, name="First", abbrev="S1")

    project = ProjectFactory(assigned_roe=roe)

    variables = get_roe_variables(project.pk)

    assert variables is not None
    assert len(variables) == 2
    assert variables[0]["name"] == "First"
    assert variables[1]["name"] == "Second"


@pytest.mark.django_db
def test_returns_none_when_no_roe():
    """get_roe_variables returns None when project has no assigned RoE."""
    project = ProjectFactory(assigned_roe=None)

    variables = get_roe_variables(project.pk)

    assert variables is None


@pytest.mark.django_db
def test_returns_none_when_no_variables():
    """get_roe_variables returns None when RoE has no variables."""
    roe = RulesOfEngagementFactory()
    RulesOfEngagementVersionFactory(roe=roe, version_number=1)

    project = ProjectFactory(assigned_roe=roe)

    variables = get_roe_variables(project.pk)

    assert variables is None


@pytest.mark.django_db
def test_each_variable_dict_has_required_keys():
    """Each variable dict contains all required keys."""
    roe = RulesOfEngagementFactory()
    version = RulesOfEngagementVersionFactory(roe=roe)
    RulesOfEngagementVariableFactory(
        roe_version=version,
        name="Throughput",
        abbrev="Tp",
        y_axis_label="merged MRs",
        calculating="Count merged MRs",
        interpreting="Green if > 10",
    )

    project = ProjectFactory(assigned_roe=roe)

    variables = get_roe_variables(project.pk)

    assert variables is not None
    assert len(variables) == 1

    var = variables[0]
    assert "name" in var
    assert "abbrev" in var
    assert "y_axis_label" in var
    assert "calculating" in var
    assert "interpreting" in var

    assert var["name"] == "Throughput"
    assert var["abbrev"] == "Tp"
    assert var["y_axis_label"] == "merged MRs"
    assert var["calculating"] == "Count merged MRs"
    assert var["interpreting"] == "Green if > 10"
