"""Operational FRAGO UI — LIST / CREATE / VIEW / EDIT / REVOKE.

Parity markup: ui/templates/ui/mockups/fragos/.
"""

from __future__ import annotations

from datetime import date
from typing import Any

from django import forms
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.db import transaction
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views import View

from ingestion.models import Project
from playbooks.markdown_utils import workflow_md_to_html
from playbooks.models import Playbook, PlaybookVariable, PlaybookVersion
from sitrep.models import Frago, FragoAuditEvent
from ui.services.frago_audit_service import record_frago_audit
from ui.services.fragos_service import apply_frago_list_filters, frago_list_queryset


def _playbook_version_for_project(project: Project) -> PlaybookVersion | None:
    if project.pinned_playbook_version_id:
        return PlaybookVersion.objects.filter(pk=project.pinned_playbook_version_id).first()
    if project.assigned_playbook_id:
        return (
            PlaybookVersion.objects.filter(playbook_id=project.assigned_playbook_id).order_by("-version_number").first()
        )
    if project.playbook_slug:
        pb = Playbook.objects.filter(slug=project.playbook_slug).first()
        if pb:
            return pb.versions.order_by("-version_number").first()
    return None


def _variable_choices(project: Project) -> list[tuple[str, str]]:
    ver = _playbook_version_for_project(project)
    if not ver:
        return []
    rows = list(
        ver.variables.order_by("sort_order").values_list("abbrev", "name"),
    )
    return [("", "All Variables")] + [(abbrev, name) for abbrev, name in rows]


def _frago_row(fr: Frago) -> dict[str, Any]:
    revoked = fr.revoked_at is not None
    tag = fr.affected_variable.name if fr.affected_variable_id else "—"
    abbrev = fr.affected_variable.abbrev if fr.affected_variable_id else ""
    parts: list[str] = []
    if fr.effective_from:
        parts.append(fr.effective_from.isoformat())
    if fr.effective_to:
        parts.append(fr.effective_to.isoformat())
    effective = " → ".join(parts) if parts else "—"

    today = date.today()
    if revoked:
        status, cls = "Revoked", "secondary"
    elif not fr.enabled:
        status, cls = "Inactive", "secondary"
    elif fr.effective_from and fr.effective_from > today:
        status, cls = "Scheduled", "info"
    elif fr.effective_to and fr.effective_to < today:
        status, cls = "Expired", "warning"
    else:
        status, cls = "Active", "success"

    in_window = True
    if fr.effective_from and fr.effective_from > today:
        in_window = False
    if fr.effective_to and fr.effective_to < today:
        in_window = False

    return {
        "id": fr.id,
        "enabled": fr.enabled,
        "title": fr.title,
        "tag": tag,
        "variable_abbrev": abbrev,
        "effective": effective,
        "status": status,
        "status_class": cls,
        "revoked": revoked,
        "in_effect_now": in_window and fr.enabled and not revoked,
        "project_slug": fr.project.slug,
        "project_label": fr.project.display_name or fr.project.name,
    }


def _project_for_list_optional(request: HttpRequest) -> tuple[Project | None, str]:
    slug = (request.GET.get("project") or "").strip()
    if not slug:
        return None, ""
    project = get_object_or_404(Project.objects.all(), slug=slug)
    return project, slug


def _active_projects_choices() -> list[tuple[str, str]]:
    rows = Project.objects.filter(status=Project.Status.ACTIVE).order_by("name")
    return [(p.slug, p.display_name or p.name) for p in rows]


