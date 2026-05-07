"""Operational FRAGO UI — LIST / CREATE / VIEW / EDIT / REVOKE.

Parity markup: ui/templates/ui/mockups/fragos/.
"""

from __future__ import annotations

from datetime import date
from typing import Any

from django import forms
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
from playbooks.models import Playbook, PlaybookVariable, PlaybookVersion
from sitrep.models import Frago


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
    }


def _project_from_request(request: HttpRequest) -> tuple[Project, str]:
    slug = (request.GET.get("project") or "").strip()
    if not slug:
        raise Http404("project query parameter is required")
    project = get_object_or_404(Project.objects.all(), slug=slug)
    return project, slug


def _apply_list_filters(rows: list[dict[str, Any]], request: HttpRequest) -> list[dict[str, Any]]:
    status = (request.GET.get("status") or "").strip()
    variable = (request.GET.get("variable") or "").strip()
    in_effect = request.GET.get("in_effect") == "1"

    out = rows
    if status and status != "All":
        out = [r for r in out if r["status"] == status]
    if variable:
        out = [r for r in out if r["variable_abbrev"] == variable]
    if in_effect:
        out = [r for r in out if r["in_effect_now"]]
    return out


@method_decorator(login_required, name="dispatch")
class FragosListView(View):
    template_name = "ui/fragos/list.html"

    def get(self, request: HttpRequest) -> HttpResponse:
        project, slug = _project_from_request(request)
        qs = Frago.objects.filter(project=project).select_related("affected_variable").order_by("-updated_at", "-pk")
        rows = [_frago_row(fr) for fr in qs]
        rows = _apply_list_filters(rows, request)
        variable_choices = _variable_choices(project)
        ctx = {
            "active_nav": "fragos",
            "project_slug": slug,
            "row_count": len(rows),
            "rows": rows,
            "variable_choices": variable_choices,
            "filter_status": (request.GET.get("status") or "All").strip(),
            "filter_variable": (request.GET.get("variable") or "").strip(),
            "filter_in_effect": request.GET.get("in_effect") == "1",
        }
        return render(request, self.template_name, ctx)

    def post(self, request: HttpRequest) -> HttpResponse:
        """Toggle enabled for a FRAGO (same listing URL + project query)."""
        project, slug = _project_from_request(request)
        if request.POST.get("toggle_frago") != "1":
            return redirect(f"{reverse('fragos-list')}?{request.GET.urlencode()}")
        try:
            frago_id = int(request.POST.get("frago_id") or "0")
        except ValueError:
            messages.error(request, "Invalid FRAGO.")
            return redirect(f"{reverse('fragos-list')}?project={slug}")
        frago = get_object_or_404(Frago.objects.filter(project=project), pk=frago_id)
        if frago.revoked_at is not None:
            messages.warning(request, "Revoked FRAGOs cannot be toggled.")
        else:
            frago.enabled = not frago.enabled
            frago.save(update_fields=["enabled", "updated_at"])
            messages.success(request, "FRAGO updated.")
        return redirect(f"{reverse('fragos-list')}?{request.GET.urlencode()}")


class FragoForm(forms.ModelForm):
    affected_variable = forms.ModelChoiceField(
        queryset=PlaybookVariable.objects.none(),
        required=False,
        empty_label="— Global narrative override —",
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
                    "placeholder": "Belay Active Bug Count = 0 on Fridays",
                    "data-testid": "frago-title-input",
                },
            ),
            "body_md": forms.Textarea(
                attrs={
                    "rows": 10,
                    "class": "form-control font-monospace small",
                    "placeholder": "Free-form natural language for Gjallarhorn…",
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
        _, slug = _project_from_request(request)
        project = get_object_or_404(Project.objects.all(), slug=slug)
        form = FragoForm()
        variable_qs = PlaybookVariable.objects.none()
        ver = _playbook_version_for_project(project)
        if ver:
            variable_qs = ver.variables.order_by("sort_order")
        form.fields["affected_variable"].queryset = variable_qs
        form.fields["affected_variable"].required = False
        return render(
            request,
            self.template_name,
            {"active_nav": "fragos", "project_slug": slug, "form": form},
        )

    def post(self, request: HttpRequest) -> HttpResponse:
        _, slug = _project_from_request(request)
        project = get_object_or_404(Project.objects.all(), slug=slug)
        form = FragoForm(request.POST)
        variable_qs = PlaybookVariable.objects.none()
        ver = _playbook_version_for_project(project)
        if ver:
            variable_qs = ver.variables.order_by("sort_order")
        form.fields["affected_variable"].queryset = variable_qs
        form.fields["affected_variable"].required = False
        if form.is_valid():
            frago = form.save(commit=False)
            frago.project = project
            frago.created_by = request.user if request.user.is_authenticated else None
            frago.updated_by = frago.created_by
            frago.full_clean()
            frago.save()
            messages.success(request, "FRAGO created.")
            return redirect(f"{reverse('fragos-list')}?project={slug}")
        return render(
            request,
            self.template_name,
            {"active_nav": "fragos", "project_slug": slug, "form": form},
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
        form = FragoForm(instance=self.frago)
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
                "changelog": [],
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
            messages.success(request, "FRAGO revoked.")
        slug = frago.project.slug
        return redirect(f"{reverse('fragos-list')}?project={slug}")
