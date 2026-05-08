"""Admin registrations for sitrep models."""

from django.contrib import admin

from sitrep.models import Frago, FragoAuditEvent, SituationalAwareness, SituationalAwarenessVersion


class FragoAuditEventInline(admin.TabularInline):
    model = FragoAuditEvent
    extra = 0
    can_delete = False
    readonly_fields = ("created_at", "actor", "kind", "message")

    def has_add_permission(self, request, obj=None) -> bool:
        return False


@admin.register(Frago)
class FragoAdmin(admin.ModelAdmin):
    list_display = ("title", "project", "enabled", "revoked_at", "updated_at")
    list_filter = ("enabled",)
    search_fields = ("title", "body_md")
    inlines = [FragoAuditEventInline]


@admin.register(SituationalAwareness)
class SituationalAwarenessAdmin(admin.ModelAdmin):
    list_display = ("project",)


@admin.register(SituationalAwarenessVersion)
class SituationalAwarenessVersionAdmin(admin.ModelAdmin):
    list_display = ("awareness", "version_number", "created_at")
