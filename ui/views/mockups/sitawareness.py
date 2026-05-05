from django.shortcuts import render


def sitawareness_view(request):
    proj = request.GET.get("project", "atlas-backend")
    ctx = {
        "active_nav": "sitawareness-placeholder",
        "project_slug": proj,
        "versions": [{"n": 4, "on": "2026-05-01", "author": "Donland", "summary": "Captured GitLab outage context"}],
        "standing": "**Team composition** …\n\n**Standing constraints** …",
        "active": "**GitLab outage** — sync gaps expected this week.",
        "recent_entries": [
            {"title": "Outage acknowledgement", "on": "2026-05-01", "by": "Donland", "from_decision": "D-501"}
        ],
    }
    return render(request, "ui/mockups/sitawareness/view.html", ctx)


def sitawareness_edit(request):
    proj = request.GET.get("project", "atlas-backend")
    return render(
        request, "ui/mockups/sitawareness/edit.html", {"active_nav": "sitawareness-placeholder", "project_slug": proj}
    )
