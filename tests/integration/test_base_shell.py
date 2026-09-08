"""Regression tests for promoted canonical base layout (design system shell)."""

from datetime import date, timedelta

import pytest
from django.test import Client
from django.urls import reverse

from tests.factories import (
    FragoFactory,
    ProjectFactory,
    SitRepFactory,
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
def test_anonymous_root_shows_marketing_landing():
    client = Client()
    r = client.get("/")
    assert r.status_code == 200
    body = r.content.decode()
    assert 'data-testid="landing-loaded"' in body
    assert 'data-testid="landing-hero"' in body
    assert 'data-testid="landing-features"' in body
    assert 'data-testid="navbar-login"' in body


@pytest.mark.django_db
def test_anonymous_root_hides_app_nav_items():
    """Anonymous landing shows only brand + Login button — no app nav items."""
    client = Client()
    r = client.get("/")
    body = r.content.decode()
    assert 'data-testid="nav-brand"' in body
    for testid in ("nav-plot", "nav-sitawareness", "nav-fragos", "nav-projects", "nav-datasources"):
        assert f'data-testid="{testid}"' not in body, f"app nav {testid!r} leaked to anonymous landing"


@pytest.mark.django_db
def test_authenticated_root_redirects_to_tactical_plot(commander_client):
    r = commander_client.get("/", follow=False)
    assert r.status_code == 302
    assert r.headers["Location"] == reverse("tactical-plot")


@pytest.mark.django_db
def test_tactical_plot_shows_real_project_card(commander_client):
    p = ProjectFactory(
        name="alpha-repo",
        display_name="Alpha Display",
        source_path="group/alpha",
    )
    r = commander_client.get(reverse("tactical-plot"))
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
def test_root_post_returns_405(commander_client):
    r = commander_client.post(reverse("home"), {})
    assert r.status_code == 405


@pytest.mark.django_db
def test_plot_nav_is_active_on_tactical_plot(commander_client):
    r = commander_client.get(reverse("tactical-plot"))
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
    # Rail query is date.today() inclusive; hardcoded May 2026 windows expire and flake CI.
    today = date.today()
    effective_from = today - timedelta(days=7)
    effective_to = today + timedelta(days=7)
    fr = FragoFactory(
        project=p,
        title="No deploys on Fridays",
        body_md="**Holiday** freeze — no merges.",
        effective_from=effective_from,
        effective_to=effective_to,
        enabled=True,
    )
    r = commander_client.get(reverse("tactical-plot"))
    assert r.status_code == 200
    body = r.content.decode()
    assert 'data-testid="dashboard-rail-sitaware-disposition-list"' in body
    assert "Mimir integration paused for the sprint." in body
    assert 'data-testid="dashboard-rail-sitaware-list"' in body
    assert "Outage" in body
    assert "ongoing until next sprint." in body
    assert f'data-testid="dashboard-rail-frago-body-{fr.pk}"' in body
    assert "Holiday" in body
    assert effective_from.strftime("%b %d, %Y") in body
    assert "No deploys on Fridays" in body
    assert "project: Acme API" in body


@pytest.mark.django_db
def test_tactical_plot_project_card_layout_description_then_dots_then_sitrep(commander_client):
    p = ProjectFactory(
        name="huginn",
        display_name="huginn",
        description="Human-AI command composite to manage projects.",
        source_path="dp2580/huginn",
    )
    sitrep = SitRepFactory(project=p, headline="GREEN — delivery pace steady")
    r = commander_client.get(reverse("tactical-plot"))
    assert r.status_code == 200
    body = r.content.decode()

    desc_idx = body.index('data-testid="dashboard-card-' + str(p.pk) + '-gitlab-description"')
    vars_idx = body.index('data-testid="dashboard-card-' + str(p.pk) + '-variables"')
    sitrep_idx = body.index('data-testid="dashboard-card-' + str(p.pk) + '-sitrep-link"')
    assert desc_idx < vars_idx < sitrep_idx

    assert "Human-AI command composite to manage projects." in body
    assert "GREEN — delivery pace steady" in body
    assert reverse("sitrep-view", kwargs={"project_pk": p.pk, "pk": sitrep.pk}) in body
