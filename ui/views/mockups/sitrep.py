from django.shortcuts import render

_ALL_ROWS = [
    {
        "id": 2001,
        "generated_at": "2026-05-11 13:15",
        "from_dt": "2026-05-11 09:00",
        "to_dt": "2026-05-11 13:15",
        "assessed_period": "Mon 09:00 → 13:15",
        "trigger": "automatic",
        "trigger_label": "Auto",
        "headline": "Delivery pace steady — no blockers detected",
        "decisions_proposed": 0,
        "decisions_accepted": 0,
        "pb_version": 12,
    },
    {
        "id": 2000,
        "generated_at": "2026-05-10 09:15",
        "from_dt": "2026-05-09 09:10",
        "to_dt": "2026-05-10 09:15",
        "assessed_period": "Fri 09:10 → Sat 09:15",
        "trigger": "manual",
        "trigger_label": "Manual",
        "headline": "Milestone v1.21 at risk — 3 critical bugs open",
        "decisions_proposed": 2,
        "decisions_accepted": 0,
        "pb_version": 12,
    },
    {
        "id": 1998,
        "generated_at": "2026-05-09 09:10",
        "from_dt": "2026-05-08 09:05",
        "to_dt": "2026-05-09 09:10",
        "assessed_period": "Thu 09:05 → Fri 09:10",
        "trigger": "automatic",
        "trigger_label": "Auto",
        "headline": "Throughput dip — team velocity down 8%",
        "decisions_proposed": 1,
        "decisions_accepted": 1,
        "pb_version": 11,
    },
]

_PB_VERSION_CHOICES = [("12", "v12"), ("11", "v11")]
_TRIGGER_CHOICES = [("automatic", "Auto"), ("manual", "Manual")]


def sitrep_list(request):
    proj = request.GET.get("project", "atlas-backend")
    filter_trigger = request.GET.get("trigger", "")
    filter_pb_version = request.GET.get("pb_version", "")
    show_toast = request.GET.get("generated") == "1"

    rows = _ALL_ROWS
    if filter_trigger:
        rows = [r for r in rows if r["trigger"] == filter_trigger]
    if filter_pb_version:
        rows = [r for r in rows if str(r["pb_version"]) == filter_pb_version]

    return render(
        request,
        "ui/mockups/sitrep/list.html",
        {
            "active_nav": "sitrep",
            "project_slug": proj,
            "rows": rows,
            "filter_trigger": filter_trigger,
            "filter_pb_version": filter_pb_version,
            "trigger_choices": _TRIGGER_CHOICES,
            "pb_version_choices": _PB_VERSION_CHOICES,
            "show_toast": show_toast,
        },
    )


def sitrep_view(request, pk: int):  # noqa: ARG001
    row = next((r for r in _ALL_ROWS if r["id"] == pk), _ALL_ROWS[0])
    ctx = {
        "active_nav": "sitrep",
        "sitrep_pk": pk,
        "project": "atlas-backend",
        "generated_at": row["generated_at"],
        "assessed_period": row["assessed_period"],
        "trigger_label": row["trigger_label"],
        "pb_version_eval": row["pb_version"],
        "mode_at_generation": "Semi-Auto",
        "situation_assessment": (
            "The team shipped 14 commits in the assessed period. "
            "Delivery pace is steady with no anomalies detected against the Playbook workflow. "
            "Sprint 47 is on track for the Friday handoff. "
            "No FRAGOs modified this assessment."
        ),
        "fragos_applied": [
            {"id": 701, "title": "Belay throughput Friday dip"},
        ],
        "notable_items": [
            {"contributor": "alex@example.com", "detail": "6 commits — highest contributor this period"},
            {"contributor": "sam@example.com", "detail": "4 commits — back to median after 0-commit gap last period"},
            {"contributor": "maria@example.com", "detail": "2 commits — 50% below 14-day median"},
        ],
    }
    return render(request, "ui/mockups/sitrep/view.html", ctx)
