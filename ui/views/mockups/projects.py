from django.shortcuts import render

MOCK_PROJECT = {
    "id": 1,
    "name": "atlas-backend",
    "datasource": "company-gitlab",
    "source_path": "company-gitlab/atlas-backend",
}

MOCK_LIST = [
    {
        **MOCK_PROJECT,
        "playbook": "Standard Engineering · v12 (auto-track)",
        "last_sync": "8 min ago",
        "sync_status": "Active",
        "row_status": "Active",
    },
    {
        "id": 2,
        "name": "billing-service",
        "datasource": "company-gitlab",
        "source_path": "company-gitlab/billing-service",
        "playbook": "Not assigned",
        "last_sync": "never",
        "sync_status": "Initial sync queued",
        "row_status": "Active",
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
    ctx = {
        "active_nav": "projects",
        "pk": pk,
        "p": {
            **MOCK_PROJECT,
            "imported_on": "2026-05-01",
            "imported_by": "donland@example.com",
            "source_url": "https://gitlab.example.com/atlas/backend",
            "playbook_display": "Standard Engineering · v12 (auto-track latest)",
            "sync_last": "8 min ago",
            "sync_next": "scheduled hourly",
            "sync_state": "Active",
            "recent_activity": [],
        },
    }
    return render(request, "ui/mockups/projects/view.html", ctx)


def projects_edit(request, pk: int):  # noqa: ARG001
    ctx = {"active_nav": "projects", "pk": pk, "p": MOCK_PROJECT}
    return render(request, "ui/mockups/projects/edit.html", ctx)


def projects_archive(request, pk: int):  # noqa: ARG001
    ctx = {"active_nav": "projects", "pk": pk, "name": MOCK_PROJECT["name"]}
    return render(request, "ui/mockups/projects/archive.html", ctx)
