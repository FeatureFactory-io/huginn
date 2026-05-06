"""Project management UI (Act 2)."""

from urllib.parse import urlencode

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.http import require_POST

from ingestion.models import DataSource, Project
from ui.services.increments_service import RANGE_LABELS, IncrementsService, normalize_range_key
from ui.services.project_vitals_service import ProjectVitalsService
from ui.services.projects_service import ProjectsService


def _project_detail_query(*, tab: str, range_key: str | None = None) -> str:
    q: dict[str, str] = {}
    if tab == "increments":
        q["tab"] = "increments"
        q["range"] = normalize_range_key(range_key)
    else:
        q["tab"] = "vitals"
    return urlencode(q)


def _import_success_message(imported_count: int) -> str:
    tail = "Sync started. Assign a Playbook to receive SitReps."
    if imported_count == 1:
        return f"1 project imported. {tail}"
    return f"{imported_count} projects imported. {tail}"


def _connected_gitlab_datasources() -> list[DataSource]:
    out: list[DataSource] = []
    for ds in DataSource.objects.all().order_by("name"):
        if ds.computed_status != DataSource.Status.CONNECTED:
            continue
        if ds.datasource_type != DataSource.Type.GITLAB:
            continue
        out.append(ds)
    return out


@method_decorator(login_required, name="dispatch")
class ProjectsListView(View):
    template_name = "ui/projects/list.html"

    def get(self, request: HttpRequest) -> HttpResponse:
        qs = Project.objects.select_related("datasource", "imported_by").all()
        ds_param = (request.GET.get("datasource") or "").strip()
        st_param = (request.GET.get("status") or "").strip()
        playbook_param = (request.GET.get("playbook") or "").strip()

        if ds_param.isdigit():
            qs = qs.filter(datasource_id=int(ds_param))
        if st_param in {Project.Status.ACTIVE, Project.Status.ARCHIVED, Project.Status.ORPHANED}:
            qs = qs.filter(status=st_param)
        if playbook_param:
            qs = qs.filter(playbook_slug__icontains=playbook_param)

        projects = list(qs.order_by("name"))
        return render(
            request,
            self.template_name,
            {
                "active_nav": "projects",
                "projects": projects,
                "filter_datasources": DataSource.objects.order_by("name"),
                "filter_datasource": ds_param,
                "filter_status": st_param,
                "filter_playbook": playbook_param,
                "imported_banner": request.GET.get("imported") == "1",
            },
        )


@method_decorator(login_required, name="dispatch")
class ProjectsImportView(View):
    template_name = "ui/projects/import.html"

    def _import_page_context(self, request: HttpRequest, **extra: object) -> dict:
        datasources = _connected_gitlab_datasources()
        ctx: dict = {
            "active_nav": "projects",
            "datasources": datasources,
            "catalog": request.session.get("projects_import_catalog"),
            "no_connected_gitlab": DataSource.objects.exists() and len(datasources) == 0,
        }
        ctx.update(extra)
        return ctx

    def get(self, request: HttpRequest) -> HttpResponse:
        return render(request, self.template_name, self._import_page_context(request))

    def post(self, request: HttpRequest) -> HttpResponse:
        action = (request.POST.get("action") or "").strip()
        datasource_raw = request.POST.get("datasource_id", "").strip()
        datasource_id = int(datasource_raw) if datasource_raw.isdigit() else 0
        datasources = _connected_gitlab_datasources()

        if action == "refresh-catalog":
            if datasource_id == 0 or not any(ds.pk == datasource_id for ds in datasources):
                return render(
                    request,
                    self.template_name,
                    self._import_page_context(
                        request,
                        form_error="Select a connected GitLab data source first.",
                    ),
                )
            snap = ProjectsService().load_remote_projects_snapshot(datasource_id)
            request.session["projects_import_catalog"] = snap
            return redirect(reverse("projects-import"))

        if action == "import":
            raw_keys = request.POST.getlist("remote_keys")
            if not raw_keys and request.POST.get("remote_keys"):
                raw_keys = [request.POST.get("remote_keys", "").strip()]
            if datasource_id == 0 or not any(ds.pk == datasource_id for ds in datasources):
                return render(
                    request,
                    self.template_name,
                    self._import_page_context(
                        request,
                        form_error="Choose a connected GitLab data source before importing.",
                    ),
                )
            catalog = request.session.get("projects_import_catalog") or {}
            if catalog.get("datasource_id") != datasource_id:
                return render(
                    request,
                    self.template_name,
                    self._import_page_context(
                        request,
                        catalog=catalog,
                        form_error="Refresh the catalog for this data source before importing.",
                    ),
                )
            entries = catalog.get("entries") or []
            if catalog.get("error"):
                return render(
                    request,
                    self.template_name,
                    self._import_page_context(
                        request,
                        catalog=catalog,
                        form_error="Fix the catalog error before importing.",
                    ),
                )

            created = ProjectsService().persist_imported_project_selection(
                datasource_id=datasource_id,
                remote_keys=raw_keys,
                catalog_entries=list(entries),
                imported_by_id=request.user.pk,
            )
            request.session.pop("projects_import_catalog", None)
            if created:
                messages.success(
                    request,
                    _import_success_message(len(created)),
                )
            url = reverse("projects-list") + "?imported=1"
            return redirect(url)

        return redirect(reverse("projects-import"))


