"""Situational Awareness capsule persistence and presentation helpers."""

from __future__ import annotations

from typing import Any

from django.utils import timezone

from ingestion.models import Project
from playbooks.markdown_utils import workflow_md_to_html
from sitrep.models import SituationalAwareness, SituationalAwarenessVersion


def get_or_create_awareness(project: Project) -> SituationalAwareness:
    sa, _ = SituationalAwareness.objects.get_or_create(project=project)
    return sa


def head_version(sa: SituationalAwareness) -> SituationalAwarenessVersion | None:
    return sa.versions.order_by("-version_number").first()


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
    return version, None


def entries_from_md(md: str, *, temporal_hint: bool) -> list[dict[str, Any]]:
    """Single readable article per markdown blob (structured headings deferred)."""
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
            "decision_pk": None,
            "decision_id": "",
            "temporal_note": temporal_note,
        },
    ]


def format_versions_rows(
    qs: list[SituationalAwarenessVersion],
    *,
    include_project_slug: bool = False,
) -> list[dict[str, Any]]:
    rows = []
    for v in qs:
        actor = "—"
        if v.created_by_id:
            u = v.created_by
            actor = getattr(u, "full_name", None) or getattr(u, "email", None) or str(u)
        slug_for_row: str | None = None
        if include_project_slug and getattr(v, "awareness_id", None):
            proj = getattr(v.awareness, "project", None)
            slug_for_row = proj.slug if proj else None
        rows.append(
            {
                "n": v.version_number,
                "on": timezone.localtime(v.created_at).strftime("%Y-%m-%d %H:%M"),
                "author": actor,
                "summary": v.change_summary or "—",
                "project_slug": slug_for_row,
            },
        )
    return rows
