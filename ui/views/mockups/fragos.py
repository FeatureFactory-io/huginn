from django.shortcuts import render

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
    timing = (request.GET.get("timing") or "").strip().lower()
    if timing not in ("", "in_effect", "scheduled", "past"):
        timing = ""
    status_f = (request.GET.get("status") or "").strip().lower()
    if status_f not in ("", "active", "disabled", "revoked"):
        status_f = ""
    affects = (request.GET.get("affects") or "").strip().lower()
    if affects not in ("", "narrative", "variables"):
        affects = ""
    rows = FRAG_ROWS if proj else []
    ctx = {
        "active_nav": "fragos",
        "project_slug": proj,
        "rows": rows,
        "project_filter_choices": [
            ("atlas-backend", "atlas-backend"),
            ("mobile-shell", "mobile-shell"),
        ],
        "filter_timing": timing,
        "filter_status": status_f,
        "filter_affects": affects,
    }
    return render(request, "ui/mockups/fragos/list.html", ctx)


def fragos_create(request):
    proj = (request.GET.get("project") or "").strip()
    ctx = {
        "active_nav": "fragos",
        "project_slug": proj,
        "project_choices": [
            ("atlas-backend", "atlas-backend"),
            ("mobile-shell", "mobile-shell"),
        ],
    }
    return render(request, "ui/mockups/fragos/create.html", ctx)


def fragos_view(request, pk: int):  # noqa: ARG001
    ctx = {"active_nav": "fragos", "pk": pk, "fg": FRAG_ROWS[0]}
    return render(request, "ui/mockups/fragos/view.html", ctx)


def fragos_edit(request, pk: int):  # noqa: ARG001
    ctx = {"active_nav": "fragos", "pk": pk, "fg": FRAG_ROWS[0]}
    return render(request, "ui/mockups/fragos/edit.html", ctx)


def fragos_revoke(request, pk: int):  # noqa: ARG001
    ctx = {"active_nav": "fragos", "pk": pk, "title": FRAG_ROWS[0]["title"]}
    return render(request, "ui/mockups/fragos/revoke.html", ctx)
