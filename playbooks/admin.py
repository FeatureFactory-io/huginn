"""Django admin for Playbooks."""

from django.contrib import admin

from playbooks.models import Playbook, PlaybookVariable, PlaybookVersion


class PlaybookVariableInline(admin.TabularInline):
    model = PlaybookVariable
    extra = 0


class PlaybookVersionInline(admin.TabularInline):
    model = PlaybookVersion
    extra = 0
    show_change_link = True


@admin.register(Playbook)
class PlaybookAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "is_system_seed", "updated_at")
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ("name", "slug")
    inlines = [PlaybookVersionInline]


@admin.register(PlaybookVersion)
class PlaybookVersionAdmin(admin.ModelAdmin):
    list_display = ("playbook", "version_number", "created_at")
    list_filter = ("playbook",)
    inlines = [PlaybookVariableInline]
