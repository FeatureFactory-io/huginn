"""Operational DataSource routes (Acts 1)."""

from django.contrib.auth.decorators import login_required
from django.db import IntegrityError
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views import View

from ingestion.models import DataSource
from ui.services.datasources_service import DataSourcesService


def _create_post_context(**kwargs) -> dict:
    ctx = {"active_nav": "datasources"}
    ctx.update(kwargs)
    return ctx


@method_decorator(login_required, name="dispatch")
class DataSourcesListView(View):
    template_name = "ui/datasources/list.html"

    def get(self, request: HttpRequest) -> HttpResponse:
        datasources = list(DataSource.objects.all())
        return render(
            request,
            self.template_name,
            {
                "active_nav": "datasources",
                "datasources": datasources,
            },
        )


@method_decorator(login_required, name="dispatch")
class DataSourcesCreateView(View):
    template_name = "ui/datasources/create.html"

    def get(self, request: HttpRequest) -> HttpResponse:
        return render(request, self.template_name, {"active_nav": "datasources"})

    def post(self, request: HttpRequest) -> HttpResponse:
        svc = DataSourcesService()
        base_url = request.POST.get("base_url", "").strip()
        token = request.POST.get("token", "").strip()
        name = request.POST.get("name", "").strip()
        base_ctx = {
            "preserve_name": name,
            "preserve_base_url": base_url,
            "preserve_token": token,
        }

        if request.POST.get("action") == "test-connection":
            try:
                meta = svc.test_gitlab_connection(base_url=base_url, token=token)
                username = meta.get("username") or meta.get("name") or "ok"
                msg = f"Connection OK ({username})."
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

        try:
            ds = svc.create_gitlab_source(
                name=name,
                base_url=base_url,
                token=token,
                token_expires_at=request.POST.get("token_expires_at") or None,
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
        return redirect(reverse("datasource-detail", args=[ds.pk]))


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
        return render(request, self.template_name, {"active_nav": "datasources", "datasource": datasource})

    def post(self, request: HttpRequest, pk: int) -> HttpResponse:
        datasource = get_object_or_404(DataSource.objects.all(), pk=pk)
        svc = DataSourcesService()
        try:
            svc.soft_delete_gitlab_source(datasource.id)
        except ValueError as exc:
            return render(
                request,
                self.template_name,
                {"active_nav": "datasources", "datasource": datasource, "form_error": str(exc)},
            )
        return redirect(reverse("datasources-list"))
