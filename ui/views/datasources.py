"""Operational DataSource routes (Acts 1)."""

import logging
from datetime import timedelta

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError
from django.db.models import Q
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views import View

from ingestion.integrations.github_client import normalize_github_token
from ingestion.models import DataSource, Project
from ui.services.datasources_service import DataSourcesService

logger = logging.getLogger("ingestion.datasources")


def _create_post_context(**kwargs) -> dict:
    ctx = {"active_nav": "datasources"}
    ctx.update(kwargs)
    ctx.setdefault("step", 1)
    return ctx


def _datasources_filtered_get_queryset(*, type_filter: str, status_filter: str):
    qs = DataSource.objects.all().order_by("name")
    if type_filter in (DataSource.Type.GITLAB, DataSource.Type.GITHUB, DataSource.Type.JIRA):
        qs = qs.filter(datasource_type=type_filter)
    now = timezone.now()
    expires_soon_limit = now + timedelta(days=30)
    if status_filter == DataSource.Status.CONNECTION_ERROR:
        qs = qs.filter(status=DataSource.Status.CONNECTION_ERROR)
    elif status_filter == DataSource.Status.TOKEN_EXPIRED:
        qs = qs.filter(token_expires_at__lt=now)
    elif status_filter == DataSource.Status.TOKEN_EXPIRING:
        qs = qs.filter(token_expires_at__lte=expires_soon_limit, token_expires_at__gte=now)
    elif status_filter == DataSource.Status.CONNECTED:
        qs = qs.filter(status=DataSource.Status.CONNECTED).filter(
            Q(token_expires_at__isnull=True) | Q(token_expires_at__gt=expires_soon_limit)
        )
    return qs


def _connection_test_message(meta: dict, *, noun: str) -> str:
    username = meta.get("username") or meta.get("login") or meta.get("name") or "unknown"
    count = meta.get("visible_project_count")
    count_str = "?" if count is None else str(count)
    return f"Connected as {username} — your token can see {count_str} {noun}"


def _connection_error_message(exc: Exception, *, label: str) -> str:
    msg = str(exc).strip()
    if "HTTP 401" in msg and label == "GitHub":
        return (
            "GitHub rejected this token (401 Bad credentials). "
            "Use a classic PAT (ghp_…) from Settings → Developer settings → "
            "Personal access tokens → Tokens (classic) with the repo scope."
        )
    if "HTTP 401" in msg:
        if ": " in msg:
            detail = msg.rsplit(": ", 1)[-1].strip()
            if detail and detail != msg:
                return f"Invalid {label} token: {detail}"
        return f"Invalid {label} token — check that it is active and has not expired."
    if "HTTP 403" in msg:
        detail = msg.rsplit(": ", 1)[-1].strip() if ": " in msg else ""
        base = f"{label} denied access — token may lack required scopes."
        return f"{base} {detail}".strip() if detail and detail != msg else base
    if "invalid characters" in msg.lower():
        return "Token contains invalid characters. Paste only the ghp_… string from GitHub."
    if "blank" in msg.lower():
        return "Personal Access Token is required."
    if msg:
        return msg
    return f"Unable to reach {label}."


@method_decorator(login_required, name="dispatch")
class DataSourcesListView(View):
    template_name = "ui/datasources/list.html"

    def get(self, request: HttpRequest) -> HttpResponse:
        active_type = (request.GET.get("type") or "").strip()
        active_status = (request.GET.get("status") or "").strip()
        qs = _datasources_filtered_get_queryset(type_filter=active_type, status_filter=active_status)
        datasources = list(qs)
        has_any_datasource = DataSource.objects.exists()
        filtered_empty = has_any_datasource and not datasources
        type_choices = [
            ("", "All"),
            (DataSource.Type.GITLAB, "GitLab"),
            (DataSource.Type.GITHUB, "GitHub"),
            (DataSource.Type.JIRA, "Jira"),
        ]
        status_choices = [
            ("", "All"),
            (DataSource.Status.CONNECTED, "Connected"),
            (DataSource.Status.TOKEN_EXPIRING, "Token expiring"),
            (DataSource.Status.TOKEN_EXPIRED, "Token expired"),
            (DataSource.Status.CONNECTION_ERROR, "Connection error"),
        ]
        return render(
            request,
            self.template_name,
            {
                "active_nav": "datasources",
                "datasources": datasources,
                "type_choices": type_choices,
                "status_choices": status_choices,
                "active_type": active_type,
                "active_status": active_status,
                "filtered_empty": filtered_empty,
            },
        )


