"""Unit tests for ui/services/roe_service.py."""

import pytest

from roe.models import RulesOfEngagementVariable
from tests.factories import RulesOfEngagementVariableFactory, RulesOfEngagementVersionFactory
from ui.services.roe_service import (
    append_roe_version,
    create_roe_with_version,
    editor_snapshot_from_version,
)


@pytest.mark.django_db
def test_editor_snapshot_from_none_returns_expected_shape() -> None:
    result = editor_snapshot_from_version(None)
    assert "variables" in result
    assert "tables" not in result
    assert result["variables"] == []


@pytest.mark.django_db
def test_editor_snapshot_from_version_no_dimensions() -> None:
    ver = RulesOfEngagementVersionFactory()
    RulesOfEngagementVariableFactory(roe_version=ver, name="Alpha", abbrev="A")
    result = editor_snapshot_from_version(ver)
    assert len(result["variables"]) == 1
    var = result["variables"][0]
    assert "dimensions" not in var
    assert var["name"] == "Alpha"
    assert var["abbrev"] == "A"


@pytest.mark.django_db
def test_create_roe_with_version_creates_variables() -> None:
    from tests.factories import UserFactory

    user = UserFactory()
    roe = create_roe_with_version(
        user=user,
        name="Test RoE",
        description="Test",
        workflow_md="# Hello",
        variables=[
            {
                "sort_order": 0,
                "name": "Throughput",
                "abbrev": "TP",
                "calculating": "count(x)",
                "interpreting": "higher is better",
                "hover": "tip",
            }
        ],
    )
    assert RulesOfEngagementVariable.objects.filter(roe_version__roe=roe, name="Throughput").exists()


@pytest.mark.django_db
def test_append_roe_version_increments_version_number() -> None:
    from tests.factories import UserFactory

    user = UserFactory()
    roe = create_roe_with_version(
        user=user,
        name="Append Test",
        description="",
        workflow_md="",
        variables=[],
    )
    ver2 = append_roe_version(
        roe=roe,
        user=user,
        change_summary="v2 changes",
        name="Append Test",
        description="",
        workflow_md="",
        variables=[],
    )
    assert ver2.version_number == 2
