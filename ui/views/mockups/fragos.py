from django.shortcuts import redirect, render
from django.urls import reverse

FRAG_ROWS = [
    {
        "id": 701,
        "enabled": True,
        "title": "Belay Active Bug Count = 0 on Fridays",
        "tag": "Quality",
        "effective": "Mon–Thu",
        "status": "Active",
        "status_class": "success",
        "scheduled": "",
    },
    {
        "id": 702,
        "enabled": False,
        "title": "Disregard flaky pipeline — infra outage window",
        "tag": "Quality",
        "effective": "today only",
        "status": "Inactive",
        "status_class": "secondary",
        "scheduled": "",
    },
    {
        "id": 703,
        "enabled": True,
        "title": "Suspend cycle-time thresholds — holiday week",
        "tag": "Cycle & Lead Time",
        "effective": "start 2026-05-10",
        "status": "Scheduled",
        "status_class": "info",
        "scheduled": "",
    },
]


def fragos_list(request):
    """No implicit project: absent ``?project=`` means all-projects mode until user picks one."""
    proj = (request.GET.get("project") or "").strip()
    rows = FRAG_ROWS if proj else []
    ctx = {
        "active_nav": "fragos",
        "project_slug": proj,
        "rows": rows,
        "project_filter_choices": [
            ("atlas-backend", "atlas-backend"),
            ("mobile-shell", "mobile-shell"),
        ],
    }
    return render(request, "ui/mockups/fragos/list.html", ctx)


def fragos_create(request):
    proj = (request.GET.get("project") or "").strip()
    if not proj:
        # Project is chosen on Project view or on FRAGO list (filter + New FRAGO)—never on this form.
        return redirect(reverse("mockup-fragos-list"))
    return render(
        request,
        "ui/mockups/fragos/create.html",
        {"active_nav": "fragos", "project_slug": proj},
    )


def fragos_view(request, pk: int):  # noqa: ARG001
    ctx = {"active_nav": "fragos", "pk": pk, "fg": FRAG_ROWS[0]}
    return render(request, "ui/mockups/fragos/view.html", ctx)


def fragos_edit(request, pk: int):  # noqa: ARG001
    ctx = {"active_nav": "fragos", "pk": pk, "fg": FRAG_ROWS[0]}
    return render(request, "ui/mockups/fragos/edit.html", ctx)


def fragos_revoke(request, pk: int):  # noqa: ARG001
    ctx = {"active_nav": "fragos", "pk": pk, "title": FRAG_ROWS[0]["title"]}
    return render(request, "ui/mockups/fragos/revoke.html", ctx)
