"""Unit tests for realm bar and app sidebar shell context."""

import pytest
from django.contrib.auth.models import AnonymousUser
from django.test import RequestFactory

from ui.context_processors import ACTIVE_REALM, REALM_ITEMS, build_shell_context


def _request(path: str, user=None):
    request = RequestFactory().get(path)
    request.user = user if user is not None else AnonymousUser()
    return request


def test_guest_chrome_and_realm_list():
    """Anonymous requests expose guest chrome and the five realm products."""
    ctx = build_shell_context(_request("/"))
    slugs = [item["slug"] for item in ctx["realm_items"]]
    assert ctx["chrome"] == "guest"
    assert ctx["active_realm"] == ACTIVE_REALM == "huginn"
    assert slugs == ["featurefactory", "mimir", "huginn", "yggdrasil", "heimdall"]
    assert ctx["realm_items"] == list(REALM_ITEMS)
    assert ctx["nav_section"] == "plot"


def test_authenticated_chrome():
    """Signed-in requests expose authenticated chrome."""
    user = type("AuthUser", (), {"is_authenticated": True})()
    ctx = build_shell_context(_request("/projects/", user=user))
    assert ctx["chrome"] == "authenticated"
    assert ctx["nav_section"] == "projects"


def test_sidebar_sections_follow_journey_phases():
    """Sidebar groups Workspace, Command, and Setup with existing test ids."""
    ctx = build_shell_context(_request("/plot/"))
    sections = {section["id"]: [item["testid"] for item in section["items"]] for section in ctx["sidebar_sections"]}
    assert list(sections) == ["workspace", "command", "setup"]
    assert sections["workspace"] == ["nav-plot", "nav-sitawareness", "nav-status"]
    assert sections["command"] == ["nav-fragos", "nav-sitreps", "nav-roe"]
    assert sections["setup"] == ["nav-projects", "nav-datasources"]


@pytest.mark.parametrize(
    ("path", "expected"),
    [
        ("/plot/", "plot"),
        ("/", "plot"),
        ("/sitawareness/", "sitawareness"),
        ("/sitawareness/edit/", "sitawareness"),
        ("/fragos/create/", "fragos"),
        ("/sitreps/", "sitreps"),
        ("/projects/4/sitreps/", "sitreps"),
        ("/projects/4/sitrep/generate/", "sitreps"),
        ("/roe/1/", "roe"),
        ("/projects/", "projects"),
        ("/projects/9/", "projects"),
        ("/datasources/create/", "datasources"),
        ("/welcome/", "status"),
        ("/mockups/fragos/", "fragos"),
        ("/mockups/", "plot"),
        ("/accounts/login/", None),
    ],
)
def test_path_maps_to_nav_section(path, expected):
    """URL path selects the sidebar slug, including nested SitReps."""
    ctx = build_shell_context(_request(path))
    assert ctx["nav_section"] == expected
