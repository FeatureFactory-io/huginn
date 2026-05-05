"""URL routes for browsing HTML mockups (fake data) under `/mockups/`."""

from django.urls import path

from .views.mockups.action_stations import action_stations_list
from .views.mockups.auth import auth_login
from .views.mockups.chat import chat_view
from .views.mockups.contributors import contributors_list, contributors_view
from .views.mockups.dashboard import dashboard_projects
from .views.mockups.datasources import (
    datasources_create,
    datasources_delete,
    datasources_edit,
    datasources_list,
    datasources_view,
)
from .views.mockups.decisions import decisions_list, decisions_view
from .views.mockups.fragos import (
    fragos_create,
    fragos_edit,
    fragos_list,
    fragos_revoke,
    fragos_view,
)
from .views.mockups.playbooks import (
    playbooks_create,
    playbooks_delete,
    playbooks_edit,
    playbooks_list,
    playbooks_view,
)
from .views.mockups.projects import (
    projects_archive,
    projects_edit,
    projects_import,
    projects_list,
    projects_view,
)
from .views.mockups.sitawareness import sitawareness_edit, sitawareness_view
from .views.mockups.sitrep import sitrep_list, sitrep_view
from .views.mockups.variables import variables_view

urlpatterns = [
    path("", dashboard_projects, name="mockup-dashboard"),
    path("auth/login/", auth_login, name="mockup-auth-login"),
    path("datasources/", datasources_list, name="mockup-datasources-list"),
    path("datasources/create/", datasources_create, name="mockup-datasources-create"),
    path("datasources/<int:pk>/", datasources_view, name="mockup-datasources-view"),
    path("datasources/<int:pk>/edit/", datasources_edit, name="mockup-datasources-edit"),
    path("datasources/<int:pk>/delete/", datasources_delete, name="mockup-datasources-delete"),
    path("projects/", projects_list, name="mockup-projects-list"),
    path("projects/import/", projects_import, name="mockup-projects-import"),
    path("projects/<int:pk>/", projects_view, name="mockup-projects-view"),
    path("projects/<int:pk>/edit/", projects_edit, name="mockup-projects-edit"),
    path("projects/<int:pk>/archive/", projects_archive, name="mockup-projects-archive"),
    path("playbooks/", playbooks_list, name="mockup-playbooks-list"),
    path("playbooks/create/", playbooks_create, name="mockup-playbooks-create"),
    path("playbooks/<int:pk>/", playbooks_view, name="mockup-playbooks-view"),
    path("playbooks/<int:pk>/edit/", playbooks_edit, name="mockup-playbooks-edit"),
    path("playbooks/<int:pk>/delete/", playbooks_delete, name="mockup-playbooks-delete"),
    path("sitrep/", sitrep_list, name="mockup-sitrep-list"),
    path("sitrep/<int:pk>/", sitrep_view, name="mockup-sitrep-view"),
    path("fragos/", fragos_list, name="mockup-fragos-list"),
    path("fragos/create/", fragos_create, name="mockup-fragos-create"),
    path("fragos/<int:pk>/", fragos_view, name="mockup-fragos-view"),
    path("fragos/<int:pk>/edit/", fragos_edit, name="mockup-fragos-edit"),
    path("fragos/<int:pk>/revoke/", fragos_revoke, name="mockup-fragos-revoke"),
    path("variables/", variables_view, name="mockup-variables-view"),
    path("chat/", chat_view, name="mockup-chat"),
    path("decisions/", decisions_list, name="mockup-decisions-list"),
    path("decisions/<int:pk>/", decisions_view, name="mockup-decisions-view"),
    path("contributors/", contributors_list, name="mockup-contributors-list"),
    path("contributors/<int:pk>/", contributors_view, name="mockup-contributors-view"),
    path("action-stations/", action_stations_list, name="mockup-action-stations-list"),
    path("sitawareness/", sitawareness_view, name="mockup-sitawareness-view"),
    path("sitawareness/edit/", sitawareness_edit, name="mockup-sitawareness-edit"),
]
