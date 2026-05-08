from django.shortcuts import render

from playbooks.markdown_utils import workflow_md_to_html


def sitawareness_view(request):
    tab = (request.GET.get("tab") or "capsule").strip().lower()
    if tab not in ("capsule", "versions"):
        tab = "capsule"

    standing_md = "**Team composition** …\n\n**Standing constraints** …"
    active_md = "**GitLab outage** — sync gaps expected this week."

    ctx = {
        "active_nav": "sitawareness",
        "active_tab": tab,
        "standing_html": workflow_md_to_html(standing_md),
        "active_html": workflow_md_to_html(active_md),
        "versions": [
            {"n": 4, "on": "2026-05-01 09:41", "author": "Donland", "summary": "Captured GitLab outage context"},
            {"n": 3, "on": "2026-04-18 14:22", "author": "Donland", "summary": "Quarterly standing refresh"},
            {"n": 2, "on": "2026-03-02 11:05", "author": "Chen", "summary": "Added contractor staffing note"},
        ],
        "recent_entries": [
            {"title": "Outage acknowledgement", "on": "2026-05-01", "by": "Donland", "from_decision": "D-501"}
        ],
    }
    return render(request, "ui/mockups/sitawareness/view.html", ctx)


def sitawareness_edit(request):
    return render(request, "ui/mockups/sitawareness/edit.html", {"active_nav": "sitawareness"})
