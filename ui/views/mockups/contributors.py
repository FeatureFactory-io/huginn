from django.shortcuts import render

ROWS = [
    {"id": 11, "name": "Anton P.", "mon": "8/3", "tue": "5/2", "wed": "6/1", "total": "23/8"},
    {"id": 12, "name": "Maria S.", "mon": "4/1", "tue": "3/2", "wed": "5/2", "total": "22/9"},
]


def contributors_list(request):
    proj = request.GET.get("project", "atlas-backend")
    ctx = {"active_nav": "contributors", "project_slug": proj, "rows": ROWS}
    return render(request, "ui/mockups/contributors/list.html", ctx)


def contributors_view(request, pk: int):  # noqa: ARG001
    ctx = {
        "active_nav": "contributors",
        "pk": pk,
        "c": {
            "name": "Anton P.",
            "handles": ("git Anton <anton@corp>", "GitLab @antonp"),
        },
    }
    return render(request, "ui/mockups/contributors/view.html", ctx)
