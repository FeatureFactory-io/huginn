"""Regression tests for promoted canonical base layout (design system shell)."""

from datetime import date

import pytest
from django.test import Client
from django.urls import reverse

from tests.factories import (
    FragoFactory,
    ProjectFactory,
    SituationalAwarenessFactory,
    SituationalAwarenessVersionFactory,
)


@pytest.mark.django_db
def test_authenticated_projects_list_includes_navbar_and_brand(commander_client):
    response = commander_client.get("/projects/")
    assert response.status_code == 200
    body = response.content.decode()
    assert 'data-testid="main-navbar"' in body
    assert 'data-testid="nav-brand"' in body
    assert "Huginn.jpeg" in body
    assert 'data-testid="nav-fragos"' in body
    assert 'data-testid="nav-sitawareness"' in body


@pytest.mark.django_db
def test_anonymous_root_shows_login_shell():
    client = Client()
    r = client.get("/")
    assert r.status_code == 200
    body = r.content.decode()
    assert 'data-testid="auth-login-loaded"' in body


@pytest.mark.django_db
def test_authenticated_root_shows_tactical_plot_with_real_project_card(commander_client):
    p = ProjectFactory(
        name="alpha-repo",
        display_name="Alpha Display",
        source_path="group/alpha",
    )
    r = commander_client.get("/")
    assert r.status_code == 200
    body = r.content.decode()
    assert 'data-testid="tactical-plot-loaded"' in body
    assert 'data-testid="tactical-plot-page-title"' in body
    assert f'data-testid="dashboard-project-card-{p.pk}"' in body
    assert 'data-testid="dashboard-card-' + str(p.pk) + '-name"' in body
    assert "Alpha Display" in body
    assert "group/alpha" in body
    assert 'data-testid="dashboard-card-' + str(p.pk) + '-source-gitlab"' in body


@pytest.mark.django_db
def test_authenticated_root_post_returns_405(commander_client):
    r = commander_client.post(reverse("auth-login"), {})
    assert r.status_code == 405


@pytest.mark.django_db
def test_plot_nav_is_active_on_root(commander_client):
    r = commander_client.get("/")
    assert r.status_code == 200
    body = r.content.decode()
    idx = body.find('data-testid="nav-plot"')
    assert idx != -1
    assert "nav-link active" in body[max(0, idx - 120) : idx]


@pytest.mark.django_db
def test_tactical_plot_rails_use_workspace_sa_and_fragos(commander_client):
    sa = SituationalAwarenessFactory()
    SituationalAwarenessVersionFactory(
        awareness=sa,
        version_number=1,
        standing_md="Mimir integration paused for the sprint.",
        active_md="**Outage** ongoing until next sprint.",
        change_summary="seed",
    )
    p = ProjectFactory(display_name="Acme API", name="acme-api", slug="acme-api")
    fr = FragoFactory(
        project=p,
        title="No deploys on Fridays",
        body_md="**Holiday** freeze — no merges.",
        effective_from=date(2026, 5, 1),
        effective_to=date(2026, 5, 31),
        enabled=True,
    )
    r = commander_client.get("/")
    assert r.status_code == 200
    body = r.content.decode()
    assert 'data-testid="dashboard-rail-sitaware-disposition-list"' in body
    assert "Mimir integration paused for the sprint." in body
    assert 'data-testid="dashboard-rail-sitaware-list"' in body
    assert "Outage" in body
    assert "ongoing until next sprint." in body
    assert f'data-testid="dashboard-rail-frago-body-{fr.pk}"' in body
    assert "Holiday" in body
    assert "May 01, 2026" in body or "May 1, 2026" in body
    assert "No deploys on Fridays" in body
    assert "project: Acme API" in body
