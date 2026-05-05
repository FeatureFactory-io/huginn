"""URL patterns for the ui app."""

from django.urls import path

from .views.health import health_json, welcome
from .views.ux_preview import palette_preview

urlpatterns = [
    path("", welcome, name="welcome"),
    path("health/", health_json, name="health-json"),
    path("ux/palette-preview/", palette_preview, name="ux-palette-preview"),
]
