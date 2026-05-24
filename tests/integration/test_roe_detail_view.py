"""RoE detail UI — strip Tables panel and Validate (#51)."""

import pytest
from django.urls import reverse

from roe.models import RulesOfEngagement
from roe.seed_constants import FEATUREFACTORY_ROE_SLUG
from tests.factories import RulesOfEngagementFactory, RulesOfEngagementVersionFactory


def _csrf(client):
    return client.cookies["csrftoken"].value


@pytest.mark.django_db
def test_detail_no_validate_button(commander_client) -> None:
    roe = RulesOfEngagement.objects.get(slug=FEATUREFACTORY_ROE_SLUG)
    r = commander_client.get(reverse("roe-detail", args=[roe.pk]))
    assert r.status_code == 200
    assert 'data-testid="roe-validate-btn"' not in r.content.decode()


@pytest.mark.django_db
def test_detail_no_tables_section_heading(commander_client) -> None:
    roe = RulesOfEngagement.objects.get(slug=FEATUREFACTORY_ROE_SLUG)
    body = commander_client.get(reverse("roe-detail", args=[roe.pk])).content.decode()
    assert ">Tables</h2>" not in body


@pytest.mark.django_db
def test_detail_variables_no_dimensions_column(commander_client) -> None:
    roe = RulesOfEngagement.objects.get(slug=FEATUREFACTORY_ROE_SLUG)
    body = commander_client.get(reverse("roe-detail", args=[roe.pk])).content.decode()
    assert '<th scope="col">Dimensions</th>' not in body


@pytest.mark.django_db
def test_detail_variables_empty_state_copy(commander_client) -> None:
    roe = RulesOfEngagementFactory(name="Empty Vars RoE", slug="empty-vars-roe-test")
    RulesOfEngagementVersionFactory(roe=roe, version_number=1)
    body = commander_client.get(reverse("roe-detail", args=[roe.pk])).content.decode()
    assert "This Rules of Engagement has no Variables yet" in body


@pytest.mark.django_db
def test_detail_clone_and_edit_buttons_present(commander_client) -> None:
    roe = RulesOfEngagement.objects.get(slug=FEATUREFACTORY_ROE_SLUG)
    body = commander_client.get(reverse("roe-detail", args=[roe.pk])).content.decode()
    assert 'data-testid="roe-clone-btn"' in body
    assert 'data-testid="roe-edit-btn"' in body


@pytest.mark.django_db
def test_detail_post_redirects_to_detail(commander_client) -> None:
    roe = RulesOfEngagement.objects.get(slug=FEATUREFACTORY_ROE_SLUG)
    commander_client.get(reverse("roe-detail", args=[roe.pk]))
    r = commander_client.post(
        reverse("roe-detail", args=[roe.pk]),
        {"csrfmiddlewaretoken": _csrf(commander_client)},
        follow=False,
    )
    assert r.status_code == 302
    assert r.url == reverse("roe-detail", args=[roe.pk])