@method_decorator(login_required, name="dispatch")
class DataSourcesCreateView(View):
    template_name = "ui/datasources/create.html"

    def get(self, request: HttpRequest) -> HttpResponse:
        return render(request, self.template_name, _create_post_context())

    def post(self, request: HttpRequest) -> HttpResponse:
        selected = request.POST.get("type")
        if selected in (DataSource.Type.GITLAB, DataSource.Type.GITHUB):
            return render(
                request,
                self.template_name,
                _create_post_context(step=2, selected_type=selected),
            )

        if request.POST.get("step") != "2":
            return redirect(reverse("datasources-create"))

        svc = DataSourcesService()
        selected_type = request.POST.get("selected_type", DataSource.Type.GITLAB)
        token = request.POST.get("token", "").strip()
        name = request.POST.get("name", "").strip()
        token_expires_raw = request.POST.get("token_expires_at", "").strip()
        base_url = request.POST.get("base_url", "").strip()
        base_ctx = {
            "step": 2,
            "selected_type": selected_type,
            "preserve_name": name,
            "preserve_base_url": base_url,
            "preserve_token": token,
            "preserve_token_expires_at": token_expires_raw,
        }

        if request.POST.get("action") == "test-connection":
            try:
                if selected_type == DataSource.Type.GITHUB:
                    meta = svc.test_github_connection(token=token)
                    msg = _connection_test_message(meta, noun="repositories")
                else:
                    meta = svc.test_gitlab_connection(base_url=base_url, token=token)
                    msg = _connection_test_message(meta, noun="projects")
                return render(
                    request,
                    self.template_name,
                    _create_post_context(**base_ctx, form_success=msg),
                )
            except (ConnectionError, ValueError, OSError) as exc:
                label = "GitHub" if selected_type == DataSource.Type.GITHUB else "GitLab"
                norm_len = (
                    len(normalize_github_token(token)) if selected_type == DataSource.Type.GITHUB and token else 0
                )
                logger.warning(
                    "datasource create %s failed type=%s raw_len=%d normalized_len=%d: %s",
                    request.POST.get("action"),
                    selected_type,
                    len(token),
                    norm_len,
                    exc,
                    exc_info=exc,
                )
                return render(
                    request,
                    self.template_name,
                    _create_post_context(**base_ctx, form_error=_connection_error_message(exc, label=label)),
                )

        if request.POST.get("action") == "save":
            if not name:
                return render(
                    request,
                    self.template_name,
                    _create_post_context(**base_ctx, form_error="Name is required."),
                )
            try:
                if selected_type == DataSource.Type.GITHUB:
                    ds = svc.create_github_source(
                        name=name,
                        token=token,
                        token_expires_at=token_expires_raw or None,
                    )
                else:
                    ds = svc.create_gitlab_source(
                        name=name,
                        base_url=base_url,
                        token=token,
                        token_expires_at=token_expires_raw or None,
                    )
            except ValueError as exc:
                return render(
                    request,
                    self.template_name,
                    _create_post_context(**base_ctx, form_error=str(exc)),
                )
            except IntegrityError:
                return render(
                    request,
                    self.template_name,
                    _create_post_context(
                        **base_ctx,
                        form_error="A data source with that name already exists.",
                    ),
                )
            target = f"{reverse('projects-import')}?datasource={ds.pk}&banner=datasource_connected"
            return redirect(target)

        return redirect(reverse("datasources-create"))


@method_decorator(login_required, name="dispatch")
class DataSourcesDetailView(View):
    template_name = "ui/datasources/detail.html"

    def get(self, request: HttpRequest, pk: int) -> HttpResponse:
        datasource = get_object_or_404(DataSource.objects.all(), pk=pk)
        return render(request, self.template_name, {"active_nav": "datasources", "datasource": datasource})


@method_decorator(login_required, name="dispatch")
class DataSourcesTestConnectionView(View):
    """HTMX endpoint — POST-only connection probe."""

    http_method_names = ["post"]
    template_name = "ui/datasources/partials/test_connection_result.html"

    def post(self, request: HttpRequest, pk: int) -> HttpResponse:
        ds = get_object_or_404(DataSource.objects.all(), pk=pk)
        svc = DataSourcesService()
        if ds.datasource_type == DataSource.Type.GITHUB:
            try:
                meta = svc.test_github_connection(token=ds.encrypted_token_ciphertext)
                username = (meta.get("login") or meta.get("username") or meta.get("name") or "unknown").strip()
                count = meta.get("visible_project_count")
                ds.connected_user = username[:255]
                ds.visible_project_count = count
                ds.status = DataSource.Status.CONNECTED
                ds.last_error_message = ""
                ds.save(
                    update_fields=[
                        "connected_user",
                        "visible_project_count",
                        "status",
                        "last_error_message",
                        "updated_at",
                    ]
                )
                msg = _connection_test_message(meta, noun="repositories")
                return render(request, self.template_name, {"ok": True, "message": msg})
            except (ConnectionError, ValueError, OSError):
                ds.status = DataSource.Status.CONNECTION_ERROR
                ds.last_error_message = "Test connection failed."
                ds.save(update_fields=["status", "last_error_message", "updated_at"])
                return render(
                    request,
                    self.template_name,
                    {"ok": False, "message": "Unable to reach GitHub or token is invalid."},
                )

        if ds.datasource_type != DataSource.Type.GITLAB:
            return render(
                request,
                self.template_name,
                {"ok": False, "message": "Test connection is only available for GitLab and GitHub data sources."},
            )
        try:
            meta = svc.test_gitlab_connection(base_url=ds.base_url, token=ds.encrypted_token_ciphertext)
            username = (meta.get("username") or meta.get("name") or "").strip() or "unknown"
            count = meta.get("visible_project_count")
            ds.connected_user = username[:255]
            ds.visible_project_count = count
            ds.status = DataSource.Status.CONNECTED
            ds.last_error_message = ""
            ds.save(
                update_fields=[
                    "connected_user",
                    "visible_project_count",
                    "status",
                    "last_error_message",
                    "updated_at",
                ]
            )
            msg = _connection_test_message(meta, noun="projects")
            return render(request, self.template_name, {"ok": True, "message": msg})
        except (ConnectionError, ValueError, OSError):
            ds.status = DataSource.Status.CONNECTION_ERROR
            ds.last_error_message = "Test connection failed."
            ds.save(update_fields=["status", "last_error_message", "updated_at"])
            return render(
                request,
                self.template_name,
                {"ok": False, "message": "Unable to reach GitLab or token is invalid."},
            )


