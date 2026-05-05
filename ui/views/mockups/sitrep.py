from django.shortcuts import render


def sitrep_list(request):
    proj = request.GET.get("project", "atlas-backend")
    rows = [
        {
            "id": 2001,
            "generated_at": "2026-05-05 09:15",
            "status": "red",
            "headline": "Milestone v1.21 at risk",
            "decisions_proposed": 3,
            "decisions_accepted": 0,
            "pb_version": 12,
        },
        {
            "id": 1998,
            "generated_at": "2026-05-04 09:10",
            "status": "orange",
            "headline": "Throughput dip",
            "decisions_proposed": 2,
            "decisions_accepted": 2,
            "pb_version": 12,
        },
    ]
    pinned = rows[0]
    return render(
        request,
        "ui/mockups/sitrep/list.html",
        {"active_nav": "sitrep-placeholder", "project_slug": proj, "pinned": pinned, "rows": rows},
    )


def sitrep_view(request, pk: int):  # noqa: ARG001
    ctx = {
        "active_nav": "sitrep-placeholder",
        "sitrep_pk": pk,
        "project": "atlas-backend",
        "overall": {"status": "red", "badge": "Red"},
        "generated": "2026-05-05 09:15",
        "pb_version_eval": 12,
        "situation_narrative": (
            "RED — Milestone v1.21 is supposed to ship Monday, but 3 critical bugs remain open. Playbook expects "
            "Active Bug Count = 0 at all times; current value is 3."
        ),
        "breaches": [
            {"var": "Active Bug Count", "expected": "= 0", "actual": "3", "sev": "red"},
            {"var": "Throughput (Weekly)", "expected": ">= prior week", "actual": "-8%", "sev": "orange"},
        ],
        "matrix_vars": [
            {"label": "Transparency", "traffic": "green"},
            {"label": "Throughput", "traffic": "orange"},
            {"label": "Cycle & Lead Time", "traffic": "green"},
            {"label": "Rework", "traffic": "green"},
            {"label": "Quality", "traffic": "red"},
            {"label": "Complexity", "traffic": "yellow"},
            {"label": "Contribution", "traffic": "green"},
        ],
        "decisions_cards": [
            {"id": 9001, "title": "Belay Active Bug Count = 0 on Fridays"},
            {"id": 9002, "title": "Open investigation into Friday bug carries"},
        ],
        "fragos_applied": [{"title": "Belay throughput Friday dip", "id": "fr-41"}],
        "notable": "Maria: 50% fewer increments vs. 14-day median.",
    }
    return render(request, "ui/mockups/sitrep/view.html", ctx)
