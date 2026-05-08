"""Situational Awareness VIEW integration tests (ACT12-SA-02 / SA workspace / snapshot)."""

import pytest
from django.test import Client
from django.urls import reverse

from ingestion.models import Project
from tests.factories import (
    ProjectFactory,
    SituationalAwarenessFactory,
    SituationalAwarenessVersionFactory,
)


@pytest.mark.django_db
def test_situational_awareness_view_renders(commander_client: Client) -> None:
    project = ProjectFactory(slug="sa-view-proj")
    url = reverse("sitawareness-view") + f"?project={project.slug}"
    resp = commander_client.get(url)
    assert resp.status_code == 200
    assert "Situational Awareness" in resp.content.decode()


@pytest.mark.django_db
def test_situational_awareness_workspace_hub(commander_client: Client) -> None:
    ProjectFactory(slug="sa-hub-a")
    resp = commander_client.get(reverse("sitawareness-view"))
    assert resp.status_code == 200
    body = resp.content.decode()
    assert "sitawareness-workspace-heading" in body
    assert "sa-hub-a" in body


@pytest.mark.django_db
def test_situational_awareness_snapshot_query(commander_client: Client) -> None:
    project = ProjectFactory(slug="sa-snap")
    sa = SituationalAwarenessFactory(project=project)
    SituationalAwarenessVersionFactory(
        awareness=sa,
        version_number=1,
        standing_md="# First capsule",
        change_summary="init",
    )
    commander_client.post(
        reverse("sitawareness-edit") + f"?project={project.slug}&tab=document",
        {
            "standing_md": "# Second capsule",
            "active_md": "",
            "change_summary": "iteration",
        },
    )
    url = reverse("sitawareness-view") + f"?project={project.slug}&tab=document&v=1"
    body = commander_client.get(url).content.decode()
    assert "sitawareness-snapshot-banner" in body


@pytest.mark.django_db
def test_situational_awareness_compare_diff(commander_client: Client) -> None:
    project = ProjectFactory(slug="sa-diff")
    sa = SituationalAwarenessFactory(project=project)
    SituationalAwarenessVersionFactory(
        awareness=sa,
        version_number=1,
        standing_md="alpha content line",
        change_summary="init",
    )
    commander_client.post(
        reverse("sitawareness-edit") + f"?project={project.slug}&tab=document",
        {
            "standing_md": "beta replaced entirely",
            "active_md": "",
            "change_summary": "v2",
        },
    )
    url = reverse("sitawareness-view") + f"?project={project.slug}&tab=document&v=1&compare=1"
    body = commander_client.get(url).content.decode()
    assert "sitawareness-compare-diff" in body


@pytest.mark.django_db
def test_archived_project_blocks_sa_edit(commander_client: Client) -> None:
    project = ProjectFactory(slug="sa-arch", status=Project.Status.ARCHIVED)
    resp = commander_client.get(
        reverse("sitawareness-edit") + f"?project={project.slug}",
        follow=False,
    )
    assert resp.status_code == 302