@method_decorator(login_required, name="dispatch")
class FragosListView(View):
    template_name = "ui/fragos/list.html"

    def get(self, request: HttpRequest) -> HttpResponse:
        project, slug = _project_for_list_optional(request)
        qs = frago_list_queryset(project)
        qs = apply_frago_list_filters(qs, request)
        rows = [_frago_row(fr) for fr in qs]
        status_raw = (request.GET.get("status") or "").strip()
        filter_status_key = status_raw.lower() if status_raw and status_raw != "All" else ""
        ctx = {
            "active_nav": "fragos",
            "project_slug": slug,
            "show_project_column": project is None,
            "row_count": len(rows),
            "rows": rows,
            "project_filter_choices": _active_projects_choices(),
            "filter_timing": (request.GET.get("timing") or "").strip().lower(),
            "filter_status": filter_status_key,
            "filter_status_raw": status_raw,
            "filter_affects": (request.GET.get("affects") or "").strip().lower(),
            "filter_variable": (request.GET.get("variable") or "").strip(),
            "filter_in_effect": request.GET.get("in_effect") == "1",
        }
        return render(request, self.template_name, ctx)

    def post(self, request: HttpRequest) -> HttpResponse:
        slug = (request.GET.get("project") or "").strip()
        q_redirect = request.GET.urlencode()
        dest = f"{reverse('fragos-list')}?{q_redirect}" if q_redirect else reverse("fragos-list")

        bulk = (request.POST.get("bulk_action") or "").strip().lower()
        if bulk in {"activate", "deactivate", "revoke"}:
            raw_ids = request.POST.getlist("frago_ids")
            id_list = [int(x) for x in raw_ids if x.isdigit()]
            if not id_list:
                messages.warning(request, "Select at least one FRAGO.")
                return redirect(dest)
            qs = Frago.objects.filter(pk__in=id_list)
            if slug:
                qs = qs.filter(project__slug=slug)
            count = 0
            with transaction.atomic():
                for frago in qs:
                    if bulk == "revoke":
                        if frago.revoked_at is not None:
                            continue
                        frago.revoked_at = timezone.now()
                        frago.enabled = False
                        frago.save(update_fields=["revoked_at", "enabled", "updated_at"])
                        record_frago_audit(
                            frago,
                            request,
                            kind=FragoAuditEvent.Kind.BULK_REVOKED.value,
                            message=f"Bulk revoked: {frago.title[:200]}",
                        )
                        count += 1
                    elif frago.revoked_at is not None:
                        continue
                    elif bulk == "activate":
                        if frago.enabled:
                            continue
                        frago.enabled = True
                        frago.save(update_fields=["enabled", "updated_at"])
                        record_frago_audit(
                            frago,
                            request,
                            kind=FragoAuditEvent.Kind.BULK_ACTIVATED.value,
                            message=f"Bulk activated: {frago.title[:200]}",
                        )
                        count += 1
                    elif bulk == "deactivate":
                        if not frago.enabled:
                            continue
                        frago.enabled = False
                        frago.save(update_fields=["enabled", "updated_at"])
                        record_frago_audit(
                            frago,
                            request,
                            kind=FragoAuditEvent.Kind.BULK_DEACTIVATED.value,
                            message=f"Bulk deactivated: {frago.title[:200]}",
                        )
                        count += 1
            if count:
                messages.success(request, f"Updated {count} FRAGO(s).")
            else:
                messages.info(request, "No eligible FRAGOs were updated.")
            return redirect(dest)

        if request.POST.get("toggle_frago") != "1":
            return redirect(dest)
        try:
            frago_id = int(request.POST.get("frago_id") or "0")
        except ValueError:
            messages.error(request, "Invalid FRAGO.")
            return redirect(dest)
        if slug:
            proj = get_object_or_404(Project.objects.all(), slug=slug)
            frago = get_object_or_404(Frago.objects.filter(project=proj), pk=frago_id)
        else:
            frago = get_object_or_404(Frago.objects.all(), pk=frago_id)
        if frago.revoked_at is not None:
            messages.warning(request, "Revoked FRAGOs cannot be toggled.")
        else:
            new_enabled = not frago.enabled
            frago.enabled = new_enabled
            frago.save(update_fields=["enabled", "updated_at"])
            record_frago_audit(
                frago,
                request,
                kind=FragoAuditEvent.Kind.ENABLED_TOGGLED.value,
                message=f"Set to {'enabled' if new_enabled else 'disabled'}.",
            )
            messages.success(request, "FRAGO updated.")
        return redirect(dest)


class FragoForm(forms.ModelForm):
    affects = forms.ChoiceField(
        label="Affects",
        choices=[
            ("", "---------"),
            ("narrative", "Narrative"),
            ("variables", "Variable(s)"),
        ],
        required=False,
        widget=forms.Select(
            attrs={
                "class": "form-select form-select-sm",
                "data-testid": "frago-affects-select",
            },
        ),
    )

    affected_variable = forms.ModelChoiceField(
        queryset=PlaybookVariable.objects.none(),
        required=False,
        empty_label="— Choose variable —",
        widget=forms.Select(
            attrs={
                "class": "form-select form-select-sm",
                "data-testid": "frago-variable-tag-select",
            },
        ),
    )

    class Meta:
        model = Frago
        fields = ("title", "body_md", "affected_variable", "effective_from", "effective_to")
        widgets = {
            "title": forms.TextInput(
                attrs={
                    "class": "form-control form-control-sm",
                    "placeholder": "Short label for this change",
                    "data-testid": "frago-title-input",
                },
            ),
            "body_md": forms.Textarea(
                attrs={
                    "rows": 10,
                    "class": "form-control font-monospace small",
                    "placeholder": "Detailed instructions—markdown supported (optional)",
                    "data-testid": "frago-body-input",
                },
            ),
            "effective_from": forms.DateInput(
                attrs={
                    "type": "date",
                    "class": "form-control form-control-sm",
                    "data-testid": "frago-scope-start",
                },
            ),
            "effective_to": forms.DateInput(
                attrs={
                    "type": "date",
                    "class": "form-control form-control-sm",
                    "data-testid": "frago-scope-end",
                },
            ),
        }

    def clean(self) -> dict[str, Any]:
        cleaned = super().clean()
        affects = (cleaned.get("affects") or "").strip()
        av = cleaned.get("affected_variable")
        if affects == "narrative":
            cleaned["affected_variable"] = None
        elif affects == "variables":
            if av is None:
                raise ValidationError(
                    {"affected_variable": "Select a Playbook Variable when Affects is Variable(s)."},
                )
        elif affects == "" and av is None:
            cleaned["affected_variable"] = None
        return cleaned

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.fields["title"].help_text = "What shall we temporarily override in the playbook and why?"


