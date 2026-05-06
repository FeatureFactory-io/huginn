"""URL patterns for the ui app."""

from django.urls import include, path
from django.views.generic import RedirectView

from .views.auth.login_view import LoginScreenView
from .views.auth.logout_view import LogoutScreenView
from .views.datasources import (
    DataSourcesCreateView,
    DataSourcesDeleteView,
    DataSourcesDetailView,
    DataSourcesEditView,
    DataSourcesListView,
    DataSourcesTestConnectionView,
)
from .views.health import health_json, welcome
from .views.projects import (
    ProjectsArchiveView,
    ProjectsDetailView,
    ProjectsEditView,
    ProjectsImportView,
    ProjectsListView,
    ProjectsSyncNowView,
)
from .views.ux_preview import palette_preview

urlpatterns = [
    path("", LoginScreenView.as_view(), name="auth-login"),
    path(
        "accounts/login/",
        RedirectView.as_view(pattern_name="auth-login"),
        name="auth-login-legacy-root",
    ),
    path("accounts/logout/", LogoutScreenView.as_view(), name="auth-logout"),
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
    path("projects/", ProjectsListView.as_view(), name="projects-list"),
    path("projects/import/", ProjectsImportView.as_view(), name="projects-import"),
    path("projects/<int:pk>/archive/", ProjectsArchiveView.as_view(), name="projects-archive"),
    path("projects/<int:pk>/edit/", ProjectsEditView.as_view(), name="projects-edit"),
    path("projects/<int:pk>/sync/", ProjectsSyncNowView.as_view(), name="projects-sync-now"),
    path("projects/<int:pk>/", ProjectsDetailView.as_view(), name="projects-detail"),
    path("health/", health_json, name="health-json"),
    path("ux/palette-preview/", palette_preview, name="ux-palette-preview"),
]
