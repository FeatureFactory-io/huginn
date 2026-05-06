"""Operational DataSource routes (Acts 1)."""

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

from ingestion.models import DataSource, Project
from ui.services.datasources_service import DataSourcesService


def _create_post_context(**kwargs) -> dict:
    ctx = {"active_nav": "datasources"}
    ctx.update(kwargs)
    ctx.setdefault("step", 1)
    return ctx


def _datasources_filtered_get_queryset(*, type_filter: str, status_filter: str):
    qs = DataSource.objects.all().order_by("name")
    if type_filter in (DataSource.Type.GITLAB, DataSource.Type.JIRA):
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
        if request.POST.get("type") == DataSource.Type.GITLAB:
            return render(
                request,
                self.template_name,
                _create_post_context(step=2, selected_type=DataSource.Type.GITLAB),
            )

        if request.POST.get("step") != "2":
            return redirect(reverse("datasources-create"))

        svc = DataSourcesService()
        base_url = request.POST.get("base_url", "").strip()
        token = request.POST.get("token", "").strip()
        name = request.POST.get("name", "").strip()
        token_expires_raw = request.POST.get("token_expires_at", "").strip()
        base_ctx = {
            "step": 2,
            "selected_type": DataSource.Type.GITLAB,
            "preserve_name": name,
            "preserve_base_url": base_url,
            "preserve_token": token,
            "preserve_token_expires_at": token_expires_raw,
        }

        if request.POST.get("action") == "test-connection":
            try:
                meta = svc.test_gitlab_connection(base_url=base_url, token=token)
                username = meta.get("username") or meta.get("name") or "unknown"
                count = meta.get("visible_project_count")
                count_str = "?" if count is None else str(count)
                msg = f"Connected as {username} — your token can see {count_str} projects"
                return render(
                    request,
                    self.template_name,
                    _create_post_context(**base_ctx, form_success=msg),
                )
            except (ConnectionError, ValueError, OSError):
                return render(
                    request,
                    self.template_name,
                    _create_post_context(**base_ctx, form_error="Unable to reach GitLab."),
                )

        if request.POST.get("action") == "save":
            if not name:
                return render(
                    request,
                    self.template_name,
                    _create_post_context(**base_ctx, form_error="Name is required."),
                )
            try:
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
class DataSourcesEditView(View):
    template_name = "ui/datasources/edit.html"

    def get(self, request: HttpRequest, pk: int) -> HttpResponse:
        datasource = get_object_or_404(DataSource.objects.all(), pk=pk)
        return render(request, self.template_name, {"active_nav": "datasources", "datasource": datasource})

    def post(self, request: HttpRequest, pk: int) -> HttpResponse:
        datasource = get_object_or_404(DataSource.objects.all(), pk=pk)
        svc = DataSourcesService()
        try:
            svc.update_gitlab_source(
                datasource.id,
                name=request.POST.get("name", "").strip(),
                base_url=request.POST.get("base_url", "").strip(),
            )
        except IntegrityError:
            return render(
                request,
                self.template_name,
                {
                    "active_nav": "datasources",
                    "datasource": datasource,
                    "form_error": "That name is already taken.",
                },
            )
        return redirect(reverse("datasource-detail", args=[datasource.pk]))


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
        svc.soft_delete_gitlab_source(datasource.id)
        messages.success(request, f"{name} has been disconnected.")
        return redirect(reverse("datasources-list"))
