"""Tactical Plot (DASHBOARD-PROJECTS-1) — real project cards + workspace rails."""

from __future__ import annotations

from datetime import date, datetime

from django.db.models import Q
from django.shortcuts import render
from django.views import View

from ingestion.models import DataSource, Project
from playbooks.markdown_utils import workflow_md_to_html
from sitrep.models import Frago
from ui.services.situational_awareness_service import (
    active_entries_for,
    get_or_create_awareness,
    head_version,
    standing_entries_for,
)

# Match SA view: generic entry titles are not used as rail fallback text.
_RAIL_SA_TITLE_FALLBACK_BLOCK = frozenset(("content", "disposition", "standing context"))

_DS_SOURCE_META = {
    DataSource.Type.GITLAB: {"key": "gitlab", "label": "GitLab", "si_slug": "gitlab"},
    DataSource.Type.JIRA: {"key": "jira", "label": "Jira", "si_slug": "jira"},
}


def _sync_visuals(sync_state: str) -> tuple[str, str]:
    """Return (Bootstrap 5 badge class, border-* class for list-row left accent)."""
    m = {
        Project.SyncState.ACTIVE.value: ("text-bg-success", "border-success"),
        Project.SyncState.ERROR.value: ("text-bg-danger", "border-danger"),
        Project.SyncState.SYNCING.value: ("text-bg-warning text-dark", "border-warning"),
        Project.SyncState.INITIAL_SYNC_QUEUED.value: ("text-bg-secondary", "border-secondary"),
    }
    return m.get(sync_state, ("text-bg-secondary", "border-secondary"))


def _sources_for_project(project: Project) -> list[dict]:
    ds = project.datasource
    if ds is None:
        return []
    meta = _DS_SOURCE_META.get(ds.datasource_type)
    if meta:
        return [dict(meta)]
    raw = str(ds.datasource_type)
    return [{"key": raw, "label": raw.replace("_", " ").title(), "si_slug": raw}]


def _project_cards(projects: list[Project]) -> list[dict]:
    """Card payload: GitLab description (prose) and source path are separate lines."""
    out: list[dict] = []
    for p in projects:
        name = (p.display_name or "").strip() or p.name
        desc = (p.description or "").strip()
        path = (p.source_path or "").strip()
        badge_cls, border_cls = _sync_visuals(str(p.sync_state))
        out.append(
            {
                "pk": p.pk,
                "name": name,
                "description": desc or None,
                "source_path": path or None,
                "sources": _sources_for_project(p),
                "sync_state": str(p.sync_state),
                "sync_state_display": p.get_sync_state_display(),
                "sync_badge_class": badge_cls,
                "sync_border_class": border_cls,
            }
        )
    return out


def _max_last_sync_among(projects: list[Project]) -> datetime | None:
    best: datetime | None = None
    for p in projects:
        t = p.last_sync_at
        if t is None:
            continue
        if best is None or t > best:
            best = t
    return best


def _rail_block_from_sa_entry(e: dict) -> dict | None:
    """Use rendered workflow HTML from SA entries (markdown preserved for the plot rail)."""
    html = (e.get("body_html") or "").strip()
    if not html:
        title = (e.get("title") or "").strip()
        if title and title.casefold() not in _RAIL_SA_TITLE_FALLBACK_BLOCK:
            html = workflow_md_to_html(title).strip()
    if not html:
        return None
    severity = "warning" if e.get("temporal_note") == "Temporal" else ""
    return {"body_html": html, "severity": severity}


def _rail_blocks_from_sa_entries(entries: list[dict], *, max_items: int) -> list[dict]:
    out: list[dict] = []
    for e in entries:
        if len(out) >= max_items:
            break
        row = _rail_block_from_sa_entry(e)
        if row:
            out.append(row)
    return out


def _rail_sa_disposition(*, max_items: int = 8) -> list[dict]:
    """Disposition (standing) blocks from the workspace SA head version."""
    awareness = get_or_create_awareness()
    version = head_version(awareness)
    return _rail_blocks_from_sa_entries(standing_entries_for(version), max_items=max_items)


def _rail_sa_active_situations(*, max_items: int = 8) -> list[dict]:
    """Active-situation blocks from the workspace SA head version."""
    awareness = get_or_create_awareness()
    version = head_version(awareness)
    return _rail_blocks_from_sa_entries(active_entries_for(version), max_items=max_items)


def _format_frago_effective_window(fr: Frago) -> str:
    def fmt(d: date) -> str:
        return d.strftime("%b %d, %Y")

    if fr.effective_from and fr.effective_to:
        return f"{fmt(fr.effective_from)} – {fmt(fr.effective_to)}"
    if fr.effective_from:
        return f"From {fmt(fr.effective_from)}"
    if fr.effective_to:
        return f"Until {fmt(fr.effective_to)}"
    return "No fixed effective dates"


def _rail_fragos_in_effect(*, max_items: int = 16) -> list[dict]:
    """FRAGOs that are enabled, not revoked, and within their effective date window."""
    today = date.today()
    qs = (
        Frago.objects.filter(
            Q(revoked_at__isnull=True, enabled=True)
            & (Q(effective_from__isnull=True) | Q(effective_from__lte=today))
            & (Q(effective_to__isnull=True) | Q(effective_to__gte=today)),
        )
        .select_related("project")
        .order_by("-updated_at", "-pk")[:max_items]
    )
    rows: list[dict] = []
    for fr in qs:
        proj = fr.project
        label = ((proj.display_name or "").strip() or proj.name).strip()
        body_raw = (fr.body_md or "").strip()
        rows.append(
            {
                "pk": fr.pk,
                "title": fr.title,
                "scope_label": f"project: {label}",
                "effective_label": _format_frago_effective_window(fr),
                "body_html": workflow_md_to_html(body_raw) if body_raw else "",
            },
        )
    return rows


class DashboardProjectsView(View):
    """GET: Tactical Plot — project list in same widget chrome as other rails."""

    template_name = "ui/dashboard/projects.html"

    def get(self, request, *args, **kwargs):
        qs = Project.objects.filter(status=Project.Status.ACTIVE).select_related("datasource").order_by("name")
        projects_list = list(qs)
        cards = _project_cards(projects_list)
        plot_last_sync_at = _max_last_sync_among(projects_list)
        return render(
            request,
            self.template_name,
            {
                "active_nav": "tactical_plot",
                "plot_last_sync_at": plot_last_sync_at,
                "rail_sa_disposition": _rail_sa_disposition(),
                "rail_situational_awareness": _rail_sa_active_situations(),
                "rail_fragos": _rail_fragos_in_effect(),
                "dashboard_projects": cards,
            },
        )
