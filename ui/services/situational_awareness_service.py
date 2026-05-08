"""Situational Awareness capsule persistence and presentation helpers."""

from __future__ import annotations

import difflib
from typing import Any

from django.utils import timezone

from playbooks.markdown_utils import workflow_md_to_html
from sitrep.models import (
    SituationalAwareness,
    SituationalAwarenessEntry,
    SituationalAwarenessVersion,
)


def get_or_create_awareness() -> SituationalAwareness:
    """Return the workspace singleton capsule (first row by pk, or create one)."""
    sa = SituationalAwareness.objects.order_by("pk").first()
    if sa is not None:
        return sa
    return SituationalAwareness.objects.create()


def head_version(sa: SituationalAwareness) -> SituationalAwarenessVersion | None:
    return sa.versions.order_by("-version_number").first()


def populate_entries_for_version(
    version: SituationalAwarenessVersion,
    *,
    standing_md: str,
    active_md: str,
    created_by,
) -> None:
    rows: list[SituationalAwarenessEntry] = []
    if (standing_md or "").strip():
        rows.append(
            SituationalAwarenessEntry(
                version=version,
                section=SituationalAwarenessEntry.Section.STANDING,
                sort_order=0,
                title="Standing context",
                body_md=standing_md,
                created_by=created_by,
            ),
        )
    if (active_md or "").strip():
        rows.append(
            SituationalAwarenessEntry(
                version=version,
                section=SituationalAwarenessEntry.Section.ACTIVE,
                sort_order=0,
                title="Content",
                body_md=active_md,
                created_by=created_by,
            ),
        )
    if rows:
        SituationalAwarenessEntry.objects.bulk_create(rows)


def append_version(
    *,
    awareness: SituationalAwareness,
    standing_md: str,
    active_md: str,
    change_summary: str,
    created_by,
) -> tuple[SituationalAwarenessVersion | None, str | None]:
    summary = (change_summary or "").strip()
    if not summary:
        return None, "Change summary is required."
    head = head_version(awareness)
    next_n = (head.version_number + 1) if head else 1
    version = SituationalAwarenessVersion.objects.create(
        awareness=awareness,
        version_number=next_n,
        standing_md=standing_md,
        active_md=active_md,
        change_summary=summary,
        created_by=created_by,
    )
    populate_entries_for_version(version, standing_md=standing_md, active_md=active_md, created_by=created_by)
    return version, None


def entries_from_md(md: str, *, temporal_hint: bool) -> list[dict[str, Any]]:
    """Single readable article per markdown blob (fallback when no structured rows)."""
    text = (md or "").strip()
    if not text:
        return []
    temporal_note = ""
    if temporal_hint:
        lowered = text.lower()
        if any(k in lowered for k in ("temporary", "until ", "next sprint", "timeboxed")):
            temporal_note = "Temporal"

    return [
        {
            "title": "Content",
            "author": "—",
            "date": "—",
            "body_html": workflow_md_to_html(text),
            "decision_label": "",
            "decision_href": "",
            "temporal_note": temporal_note,
        },
    ]


def _serialize_entry_row(ent: SituationalAwarenessEntry, *, temporal_hint: bool) -> dict[str, Any]:
    temporal_note = ""
    body_lower = (ent.body_md or "").lower()
    if temporal_hint and ent.section == SituationalAwarenessEntry.Section.ACTIVE:
        if any(k in body_lower for k in ("temporary", "until ", "next sprint", "timeboxed")):
            temporal_note = "Temporal"
    actor = "—"
    if ent.created_by_id:
        u = ent.created_by
        actor = u.get_full_name() or u.email or str(u)
    dt = timezone.localtime(ent.created_at).strftime("%Y-%m-%d %H:%M") if ent.created_at else "—"
    return {
        "title": ent.title or "Content",
        "author": actor,
        "date": dt,
        "body_html": workflow_md_to_html(ent.body_md or ""),
        "decision_label": (ent.decision_label or "").strip(),
        "decision_href": (ent.decision_href or "").strip(),
        "temporal_note": temporal_note,
    }


def standing_entries_for(version: SituationalAwarenessVersion | None) -> list[dict[str, Any]]:
    if version is None:
        return []
    qs = version.entries.filter(section=SituationalAwarenessEntry.Section.STANDING).order_by("sort_order", "pk")
    if qs.exists():
        return [_serialize_entry_row(e, temporal_hint=False) for e in qs]
    return entries_from_md(version.standing_md, temporal_hint=False)


def active_entries_for(version: SituationalAwarenessVersion | None) -> list[dict[str, Any]]:
    if version is None:
        return []
    qs = version.entries.filter(section=SituationalAwarenessEntry.Section.ACTIVE).order_by("sort_order", "pk")
    if qs.exists():
        return [_serialize_entry_row(e, temporal_hint=True) for e in qs]
    return entries_from_md(version.active_md, temporal_hint=True)


def combined_markdown_for_version(version: SituationalAwarenessVersion | None) -> str:
    if version is None:
        return ""
    parts: list[str] = []
    for ent in version.entries.filter(section=SituationalAwarenessEntry.Section.STANDING).order_by(
        "sort_order",
        "pk",
    ):
        if (ent.body_md or "").strip():
            parts.append(ent.body_md.strip())
    for ent in version.entries.filter(section=SituationalAwarenessEntry.Section.ACTIVE).order_by(
        "sort_order",
        "pk",
    ):
        if (ent.body_md or "").strip():
            parts.append(ent.body_md.strip())
    if parts:
        return "\n\n".join(parts)
    return "\n\n".join(p for p in [(version.standing_md or "").strip(), (version.active_md or "").strip()] if p)


def unified_diff_versions(old: SituationalAwarenessVersion | None, new: SituationalAwarenessVersion | None) -> str:
    a = combined_markdown_for_version(old)
    b = combined_markdown_for_version(new)
    on = old.version_number if old else "?"
    nn = new.version_number if new else "?"
    return "\n".join(
        difflib.unified_diff(
            a.splitlines(),
            b.splitlines(),
            fromfile=f"v{on}",
            tofile=f"v{nn}",
            lineterm="",
        ),
    )


def format_versions_rows(qs: list[SituationalAwarenessVersion]) -> list[dict[str, Any]]:
    rows = []
    for v in qs:
        actor = "—"
        if v.created_by_id:
            u = v.created_by
            actor = u.get_full_name() or u.email or str(u)
        rows.append(
            {
                "n": v.version_number,
                "on": timezone.localtime(v.created_at).strftime("%Y-%m-%d %H:%M"),
                "author": actor,
                "summary": v.change_summary or "—",
            },
        )
    return rows
