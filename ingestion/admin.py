from django.contrib import admin

from ingestion.models import DataSource, Project


@admin.register(DataSource)
class DataSourceAdmin(admin.ModelAdmin):
    list_display = ("name", "datasource_type", "status", "base_url", "updated_at")


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ("slug", "name", "datasource", "status", "updated_at")
