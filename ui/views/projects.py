"""Project management UI (Act 2)."""

from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.http import require_POST

from ingestion.models import DataSource, Project
from ui.services.projects_service import ProjectsService


@method_decorator(login_required, name="dispatch")
class ProjectsListView(View):
    template_name = "ui/projects/list.html"

    def get(self, request: HttpRequest) -> HttpResponse:
        projects = list(Project.objects.select_related("datasource").all())
        return render(
            request,
            self.template_name,
            {
                "active_nav": "projects",
                "projects": projects,
            },
        )


@method_decorator(login_required, name="dispatch")
class ProjectsImportView(View):
    template_name = "ui/projects/import.html"

    def get(self, request: HttpRequest) -> HttpResponse:
        datasources = list(DataSource.objects.all())
        catalog = request.session.get("projects_import_catalog")
        return render(
            request,
            self.template_name,
            {
                "active_nav": "projects",
                "datasources": datasources,
                "catalog": catalog,
            },
        )

    def post(self, request: HttpRequest) -> HttpResponse:
        action = (request.POST.get("action") or "").strip()
        datasource_raw = request.POST.get("datasource_id", "").strip()
        datasource_id = int(datasource_raw) if datasource_raw.isdigit() else 0

        if action == "refresh-catalog":
            if datasource_id == 0 or not DataSource.objects.filter(pk=datasource_id).exists():
                datasources = list(DataSource.objects.all())
                return render(
                    request,
                    self.template_name,
                    {
                        "active_nav": "projects",
                        "datasources": datasources,
                        "form_error": "Select a data source first.",
                    },
                )
            snap = ProjectsService().load_remote_projects_snapshot(datasource_id)
            request.session["projects_import_catalog"] = snap
            return redirect(reverse("projects-import"))

        if action == "import":
            raw_keys = request.POST.getlist("remote_keys")
            if not raw_keys and request.POST.get("remote_keys"):
                raw_keys = [request.POST.get("remote_keys", "").strip()]
            if datasource_id == 0 or not DataSource.objects.filter(pk=datasource_id).exists():
                datasources = list(DataSource.objects.all())
                return render(
                    request,
                    self.template_name,
                    {
                        "active_nav": "projects",
                        "datasources": datasources,
                        "form_error": "Choose a connected data source before importing.",
                    },
                )
            ProjectsService().persist_imported_project_selection(
                datasource_id=datasource_id,
                remote_keys=raw_keys,
            )
            request.session.pop("projects_import_catalog", None)
            return redirect(reverse("projects-list"))

        return redirect(reverse("projects-import"))


@method_decorator(login_required, name="dispatch")
class ProjectsDetailView(View):
    template_name = "ui/projects/detail.html"

    def get(self, request: HttpRequest, pk: int) -> HttpResponse:
        project = get_object_or_404(Project.objects.select_related("datasource"), pk=pk)
        return render(request, self.template_name, {"active_nav": "projects", "project": project})


@method_decorator(login_required, name="dispatch")
@method_decorator(require_POST, name="dispatch")
class ProjectsSyncNowView(View):
    def post(self, request: HttpRequest, pk: int) -> HttpResponse:
        project = get_object_or_404(Project.objects.all(), pk=pk)
        ProjectsService().enqueue_immediate_project_sync(project.pk)
        return redirect(reverse("projects-detail", args=[project.pk]))


@method_decorator(login_required, name="dispatch")
class ProjectsEditView(View):
    template_name = "ui/projects/edit.html"

    def get(self, request: HttpRequest, pk: int) -> HttpResponse:
        project = get_object_or_404(Project.objects.select_related("datasource"), pk=pk)
        return render(request, self.template_name, {"active_nav": "projects", "project": project})

    def post(self, request: HttpRequest, pk: int) -> HttpResponse:
        project = get_object_or_404(Project.objects.select_related("datasource"), pk=pk)
        ProjectsService().update_project_configuration(
            project.id,
            display_name=request.POST.get("display_name", "").strip(),
        )
        return redirect(reverse("projects-detail", args=[project.pk]))


@method_decorator(login_required, name="dispatch")
class ProjectsArchiveView(View):
    template_name = "ui/projects/archive.html"

    def get(self, request: HttpRequest, pk: int) -> HttpResponse:
        project = get_object_or_404(Project.objects.select_related("datasource"), pk=pk)
        return render(request, self.template_name, {"active_nav": "projects", "project": project})

    def post(self, request: HttpRequest, pk: int) -> HttpResponse:
        project = get_object_or_404(Project.objects.all(), pk=pk)
        ProjectsService().archive_project(project.id)
        return redirect(reverse("projects-list"))
