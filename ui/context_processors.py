"""Shell context for the realm bar and journey-phase app sidebar."""

import logging

from django.urls import reverse

logger = logging.getLogger(__name__)

ACTIVE_REALM = "huginn"
REALM_ITEMS = (
    {
        "slug": "featurefactory",
        "label": "FeatureFactory",
        "url": "https://featurefactory.io",
        "tooltip": "FeatureFactory home",
        "mark": "images/realm/featurefactory-mark.svg",
    },
    {
        "slug": "mimir",
        "label": "Mimir",
        "url": "https://mimir.featurefactory.io",
        "tooltip": "Mimir — engineering playbooks",
        "mark": "images/realm/mimir-logo.png",
    },
    {
        "slug": "huginn",
        "label": "Huginn",
        "url": "/",
        "tooltip": "Huginn — this app",
        "mark": "images/realm/huginn-logo.jpeg",
    },
    {
        "slug": "yggdrasil",
        "label": "Yggdrasil",
        "url": "https://yggdrasil.featurefactory.io",
        "tooltip": "Yggdrasil",
        "mark": "images/realm/yggdrasil-mark.svg",
    },
    {
        "slug": "heimdall",
        "label": "Heimdall",
        "url": "https://heimdall.featurefactory.io",
        "tooltip": "Heimdall",
        "mark": "images/realm/heimdall-mark.svg",
    },
)

_PREFIX_SECTIONS = (
    ("/sitawareness/", "sitawareness"),
    ("/fragos/", "fragos"),
    ("/roe/", "roe"),
    ("/datasources/", "datasources"),
    ("/projects/", "projects"),
    ("/welcome/", "status"),
    ("/decisions/", "decisions"),
    ("/contributors/", "contributors"),
    ("/action-stations/", "action-stations"),
    ("/chat/", "gjallarhorn"),
)


def primary_nav_section(request):
    """
    Inject realm bar and app sidebar context.

    :param request: Django HTTP request. Example: GET /projects/
    :return: Shell dict. Example: {"nav_section": "projects", "chrome": "authenticated"}
    """
    logger.info("primary_nav_section entry path=%s", request.path)
    return build_shell_context(request)


def build_shell_context(request) -> dict:
    """
    Build realm items, sidebar sections, and guest or authenticated chrome.

    :param request: Django HTTP request. Example: GET /plot/
    :return: Shell dict. Example: {"active_realm": "huginn", "chrome": "guest", "nav_section": "plot"}
    """
    section = _resolve_nav_section(request.path)
    chrome = _chrome_for(request)
    logger.info("primary_nav_section branch chrome=%s", chrome)
    logger.info("primary_nav_section exit nav_section=%s", section or "none")
    return {
        "nav_section": section,
        "chrome": chrome,
        "active_realm": ACTIVE_REALM,
        "realm_items": list(REALM_ITEMS),
        "sidebar_sections": _sidebar_sections(),
    }


def _chrome_for(request) -> str:
    """
    Return guest or authenticated chrome for the request.

    :param request: Django HTTP request. Example: GET /plot/
    :return: chrome label. Example: "authenticated"
    """
    user = getattr(request, "user", None)
    if getattr(user, "is_authenticated", False):
        return "authenticated"
    return "guest"


def _sidebar_sections() -> list:
    """
    Return Workspace, Command, and Setup sidebar groups.

    :return: Section list. Example: [{"id": "workspace", "label": "Workspace", "items": [{"slug": "plot"}]}]
    """
    return [
        _section("workspace", "Workspace", _workspace_items()),
        _section("command", "Command", _command_items()),
        _section("setup", "Setup", _setup_items()),
    ]


def _section(section_id: str, label: str, items: list) -> dict:
    """
    Wrap sidebar links in a labeled group.

    :param section_id: Group id. Example: "command"
    :param label: Visible heading. Example: "Command"
    :param items: Link dicts. Example: [{"slug": "fragos", "testid": "nav-fragos"}]
    :return: Section dict. Example: {"id": "command", "label": "Command", "items": []}
    """
    return {"id": section_id, "label": label, "items": items}


