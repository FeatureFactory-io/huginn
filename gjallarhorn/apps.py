from django.apps import AppConfig


class GjallarhornConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "gjallarhorn"

    def ready(self):
        from gjallarhorn.tasks.sitrep_tasks import on_sync_project_completed  # noqa: PLC0415
        from ingestion.signals import sync_project_completed  # noqa: PLC0415

        sync_project_completed.connect(on_sync_project_completed)
