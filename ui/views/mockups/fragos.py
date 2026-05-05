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
    proj = request.GET.get("project", "atlas-backend")
    ctx = {"active_nav": "fragos", "project_slug": proj, "rows": FRAG_ROWS}
    return render(request, "ui/mockups/fragos/list.html", ctx)


def fragos_create(request):
    return render(request, "ui/mockups/fragos/create.html", {"active_nav": "fragos"})


def fragos_view(request, pk: int):  # noqa: ARG001
    ctx = {"active_nav": "fragos", "pk": pk, "fg": FRAG_ROWS[0]}
    return render(request, "ui/mockups/fragos/view.html", ctx)


def fragos_edit(request, pk: int):  # noqa: ARG001
    ctx = {"active_nav": "fragos", "pk": pk, "fg": FRAG_ROWS[0]}
    return render(request, "ui/mockups/fragos/edit.html", ctx)


def fragos_revoke(request, pk: int):  # noqa: ARG001
    ctx = {"active_nav": "fragos", "pk": pk, "title": FRAG_ROWS[0]["title"]}
    return render(request, "ui/mockups/fragos/revoke.html", ctx)
