"""Operational Playbooks UI — LIST / CREATE / VIEW / EDIT / DELETE."""

from __future__ import annotations

from urllib.parse import urlencode

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Count
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views import View

from ingestion.models import Project
from playbooks.markdown_utils import workflow_md_to_html
from playbooks.models import Playbook, PlaybookVersion
from playbooks.seed_constants import FEATUREFACTORY_PLAYBOOK_SLUG
from ui.services.playbooks_service import (
    append_playbook_version,
    apply_playbook_list_filters,
    create_playbook_with_version,
    delete_playbook_if_allowed,
    editor_snapshot_from_version,
    parse_variables_from_post,
    playbook_queryset_for_list,
)

PAD_VAR_ROWS = 24
PAD_TBL_ROWS = 12


def _pb_author(pb: Playbook) -> str:
    if pb.created_by_id:
        return pb.created_by.email
    if pb.is_system_seed:
        return "system@huginn"
    return "—"


def _latest_version(playbook: Playbook) -> PlaybookVersion | None:
    return playbook.versions.order_by("-version_number").first()


def _attach_snapshot_preview(snapshot: dict) -> None:
    snapshot["workflow_html"] = workflow_md_to_html(snapshot.get("workflow_md", "") or "")


def _padded_variable_slots(variables: list[dict]) -> list[tuple[int, dict]]:
    base = variables[:] + [{}] * max(0, PAD_VAR_ROWS - len(variables))
    return [(i, base[i]) for i in range(min(len(base), PAD_VAR_ROWS))]


def _padded_table_slots(tables: list[dict]) -> list[tuple[int, dict]]:
    augmented = [{**row, "drift_warning": ""} for row in tables]
    base = augmented + [{}] * max(0, PAD_TBL_ROWS - len(augmented))
    return [(i, base[i]) for i in range(min(len(base), PAD_TBL_ROWS))]


def _annotate_table_display(snapshot: dict) -> None:
    for t in snapshot.get("tables", []):
        t.setdefault("entity_label", t.get("entity", ""))


@method_decorator(login_required, name="dispatch")
class PlaybooksListView(View):
    template_name = "ui/playbooks/list.html"

    def get(self, request: HttpRequest) -> HttpResponse:
        qs = playbook_queryset_for_list().select_related("created_by").order_by("name")
        qs = apply_playbook_list_filters(
            qs,
            author=(request.GET.get("author") or "").strip(),
            used_by=(request.GET.get("used_by") or "").strip(),
            updated_within=(request.GET.get("updated_within") or "").strip(),
        )
        playbooks = list(qs)
        return render(
            request,
            self.template_name,
            {
                "active_nav": "playbooks",
                "playbooks": playbooks,
                "row_count": len(playbooks),
                "filter_author": (request.GET.get("author") or "").strip(),
                "filter_used_by": (request.GET.get("used_by") or "").strip(),
                "filter_updated_within": (request.GET.get("updated_within") or "").strip(),
            },
        )


@method_decorator(login_required, name="dispatch")
class PlaybooksCreateView(View):
    template_name = "ui/playbooks/create.html"

    def get(self, request: HttpRequest) -> HttpResponse:
        seed = request.GET.get("seed") == "1"
        clone_id = (request.GET.get("clone") or "").strip()
        snapshot = editor_snapshot_from_version(None)
        banner = ""

        if seed:
            pb = Playbook.objects.filter(slug=FEATUREFACTORY_PLAYBOOK_SLUG).first()
            if pb:
                ver = _latest_version(pb)
                if ver:
                    snapshot = editor_snapshot_from_version(ver)
                    snapshot["name"] = ""
                    banner = "Cloning FeatureFactory Playbook — set a name before Save as v1."
        elif clone_id.isdigit():
            src = Playbook.objects.filter(pk=int(clone_id)).first()
            if src:
                ver = _latest_version(src)
                if ver:
                    snapshot = editor_snapshot_from_version(ver)
                    snapshot["name"] = ""
                    banner = f"Cloning {src.name} — pick a new name."

        _attach_snapshot_preview(snapshot)
        _annotate_table_display(snapshot)
        ctx = {
            "active_nav": "playbooks",
            "mode": "create",
            "form": snapshot,
            "form_errors": [],
            "page_title": "New Playbook",
            "save_button_label": "Save as v1",
            "cancel_url": reverse("playbooks-list"),
            "banner": banner,
            "variable_slots": _padded_variable_slots(snapshot["variables"]),
            "table_slots": _padded_table_slots(snapshot.get("tables", [])),
            "entity_choices": [],
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
            "tables": [],
        }
        _attach_snapshot_preview(snapshot)
        _annotate_table_display(snapshot)

        if errors:
            ctx = {
                "active_nav": "playbooks",
                "mode": "create",
                "form": snapshot,
                "form_errors": errors,
                "page_title": "New Playbook",
                "save_button_label": "Save as v1",
                "cancel_url": reverse("playbooks-list"),
                "banner": "",
                "variable_slots": _padded_variable_slots(vars_),
                "table_slots": _padded_table_slots([]),
                "entity_choices": [],
            }
            return render(request, self.template_name, ctx, status=400)

        pb = create_playbook_with_version(
            user=request.user,
            name=name,
            description=description,
            workflow_md=workflow_md,
            variables=vars_,
        )
        messages.success(request, f"Playbook “{pb.name}” created as v1.")
        return redirect(reverse("playbooks-detail", args=[pb.pk]))


