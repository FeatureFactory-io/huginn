"""Situational Awareness EDIT integration tests (ACT12-SA-03)."""

import pytest
from django.test import Client
from django.urls import reverse

from tests.factories import ProjectFactory, SituationalAwarenessFactory, SituationalAwarenessVersionFactory


@pytest.mark.django_db
def test_situational_awareness_save_creates_version(commander_client: Client) -> None:
    project = ProjectFactory(slug="sa-edit-proj")
    sa = SituationalAwarenessFactory(project=project)
    SituationalAwarenessVersionFactory(
        awareness=sa,
        version_number=1,
        standing_md="first",
        change_summary="init",
    )
    url = reverse("sitawareness-edit") + f"?project={project.slug}&tab=document"
    resp = commander_client.post(
        url,
        {
            "standing_md": "## Updated standing",
            "active_md": "",
            "change_summary": "Iteration note",
        },
    )
    assert resp.status_code == 302
    assert sa.versions.count() == 2
    head = sa.versions.order_by("-version_number").first()
    assert head is not None
    assert "## Updated standing" in head.standing_md
    assert head.change_summary == "Iteration note"
