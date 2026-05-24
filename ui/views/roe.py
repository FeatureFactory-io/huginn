"""Operational Rules of Engagement UI — LIST / CREATE / VIEW / EDIT / DELETE."""

from __future__ import annotations

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Count
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views import View

from ingestion.models import Project
from roe.markdown_utils import workflow_md_to_html
from roe.models import RulesOfEngagement, RulesOfEngagementVersion
from roe.seed_constants import FEATUREFACTORY_ROE_SLUG
from ui.services.roe_service import (
    append_roe_version,
    apply_roe_list_filters,
    create_roe_with_version,
    delete_roe_if_allowed,
    editor_snapshot_from_version,
    parse_variables_from_post,
    roe_queryset_for_list,
)

PAD_VAR_ROWS = 24


def _roe_author(roe: RulesOfEngagement) -> str:
    if roe.created_by_id:
        return roe.created_by.email
    if roe.is_system_seed:
        return "system@huginn"
    return "—"


def _latest_version(roe: RulesOfEngagement) -> RulesOfEngagementVersion | None:
    return roe.versions.order_by("-version_number").first()


def _attach_snapshot_preview(snapshot: dict) -> None:
    snapshot["workflow_html"] = workflow_md_to_html(snapshot.get("workflow_md", "") or "")


def _padded_variable_slots(variables: list[dict]) -> list[tuple[int, dict]]:
    base = variables[:] + [{}] * max(0, PAD_VAR_ROWS - len(variables))
    return [(i, base[i]) for i in range(min(len(base), PAD_VAR_ROWS))]


@method_decorator(login_required, name="dispatch")
class RulesOfEngagementListView(View):
    template_name = "ui/roe/list.html"

    def get(self, request: HttpRequest) -> HttpResponse:
        qs = roe_queryset_for_list().select_related("created_by").order_by("name")
        qs = apply_roe_list_filters(
            qs,
            author=(request.GET.get("author") or "").strip(),
            used_by=(request.GET.get("used_by") or "").strip(),
            updated_within=(request.GET.get("updated_within") or "").strip(),
        )
        roes = list(qs)
        return render(
            request,
            self.template_name,
            {
                "active_nav": "roe",
                "roes": roes,
                "row_count": len(roes),
                "filter_author": (request.GET.get("author") or "").strip(),
                "filter_used_by": (request.GET.get("used_by") or "").strip(),
                "filter_updated_within": (request.GET.get("updated_within") or "").strip(),
            },
        )


@method_decorator(login_required, name="dispatch")
class RulesOfEngagementCreateView(View):
    template_name = "ui/roe/create.html"

    def get(self, request: HttpRequest) -> HttpResponse:
        seed = request.GET.get("seed") == "1"
        clone_id = (request.GET.get("clone") or "").strip()
        snapshot = editor_snapshot_from_version(None)
        banner = ""

        if seed:
            roe = RulesOfEngagement.objects.filter(slug=FEATUREFACTORY_ROE_SLUG).first()
            if roe:
                ver = _latest_version(roe)
                if ver:
                    snapshot = editor_snapshot_from_version(ver)
                    snapshot["name"] = ""
                    banner = "Cloning FeatureFactory RoE — set a name before Save as v1."
        elif clone_id.isdigit():
            src = RulesOfEngagement.objects.filter(pk=int(clone_id)).first()
            if src:
                ver = _latest_version(src)
                if ver:
                    snapshot = editor_snapshot_from_version(ver)
                    snapshot["name"] = ""
                    banner = f"Cloning {src.name} — pick a new name."

        _attach_snapshot_preview(snapshot)
        ctx = {
            "active_nav": "roe",
            "mode": "create",
            "form": snapshot,
            "form_errors": [],
            "page_title": "New Rules of Engagement",
            "save_button_label": "Save as v1",
            "cancel_url": reverse("roe-list"),
            "banner": banner,
            "variable_slots": _padded_variable_slots(snapshot["variables"]),
        }
        return render(request, self.template_name, ctx)

    def post(self, request: HttpRequest) -> HttpResponse:
        name = (request.POST.get("name") or "").strip()
        description = (request.POST.get("description") or "").strip()
        workflow_md = request.POST.get("workflow_md") or ""
        vars_, verr = parse_variables_from_post(request.POST)
        errors = [*verr]
        if not name:
            errors.insert(0, "Name is required.")

        snapshot = {
            "name": name,
            "description": description,
            "workflow_md": workflow_md,
            "variables": vars_,
        }
        _attach_snapshot_preview(snapshot)

        if errors:
            ctx = {
                "active_nav": "roe",
                "mode": "create",
                "form": snapshot,
                "form_errors": errors,
                "page_title": "New Rules of Engagement",
                "save_button_label": "Save as v1",
                "cancel_url": reverse("roe-list"),
                "banner": "",
                "variable_slots": _padded_variable_slots(vars_),
            }
            return render(request, self.template_name, ctx, status=400)

        roe = create_roe_with_version(
            user=request.user,
            name=name,
            description=description,
            workflow_md=workflow_md,
            variables=vars_,
        )
        messages.success(request, f"Rules of Engagement \u201c{roe.name}\u201d created as v1.")
        return redirect(reverse("roe-detail", args=[roe.pk]))


