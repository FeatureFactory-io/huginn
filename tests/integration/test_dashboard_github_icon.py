"""Tactical Plot GitHub datasource icon."""

import pytest
from django.urls import reverse

from ingestion.models import DataSource
from tests.factories import DataSourceFactory, ProjectFactory


@pytest.mark.django_db
def test_dashboard_github_project_shows_github_icon(commander_client) -> None:
    ds = DataSourceFactory(datasource_type=DataSource.Type.GITHUB, base_url="https://api.github.com")
    ProjectFactory(datasource=ds, name="widget", slug="widget-gh", source_path="acme/widget")
    r = commander_client.get(reverse("tactical-plot"))
    assert r.status_code == 200
    assert "simpleicons.org/github" in r.content.decode()
