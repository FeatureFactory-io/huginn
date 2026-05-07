"""FRAGO VIEW + REVOKE integration tests (ACT6-FRAGO-04)."""

import pytest
from django.test import Client
from django.urls import reverse

from tests.factories import FragoFactory, ProjectFactory


@pytest.mark.django_db
def test_fragos_detail_renders(commander_client: Client) -> None:
    project = ProjectFactory(slug="view-fr")
    fr = FragoFactory(project=project, title="Alpha Directive", body_md="# Hello")
    url = reverse("fragos-detail", args=[fr.pk])
    resp = commander_client.get(url)
    assert resp.status_code == 200
    body = resp.content.decode()
    assert "Alpha Directive" in body


@pytest.mark.django_db
def test_fragos_revoke_posts(commander_client: Client) -> None:
    project = ProjectFactory(slug="rev-fr")
    fr = FragoFactory(project=project)
    url = reverse("fragos-revoke", args=[fr.pk])
    resp = commander_client.post(url, {})
    assert resp.status_code == 302
    fr.refresh_from_db()
    assert fr.revoked_at is not None
    assert fr.enabled is False
