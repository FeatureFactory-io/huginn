from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("ingestion", "0002_sync_due_projects_beat"),
    ]

    operations = [
        migrations.AddField(
            model_name="project",
            name="sync_daily_hour",
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="project",
            name="sync_weekly_day",
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="project",
            name="sync_weekly_hour",
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name="project",
            name="sync_schedule",
            field=models.CharField(
                choices=[
                    ("hourly", "Hourly"),
                    ("every_6h", "Every 6h"),
                    ("daily", "Daily"),
                    ("weekly", "Weekly"),
                    ("manual", "Manual"),
                ],
                default="hourly",
                max_length=16,
            ),
        ),
    ]
