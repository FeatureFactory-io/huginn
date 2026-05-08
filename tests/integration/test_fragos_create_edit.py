"""FRAGO CREATE + EDIT integration tests (ACT6-FRAGO-03)."""

import pytest
from django.test import Client
from django.urls import reverse

from sitrep.models import Frago
from tests.factories import FragoFactory, ProjectFactory


@pytest.mark.django_db
def test_fragos_create_redirects_and_persists(commander_client: Client) -> None:
    project = ProjectFactory(slug="create-fr")
    url = reverse("fragos-create") + f"?project={project.slug}"
    resp = commander_client.post(
        url,
        {
            "project": project.slug,
            "title": "New Order",
            "body_md": "## Standing change",
            "affects": "",
            "affected_variable": "",
            "effective_from": "",
            "effective_to": "",
        },
    )
    assert resp.status_code == 302
    assert Frago.objects.filter(project=project, title="New Order").exists()


@pytest.mark.django_db
def test_fragos_edit_updates(commander_client: Client) -> None:
    project = ProjectFactory(slug="edit-fr")
    fr = FragoFactory(project=project, title="Old Title")
    url = reverse("fragos-edit", args=[fr.pk])
    resp = commander_client.post(
        url,
        {
            "title": "Renamed",
            "body_md": fr.body_md,
            "affects": "narrative",
            "affected_variable": "",
            "effective_from": "",
            "effective_to": "",
        },
    )
    assert resp.status_code == 302
    fr.refresh_from_db()
    assert fr.title == "Renamed"
