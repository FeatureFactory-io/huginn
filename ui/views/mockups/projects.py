from django.shortcuts import render

from ui.services.increments_service import RANGE_LABELS

MOCK_PROJECT = {
    "id": 1,
    "name": "atlas-backend",
    "datasource": "company-gitlab",
    "source_path": "company-gitlab/atlas-backend",
}

_ATLAS_VARIABLES_SNAPSHOT = [
    {"name": "Transparency", "abbrev": "Tr", "y_axis_label": "% linked", "value": "92%", "color": "green"},
    {"name": "Throughput", "abbrev": "Tp", "y_axis_label": "merged MRs", "value": "15", "color": "orange"},
    {"name": "Cycle & Lead Time", "abbrev": "CLT", "y_axis_label": "days", "value": "8d", "color": "red"},
    {"name": "Rework", "abbrev": "Rw", "y_axis_label": "% rework", "value": "4%", "color": "green"},
    {"name": "Quality", "abbrev": "Q", "y_axis_label": "% pipelines passing", "value": "78%", "color": "orange"},
    {"name": "Complexity", "abbrev": "X", "y_axis_label": "avg lines/MR", "value": "142", "color": "green"},
    {"name": "Contribution", "abbrev": "Co", "y_axis_label": "Gini coefficient", "value": None, "color": "grey"},
]

MOCK_LIST = [
    {
        **MOCK_PROJECT,
        "roe": "Atlas Engineering RoE · v1 (auto-track)",
        "last_sync": "8 min ago",
        "sync_status": "Active",
        "row_status": "Active",
        "last_sitrep_pk": 2001,
        "last_sitrep_headline": "Delivery pace steady — no blockers detected",
        "last_sitrep_generated_at": "2026-05-11 13:15",
        "variables_snapshot": _ATLAS_VARIABLES_SNAPSHOT,
    },
    {
        "id": 2,
        "name": "billing-service",
        "datasource": "company-gitlab",
        "source_path": "company-gitlab/billing-service",
        "roe": "Not assigned",
        "last_sync": "never",
        "sync_status": "Initial sync queued",
        "row_status": "Active",
        "last_sitrep_pk": None,
        "last_sitrep_headline": None,
        "last_sitrep_generated_at": None,
        "variables_snapshot": [],
    },
]


def projects_list(request):
    return render(request, "ui/mockups/projects/list.html", {"active_nav": "projects", "rows": MOCK_LIST})


def projects_import(request):
    upstream = [
        {
            "id": 101,
            "source_name": "atlas-backend",
            "slug": "company-gitlab/atlas-backend",
            "description": "Core API services",
            "imported": True,
            "last_activity_source": "2 h ago",
        },
        {
            "id": 102,
            "source_name": "atlas-frontend",
            "slug": "company-gitlab/atlas-frontend",
            "description": "Web client",
            "imported": False,
            "last_activity_source": "30 min ago",
        },
        {
            "id": 103,
            "source_name": "infra-core",
            "slug": "company-gitlab/infra-core",
            "description": "Infra primitives",
            "imported": False,
            "last_activity_source": "3 d ago",
        },
    ]
    return render(
        request,
        "ui/mockups/projects/import.html",
        {"active_nav": "projects", "sources_dropdown": MOCK_LIST[:1], "upstream": upstream},
    )


def projects_view(request, pk: int):  # noqa: ARG001
    tab = (request.GET.get("tab") or "vitals").strip().lower()
    if tab not in ("vitals", "increments"):
        tab = "vitals"
    range_key = (request.GET.get("range") or "last_14d").strip().lower()
    valid_ranges = {"today", "yesterday", "this_week", "last_week", "last_14d"}
    if range_key not in valid_ranges:
        range_key = "last_14d"
    range_order = ["today", "yesterday", "this_week", "last_week", "last_14d"]
    time_range_choices = [(k, RANGE_LABELS[k]) for k in range_order]
    time_range = range_key if tab == "increments" else "last_14d"
    increments = []
    if tab == "increments":
        increments = [
            {
                "kind": "commit",
                "external_id": "a" * 40,
                "occurred_at": "2026-05-06 14:30",
                "author": "Ada Lovelace",
                "summary": "Harden token refresh path",
                "branches": ["main", "release"],
                "web_url": "https://gitlab.example.com/co/atlas-backend/-/commit/" + "a" * 40,
            },
            {
                "kind": "commit",
                "external_id": "b" * 40,
                "occurred_at": "2026-05-05 09:15",
                "author": "billing-bot@example.com",
                "summary": "Invoice export retry backoff",
                "branches": ["main"],
                "web_url": "https://gitlab.example.com/co/atlas-backend/-/commit/" + "b" * 40,
            },
        ]
    ctx = {
        "active_nav": "projects",
        "pk": pk,
        "active_tab": tab,
        "time_range": time_range,
        "time_range_choices": time_range_choices,
        "increments": increments,
        "p": {
            **MOCK_PROJECT,
            "imported_on": "2026-05-01",
            "imported_by": "donland@example.com",
            "source_url": "https://gitlab.example.com/atlas/backend",
            "roe_display": "FeatureFactory RoE · v12 (auto-track latest)",
            "sync_last": "8 min ago",
            "sync_next": "scheduled hourly",
            "sync_schedule_display": "Hourly",
            "sync_state": "Active",
        },
    }
    return render(request, "ui/mockups/projects/view.html", ctx)


def projects_edit(request, pk: int):  # noqa: ARG001
    ctx = {"active_nav": "projects", "pk": pk, "p": MOCK_PROJECT}
    return render(request, "ui/mockups/projects/edit.html", ctx)


def projects_archive(request, pk: int):  # noqa: ARG001
    ctx = {"active_nav": "projects", "pk": pk, "name": MOCK_PROJECT["name"]}
    return render(request, "ui/mockups/projects/archive.html", ctx)
