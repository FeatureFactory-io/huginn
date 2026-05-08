"""Operational Situational Awareness — VIEW / EDIT.

Template parity: ui/templates/ui/situational_awareness/ from ui/templates/ui/mockups/sitawareness/.
"""

from __future__ import annotations

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import Http404, HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views import View

from ingestion.models import Project
from sitrep.models import SituationalAwarenessVersion
from ui.services import situational_awareness_service as sa_svc


def _active_tab(request: HttpRequest) -> str:
    raw = (request.GET.get("tab") or "document").strip().lower()
    return raw if raw in {"document", "versions"} else "document"


def _parse_version_param(raw: str | None) -> int | None:
    if raw is None:
        return None
    s = str(raw).strip()
    return int(s) if s.isdigit() else None


def _want_compare(request: HttpRequest) -> bool:
    return (request.GET.get("compare") or "").strip().lower() in {"1", "true", "yes"}


@method_decorator(login_required, name="dispatch")
class SituationalAwarenessView(View):
    """SITAWARENESS-VIEW-1 — workspace hub or Document | Versions tabs."""

    template_name = "ui/situational_awareness/view.html"

    def get(self, request: HttpRequest) -> HttpResponse:
        slug = (request.GET.get("project") or "").strip()
        if not slug:
            projects = list(Project.objects.filter(status=Project.Status.ACTIVE).order_by("name"))
            return render(
                request,
                "ui/situational_awareness/workspace.html",
                {"active_nav": "sitawareness", "projects": projects},
            )

        project = get_object_or_404(Project.objects.all(), slug=slug)
        tab = _active_tab(request)
        sa = sa_svc.get_or_create_awareness(project)
        head = sa_svc.head_version(sa)
        snap_n = _parse_version_param(request.GET.get("v"))
        snapshot_ver: SituationalAwarenessVersion | None = None
        if snap_n is not None:
            snapshot_ver = sa.versions.filter(version_number=snap_n).first()

        display_ver = snapshot_ver or head
        standing_entries = sa_svc.standing_entries_for(display_ver)
        active_entries = sa_svc.active_entries_for(display_ver)

        versions_qs = list(sa.versions.select_related("created_by").order_by("-version_number"))
        versions = sa_svc.format_versions_rows(versions_qs)

        compare_diff = ""
        if _want_compare(request) and snapshot_ver and head and snapshot_ver.pk != head.pk:
            compare_diff = sa_svc.unified_diff_versions(snapshot_ver, head)

        ctx = {
            "active_nav": "sitawareness",
            "project_slug": slug,
            "project_archived": project.status == Project.Status.ARCHIVED,
            "active_tab": tab,
            "standing_entries": standing_entries,
            "active_entries": active_entries,
            "versions": versions,
            "head_version_n": head.version_number if head else None,
            "snapshot_version_n": snapshot_ver.version_number if snapshot_ver else None,
            "compare_diff": compare_diff,
        }
        return render(request, self.template_name, ctx)


@method_decorator(login_required, name="dispatch")
class SituationalAwarenessEditView(View):
    template_name = "ui/situational_awareness/edit.html"

    def _archived_redirect(self, request: HttpRequest, slug: str) -> HttpResponse:
        messages.warning(request, "Archived projects cannot edit Situational Awareness.")
        return redirect(f"{reverse('sitawareness-view')}?project={slug}&tab=document")

    def get(self, request: HttpRequest) -> HttpResponse:
        slug = (request.GET.get("project") or "").strip()
        if not slug:
            raise Http404("project query parameter is required")
        project = get_object_or_404(Project.objects.all(), slug=slug)
        if project.status == Project.Status.ARCHIVED:
            return self._archived_redirect(request, slug)

        tab = _active_tab(request)
        sa = sa_svc.get_or_create_awareness(project)
        head = sa_svc.head_version(sa)
        standing_text = head.standing_md if head else ""
        active_text = head.active_md if head else ""
        versions_qs = list(sa.versions.select_related("created_by").order_by("-version_number"))
        versions = sa_svc.format_versions_rows(versions_qs)
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
        slug = (request.GET.get("project") or "").strip()
        if not slug:
            raise Http404("project query parameter is required")
        project = get_object_or_404(Project.objects.all(), slug=slug)
        if project.status == Project.Status.ARCHIVED:
            return self._archived_redirect(request, slug)

        tab = _active_tab(request)
        if tab != "document":
            return redirect(f"{reverse('sitawareness-edit')}?project={slug}&tab=document")

        standing_md = request.POST.get("standing_md", "")
        active_md = request.POST.get("active_md", "")
        change_summary = (request.POST.get("change_summary") or "").strip()
        sa = sa_svc.get_or_create_awareness(project)
        head = sa_svc.head_version(sa)
        versions_qs = list(sa.versions.select_related("created_by").order_by("-version_number"))
        versions = sa_svc.format_versions_rows(versions_qs)
        head_n = head.version_number if head else 0
        user = request.user if request.user.is_authenticated else None

        if not change_summary:
            messages.error(request, "Change summary is required.")
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

        _ver, err = sa_svc.append_version(
            awareness=sa,
            standing_md=standing_md,
            active_md=active_md,
            change_summary=change_summary,
            created_by=user,
        )
        if err:
            messages.error(request, err)
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

        messages.success(request, "Situational Awareness saved.")
        return redirect(f"{reverse('sitawareness-view')}?project={slug}&tab=document")
