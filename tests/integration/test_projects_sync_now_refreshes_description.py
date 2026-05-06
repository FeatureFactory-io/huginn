"""Sync now refreshes GitLab-backed project.description before enqueue."""

from unittest.mock import MagicMock, patch

import pytest
from django.urls import reverse

from ingestion.models import DataSource, Project
from tests.integration.gitlab_test_mocks import gitlab_catalog_urlopen_side_effect


def _csrf(client) -> str:
    return client.cookies["csrftoken"].value


@pytest.mark.django_db
@patch("ui.services.projects_service.sync_project.delay")
@patch("ingestion.integrations.gitlab_client.urlopen")
def test_projects_sync_now_refreshes_description(mock_urlopen, mock_delay, commander_client):
    mock_delay.return_value = MagicMock()
    ds = DataSource.objects.create(
        name="gl-sync-meta",
        datasource_type=DataSource.Type.GITLAB,
        base_url="https://gitlab.example.com/",
        status=DataSource.Status.CONNECTED,
        encrypted_token_ciphertext="glpat-sync",
    )
    proj = Project.objects.create(
        datasource=ds,
        name="p",
        slug="sync-meta-proj",
        gitlab_project_id=77,
        source_path="a/b",
        source_url="https://gitlab.example.com/a/b",
        description="before",
        sync_state=Project.SyncState.ACTIVE,
    )

    detail_payload = {
        "id": 77,
        "name": "p",
        "description": "fresh-from-remote",
        "web_url": "https://gitlab.example.com/a/b",
        "path_with_namespace": "a/b",
    }
    mock_urlopen.side_effect = gitlab_catalog_urlopen_side_effect(
        [],
        single_project_by_id={77: detail_payload},
    )

    commander_client.get(reverse("projects-detail", args=[proj.pk]))
    commander_client.post(
        reverse("projects-sync-now", args=[proj.pk]),
        {"csrfmiddlewaretoken": _csrf(commander_client), "tab": "vitals"},
    )

    mock_delay.assert_called_once_with(proj.pk)
    proj.refresh_from_db()
    assert proj.description == "fresh-from-remote"


@pytest.mark.django_db
@patch("ui.services.projects_service.sync_project.delay")
def test_projects_sync_now_metadata_failure_does_not_break_sync(mock_delay, commander_client):
    mock_delay.return_value = MagicMock()
    ds = DataSource.objects.create(
        name="gl-sync-fail-meta",
        datasource_type=DataSource.Type.GITLAB,
        base_url="https://gitlab.example.com/",
        status=DataSource.Status.CONNECTED,
        encrypted_token_ciphertext="glpat-sync",
    )
    proj = Project.objects.create(
        datasource=ds,
        name="dead",
        slug="sync-meta-fail-proj",
        gitlab_project_id=88,
        description="sticky",
        sync_state=Project.SyncState.ACTIVE,
    )

    def boom(req, *_a, **_k):
        url = getattr(req, "full_url", str(req))
        if "/api/v4/projects/88" in url and "/repository/" not in url:
            raise ConnectionError("boom")
        msg = f"missing mock branch for URL: {url!r}"
        raise AssertionError(msg)

    commander_client.get(reverse("projects-detail", args=[proj.pk]))
    with patch("ingestion.integrations.gitlab_client.urlopen", side_effect=boom):
        commander_client.post(
            reverse("projects-sync-now", args=[proj.pk]),
            {"csrfmiddlewaretoken": _csrf(commander_client), "tab": "vitals"},
        )

    mock_delay.assert_called_once_with(proj.pk)
    proj.refresh_from_db()
    assert proj.description == "sticky"
