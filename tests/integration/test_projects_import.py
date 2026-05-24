"""Projects import flow (catalog + multi-select)."""

from unittest.mock import MagicMock, patch
from urllib.error import HTTPError

import pytest
from django.urls import reverse

from ingestion.models import DataSource, Project
from tests.factories import ProjectFactory
from tests.integration.gitlab_test_mocks import gitlab_catalog_mocks


def _csrf_token(client) -> str:
    return client.cookies["csrftoken"].value


@pytest.mark.django_db
def test_projects_import_screen_renders(commander_client):
    r = commander_client.get(reverse("projects-import"))
    assert r.status_code == 200
    assert "Import Projects from Data Source" in r.content.decode()


@pytest.mark.django_db
@patch("ingestion.integrations.gitlab_client.urlopen")
def test_projects_import_refresh_then_import(mock_urlopen, commander_client, db):
    project_json = [
        {
            "id": 42,
            "name": "Demo",
            "path_with_namespace": "acme/demo",
            "description": "Hi",
            "web_url": "https://gitlab.example.com/acme/demo",
            "last_activity_at": "2024-06-01T00:00:00Z",
        }
    ]
    mock_urlopen.side_effect = gitlab_catalog_mocks(project_json)

    ds = DataSource.objects.create(
        name="gitlab-a",
        datasource_type=DataSource.Type.GITLAB,
        base_url="https://gitlab.example.com/",
        status=DataSource.Status.CONNECTED,
        encrypted_token_ciphertext="glpat-test",
    )

    commander_client.get(reverse("projects-import"))
    refresh = commander_client.post(
        reverse("projects-import"),
        {
            "csrfmiddlewaretoken": _csrf_token(commander_client),
            "action": "refresh-catalog",
            "datasource_id": str(ds.pk),
        },
    )
    assert refresh.status_code == 302

    follow = commander_client.get(reverse("projects-import"))
    assert follow.status_code == 200
    assert "acme/demo" in follow.content.decode()

    imp = commander_client.post(
        reverse("projects-import"),
        {
            "csrfmiddlewaretoken": _csrf_token(commander_client),
            "action": "import",
            "datasource_id": str(ds.pk),
            "remote_keys": ["42"],
        },
    )
    assert imp.status_code == 302
    proj = Project.objects.get(datasource=ds, gitlab_project_id=42)
    assert proj.slug == "acme-demo"
    assert proj.sync_state == Project.SyncState.ACTIVE
    assert proj.source_path == "acme/demo"
    assert proj.source_url == "https://gitlab.example.com/acme/demo"
    assert proj.description == "Hi"


