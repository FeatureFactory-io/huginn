"""Situational Awareness VIEW integration tests (ACT12-SA-02 / snapshot)."""

import pytest
from django.test import Client
from django.urls import reverse

from tests.factories import SituationalAwarenessFactory, SituationalAwarenessVersionFactory


@pytest.mark.django_db
def test_situational_awareness_view_renders(commander_client: Client) -> None:
    url = reverse("sitawareness-view")
    resp = commander_client.get(url)
    assert resp.status_code == 200
    assert "Situational Awareness" in resp.content.decode()


@pytest.mark.django_db
def test_situational_awareness_snapshot_query(commander_client: Client) -> None:
    sa = SituationalAwarenessFactory()
    SituationalAwarenessVersionFactory(
        awareness=sa,
        version_number=1,
        standing_md="# First capsule",
        change_summary="init",
    )
    commander_client.post(
        reverse("sitawareness-edit") + "?tab=document",
        {
            "standing_md": "# Second capsule",
            "active_md": "",
            "change_summary": "iteration",
        },
    )
    url = reverse("sitawareness-view") + "?tab=document&v=1"
    body = commander_client.get(url).content.decode()
    assert "sitawareness-snapshot-banner" in body


@pytest.mark.django_db
def test_situational_awareness_compare_diff(commander_client: Client) -> None:
    sa = SituationalAwarenessFactory()
    SituationalAwarenessVersionFactory(
        awareness=sa,
        version_number=1,
        standing_md="alpha content line",
        change_summary="init",
    )
    commander_client.post(
        reverse("sitawareness-edit") + "?tab=document",
        {
            "standing_md": "beta replaced entirely",
            "active_md": "",
            "change_summary": "v2",
        },
    )
    url = reverse("sitawareness-view") + "?tab=document&v=1&compare=1"
    body = commander_client.get(url).content.decode()
    assert "sitawareness-compare-diff" in body
