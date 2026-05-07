"""Operational Playbooks UI smoke tests (Act 3)."""

import pytest
from django.urls import reverse

from playbooks.models import Playbook
from playbooks.seed_constants import FEATUREFACTORY_PLAYBOOK_SLUG


def _csrf(client):
    return client.cookies["csrftoken"].value


@pytest.mark.django_db
def test_featurefactory_seed_playbook_exists() -> None:
    assert Playbook.objects.filter(slug=FEATUREFACTORY_PLAYBOOK_SLUG).exists()


@pytest.mark.django_db
def test_playbooks_list_renders(commander_client) -> None:
    r = commander_client.get(reverse("playbooks-list"))
    assert r.status_code == 200
    body = r.content.decode()
    assert "Playbooks" in body or "playbooks" in body.lower()


@pytest.mark.django_db
def test_playbook_create_minimal_redirects_to_detail(commander_client) -> None:
    commander_client.get(reverse("playbooks-create"))
    r = commander_client.post(
        reverse("playbooks-create"),
        {
            "csrfmiddlewaretoken": _csrf(commander_client),
            "name": "Integration Test PB",
            "description": "via pytest",
            "workflow_md": "# Workflow\n\nHello.",
        },
        follow=False,
    )
    assert r.status_code == 302
    pb = Playbook.objects.get(name="Integration Test PB")
    loc = r.headers.get("Location") or ""
    assert loc.endswith(reverse("playbooks-detail", args=[pb.pk]))
