"""Unit tests for ProjectsService (GitLab catalog + import)."""

from unittest.mock import MagicMock, patch

import pytest

from ingestion.models import Project
from tests.factories import DataSourceFactory, ProjectFactory
from ui.services.projects_service import ProjectsService


@pytest.mark.django_db
@patch("ui.services.projects_service.GitlabClient")
def test_snapshot_sets_error_on_api_failure(mock_gc_class) -> None:
    ds = DataSourceFactory(encrypted_token_ciphertext="glpat-x")
    inst = MagicMock()
    inst.verify_token.return_value = {"username": "u"}
    inst.list_visible_projects.side_effect = ConnectionError("GitLab responded with HTTP 503")
    mock_gc_class.return_value = inst

    snap = ProjectsService().load_remote_projects_snapshot(ds.pk)
    assert snap["error"]
    assert "503" in snap["error"] or "GitLab" in snap["error"]
    assert snap["entries"] == []


@pytest.mark.django_db
@patch("ui.services.projects_service.GitlabClient")
def test_snapshot_marks_already_imported_entries(mock_gc_class) -> None:
    ds = DataSourceFactory(encrypted_token_ciphertext="glpat-x")
    ProjectFactory(
        datasource=ds,
        name="old",
        slug="old-5",
        gitlab_project_id=5,
        sync_state=Project.SyncState.ACTIVE,
    )

    inst = MagicMock()
    inst.verify_token.return_value = {"username": "u"}
    inst.list_visible_projects.return_value = [
        {
            "id": 5,
            "name": "A",
            "path_with_namespace": "g/a",
            "description": "",
            "web_url": "https://x/g/a",
            "last_activity_at": None,
        },
        {
            "id": 99,
            "name": "B",
            "path_with_namespace": "g/b",
            "description": "",
            "web_url": "https://x/g/b",
            "last_activity_at": None,
        },
    ]
    mock_gc_class.return_value = inst

    snap = ProjectsService().load_remote_projects_snapshot(ds.pk)
    by_key = {e["key"]: e for e in snap["entries"]}
    assert by_key["5"]["already_imported"] is True
    assert by_key["99"]["already_imported"] is False


@pytest.mark.django_db
@patch("ui.services.projects_service.GitlabClient")
def test_snapshot_sets_all_imported_when_every_row_imported(mock_gc_class) -> None:
    ds = DataSourceFactory(encrypted_token_ciphertext="glpat-x")
    ProjectFactory(
        datasource=ds,
        name="x",
        slug="x-5",
        gitlab_project_id=5,
    )

    inst = MagicMock()
    inst.verify_token.return_value = {"username": "u"}
    inst.list_visible_projects.return_value = [
        {
            "id": 5,
            "name": "A",
            "path_with_namespace": "g/a",
            "description": "",
            "web_url": "",
            "last_activity_at": None,
        },
    ]
    mock_gc_class.return_value = inst

    snap = ProjectsService().load_remote_projects_snapshot(ds.pk)
    assert snap.get("all_imported") is True


@pytest.mark.django_db
@patch("ui.services.projects_service.sync_project")
def test_persist_skips_already_imported_via_catalog_flag(mock_delay) -> None:
    ds = DataSourceFactory(encrypted_token_ciphertext="glpat-x")
    entries = [
        {
            "key": "7",
            "name": "g/ex / Ex",
            "short_name": "Ex",
            "path": "g/ex",
            "description": "",
            "web_url": "",
            "last_activity_at": None,
            "already_imported": True,
        },
    ]
    before = Project.objects.count()
    created = ProjectsService().persist_imported_project_selection(
        datasource_id=ds.pk,
        remote_keys=["7"],
        catalog_entries=entries,
        imported_by_id=None,
    )
    assert created == []
    assert Project.objects.count() == before
    mock_delay.delay.assert_not_called()


@pytest.mark.django_db
def test_update_configuration_sets_playbook_and_clears_invalid_pin() -> None:
    from tests.factories import PlaybookFactory, PlaybookVersionFactory, ProjectFactory

    p = ProjectFactory(playbook_slug="")
    pb_a = PlaybookFactory(slug="pb-a")
    pb_b = PlaybookFactory(slug="pb-b")
    va = PlaybookVersionFactory(playbook=pb_a, version_number=1)
    PlaybookVersionFactory(playbook=pb_b, version_number=1)

    ProjectsService().update_project_configuration(
        p.pk,
        assigned_playbook=str(pb_a.pk),
        pinned_playbook_version=str(va.pk),
    )
    p.refresh_from_db()
    assert p.assigned_playbook_id == pb_a.pk
    assert p.playbook_slug == "pb-a"
    assert p.pinned_playbook_version_id == va.pk

    ProjectsService().update_project_configuration(
        p.pk,
        assigned_playbook=str(pb_b.pk),
        pinned_playbook_version=str(va.pk),
    )
    p.refresh_from_db()
    assert p.assigned_playbook_id == pb_b.pk
    assert p.pinned_playbook_version_id is None


@pytest.mark.django_db
def test_update_configuration_clears_playbook_when_empty() -> None:
    from tests.factories import PlaybookFactory, ProjectFactory

    pb = PlaybookFactory(slug="keep-slug")
    p = ProjectFactory(assigned_playbook=pb, playbook_slug=pb.slug)

    ProjectsService().update_project_configuration(p.pk, assigned_playbook="", pinned_playbook_version="")
    p.refresh_from_db()
    assert p.assigned_playbook_id is None
    assert p.playbook_slug == ""
    assert p.pinned_playbook_version_id is None
