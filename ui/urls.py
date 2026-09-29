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
from .views.projects import (
    ProjectsArchiveView,
    ProjectsDetailView,
    ProjectsEditView,
    ProjectsImportView,
    ProjectsListView,
    ProjectsSyncNowView,
)
from .views.roe import (
    RulesOfEngagementCreateView,
    RulesOfEngagementDeleteView,
    RulesOfEngagementDetailView,
    RulesOfEngagementEditView,
    RulesOfEngagementListView,
)
from .views.seo import robots_txt, sitemap_xml
from .views.sitrep import SitRepAllListView, SitRepDetailView, SitRepListView, sitrep_generate_view
from .views.situational_awareness import SituationalAwarenessEditView, SituationalAwarenessView
from .views.ux_preview import palette_preview
from .views.variables import ProjectVariablesEChartsApiView

urlpatterns = [
    path("", HomeView.as_view(), name="home"),
    path("robots.txt", robots_txt, name="robots-txt"),
    path("sitemap.xml", sitemap_xml, name="sitemap-xml"),
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
    path("roe/", RulesOfEngagementListView.as_view(), name="roe-list"),
    path("roe/new/", RulesOfEngagementCreateView.as_view(), name="roe-create"),
    path("roe/<int:pk>/", RulesOfEngagementDetailView.as_view(), name="roe-detail"),
    path("roe/<int:pk>/edit/", RulesOfEngagementEditView.as_view(), name="roe-edit"),
    path("roe/<int:pk>/delete/", RulesOfEngagementDeleteView.as_view(), name="roe-delete"),
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
    path("sitreps/", SitRepAllListView.as_view(), name="sitreps-list"),
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
    path(
        "projects/<int:project_pk>/variables/echarts/",
        ProjectVariablesEChartsApiView.as_view(),
        name="project-variables-echarts",
    ),
    # TODO(sitrep-sprint): sitrep-view URL lands in SITREP-VIEW_SITREP-1
    path("projects/<int:pk>/", ProjectsDetailView.as_view(), name="projects-detail"),
    path("health/", health_json, name="health-json"),
    path("ux/palette-preview/", palette_preview, name="ux-palette-preview"),
]
