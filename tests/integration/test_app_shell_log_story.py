"""Log story for the realm shell context processor."""

import logging

import pytest


def _assert_shell_beats(caplog, path_fragment: str, chrome: str, section: str):
    text = caplog.text
    assert f"path={path_fragment}" in text or "path=" in text
    assert "primary_nav_section entry path=" in text
    assert f"chrome={chrome}" in text
    assert f"nav_section={section}" in text


@pytest.mark.django_db
def test_app_shell_log_story_happy(commander_client, caplog):
    """Authenticated /projects/ logs section projects and authenticated chrome."""
    with caplog.at_level(logging.INFO, logger="ui.context_processors"):
        response = commander_client.get("/projects/")
    assert response.status_code == 200
    _assert_shell_beats(caplog, "/projects/", "authenticated", "projects")
    assert "password" not in caplog.text.lower()


@pytest.mark.django_db
def test_app_shell_log_story_guest(client, caplog):
    """Anonymous / logs guest chrome."""
    with caplog.at_level(logging.INFO, logger="ui.context_processors"):
        response = client.get("/")
    assert response.status_code == 200
    _assert_shell_beats(caplog, "/", "guest", "plot")
