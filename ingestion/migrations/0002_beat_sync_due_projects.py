"""Periodic ingestion.sync_due_projects task via django-celery-beat (data migration)."""

from django.db import migrations


def create_ingestion_beat_schedule(apps, schema_editor) -> None:
    IntervalSchedule = apps.get_model("django_celery_beat", "IntervalSchedule")
    PeriodicTask = apps.get_model("django_celery_beat", "PeriodicTask")
    schedule, _ = IntervalSchedule.objects.get_or_create(every=15, period="minutes")
    PeriodicTask.objects.get_or_create(
        name="ingestion-sync-due-projects",
        defaults={
            "task": "ingestion.sync_due_projects",
            "interval": schedule,
            "enabled": True,
        },
    )


def remove_ingestion_beat_schedule(apps, schema_editor) -> None:
    PeriodicTask = apps.get_model("django_celery_beat", "PeriodicTask")
    PeriodicTask.objects.filter(name="ingestion-sync-due-projects").delete()


class Migration(migrations.Migration):
    dependencies = [
        ("ingestion", "0001_initial"),
        ("django_celery_beat", "0019_alter_periodictasks_options"),
    ]

    operations = [
        migrations.RunPython(create_ingestion_beat_schedule, remove_ingestion_beat_schedule),
    ]
