"""Situational Awareness VIEW integration tests (ACT12-SA-02)."""

import pytest
from django.test import Client
from django.urls import reverse

from tests.factories import ProjectFactory


@pytest.mark.django_db
def test_situational_awareness_view_renders(commander_client: Client) -> None:
    project = ProjectFactory(slug="sa-view-proj")
    url = reverse("sitawareness-view") + f"?project={project.slug}"
    resp = commander_client.get(url)
    assert resp.status_code == 200
    assert "Situational Awareness" in resp.content.decode()
