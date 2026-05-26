"""Unit tests for SitRep variable snapshot display helpers."""

from ui.services.sitrep_variables_service import (
    format_variable_display_value,
    normalize_snapshot,
    normalize_snapshot_entry,
)


def test_normalize_snapshot_entry_adds_name_and_display_fields():
    entry = {
        "variable_name": "Transparency",
        "abbrev": "T",
        "y_axis_label": "hours",
        "value": "Last increment 2026-05-25T01:30:51Z — ~0–2h ago (within 24h SLA)",
        "color": "green",
    }
    out = normalize_snapshot_entry(entry)
    assert out["name"] == "Transparency"
    assert out["variable_name"] == "Transparency"
    assert out["value_title"] == entry["value"]
    assert out["value_display"].endswith("…")
    assert len(out["value_display"]) < len(entry["value"])


def test_normalize_snapshot_entry_handles_null_value():
    out = normalize_snapshot_entry({"variable_name": "Throughput", "abbrev": "TP", "value": None, "color": "grey"})
    assert out["value_display"] == ""
    assert out["value_title"] == ""


def test_format_variable_display_value_short_unchanged():
    assert format_variable_display_value("15") == "15"


def test_normalize_snapshot_list():
    rows = normalize_snapshot([{"variable_name": "A", "abbrev": "A", "value": "1", "color": "green"}])
    assert len(rows) == 1
    assert rows[0]["name"] == "A"
