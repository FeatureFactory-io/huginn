from django.apps import AppConfig


class IngestionConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "ingestion"

    def ready(self) -> None:
        import ingestion.adapters.gitlab_commits  # noqa: F401 — registers GitLab adapters