@method_decorator(login_required, name="dispatch")
class RulesOfEngagementDetailView(View):
    template_name = "ui/roe/detail.html"

    def get(self, request: HttpRequest, pk: int) -> HttpResponse:
        roe = get_object_or_404(
            RulesOfEngagement.objects.select_related("created_by").prefetch_related(
                "versions__variables",
                "versions__created_by",
            ),
            pk=pk,
        )
        tab = (request.GET.get("tab") or "roe").strip().lower()
        if tab not in ("roe", "versions"):
            tab = "roe"

        ver_num_raw = (request.GET.get("version") or "").strip()
        latest = _latest_version(roe)
        focused = latest
        if ver_num_raw.isdigit():
            focused = roe.versions.filter(version_number=int(ver_num_raw)).first() or latest

        snapshot = editor_snapshot_from_version(focused)
        _attach_snapshot_preview(snapshot)

        versions = list(roe.versions.order_by("-version_number"))
        assigned = list(
            Project.objects.filter(assigned_roe_id=roe.pk)
            .select_related("datasource", "pinned_roe_version")
            .order_by("name"),
        )

        ctx = {
            "active_nav": "roe",
            "roe": roe,
            "roe_author": _roe_author(roe),
            "active_tab": tab,
            "focused_version": focused,
            "snapshot": snapshot,
            "versions": versions,
            "used_projects": assigned,
            "latest_version": latest,
        }
        return render(request, self.template_name, ctx)

    def post(self, request: HttpRequest, pk: int) -> HttpResponse:
        return redirect(reverse("roe-detail", args=[pk]))


@method_decorator(login_required, name="dispatch")
class RulesOfEngagementEditView(View):
    template_name = "ui/roe/edit.html"

    def get(self, request: HttpRequest, pk: int) -> HttpResponse:
        roe = get_object_or_404(RulesOfEngagement.objects.select_related("created_by"), pk=pk)
        latest = _latest_version(roe)
        snapshot = editor_snapshot_from_version(latest)
        _attach_snapshot_preview(snapshot)
        next_n = (latest.version_number + 1) if latest else 1
        ctx = {
            "active_nav": "roe",
            "mode": "edit",
            "roe": roe,
            "roe_author": _roe_author(roe),
            "form": snapshot,
            "form_errors": [],
            "save_button_label": f"Save as v{next_n}",
            "cancel_url": reverse("roe-detail", args=[pk]),
            "variable_slots": _padded_variable_slots(snapshot["variables"]),
            "latest_version": latest,
        }
        return render(request, self.template_name, ctx)

    def post(self, request: HttpRequest, pk: int) -> HttpResponse:
        roe = get_object_or_404(RulesOfEngagement.objects.select_related("created_by"), pk=pk)
        latest = _latest_version(roe)
        change_summary = (request.POST.get("change_summary") or "").strip()
        name = (request.POST.get("name") or "").strip()
        description = (request.POST.get("description") or "").strip()
        workflow_md = request.POST.get("workflow_md") or ""
        vars_, verr = parse_variables_from_post(request.POST)
        errors = [*verr]
        if not name:
            errors.insert(0, "Name is required.")
        if not change_summary:
            errors.append("Change summary is required.")

        snapshot = {
            "name": name,
            "description": description,
            "workflow_md": workflow_md,
            "variables": vars_,
        }
        _attach_snapshot_preview(snapshot)

        if errors:
            next_n = (latest.version_number + 1) if latest else 1
            ctx = {
                "active_nav": "roe",
                "mode": "edit",
                "roe": roe,
                "roe_author": _roe_author(roe),
                "form": snapshot,
                "form_errors": errors,
                "save_button_label": f"Save as v{next_n}",
                "cancel_url": reverse("roe-detail", args=[pk]),
                "variable_slots": _padded_variable_slots(vars_),
                "latest_version": latest,
            }
            return render(request, self.template_name, ctx, status=400)

        append_roe_version(
            roe=roe,
            user=request.user,
            change_summary=change_summary,
            name=name,
            description=description,
            workflow_md=workflow_md,
            variables=vars_,
        )
        messages.success(request, f"Saved new version for \u201c{roe.name}\u201d.")
        return redirect(reverse("roe-detail", args=[pk]))


@method_decorator(login_required, name="dispatch")
class RulesOfEngagementDeleteView(View):
    template_name = "ui/roe/delete.html"

    def get(self, request: HttpRequest, pk: int) -> HttpResponse:
        roe = get_object_or_404(
            RulesOfEngagement.objects.annotate(used_by_count=Count("assigned_projects")),
            pk=pk,
        )
        used = list(Project.objects.filter(assigned_roe_id=roe.pk).order_by("name"))
        delete_disabled = roe.used_by_count > 0 or roe.is_system_seed
        return render(
            request,
            self.template_name,
            {
                "active_nav": "roe",
                "roe": roe,
                "project_count": roe.used_by_count,
                "delete_disabled": delete_disabled,
                "used_projects": used,
            },
        )

    def post(self, request: HttpRequest, pk: int) -> HttpResponse:
        ok, msg = delete_roe_if_allowed(pk)
        if ok:
            messages.success(request, "Rules of Engagement deleted.")
            return redirect(reverse("roe-list"))
        messages.error(request, msg or "Unable to delete Rules of Engagement.")
        return redirect(reverse("roe-delete", args=[pk]))