def _workspace_items() -> list:
    """
    Return Workspace sidebar links.

    :return: Link dicts. Example: [{"slug": "plot", "testid": "nav-plot"}]
    """
    return [
        _link("plot", "Plot", reverse("tactical-plot"), "nav-plot", "fa-sharp fa-solid fa-wave-pulse", "Tactical Plot"),
        _link(
            "sitawareness",
            "SA",
            reverse("sitawareness-view"),
            "nav-sitawareness",
            "fa-solid fa-map-location-dot",
            "Situational Awareness",
        ),
        _link("status", "Status", reverse("welcome"), "nav-status", "fa-solid fa-heart-pulse", "Health and welcome"),
    ]


def _command_items() -> list:
    """
    Return Command sidebar links.

    :return: Link dicts. Example: [{"slug": "fragos", "testid": "nav-fragos"}]
    """
    return [
        _link("fragos", "FRAGOs", reverse("fragos-list"), "nav-fragos", "fa-solid fa-puzzle", "Fragmentary orders"),
        _link(
            "sitreps",
            "SitReps",
            reverse("sitreps-list"),
            "nav-sitreps",
            "fa-solid fa-display-chart-up-circle-currency",
            "Situation reports",
        ),
        _link("roe", "RoE", reverse("roe-list"), "nav-roe", "fa-solid fa-ballot-check", "Rules of engagement"),
    ]


def _setup_items() -> list:
    """
    Return Setup sidebar links.

    :return: Link dicts. Example: [{"slug": "projects", "testid": "nav-projects"}]
    """
    return [
        _link("projects", "Projects", reverse("projects-list"), "nav-projects", "fa-solid fa-folder-open", "Projects"),
        _link(
            "datasources", "Sources", reverse("datasources-list"), "nav-datasources", "fa-solid fa-plug", "Data sources"
        ),
    ]


def _link(slug: str, label: str, url: str, testid: str, icon: str, tooltip: str) -> dict:
    """
    Build one sidebar link.

    :param slug: Active-item key. Example: "projects"
    :param label: Visible text. Example: "Projects"
    :param url: Destination. Example: "/projects/"
    :param testid: data-testid. Example: "nav-projects"
    :param icon: Font Awesome classes. Example: "fa-solid fa-folder-open"
    :param tooltip: Hover text. Example: "Projects"
    :return: Link dict. Example: {"slug": "projects", "testid": "nav-projects"}
    """
    return {
        "slug": slug,
        "label": label,
        "url": url,
        "testid": testid,
        "icon": icon,
        "tooltip": tooltip,
    }


def _resolve_nav_section(path: str) -> str | None:
    """
    Return the sidebar slug for a URL path.

    Nested project SitReps highlight SitReps. Mockup URLs under /mockups/ use the same rules.

    :param path: URL path. Example: "/projects/3/sitreps/"
    :return: Section slug or None. Example: "sitreps"
    """
    normalized = _app_path(path)
    if _is_sitrep_path(normalized):
        return "sitreps"
    for prefix, section in _PREFIX_SECTIONS:
        if normalized.startswith(prefix):
            return section
    if normalized in ("/", "/plot", "/plot/") or normalized.startswith("/dashboard/"):
        return "plot"
    return None


def _app_path(path: str) -> str:
    """
    Strip the mockup prefix so preview routes share production section rules.

    :param path: URL path. Example: "/mockups/fragos/"
    :return: App path. Example: "/fragos/"
    """
    if path == "/mockups" or path.startswith("/mockups/"):
        rest = path[len("/mockups") :]
        return rest or "/"
    return path


def _is_sitrep_path(path: str) -> bool:
    """
    True when the path is a SitRep list, detail, or generate route.

    :param path: URL path. Example: "/projects/3/sitreps/"
    :return: Whether the path is a SitRep surface. Example: True
    """
    return "/sitreps/" in path or path.startswith("/sitrep/") or "/sitrep/" in path
