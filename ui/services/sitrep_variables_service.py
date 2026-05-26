"""Helpers for SitRep variable snapshot display (aggregate color, backfill)."""

from __future__ import annotations

from typing import Any

DISPLAY_VALUE_MAX_LENGTH = 32


def format_variable_display_value(value) -> str:
    """Short label for tables/list tooltips; full value stays in value_title."""
    if value is None:
        return ""
    text = str(value).strip()
    if len(text) <= DISPLAY_VALUE_MAX_LENGTH:
        return text
    return text[: DISPLAY_VALUE_MAX_LENGTH - 1] + "…"


def normalize_snapshot_entry(entry: dict) -> dict:
    """Ensure mockup + production keys; add display-friendly value fields."""
    name = entry.get("variable_name") or entry.get("name") or ""
    raw_value = entry.get("value")
    y_axis = (entry.get("y_axis_label") or "").strip()
    title = str(raw_value).strip() if raw_value is not None else ""
    if raw_value is None or not title:
        display = ""
    elif len(title) <= DISPLAY_VALUE_MAX_LENGTH:
        display = f"{title} {y_axis}".strip() if y_axis and y_axis not in title else title
    else:
        display = format_variable_display_value(title)
    return {
        **entry,
        "variable_name": name,
        "name": name,
        "y_axis_label": y_axis,
        "value_display": display,
        "value_title": title,
    }


def normalize_snapshot(snapshot: list[dict] | None) -> list[dict]:
    return [normalize_snapshot_entry(entry) for entry in (snapshot or [])]


def variables_snapshot_for_project(project_id: int) -> list[dict]:
    """Latest variable strip for project list rows (from VariableDatapoint service)."""
    from ui.services.variable_datapoints_service import get_latest_datapoints  # noqa: PLC0415

    raw = [
        {
            "variable_name": dp["variable_name"],
            "abbrev": dp["abbrev"],
            "y_axis_label": dp["y_axis_label"] or "",
            "value": dp["value"],
            "color": dp["color"],
        }
        for dp in get_latest_datapoints(project_id)
    ]
    return normalize_snapshot(raw)


def aggregate_status_from_snapshot(snapshot: list[dict] | None) -> dict[str, str]:
    """Derive traffic-light aggregate badge fields from variables_snapshot."""
    if not snapshot:
        return {
            "agg_color": "grey",
            "agg_color_bs": "bg-secondary",
            "agg_color_label": "No Data",
        }

    colors = [entry.get("color") for entry in snapshot if entry.get("color")]
    if not colors:
        return {
            "agg_color": "grey",
            "agg_color_bs": "bg-secondary",
            "agg_color_label": "No Data",
        }
    if "red" in colors:
        return {"agg_color": "red", "agg_color_bs": "bg-danger", "agg_color_label": "Red"}
    if "orange" in colors:
        return {
            "agg_color": "orange",
            "agg_color_bs": "bg-warning text-dark",
            "agg_color_label": "Orange",
        }
    if all(c == "green" for c in colors):
        return {"agg_color": "green", "agg_color_bs": "bg-success", "agg_color_label": "Green"}
    return {"agg_color": "grey", "agg_color_bs": "bg-secondary", "agg_color_label": "Mixed"}


def backfill_sitrep_variables(sitrep) -> int:
    """Re-run variable persist from source plan. Returns datapoint count written."""
    from gjallarhorn.services.sitrep_service import _persist_variable_datapoints  # noqa: PLC0415
    from sitrep.models import VariableDatapoint  # noqa: PLC0415

    plan = sitrep.source_plan
    if plan is None:
        return 0
    if not plan.steps.filter(is_variable_assessment=True).exists():
        return 0

    _persist_variable_datapoints(sitrep, plan)
    sitrep.refresh_from_db()
    return VariableDatapoint.objects.filter(sitrep=sitrep).count()


def backfill_all_empty_sitreps(*, project_id: int | None = None) -> list[dict[str, Any]]:
    """Backfill every SitRep with empty snapshot but completed variable steps."""
    from sitrep.models import SitRep  # noqa: PLC0415

    qs = SitRep.objects.filter(source_plan__isnull=False).select_related("source_plan")
    if project_id is not None:
        qs = qs.filter(project_id=project_id)

    results: list[dict[str, Any]] = []
    for sitrep in qs.order_by("pk"):
        if sitrep.variables_snapshot:
            continue
        plan = sitrep.source_plan
        if not plan or plan.steps.filter(is_variable_assessment=True, status="completed").count() == 0:
            continue
        count = backfill_sitrep_variables(sitrep)
        results.append({"sitrep_id": sitrep.pk, "datapoints": count})
    return results
