"""Tactical Plot (DASHBOARD-PROJECTS-1) — real project cards + mock rail."""

from __future__ import annotations

from django.shortcuts import render
from django.views import View

from ingestion.models import DataSource, Project

# Mock sidebar / summary (SitReps, FRAGOs, SA not wired in v1).
MOCK_SUMMARY_STRIP = {"red": 2, "orange": 1, "yellow": 4, "green": 6}
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


def _sources_for_project(project: Project) -> list[dict]:
    ds = project.datasource
    if ds is None:
        return []
    meta = _DS_SOURCE_META.get(ds.datasource_type)
    if meta:
        return [dict(meta)]
    raw = str(ds.datasource_type)
    return [{"key": raw, "label": raw.replace("_", " ").title(), "si_slug": raw}]


def _description_for_project(project: Project) -> str:
    """Prefer persisted GitLab description for the dashboard card subtitle."""
    desc = (project.description or "").strip()
    if desc:
        return desc
    path = (project.source_path or "").strip()
    if path:
        return path
    return "—"


def _project_cards(projects: list[Project]) -> list[dict]:
    out: list[dict] = []
    for p in projects:
        name = (p.display_name or "").strip() or p.name
        out.append(
            {
                "pk": p.pk,
                "name": name,
                "description": _description_for_project(p),
                "sources": _sources_for_project(p),
            }
        )
    return out


class DashboardProjectsView(View):
    """GET: Tactical Plot — real project cards + mock chrome."""

    template_name = "ui/dashboard/projects.html"

    def get(self, request, *args, **kwargs):
        qs = Project.objects.filter(status=Project.Status.ACTIVE).select_related("datasource").order_by("name")
        cards = _project_cards(list(qs))
        return render(
            request,
            self.template_name,
            {
                "active_nav": "tactical_plot",
                "summary_strip": MOCK_SUMMARY_STRIP,
                "rail_situational_awareness": MOCK_RAIL_SITUATIONAL_AWARENESS,
                "rail_fragos": MOCK_RAIL_FRAGOS,
                "dashboard_projects": cards,
            },
        )
