"""Django admin for Rules of Engagement."""

from django.contrib import admin

from roe.models import RulesOfEngagement, RulesOfEngagementVariable, RulesOfEngagementVersion


class RulesOfEngagementVariableInline(admin.TabularInline):
    model = RulesOfEngagementVariable
    extra = 0


class RulesOfEngagementVersionInline(admin.TabularInline):
    model = RulesOfEngagementVersion
    extra = 0
    show_change_link = True


@admin.register(RulesOfEngagement)
class RulesOfEngagementAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "is_system_seed", "updated_at")
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ("name", "slug")
    inlines = [RulesOfEngagementVersionInline]


@admin.register(RulesOfEngagementVersion)
class RulesOfEngagementVersionAdmin(admin.ModelAdmin):
    list_display = ("roe", "version_number", "created_at")
    list_filter = ("roe",)
    inlines = [RulesOfEngagementVariableInline]
