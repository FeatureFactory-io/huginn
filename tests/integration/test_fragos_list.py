"""FRAGO LIST+FIND integration tests (ACT6-FRAGO-02)."""

import pytest
from django.test import Client
from django.urls import reverse

from tests.factories import FragoFactory, ProjectFactory


@pytest.mark.django_db
def test_fragos_list_requires_login(client: Client) -> None:
    ProjectFactory(slug="need-login")
    url = reverse("fragos-list") + "?project=need-login"
    resp = client.get(url)
    assert resp.status_code == 302


@pytest.mark.django_db
def test_fragos_list_renders(commander_client: Client) -> None:
    project = ProjectFactory(slug="acme-fragos")
    FragoFactory(project=project, title="Mission Alpha")
    url = reverse("fragos-list") + "?project=acme-fragos"
    resp = commander_client.get(url)
    assert resp.status_code == 200
    assert "Mission Alpha" in resp.content.decode()


@pytest.mark.django_db
def test_fragos_toggle_posts(commander_client: Client) -> None:
    project = ProjectFactory(slug="toggle-fr")
    fr = FragoFactory(project=project, enabled=True)
    base = reverse("fragos-list") + f"?project={project.slug}"
    resp = commander_client.post(
        base,
        {"toggle_frago": "1", "frago_id": str(fr.pk)},
        follow=True,
    )
    assert resp.status_code == 200
    fr.refresh_from_db()
    assert fr.enabled is False
