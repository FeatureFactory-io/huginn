"""Admin registrations for sitrep models."""

from django.contrib import admin

from sitrep.models import Frago


@admin.register(Frago)
class FragoAdmin(admin.ModelAdmin):
    list_display = ("title", "project", "enabled", "revoked_at", "updated_at")
    list_filter = ("enabled",)
    search_fields = ("title", "body_md")
