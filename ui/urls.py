"""URL patterns for the ui app."""

from django.urls import path

from .views.health import health_json, welcome

urlpatterns = [
    path("", welcome, name="welcome"),
    path("health/", health_json, name="health-json"),
]
