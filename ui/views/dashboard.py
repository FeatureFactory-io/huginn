"""Tactical Plot (DASHBOARD-PROJECTS-1) — real project cards + mock rail."""

from __future__ import annotations

from datetime import datetime

from django.shortcuts import render
from django.views import View

from ingestion.models import DataSource, Project

# Mock sidebar (SitReps, FRAGOs, SA not wired in v1); plot header uses real last-sync when available.
MOCK_RAIL_SITUATIONAL_AWARENESS = [
    {"text": "Gitlab outage in progress", "severity": "warning"},
    {"text": "ESB to mainframes offline till tomorrow", "severity": "warning"},
]
MOCK_RAIL_FRAGOS = [
    {
        "title": ("Project X is in refactoring sprint — most of commits will fix(*) and refactor(*) — this is ok"),
        "scope_label": "project affected: X",
        "fragos_project": "project-x",
    },
    {
        "title": ("Angular commit conventional supersedes symantic convention — mix is fine for now"),
        "scope_label": "projects affected: ALL",
        "fragos_project": "",
    },
]

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
                "rail_situational_awareness": MOCK_RAIL_SITUATIONAL_AWARENESS,
                "rail_fragos": MOCK_RAIL_FRAGOS,
                "dashboard_projects": cards,
            },
        )
