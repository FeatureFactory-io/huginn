from django.apps import AppConfig


class IngestionConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "ingestion"

    def ready(self) -> None:
        import ingestion.adapters.gitlab_commits  # noqa: F401
        import ingestion.adapters.gitlab_issues  # noqa: F401
        import ingestion.adapters.gitlab_merge_requests  # noqa: F401
        import ingestion.adapters.gitlab_milestones  # noqa: F401