@method_decorator(login_required, name="dispatch")
class DataSourcesEditView(View):
    template_name = "ui/datasources/edit.html"

    def get(self, request: HttpRequest, pk: int) -> HttpResponse:
        datasource = get_object_or_404(DataSource.objects.all(), pk=pk)
        return render(
            request,
            self.template_name,
            {
                "active_nav": "datasources",
                "datasource": datasource,
            },
        )

    def post(self, request: HttpRequest, pk: int) -> HttpResponse:
        datasource = get_object_or_404(DataSource.objects.all(), pk=pk)
        svc = DataSourcesService()
        name = request.POST.get("name", "").strip()
        base_url = request.POST.get("base_url", "").strip()
        replace = request.POST.get("replace_token") == "1"
        new_tok = request.POST.get("new_token", "").strip()
        expires = request.POST.get("token_expires_at", "").strip()
        is_github = datasource.datasource_type == DataSource.Type.GITHUB

        def _ctx(**extra):
            base = {
                "active_nav": "datasources",
                "datasource": datasource,
                "preserve_name": name or datasource.name,
                "preserve_base_url": base_url or datasource.base_url,
                "preserve_expires": expires,
                "preserve_replace": replace,
                "preserve_new_token": new_tok if replace else "",
            }
            base.update(extra)
            return base

        if request.POST.get("action") == "test-connection":
            if not is_github and not base_url:
                return render(request, self.template_name, _ctx(form_error="Base URL is required."))
            if replace and not new_tok:
                return render(request, self.template_name, _ctx(form_error="Enter a new token before testing."))
            token_for_test = new_tok if replace else datasource.encrypted_token_ciphertext
            try:
                if is_github:
                    meta = svc.test_github_connection(token=token_for_test)
                    msg = _connection_test_message(meta, noun="repositories")
                else:
                    meta = svc.test_gitlab_connection(base_url=base_url, token=token_for_test)
                    msg = _connection_test_message(meta, noun="projects")
                return render(request, self.template_name, _ctx(test_success=msg))
            except (ConnectionError, ValueError, OSError) as exc:
                label = "GitHub" if is_github else "GitLab"
                return render(
                    request,
                    self.template_name,
                    _ctx(form_error=_connection_error_message(exc, label=label)),
                )

        if request.POST.get("action") == "save":
            if not name:
                return render(request, self.template_name, _ctx(form_error="Name is required."))
            if replace and not new_tok:
                return render(request, self.template_name, _ctx(form_error="New token is required when replacing."))
            try:
                if is_github:
                    svc.update_github_source(
                        datasource.id,
                        name=name,
                        token_expires_at=expires or None,
                        new_token=new_tok if replace else None,
                    )
                else:
                    svc.update_gitlab_source(
                        datasource.id,
                        name=name,
                        base_url=base_url,
                        token_expires_at=expires or None,
                        new_token=new_tok if replace else None,
                    )
            except ValueError as exc:
                return render(request, self.template_name, _ctx(form_error=str(exc)))
            except IntegrityError:
                return render(
                    request,
                    self.template_name,
                    _ctx(form_error="That name is already taken."),
                )
            return redirect(reverse("datasource-detail", args=[datasource.pk]))

        return redirect(reverse("datasource-edit", args=[datasource.pk]))


@method_decorator(login_required, name="dispatch")
class DataSourcesDeleteView(View):
    template_name = "ui/datasources/delete.html"

    def get(self, request: HttpRequest, pk: int) -> HttpResponse:
        datasource = get_object_or_404(DataSource.objects.all(), pk=pk)
        project_count = datasource.projects.filter(status=Project.Status.ACTIVE).count()
        return render(
            request,
            self.template_name,
            {
                "active_nav": "datasources",
                "datasource": datasource,
                "project_count": project_count,
            },
        )

    def post(self, request: HttpRequest, pk: int) -> HttpResponse:
        datasource = get_object_or_404(DataSource.objects.all(), pk=pk)
        name = datasource.name
        svc = DataSourcesService()
        svc.soft_delete_source(datasource.id)
        messages.success(request, f"{name} has been disconnected.")
        return redirect(reverse("datasources-list"))
