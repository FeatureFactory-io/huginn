from django.apps import AppConfig


class GjallarhornConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "gjallarhorn"

    def ready(self):
        pass  # TODO(sitrep-sprint): import gjallarhorn.tasks.sitrep_tasks to register sync signal receiver