def _apply_frago_edit_widgets(form: FragoForm) -> None:
    """Match operational edit template data-testids."""
    form.fields["title"].widget.attrs.update(
        {
            "id": "edit-frago-title",
            "data-testid": "frago-edit-title-input",
        },
    )
    form.fields["body_md"].widget.attrs.update(
        {
            "id": "edit-frago-body",
            "rows": 10,
            "data-testid": "frago-edit-body-input",
        },
    )
    form.fields["affected_variable"].widget.attrs.update(
        {
            "id": "edit-frago-tag",
            "data-testid": "frago-edit-variable-tag",
        },
    )
    form.fields["affects"].widget.attrs.update(
        {
            "id": "edit-frago-affects",
            "data-testid": "frago-edit-affects-select",
        },
    )
    form.fields["effective_from"].widget.attrs.update(
        {
            "id": "edit-frago-effective-from",
            "data-testid": "frago-edit-scope-start",
        },
    )
    form.fields["effective_to"].widget.attrs.update(
        {
            "id": "edit-frago-effective-to",
            "data-testid": "frago-edit-scope-end",
        },
    )


@method_decorator(login_required, name="dispatch")
class FragosCreateView(View):
    template_name = "ui/fragos/create.html"

    def get(self, request: HttpRequest) -> HttpResponse:
        slug = (request.GET.get("project") or "").strip()
        project = get_object_or_404(Project.objects.all(), slug=slug) if slug else None
        form = FragoForm()
        variable_qs = PlaybookVariable.objects.none()
        ver = _playbook_version_for_project(project) if project else None
        if ver:
            variable_qs = ver.variables.order_by("sort_order")
        form.fields["affected_variable"].queryset = variable_qs
        form.fields["affected_variable"].required = False
        return render(
            request,
            self.template_name,
            {
                "active_nav": "fragos",
                "project_slug": slug,
                "project_choices": _active_projects_choices(),
                "form": form,
            },
        )

    def post(self, request: HttpRequest) -> HttpResponse:
        slug = (request.POST.get("project") or "").strip()
        project_choices = _active_projects_choices()
        form = FragoForm(request.POST)
        project = get_object_or_404(Project.objects.all(), slug=slug) if slug else None
        variable_qs = PlaybookVariable.objects.none()
        ver = _playbook_version_for_project(project) if project else None
        if ver:
            variable_qs = ver.variables.order_by("sort_order")
        form.fields["affected_variable"].queryset = variable_qs
        form.fields["affected_variable"].required = False
        if not project:
            messages.error(request, "Choose a project.")
            return render(
                request,
                self.template_name,
                {
                    "active_nav": "fragos",
                    "project_slug": "",
                    "project_choices": project_choices,
                    "form": form,
                },
            )
        if form.is_valid():
            frago = form.save(commit=False)
            frago.project = project
            frago.created_by = request.user if request.user.is_authenticated else None
            frago.updated_by = frago.created_by
            frago.full_clean()
            frago.save()
            record_frago_audit(
                frago,
                request,
                kind=FragoAuditEvent.Kind.CREATED.value,
                message="FRAGO created.",
            )
            messages.success(request, "FRAGO created.")
            return redirect(f"{reverse('fragos-list')}?project={slug}")
        return render(
            request,
            self.template_name,
            {
                "active_nav": "fragos",
                "project_slug": slug,
                "project_choices": project_choices,
                "form": form,
            },
        )


