from django.apps import AppConfig


class GjallarhornConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "gjallarhorn"

    def ready(self):
        import gjallarhorn.tasks.sitrep_tasks  # noqa: F401 — registers signal receiver
