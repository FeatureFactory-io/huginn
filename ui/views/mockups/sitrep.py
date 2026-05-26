from django.shortcuts import render

_IN_PROGRESS_ROW = {
    "plan_id": "plan-abc-123",
    "assessed_period": "Fri 17:00 → 21:00",
    "trigger": "manual",
    "trigger_label": "Manual",
    "progress_current": 3,
    "progress_total": 9,
}

_FAILED_ROW = {
    "plan_id": "plan-xyz-456",
    "assessed_period": "Thu 09:00 → 13:00",
    "trigger": "automatic",
    "trigger_label": "Auto",
    "last_error": "GitLab API unreachable after 3 retries",
    "created_at": "2026-05-11 09:00",
    "conversation_id": 999,
}

# Each row's variables_snapshot mirrors the 7-variable seed RoE.
# color: green | orange | red | grey; agg_color: dominant color; agg_color_bs: Bootstrap class.
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
        "agg_color": "red",
        "agg_color_bs": "bg-danger",
        "agg_color_label": "Red",
        "variables_snapshot": [
            {"name": "Transparency", "abbrev": "Tr", "y_axis_label": "% linked", "value": "92%", "color": "green"},
            {"name": "Throughput", "abbrev": "Tp", "y_axis_label": "merged MRs", "value": "15", "color": "orange"},
            {"name": "Cycle & Lead Time", "abbrev": "CLT", "y_axis_label": "days", "value": "8d", "color": "red"},
            {"name": "Rework", "abbrev": "Rw", "y_axis_label": "% rework", "value": "4%", "color": "green"},
            {
                "name": "Quality",
                "abbrev": "Q",
                "y_axis_label": "% pipelines passing",
                "value": "78%",
                "color": "orange",
            },
            {"name": "Complexity", "abbrev": "X", "y_axis_label": "avg lines/MR", "value": "142", "color": "green"},
            {
                "name": "Contribution",
                "abbrev": "Co",
                "y_axis_label": "Gini coefficient",
                "value": None,
                "color": "grey",
            },
        ],
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
        "agg_color": "red",
        "agg_color_bs": "bg-danger",
        "agg_color_label": "Red",
        "variables_snapshot": [
            {"name": "Transparency", "abbrev": "Tr", "y_axis_label": "% linked", "value": "81%", "color": "orange"},
            {"name": "Throughput", "abbrev": "Tp", "y_axis_label": "merged MRs", "value": "8", "color": "red"},
            {"name": "Cycle & Lead Time", "abbrev": "CLT", "y_axis_label": "days", "value": "11d", "color": "red"},
            {"name": "Rework", "abbrev": "Rw", "y_axis_label": "% rework", "value": "18%", "color": "red"},
            {"name": "Quality", "abbrev": "Q", "y_axis_label": "% pipelines passing", "value": "91%", "color": "green"},
            {"name": "Complexity", "abbrev": "X", "y_axis_label": "avg lines/MR", "value": "340", "color": "orange"},
            {
                "name": "Contribution",
                "abbrev": "Co",
                "y_axis_label": "Gini coefficient",
                "value": "0.51",
                "color": "orange",
            },
        ],
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
        "agg_color": "orange",
        "agg_color_bs": "bg-warning text-dark",
        "agg_color_label": "Orange",
        "variables_snapshot": [
            {"name": "Transparency", "abbrev": "Tr", "y_axis_label": "% linked", "value": "88%", "color": "green"},
            {"name": "Throughput", "abbrev": "Tp", "y_axis_label": "merged MRs", "value": "12", "color": "orange"},
            {"name": "Cycle & Lead Time", "abbrev": "CLT", "y_axis_label": "days", "value": "5d", "color": "orange"},
            {"name": "Rework", "abbrev": "Rw", "y_axis_label": "% rework", "value": "3%", "color": "green"},
            {
                "name": "Quality",
                "abbrev": "Q",
                "y_axis_label": "% pipelines passing",
                "value": "87%",
                "color": "orange",
            },
            {"name": "Complexity", "abbrev": "X", "y_axis_label": "avg lines/MR", "value": "178", "color": "green"},
            {
                "name": "Contribution",
                "abbrev": "Co",
                "y_axis_label": "Gini coefficient",
                "value": "0.38",
                "color": "green",
            },
        ],
    },
]

_PB_VERSION_CHOICES = [("12", "v12"), ("11", "v11")]
_TRIGGER_CHOICES = [("automatic", "Auto"), ("manual", "Manual")]


def sitrep_list(request):
    proj = request.GET.get("project", "atlas-backend")
    filter_trigger = request.GET.get("trigger", "")
    filter_pb_version = request.GET.get("pb_version", "")
    filter_from = request.GET.get("from", "")
    filter_to = request.GET.get("to", "")
    show_toast = request.GET.get("generated") == "1"
    # ?state=generating  → show in-progress row (default when ?generated=1)
    # ?state=failed       → show failed row
    # ?state=done         → show only completed rows
    state = request.GET.get("state", "generating" if show_toast else "done")

    rows = _ALL_ROWS
    if filter_trigger:
        rows = [r for r in rows if r["trigger"] == filter_trigger]
    if filter_pb_version:
        rows = [r for r in rows if str(r["pb_version"]) == filter_pb_version]

    in_progress_row = _IN_PROGRESS_ROW if state == "generating" else None
    failed_rows = [_FAILED_ROW] if state == "failed" else []

    since_last_disabled = len(rows) == 0
    since_last_label = "Since last SitRep (3h 20m ago)" if not since_last_disabled else "Since last SitRep"

    return render(
        request,
        "ui/mockups/sitrep/list.html",
        {
            "active_nav": "sitrep",
            "project_slug": proj,
            "rows": rows,
            "filter_trigger": filter_trigger,
            "filter_pb_version": filter_pb_version,
            "filter_from": filter_from,
            "filter_to": filter_to,
            "trigger_choices": _TRIGGER_CHOICES,
            "pb_version_choices": _PB_VERSION_CHOICES,
            "show_toast": show_toast,
            "in_progress_row": in_progress_row,
            "failed_rows": failed_rows,
            "since_last_disabled": since_last_disabled,
            "since_last_label": since_last_label,
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
        "agg_color": row.get("agg_color", "grey"),
        "agg_color_bs": row.get("agg_color_bs", "bg-secondary"),
        "agg_color_label": row.get("agg_color_label", "No Data"),
        "variables_snapshot": row.get("variables_snapshot", []),
        "situation_assessment": (
            "The team shipped 14 commits in the assessed period. "
            "Delivery pace is steady with no anomalies detected against the RoE workflow. "
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
