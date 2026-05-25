from django.db import migrations


def create_periodic_task(apps, schema_editor):
    IntervalSchedule = apps.get_model("django_celery_beat", "IntervalSchedule")
    PeriodicTask = apps.get_model("django_celery_beat", "PeriodicTask")

    schedule, _ = IntervalSchedule.objects.get_or_create(
        every=60,
        period="seconds",
    )
    PeriodicTask.objects.get_or_create(
        name="Recover orphaned ExecutionPlans",
        defaults={
            "interval": schedule,
            "task": "gjallarhorn.recover_orphaned_plans",
            "enabled": True,
        },
    )


def delete_periodic_task(apps, schema_editor):
    PeriodicTask = apps.get_model("django_celery_beat", "PeriodicTask")
    PeriodicTask.objects.filter(name="Recover orphaned ExecutionPlans").delete()


class Migration(migrations.Migration):
    dependencies = [
        ("gjallarhorn", "0001_initial"),
        ("django_celery_beat", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(create_periodic_task, delete_periodic_task),
    ]
