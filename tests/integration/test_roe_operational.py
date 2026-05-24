"""Operational Rules of Engagement UI smoke tests (Act 3)."""

import pytest
from django.urls import reverse

from roe.models import RulesOfEngagement
from roe.seed_constants import FEATUREFACTORY_ROE_SLUG


def _csrf(client):
    return client.cookies["csrftoken"].value


@pytest.mark.django_db
def test_featurefactory_seed_roe_exists() -> None:
    assert RulesOfEngagement.objects.filter(slug=FEATUREFACTORY_ROE_SLUG).exists()


@pytest.mark.django_db
def test_roe_list_renders(commander_client) -> None:
    r = commander_client.get(reverse("roe-list"))
    assert r.status_code == 200
    body = r.content.decode()
    assert "Rules of Engagement" in body or "roe" in body.lower()


@pytest.mark.django_db
def test_roe_create_minimal_redirects_to_detail(commander_client) -> None:
    commander_client.get(reverse("roe-create"))
    r = commander_client.post(
        reverse("roe-create"),
        {
            "csrfmiddlewaretoken": _csrf(commander_client),
            "name": "Integration Test RoE",
            "description": "via pytest",
            "workflow_md": "# Workflow\n\nHello.",
        },
        follow=False,
    )
    assert r.status_code == 302
    roe = RulesOfEngagement.objects.get(name="Integration Test RoE")
    loc = r.headers.get("Location") or ""
    assert loc.endswith(reverse("roe-detail", args=[roe.pk]))
