from django.contrib import admin

from ingestion.models import Contributor, DataSource, Increment, IngestionRun, Project


@admin.register(DataSource)
class DataSourceAdmin(admin.ModelAdmin):
    list_display = ("name", "datasource_type", "status", "base_url", "updated_at")


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ("slug", "name", "datasource", "status", "updated_at")


@admin.register(Contributor)
class ContributorAdmin(admin.ModelAdmin):
    list_display = ("email", "name", "datasource", "last_seen_at")


@admin.register(Increment)
class IncrementAdmin(admin.ModelAdmin):
    list_display = ("kind", "external_id", "summary", "project", "occurred_at")


@admin.register(IngestionRun)
class IngestionRunAdmin(admin.ModelAdmin):
    list_display = ("project", "status", "started_at", "finished_at", "increments_ingested")
