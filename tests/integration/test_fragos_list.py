"""FRAGO LIST+FIND integration tests (ACT6-FRAGO-02 / ACT6-FRAGO-05)."""

import pytest
from django.test import Client
from django.urls import reverse

from tests.factories import (
    FragoFactory,
    PlaybookFactory,
    PlaybookVariableFactory,
    PlaybookVersionFactory,
    ProjectFactory,
)


@pytest.mark.django_db
def test_fragos_list_requires_login(client: Client) -> None:
    ProjectFactory(slug="need-login")
    url = reverse("fragos-list") + "?project=need-login"
    resp = client.get(url)
    assert resp.status_code == 302


@pytest.mark.django_db
def test_fragos_list_all_projects_without_query(commander_client: Client) -> None:
    """Unauthenticated-style guard already covered; logged-in user may open global list."""
    p1 = ProjectFactory(slug="acme-fragos")
    FragoFactory(project=p1, title="Mission Alpha")
    url = reverse("fragos-list")
    resp = commander_client.get(url)
    assert resp.status_code == 200
    assert "Mission Alpha" in resp.content.decode()


@pytest.mark.django_db
def test_fragos_list_renders(commander_client: Client) -> None:
    project = ProjectFactory(slug="acme-fragos")
    FragoFactory(project=project, title="Mission Alpha")
    url = reverse("fragos-list") + "?project=acme-fragos"
    resp = commander_client.get(url)
    assert resp.status_code == 200
    assert "Mission Alpha" in resp.content.decode()


@pytest.mark.django_db
def test_fragos_filter_affects_narrative(commander_client: Client) -> None:
    pb = PlaybookFactory()
    ver = PlaybookVersionFactory(playbook=pb, version_number=1)
    var = PlaybookVariableFactory(playbook_version=ver, abbrev="ABC", name="Alpha")
    project = ProjectFactory(slug="aff-n")
    project.assigned_playbook = pb
    project.save(update_fields=["assigned_playbook"])
    FragoFactory(project=project, title="Global narrative", affected_variable=None)
    FragoFactory(project=project, title="Scope ABC", affected_variable=var)
    url = reverse("fragos-list") + f"?project={project.slug}&affects=narrative"
    body = commander_client.get(url).content.decode()
    assert "Global narrative" in body
    assert "Scope ABC" not in body


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
