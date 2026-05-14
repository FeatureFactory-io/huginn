"""URL patterns for the ui app."""

from django.urls import include, path

from .views.auth.login_view import LoginScreenView
from .views.auth.logout_view import LogoutScreenView
from .views.auth.register_view import RegisterView
from .views.dashboard import DashboardProjectsView
from .views.datasources import (
    DataSourcesCreateView,
    DataSourcesDeleteView,
    DataSourcesDetailView,
    DataSourcesEditView,
    DataSourcesListView,
    DataSourcesTestConnectionView,
)
from .views.fragos import (
    FragosCreateView,
    FragosDetailView,
    FragosEditView,
    FragosListView,
    FragosRevokeView,
)
from .views.health import health_json, welcome
from .views.home import HomeView
from .views.playbooks import (
    PlaybooksCreateView,
    PlaybooksDeleteView,
    PlaybooksDetailView,
    PlaybooksEditView,
    PlaybooksListView,
)
from .views.projects import (
    ProjectsArchiveView,
    ProjectsDetailView,
    ProjectsEditView,
    ProjectsImportView,
    ProjectsListView,
    ProjectsSyncNowView,
)
from .views.sitrep import SitRepDetailView, SitRepListView, sitrep_generate_view
from .views.situational_awareness import SituationalAwarenessEditView, SituationalAwarenessView
from .views.ux_preview import palette_preview

urlpatterns = [
    path("", HomeView.as_view(), name="home"),
    path("plot/", DashboardProjectsView.as_view(), name="tactical-plot"),
    path("accounts/login/", LoginScreenView.as_view(), name="auth-login"),
    path("accounts/logout/", LogoutScreenView.as_view(), name="auth-logout"),
    path("accounts/register/", RegisterView.as_view(), name="auth-register"),
    path("welcome/", welcome, name="welcome"),
    path("mockups/", include("ui.urls_mockups")),
    path("datasources/", DataSourcesListView.as_view(), name="datasources-list"),
    path("datasources/create/", DataSourcesCreateView.as_view(), name="datasources-create"),
    path("datasources/<int:pk>/", DataSourcesDetailView.as_view(), name="datasource-detail"),
    path(
        "datasources/<int:pk>/test-connection/",
        DataSourcesTestConnectionView.as_view(),
        name="datasource-test-connection",
    ),
    path("datasources/<int:pk>/edit/", DataSourcesEditView.as_view(), name="datasource-edit"),
    path("datasources/<int:pk>/delete/", DataSourcesDeleteView.as_view(), name="datasource-delete"),
    path("playbooks/", PlaybooksListView.as_view(), name="playbooks-list"),
    path("playbooks/create/", PlaybooksCreateView.as_view(), name="playbooks-create"),
    path("playbooks/<int:pk>/", PlaybooksDetailView.as_view(), name="playbooks-detail"),
    path("playbooks/<int:pk>/edit/", PlaybooksEditView.as_view(), name="playbooks-edit"),
    path("playbooks/<int:pk>/delete/", PlaybooksDeleteView.as_view(), name="playbooks-delete"),
    path("fragos/", FragosListView.as_view(), name="fragos-list"),
    path("fragos/create/", FragosCreateView.as_view(), name="fragos-create"),
    path("fragos/<int:pk>/", FragosDetailView.as_view(), name="fragos-detail"),
    path("fragos/<int:pk>/edit/", FragosEditView.as_view(), name="fragos-edit"),
    path("fragos/<int:pk>/revoke/", FragosRevokeView.as_view(), name="fragos-revoke"),
    path("sitawareness/", SituationalAwarenessView.as_view(), name="sitawareness-view"),
    path("sitawareness/edit/", SituationalAwarenessEditView.as_view(), name="sitawareness-edit"),
    path("projects/", ProjectsListView.as_view(), name="projects-list"),
    path("projects/import/", ProjectsImportView.as_view(), name="projects-import"),
    path("projects/<int:pk>/archive/", ProjectsArchiveView.as_view(), name="projects-archive"),
    path("projects/<int:pk>/edit/", ProjectsEditView.as_view(), name="projects-edit"),
    path("projects/<int:pk>/sync/", ProjectsSyncNowView.as_view(), name="projects-sync-now"),
    path(
        "projects/<int:project_pk>/sitrep/generate/",
        sitrep_generate_view,
        name="sitrep-generate",
    ),
    path(
        "projects/<int:project_pk>/sitreps/",
        SitRepListView.as_view(),
        name="sitrep-list",
    ),
    path(
        "projects/<int:project_pk>/sitreps/<int:pk>/",
        SitRepDetailView.as_view(),
        name="sitrep-view",
    ),
    # TODO(sitrep-sprint): sitrep-view URL lands in SITREP-VIEW_SITREP-1
    path("projects/<int:pk>/", ProjectsDetailView.as_view(), name="projects-detail"),
    path("health/", health_json, name="health-json"),
    path("ux/palette-preview/", palette_preview, name="ux-palette-preview"),
]
