"""Admin registrations for sitrep models."""

from django.contrib import admin

from sitrep.models import Frago, FragoAuditEvent, SitRep, SituationalAwareness, SituationalAwarenessVersion


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
    list_display = ("workspace_capsule",)

    @admin.display(description="Workspace capsule")
    def workspace_capsule(self, obj: SituationalAwareness) -> str:
        return str(obj)


@admin.register(SituationalAwarenessVersion)
class SituationalAwarenessVersionAdmin(admin.ModelAdmin):
    list_display = ("awareness", "version_number", "created_at")


@admin.register(SitRep)
class SitRepAdmin(admin.ModelAdmin):
    list_display = ("project", "generated_at", "trigger", "headline")
    list_filter = ("trigger", "mode_at_generation")
    search_fields = ("headline", "situation_assessment")
    readonly_fields = (
        "project",
        "generated_at",
        "from_dt",
        "to_dt",
        "trigger",
        "mode_at_generation",
        "playbook_version",
        "headline",
        "situation_assessment",
        "notable_activity",
        "source_plan",
    )

    def has_add_permission(self, request) -> bool:
        return False

    def has_delete_permission(self, request, obj=None) -> bool:
        return request.user.is_superuser