@method_decorator(login_required, name="dispatch")
class FragosEditView(View):
    template_name = "ui/fragos/edit.html"

    def dispatch(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        self.frago = get_object_or_404(Frago.objects.select_related("project"), pk=kwargs["pk"])
        if self.frago.revoked_at is not None:
            messages.warning(request, "This FRAGO is revoked and cannot be edited.")
            return redirect(f"{reverse('fragos-detail', args=[self.frago.pk])}")
        return super().dispatch(request, *args, **kwargs)

    def get(self, request: HttpRequest, pk: int) -> HttpResponse:
        del pk
        initial_affects = "variables" if self.frago.affected_variable_id else "narrative"
        form = FragoForm(instance=self.frago, initial={"affects": initial_affects})
        variable_qs = PlaybookVariable.objects.none()
        ver = _playbook_version_for_project(self.frago.project)
        if ver:
            variable_qs = ver.variables.order_by("sort_order")
        form.fields["affected_variable"].queryset = variable_qs
        form.fields["affected_variable"].required = False
        _apply_frago_edit_widgets(form)
        fg = {"id": self.frago.pk, "title": self.frago.title}
        ctx = {
            "active_nav": "fragos",
            "project_slug": self.frago.project.slug,
            "fg": fg,
            "form": form,
        }
        return render(request, self.template_name, ctx)

    def post(self, request: HttpRequest, pk: int) -> HttpResponse:
        del pk
        form = FragoForm(request.POST, instance=self.frago)
        variable_qs = PlaybookVariable.objects.none()
        ver = _playbook_version_for_project(self.frago.project)
        if ver:
            variable_qs = ver.variables.order_by("sort_order")
        form.fields["affected_variable"].queryset = variable_qs
        form.fields["affected_variable"].required = False
        _apply_frago_edit_widgets(form)
        if form.is_valid():
            frago = form.save(commit=False)
            frago.updated_by = request.user if request.user.is_authenticated else None
            frago.full_clean()
            frago.save()
            record_frago_audit(
                frago,
                request,
                kind=FragoAuditEvent.Kind.UPDATED.value,
                message="FRAGO saved.",
            )
            messages.success(request, "FRAGO saved.")
            return redirect(reverse("fragos-detail", args=[frago.pk]))
        fg = {"id": self.frago.pk, "title": self.frago.title}
        ctx = {
            "active_nav": "fragos",
            "project_slug": self.frago.project.slug,
            "fg": fg,
            "form": form,
        }
        return render(request, self.template_name, ctx)


@method_decorator(login_required, name="dispatch")
class FragosDetailView(View):
    template_name = "ui/fragos/view.html"

    def get(self, request: HttpRequest, pk: int) -> HttpResponse:
        frago = get_object_or_404(
            Frago.objects.select_related("project", "affected_variable"),
            pk=pk,
        )
        tag = frago.affected_variable.name if frago.affected_variable_id else "—"
        parts: list[str] = []
        if frago.effective_from:
            parts.append(f"from {frago.effective_from.isoformat()}")
        if frago.effective_to:
            parts.append(f"to {frago.effective_to.isoformat()}")
        effective = ", ".join(parts) if parts else "—"

        today = date.today()
        if frago.revoked_at:
            st, sc = "Revoked", "secondary"
        elif not frago.enabled:
            st, sc = "Inactive", "secondary"
        elif frago.effective_from and frago.effective_from > today:
            st, sc = "Scheduled", "info"
        elif frago.effective_to and frago.effective_to < today:
            st, sc = "Expired", "warning"
        else:
            st, sc = "Active", "success"

        changelog: list[dict[str, Any]] = []
        for ev in frago.audit_events.select_related("actor").order_by("-created_at")[:100]:
            actor_label = "—"
            if ev.actor_id:
                actor_label = ev.actor.get_full_name() or ev.actor.email or "—"
            changelog.append(
                {
                    "action": ev.message,
                    "actor": actor_label,
                    "at": ev.created_at,
                },
            )

        ctx = {
            "active_nav": "fragos",
            "project_slug": frago.project.slug,
            "fg": {
                "id": frago.pk,
                "title": frago.title,
                "enabled": frago.enabled,
                "revoked": frago.revoked_at is not None,
                "tag": tag,
                "status": st,
                "status_class": sc,
                "effective": effective,
                "markdown_body_html": workflow_md_to_html(frago.body_md or ""),
                "applications": [],
                "changelog": changelog,
            },
        }
        return render(request, self.template_name, ctx)


@method_decorator(login_required, name="dispatch")
class FragosRevokeView(View):
    template_name = "ui/fragos/revoke.html"

    def get(self, request: HttpRequest, pk: int) -> HttpResponse:
        frago = get_object_or_404(Frago.objects.all(), pk=pk)
        return render(
            request,
            self.template_name,
            {"active_nav": "fragos", "title": frago.title, "frago": frago},
        )

    def post(self, request: HttpRequest, pk: int) -> HttpResponse:
        frago = get_object_or_404(Frago.objects.select_related("project"), pk=pk)
        if frago.revoked_at is None:
            frago.revoked_at = timezone.now()
            frago.enabled = False
            frago.save(update_fields=["revoked_at", "enabled", "updated_at"])
            record_frago_audit(
                frago,
                request,
                kind=FragoAuditEvent.Kind.REVOKED.value,
                message="FRAGO revoked.",
            )
            messages.success(request, "FRAGO revoked.")
        slug = frago.project.slug
        return redirect(f"{reverse('fragos-list')}?project={slug}")
