from django.db import migrations


def create_periodic_task(apps, schema_editor):
    IntervalSchedule = apps.get_model("django_celery_beat", "IntervalSchedule")
    PeriodicTask = apps.get_model("django_celery_beat", "PeriodicTask")

    schedule, _ = IntervalSchedule.objects.get_or_create(
        every=15,
        period="minutes",
    )
    PeriodicTask.objects.get_or_create(
        name="Sync due projects",
        defaults={
            "interval": schedule,
            "task": "ingestion.sync_due_projects",
            "enabled": True,
        },
    )


def delete_periodic_task(apps, schema_editor):
    PeriodicTask = apps.get_model("django_celery_beat", "PeriodicTask")
    PeriodicTask.objects.filter(name="Sync due projects").delete()


class Migration(migrations.Migration):
    dependencies = [
        ("ingestion", "0001_initial"),
        ("django_celery_beat", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(create_periodic_task, delete_periodic_task),
    ]
