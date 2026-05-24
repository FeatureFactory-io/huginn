from django.apps import AppConfig


class RoeConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "roe"
    label = "playbooks"  # Preserve existing app label so legacy migrations + FK strings remain valid