@method_decorator(login_required, name="dispatch")
class ProjectsDetailView(View):
    template_name = "ui/projects/detail.html"

    def get(self, request: HttpRequest, pk: int) -> HttpResponse:
        project = get_object_or_404(Project.objects.select_related("datasource", "imported_by"), pk=pk)
        tab = (request.GET.get("tab") or "vitals").strip().lower()
        if tab not in {"vitals", "increments"}:
            tab = "vitals"
        inc_range = normalize_range_key(request.GET.get("range"))
        increments = list(IncrementsService().increments_for_project(project.pk, inc_range))
        range_order = ["today", "yesterday", "this_week", "last_week", "last_14d"]
        time_range_choices = [(k, RANGE_LABELS[k]) for k in range_order]
        latest_commit_at = ProjectVitalsService().latest_increment_occurred_at(project.pk)
        return render(
            request,
            self.template_name,
            {
                "active_nav": "projects",
                "project": project,
                "active_tab": tab,
                "time_range": inc_range,
                "time_range_choices": time_range_choices,
                "increments": increments,
                "latest_commit_at": latest_commit_at,
            },
        )


@method_decorator(login_required, name="dispatch")
@method_decorator(require_POST, name="dispatch")
class ProjectsSyncNowView(View):
    def post(self, request: HttpRequest, pk: int) -> HttpResponse:
        project = get_object_or_404(Project.objects.all(), pk=pk)
        if project.status == Project.Status.ARCHIVED:
            messages.warning(request, "Archived projects are not synced.")
        else:
            ProjectsService().enqueue_immediate_project_sync(project.pk)
            messages.info(request, "Sync has been queued.")
        tab = (request.POST.get("tab") or "vitals").strip().lower()
        range_raw = (request.POST.get("range") or "").strip()
        query = _project_detail_query(
            tab=tab if tab in {"vitals", "increments"} else "vitals",
            range_key=range_raw if tab == "increments" else None,
        )
        url = reverse("projects-detail", args=[project.pk]) + "?" + query
        return redirect(url)


@method_decorator(login_required, name="dispatch")
class ProjectsEditView(View):
    template_name = "ui/projects/edit.html"

    def get(self, request: HttpRequest, pk: int) -> HttpResponse:
        project = get_object_or_404(Project.objects.select_related("datasource"), pk=pk)
        return render(request, self.template_name, {"active_nav": "projects", "project": project})

    def post(self, request: HttpRequest, pk: int) -> HttpResponse:
        project = get_object_or_404(Project.objects.select_related("datasource"), pk=pk)
        display_name = (request.POST.get("display_name") or "").strip()
        if not display_name:
            return render(
                request,
                self.template_name,
                {
                    "active_nav": "projects",
                    "project": project,
                    "form_error": "Display name is required.",
                },
            )
        ProjectsService().update_project_configuration(
            project.id,
            display_name=display_name,
            sync_schedule=(request.POST.get("sync_schedule") or "").strip(),
        )
        messages.success(request, "Project settings updated.")
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
        messages.success(request, "Project archived.")
        return redirect(reverse("projects-list"))
