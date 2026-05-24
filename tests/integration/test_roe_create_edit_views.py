"""RoE create/edit UI — strip Tables and Dimensions (#50)."""

import pytest
from django.urls import reverse

from roe.models import RulesOfEngagement, RulesOfEngagementVariable
from roe.seed_constants import FEATUREFACTORY_ROE_SLUG


def _csrf(client):
    return client.cookies["csrftoken"].value


@pytest.mark.django_db
def test_create_form_has_three_regions_no_tables_section(commander_client) -> None:
    r = commander_client.get(reverse("roe-create"))
    assert r.status_code == 200
    body = r.content.decode()
    assert "Metadata" in body
    assert "Workflow" in body
    assert "Variables" in body
    assert 'data-testid="roe-tables-table"' not in body
    assert '<span class="badge bg-secondary me-2">4</span>' not in body


@pytest.mark.django_db
def test_create_form_variables_table_has_no_dimensions_column(commander_client) -> None:
    r = commander_client.get(reverse("roe-create"))
    assert r.status_code == 200
    assert '<th scope="col">Dimensions</th>' not in r.content.decode()


@pytest.mark.django_db
def test_create_form_no_catalog_drift_banner(commander_client) -> None:
    r = commander_client.get(reverse("roe-create"))
    assert r.status_code == 200
    assert 'data-testid="roe-catalog-drift-banner"' not in r.content.decode()


@pytest.mark.django_db
def test_create_post_saves_variables(commander_client) -> None:
    commander_client.get(reverse("roe-create"))
    r = commander_client.post(
        reverse("roe-create"),
        {
            "csrfmiddlewaretoken": _csrf(commander_client),
            "name": "Integration Variables RoE",
            "description": "test",
            "workflow_md": "# Hello",
            "var_0_name": "Commits today",
            "var_0_abbrev": "CMT_T",
            "var_0_calculating": "count",
            "var_0_interpreting": "green",
            "var_0_hover": "hover text",
        },
        follow=False,
    )
    assert r.status_code == 302
    roe = RulesOfEngagementVariable.objects.get(name="Commits today").roe_version.roe
    assert roe.name == "Integration Variables RoE"


@pytest.mark.django_db
def test_edit_form_no_catalog_drift_banner(commander_client) -> None:
    roe = RulesOfEngagement.objects.get(slug=FEATUREFACTORY_ROE_SLUG)
    r = commander_client.get(reverse("roe-edit", args=[roe.pk]))
    assert r.status_code == 200
    assert 'data-testid="roe-catalog-drift-banner"' not in r.content.decode()


@pytest.mark.django_db
def test_edit_form_pre_populates_variable_names(commander_client) -> None:
    roe = RulesOfEngagement.objects.get(slug=FEATUREFACTORY_ROE_SLUG)
    ver = roe.versions.order_by("-version_number").first()
    assert ver is not None
    first_var = ver.variables.order_by("sort_order").first()
    assert first_var is not None
    r = commander_client.get(reverse("roe-edit", args=[roe.pk]))
    assert r.status_code == 200
    assert first_var.name in r.content.decode()
