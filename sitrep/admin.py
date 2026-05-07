"""Admin registrations for sitrep models."""

from django.contrib import admin

from sitrep.models import Frago, SituationalAwareness, SituationalAwarenessVersion


@admin.register(Frago)
class FragoAdmin(admin.ModelAdmin):
    list_display = ("title", "project", "enabled", "revoked_at", "updated_at")
    list_filter = ("enabled",)
    search_fields = ("title", "body_md")


@admin.register(SituationalAwareness)
class SituationalAwarenessAdmin(admin.ModelAdmin):
    list_display = ("project",)


@admin.register(SituationalAwarenessVersion)
class SituationalAwarenessVersionAdmin(admin.ModelAdmin):
    list_display = ("awareness", "version_number", "created_at")
