"""Imported project persists GitLab catalog description."""

from unittest.mock import patch

import pytest
from django.urls import reverse

from ingestion.models import DataSource, Project
from tests.integration.gitlab_test_mocks import gitlab_catalog_mocks


def _csrf_token(client) -> str:
    return client.cookies["csrftoken"].value


@pytest.mark.django_db
@patch("ingestion.integrations.gitlab_client.urlopen")
def test_projects_import_persists_description(mock_urlopen, commander_client, db):
    project_json = [
        {
            "id": 99,
            "name": "DescProj",
            "path_with_namespace": "acme/desc-proj",
            "description": "hello from gitlab",
            "web_url": "https://gitlab.example.com/acme/desc-proj",
            "last_activity_at": None,
        }
    ]
    mock_urlopen.side_effect = gitlab_catalog_mocks(project_json)

    ds = DataSource.objects.create(
        name="gitlab-desc",
        datasource_type=DataSource.Type.GITLAB,
        base_url="https://gitlab.example.com/",
        status=DataSource.Status.CONNECTED,
        encrypted_token_ciphertext="glpat-test",
    )

    commander_client.get(reverse("projects-import"))
    commander_client.post(
        reverse("projects-import"),
        {
            "csrfmiddlewaretoken": _csrf_token(commander_client),
            "action": "refresh-catalog",
            "datasource_id": str(ds.pk),
        },
    )
    commander_client.post(
        reverse("projects-import"),
        {
            "csrfmiddlewaretoken": _csrf_token(commander_client),
            "action": "import",
            "datasource_id": str(ds.pk),
            "remote_keys": ["99"],
        },
    )
    proj = Project.objects.get(datasource=ds, external_project_id=99)
    assert proj.description == "hello from gitlab"
