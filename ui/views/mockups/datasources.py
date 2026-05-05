from django.shortcuts import render

MOCK_ROW = {"id": 1, "type": "GitLab", "name": "company-gitlab", "base_url": "https://gitlab.example.com"}

MOCK_LIST = [
    {
        **MOCK_ROW,
        "token_expires_in": 14,
        "status": "expiring",
        "status_label": "Token expiring in 14 days",
        "last_activity": "5 min ago",
    },
    {
        "id": 2,
        "type": "GitLab",
        "name": "oss-gitlab",
        "base_url": "https://gitlab.com",
        "token_expires_in": None,
        "status": "connected",
        "status_label": "Connected",
        "last_activity": "2 min ago",
    },
]


def datasources_list(request):
    ctx = {"active_nav": "datasources", "rows": MOCK_LIST}
    return render(request, "ui/mockups/datasources/list.html", ctx)


def datasources_create(request):
    ctx = {"active_nav": "datasources", "step": int(request.GET.get("step", "1"))}
    return render(request, "ui/mockups/datasources/create.html", ctx)


def datasources_view(request, pk: int):  # noqa: ARG001
    ctx = {
        "active_nav": "datasources",
        "ds": {
            **MOCK_ROW,
            "status": "Token expiring in 14 days",
            "token_last4": "a9f2",
            "expires_on": "2026-06-05",
            "expires_in_days": 14,
            "auth_as": "user@example.com",
            "sync_runs": [
                {
                    "at": "10:41",
                    "project": "atlas-backend",
                    "duration_ms": 8420,
                    "ingested": 128,
                    "errors": 0,
                },
                {"at": "10:12", "project": "billing-service", "duration_ms": 4102, "ingested": 64, "errors": 1},
            ],
        },
        "pk": pk,
    }
    return render(request, "ui/mockups/datasources/view.html", ctx)


def datasources_edit(request, pk: int):  # noqa: ARG001
    ctx = {"active_nav": "datasources", "ds": MOCK_ROW, "pk": pk}
    return render(request, "ui/mockups/datasources/edit.html", ctx)


def datasources_delete(request, pk: int):  # noqa: ARG001
    ctx = {
        "active_nav": "datasources",
        "ds": MOCK_ROW,
        "imported_projects": 3,
        "pk": pk,
    }
    return render(request, "ui/mockups/datasources/delete.html", ctx)
