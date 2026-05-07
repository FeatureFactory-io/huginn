"""Operational Situational Awareness — VIEW / EDIT.

Template parity: ui/templates/ui/situational_awareness/ from ui/templates/ui/mockups/sitawareness/.
"""

from __future__ import annotations

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import Http404, HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views import View

from ingestion.models import Project
from playbooks.markdown_utils import workflow_md_to_html
from sitrep.models import SituationalAwareness, SituationalAwarenessVersion


def _project_from_request(request: HttpRequest) -> tuple[Project, str]:
    slug = (request.GET.get("project") or "").strip()
    if not slug:
        raise Http404("project query parameter is required")
    project = get_object_or_404(Project.objects.all(), slug=slug)
    return project, slug


def _active_tab(request: HttpRequest) -> str:
    raw = (request.GET.get("tab") or "document").strip().lower()
    return raw if raw in {"document", "versions"} else "document"


def _get_or_create_awareness(project: Project) -> SituationalAwareness:
    sa, _ = SituationalAwareness.objects.get_or_create(project=project)
    return sa


def _head_version(sa: SituationalAwareness) -> SituationalAwarenessVersion | None:
    return sa.versions.order_by("-version_number").first()


def _entries_from_md(md: str, *, temporal_hint: bool) -> list[dict]:
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


def _format_versions_rows(qs: list[SituationalAwarenessVersion]) -> list[dict]:
    rows = []
    for v in qs:
        actor = "—"
        if v.created_by_id:
            u = v.created_by
            actor = getattr(u, "full_name", None) or getattr(u, "email", None) or str(u)
        rows.append(
            {
                "n": v.version_number,
                "on": timezone.localtime(v.created_at).strftime("%Y-%m-%d %H:%M"),
                "author": actor,
                "summary": v.change_summary or "—",
            },
        )
    return rows


@method_decorator(login_required, name="dispatch")
class SituationalAwarenessView(View):
    """SITAWARENESS-VIEW-1 — Document | Versions tabs."""

    template_name = "ui/situational_awareness/view.html"

    def get(self, request: HttpRequest) -> HttpResponse:
        project, slug = _project_from_request(request)
        tab = _active_tab(request)
        sa = _get_or_create_awareness(project)
        head = _head_version(sa)
        standing_md = head.standing_md if head else ""
        active_md = head.active_md if head else ""
        standing_entries = _entries_from_md(standing_md, temporal_hint=False)
        active_entries = _entries_from_md(active_md, temporal_hint=True)
        versions_qs = list(sa.versions.select_related("created_by").order_by("-version_number"))
        versions = _format_versions_rows(versions_qs)

        ctx = {
            "active_nav": "sitawareness",
            "project_slug": slug,
            "active_tab": tab,
            "standing_entries": standing_entries,
            "active_entries": active_entries,
            "versions": versions,
        }
        return render(request, self.template_name, ctx)


@method_decorator(login_required, name="dispatch")
class SituationalAwarenessEditView(View):
    template_name = "ui/situational_awareness/edit.html"

    def get(self, request: HttpRequest) -> HttpResponse:
        project, slug = _project_from_request(request)
        tab = _active_tab(request)
        sa = _get_or_create_awareness(project)
        head = _head_version(sa)
        standing_text = head.standing_md if head else ""
        active_text = head.active_md if head else ""
        versions_qs = list(sa.versions.select_related("created_by").order_by("-version_number"))
        versions = _format_versions_rows(versions_qs)
        head_n = head.version_number if head else 0

        ctx = {
            "active_nav": "sitawareness",
            "project_slug": slug,
            "active_tab": tab,
            "standing_text": standing_text,
            "active_text": active_text,
            "versions": versions,
            "head_version_n": head_n,
        }
        return render(request, self.template_name, ctx)

    def post(self, request: HttpRequest) -> HttpResponse:
        project, slug = _project_from_request(request)
        tab = _active_tab(request)
        if tab != "document":
            return redirect(f"{reverse('sitawareness-edit')}?project={slug}&tab=document")

        standing_md = request.POST.get("standing_md", "")
        active_md = request.POST.get("active_md", "")
        change_summary = (request.POST.get("change_summary") or "").strip()
        if not change_summary:
            messages.error(request, "Change summary is required.")
            sa = _get_or_create_awareness(project)
            head = _head_version(sa)
            versions_qs = list(sa.versions.select_related("created_by").order_by("-version_number"))
            versions = _format_versions_rows(versions_qs)
            head_n = head.version_number if head else 0
            return render(
                request,
                self.template_name,
                {
                    "active_nav": "sitawareness",
                    "project_slug": slug,
                    "active_tab": "document",
                    "standing_text": standing_md,
                    "active_text": active_md,
                    "versions": versions,
                    "head_version_n": head_n,
                },
            )

        sa = _get_or_create_awareness(project)
        head = _head_version(sa)
        next_n = (head.version_number + 1) if head else 1
        user = request.user if request.user.is_authenticated else None
        SituationalAwarenessVersion.objects.create(
            awareness=sa,
            version_number=next_n,
            standing_md=standing_md,
            active_md=active_md,
            change_summary=change_summary,
            created_by=user,
        )
        messages.success(request, "Situational Awareness saved.")
        return redirect(f"{reverse('sitawareness-view')}?project={slug}&tab=document")
