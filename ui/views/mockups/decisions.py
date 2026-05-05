from django.shortcuts import render

ROWS = [
    {
        "id": 501,
        "when": "20 Apr 09:15",
        "title": "Belay Active Bug Count = 0 on Fridays",
        "status": "Accepted",
        "outcome": "FRAGO #701",
        "sitrep_ref": "#2001",
    },
    {
        "id": 502,
        "when": "20 Apr 09:15",
        "title": "Investigate Friday bug carry",
        "status": "Accepted",
        "outcome": "Jira HUGINN-302",
        "sitrep_ref": "#2001",
    },
    {
        "id": 503,
        "when": "19 Apr 09:00",
        "title": "Refactor auth immediately",
        "status": "Rejected",
        "outcome": "—",
        "sitrep_ref": "#1998",
    },
]


def decisions_list(request):
    return render(request, "ui/mockups/decisions/list.html", {"active_nav": "decisions", "rows": ROWS})


def decisions_view(request, pk: int):  # noqa: ARG001
    row = ROWS[0]
    ctx = {
        "active_nav": "decisions",
        "pk": pk,
        "d": row,
        "proposal_status": "Proposed",
        "proposed_body": ("Gjallarhorn proposes belaying the playbook expectation…",),
    }
    return render(request, "ui/mockups/decisions/view.html", ctx)
