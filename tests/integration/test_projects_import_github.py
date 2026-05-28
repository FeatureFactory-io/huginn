"""GitHub project import integration tests."""

from unittest.mock import patch

import pytest
from django.urls import reverse

from ingestion.models import DataSource, Project
from tests.integration.github_test_mocks import github_catalog_urlopen_side_effect


def _csrf(client) -> str:
    return client.cookies["csrftoken"].value


@pytest.mark.django_db
@patch("ingestion.integrations.github_client.urlopen")
def test_github_import_catalog_and_persist(mock_urlopen, commander_client) -> None:
    ds = DataSource.objects.create(
        name="company-github",
        datasource_type=DataSource.Type.GITHUB,
        base_url="https://api.github.com",
        encrypted_token_ciphertext="ghp-x",
        status=DataSource.Status.CONNECTED,
        connected_user="octocat",
    )
    repo_rows = [
        {
            "id": 9001,
            "name": "widget",
            "full_name": "acme/widget",
            "description": "Core API",
            "html_url": "https://github.com/acme/widget",
            "updated_at": "2026-05-06T10:00:00Z",
        }
    ]
    mock_urlopen.side_effect = github_catalog_urlopen_side_effect(repo_rows)

    commander_client.get(reverse("projects-import"))
    commander_client.post(
        reverse("projects-import"),
        {
            "csrfmiddlewaretoken": _csrf(commander_client),
            "action": "refresh-catalog",
            "datasource_id": str(ds.pk),
        },
    )
    r = commander_client.post(
        reverse("projects-import"),
        {
            "csrfmiddlewaretoken": _csrf(commander_client),
            "action": "import",
            "datasource_id": str(ds.pk),
            "remote_keys": ["9001"],
        },
    )
    assert r.status_code == 302
    proj = Project.objects.get(datasource=ds, external_project_id=9001)
    assert proj.source_path == "acme/widget"
    assert proj.sync_state in (Project.SyncState.INITIAL_SYNC_QUEUED, Project.SyncState.ACTIVE)
