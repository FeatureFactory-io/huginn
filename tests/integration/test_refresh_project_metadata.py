"""On-demand GitLab metadata refresh."""

import json
from unittest.mock import MagicMock, patch

import pytest

from ingestion.integrations.gitlab_client import GitlabClient
from ingestion.services.project_metadata import refresh_project_metadata
from tests.factories import ProjectFactory


@pytest.mark.django_db
@patch("ingestion.integrations.gitlab_client.urlopen")
def test_refresh_project_metadata_updates_description(mock_urlopen, db):
    p = ProjectFactory(
        datasource__encrypted_token_ciphertext="glpat-x",
        gitlab_project_id=12,
        description="old",
        name="stay",
        source_path="grp/old",
        source_url="https://gitlab.example.com/g/old",
    )
    body = {
        "id": 12,
        "name": "new-name",
        "description": "from-api",
        "web_url": "https://gitlab.example.com/grp/new-path",
        "path_with_namespace": "grp/new-path",
    }
    cm = MagicMock()
    enter = cm.__enter__.return_value
    enter.read.return_value = json.dumps(body).encode()
    mock_urlopen.return_value = cm

    refresh_project_metadata(p)

    p.refresh_from_db()
    assert p.description == "from-api"
    assert p.name == "new-name"
    assert p.source_path == "grp/new-path"
    assert "new-path" in p.source_url


@pytest.mark.django_db
@patch("ingestion.services.project_metadata.logger")
@patch.object(GitlabClient, "get_project", side_effect=ConnectionError("simulated-unreachable-gitlab"))
def test_refresh_project_metadata_handles_connection_error(_mock_gp, mock_log, db):
    p = ProjectFactory(
        datasource__encrypted_token_ciphertext="glpat-x",
        gitlab_project_id=9,
        description="unchanged",
    )

    refresh_project_metadata(p)

    p.refresh_from_db()
    assert p.description == "unchanged"
    assert mock_log.warning.call_count >= 1
    fmt, project_id, reason = mock_log.warning.call_args[0]
    assert "project metadata refresh skipped" in fmt