@pytest.mark.django_db
@patch("ingestion.integrations.gitlab_client.urlopen")
def test_import_post_banner_text(mock_urlopen, commander_client, db):
    project_json = [
        {
            "id": 10,
            "name": "One",
            "path_with_namespace": "acme/one",
            "description": "",
            "web_url": "https://gitlab.example.com/acme/one",
            "last_activity_at": None,
        },
        {
            "id": 11,
            "name": "Two",
            "path_with_namespace": "acme/two",
            "description": "",
            "web_url": "https://gitlab.example.com/acme/two",
            "last_activity_at": None,
        },
    ]
    mock_urlopen.side_effect = gitlab_catalog_mocks(project_json)

    ds = DataSource.objects.create(
        name="gitlab-a",
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

    r = commander_client.post(
        reverse("projects-import"),
        {
            "csrfmiddlewaretoken": _csrf_token(commander_client),
            "action": "import",
            "datasource_id": str(ds.pk),
            "remote_keys": ["10", "11"],
        },
        follow=True,
    )
    assert r.status_code == 200
    body = r.content.decode()
    expected = "2 projects imported. Sync started. Assign a Rules of Engagement to receive SitReps."
    assert expected in body


@pytest.mark.django_db
@patch("ingestion.integrations.gitlab_client.urlopen")
def test_import_09_sync_job_sets_active_state(mock_urlopen, commander_client, db):
    project_json = [
        {
            "id": 99,
            "name": "SyncMe",
            "path_with_namespace": "co/sync-me",
            "description": "",
            "web_url": "https://gitlab.example.com/co/sync-me",
            "last_activity_at": None,
        }
    ]
    mock_urlopen.side_effect = gitlab_catalog_mocks(project_json)

    ds = DataSource.objects.create(
        name="gitlab-a",
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
    proj = Project.objects.get(datasource=ds, gitlab_project_id=99)
    assert proj.sync_state == Project.SyncState.ACTIVE


@pytest.mark.django_db
@patch("ingestion.integrations.gitlab_client.urlopen")
def test_projects_import_catalog_gitlab_error_message(mock_urlopen, commander_client, db):
    def _side_effect(req, timeout=10):
        url = getattr(req, "full_url", str(req))
        cm = MagicMock()
        enter = cm.__enter__.return_value
        if "/api/v4/user" in url:
            enter.read.return_value = b'{"username":"u"}'
            enter.headers = {}
            return cm
        raise HTTPError(url, 503, "Service Unavailable", hdrs=None, fp=None)

    mock_urlopen.side_effect = _side_effect

    ds = DataSource.objects.create(
        name="gitlab-a",
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
    r = commander_client.get(reverse("projects-import"))
    body = r.content.decode()
    assert "projects-import-catalog-error" in body or "503" in body


@pytest.mark.django_db
@patch("ingestion.integrations.gitlab_client.urlopen")
def test_projects_import_skips_already_imported_row(mock_urlopen, commander_client, db):
    project_json = [
        {
            "id": 7,
            "name": "Ex",
            "path_with_namespace": "g/ex",
            "description": "",
            "web_url": "https://gitlab.example.com/g/ex",
            "last_activity_at": None,
        }
    ]
    mock_urlopen.side_effect = gitlab_catalog_mocks(project_json)

    ds = DataSource.objects.create(
        name="gitlab-a",
        datasource_type=DataSource.Type.GITLAB,
        base_url="https://gitlab.example.com/",
        status=DataSource.Status.CONNECTED,
        encrypted_token_ciphertext="glpat-test",
    )
    ProjectFactory(
        datasource=ds,
        name="Ex",
        slug="g-ex",
        source_path="g/ex",
        gitlab_project_id=7,
        sync_state=Project.SyncState.ACTIVE,
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
    r = commander_client.get(reverse("projects-import"))
    assert "Already imported" in r.content.decode()
    assert Project.objects.filter(datasource=ds, gitlab_project_id=7).count() == 1


@pytest.mark.django_db
def test_projects_list_links_to_import(commander_client):
    r = commander_client.get(reverse("projects-list"))
    assert r.status_code == 200
    body = r.content.decode()
    assert "/projects/import/" in body


@pytest.mark.django_db
def test_projects_import_disconnected_datasource_hidden(commander_client, db):
    DataSource.objects.create(
        name="ds-broken",
        datasource_type=DataSource.Type.GITLAB,
        base_url="https://gitlab.example.com/",
        status=DataSource.Status.CONNECTION_ERROR,
        encrypted_token_ciphertext="x",
    )
    commander_client.get(reverse("projects-import"))
    r = commander_client.get(reverse("projects-import"))
    body = r.content.decode()
    assert "ds-broken" not in body
    assert "projects-import-no-connected" in body or "No GitLab data sources" in body


@pytest.mark.django_db
@patch("ingestion.integrations.gitlab_client.urlopen")
def test_import_17_all_imported_shows_info_message(mock_urlopen, commander_client, db):
    project_json = [
        {
            "id": 7,
            "name": "Ex",
            "path_with_namespace": "g/ex",
            "description": "",
            "web_url": "https://gitlab.example.com/g/ex",
            "last_activity_at": None,
        }
    ]
    mock_urlopen.side_effect = gitlab_catalog_mocks(project_json)

    ds = DataSource.objects.create(
        name="gitlab-a",
        datasource_type=DataSource.Type.GITLAB,
        base_url="https://gitlab.example.com/",
        status=DataSource.Status.CONNECTED,
        encrypted_token_ciphertext="glpat-test",
    )
    ProjectFactory(
        datasource=ds,
        name="Ex",
        slug="g-ex",
        source_path="g/ex",
        gitlab_project_id=7,
        sync_state=Project.SyncState.ACTIVE,
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
    r = commander_client.get(reverse("projects-import"))
    body = r.content.decode()
    assert "projects-import-all-imported" in body
    assert "All available projects have already been imported." in body


@pytest.mark.django_db
@patch("ingestion.integrations.gitlab_client.urlopen")
def test_import_18_checkboxes_have_aria_labels(mock_urlopen, commander_client, db):
    project_json = [
        {
            "id": 1,
            "name": "Alpha",
            "path_with_namespace": "g/a",
            "description": "",
            "web_url": "",
            "last_activity_at": None,
        },
        {
            "id": 2,
            "name": "Beta",
            "path_with_namespace": "g/b",
            "description": "",
            "web_url": "",
            "last_activity_at": None,
        },
    ]
    mock_urlopen.side_effect = gitlab_catalog_mocks(project_json)

    ds = DataSource.objects.create(
        name="gitlab-a",
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
    r = commander_client.get(reverse("projects-import"))
    body = r.content.decode()
    assert 'aria-label="Alpha"' in body
    assert 'aria-label="Beta"' in body


@pytest.mark.django_db
@patch("ingestion.integrations.gitlab_client.urlopen")
def test_import_19_import_button_accessible(mock_urlopen, commander_client, db):
    project_json = [
        {
            "id": 1,
            "name": "Alpha",
            "path_with_namespace": "g/a",
            "description": "",
            "web_url": "",
            "last_activity_at": None,
        },
    ]
    mock_urlopen.side_effect = gitlab_catalog_mocks(project_json)

    ds = DataSource.objects.create(
        name="gitlab-a",
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
    r = commander_client.get(reverse("projects-import"))
    body = r.content.decode()
    assert body.count("Import selected") >= 2
    assert "projects-import-selected" in body
    assert "projects-import-submit" in body