@method_decorator(login_required, name="dispatch")
class PlaybooksDetailView(View):
    template_name = "ui/playbooks/detail.html"

    def get(self, request: HttpRequest, pk: int) -> HttpResponse:
        playbook = get_object_or_404(
            Playbook.objects.select_related("created_by").prefetch_related(
                "versions__variables",
                "versions__created_by",
            ),
            pk=pk,
        )
        tab = (request.GET.get("tab") or "playbook").strip().lower()
        if tab not in ("playbook", "versions"):
            tab = "playbook"

        ver_num_raw = (request.GET.get("version") or "").strip()
        latest = _latest_version(playbook)
        focused = latest
        if ver_num_raw.isdigit():
            focused = playbook.versions.filter(version_number=int(ver_num_raw)).first() or latest

        snapshot = editor_snapshot_from_version(focused)
        _attach_snapshot_preview(snapshot)
        _annotate_table_display(snapshot)

        versions = list(playbook.versions.order_by("-version_number"))
        assigned = list(
            Project.objects.filter(assigned_playbook_id=playbook.pk)
            .select_related("datasource", "pinned_playbook_version")
            .order_by("name"),
        )

        validate_results: list[str] | None = None
        if request.GET.get("validate") == "1":
            validate_results = []

        ctx = {
            "active_nav": "playbooks",
            "pb": playbook,
            "pb_author": _pb_author(playbook),
            "active_tab": tab,
            "focused_version": focused,
            "snapshot": snapshot,
            "versions": versions,
            "used_projects": assigned,
            "validate_results": validate_results,
            "latest_version": latest,
            "version_total": playbook.versions.count(),
        }
        return render(request, self.template_name, ctx)

    def post(self, request: HttpRequest, pk: int) -> HttpResponse:
        if (request.POST.get("action") or "").strip() != "validate":
            return redirect(reverse("playbooks-detail", args=[pk]))
        q = urlencode({"validate": "1"})
        return redirect(f"{reverse('playbooks-detail', args=[pk])}?{q}")


@method_decorator(login_required, name="dispatch")
class PlaybooksEditView(View):
    template_name = "ui/playbooks/edit.html"

    def get(self, request: HttpRequest, pk: int) -> HttpResponse:
        playbook = get_object_or_404(Playbook.objects.select_related("created_by"), pk=pk)
        latest = _latest_version(playbook)
        snapshot = editor_snapshot_from_version(latest)
        _attach_snapshot_preview(snapshot)
        _annotate_table_display(snapshot)
        next_n = (latest.version_number + 1) if latest else 1
        ctx = {
            "active_nav": "playbooks",
            "mode": "edit",
            "pb": playbook,
            "pb_author": _pb_author(playbook),
            "form": snapshot,
            "form_errors": [],
            "catalog_drift_banner": "",
            "save_button_label": f"Save as v{next_n}",
            "cancel_url": reverse("playbooks-detail", args=[pk]),
            "variable_slots": _padded_variable_slots(snapshot["variables"]),
            "table_slots": _padded_table_slots(snapshot.get("tables", [])),
            "entity_choices": [],
            "latest_version": latest,
        }
        return render(request, self.template_name, ctx)

    def post(self, request: HttpRequest, pk: int) -> HttpResponse:
        playbook = get_object_or_404(Playbook.objects.select_related("created_by"), pk=pk)
        latest = _latest_version(playbook)
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
            "tables": [],
        }
        _attach_snapshot_preview(snapshot)
        _annotate_table_display(snapshot)

        if errors:
            next_n = (latest.version_number + 1) if latest else 1
            ctx = {
                "active_nav": "playbooks",
                "mode": "edit",
                "pb": playbook,
                "pb_author": _pb_author(playbook),
                "form": snapshot,
                "form_errors": errors,
                "catalog_drift_banner": "",
                "save_button_label": f"Save as v{next_n}",
                "cancel_url": reverse("playbooks-detail", args=[pk]),
                "variable_slots": _padded_variable_slots(vars_),
                "table_slots": _padded_table_slots([]),
                "entity_choices": [],
                "latest_version": latest,
            }
            return render(request, self.template_name, ctx, status=400)

        append_playbook_version(
            playbook=playbook,
            user=request.user,
            change_summary=change_summary,
            name=name,
            description=description,
            workflow_md=workflow_md,
            variables=vars_,
        )
        messages.success(request, f"Saved new version for “{playbook.name}”.")
        return redirect(reverse("playbooks-detail", args=[pk]))


@method_decorator(login_required, name="dispatch")
class PlaybooksDeleteView(View):
    template_name = "ui/playbooks/delete.html"

    def get(self, request: HttpRequest, pk: int) -> HttpResponse:
        playbook = get_object_or_404(
            Playbook.objects.annotate(used_by_count=Count("assigned_projects")),
            pk=pk,
        )
        used = list(Project.objects.filter(assigned_playbook_id=playbook.pk).order_by("name"))
        delete_disabled = playbook.used_by_count > 0 or playbook.is_system_seed
        return render(
            request,
            self.template_name,
            {
                "active_nav": "playbooks",
                "pb": playbook,
                "project_count": playbook.used_by_count,
                "delete_disabled": delete_disabled,
                "used_projects": used,
            },
        )

    def post(self, request: HttpRequest, pk: int) -> HttpResponse:
        ok, msg = delete_playbook_if_allowed(pk)
        if ok:
            messages.success(request, "Playbook deleted.")
            return redirect(reverse("playbooks-list"))
        messages.error(request, msg or "Unable to delete playbook.")
        return redirect(reverse("playbooks-delete", args=[pk]))
