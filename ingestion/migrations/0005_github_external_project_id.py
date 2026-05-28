# Generated manually for GitHub datasource support.

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("ingestion", "0004_work_items"),
    ]

    operations = [
        migrations.RemoveConstraint(
            model_name="project",
            name="ingestion_project_ds_gitlab_id_uniq",
        ),
        migrations.RenameField(
            model_name="project",
            old_name="gitlab_project_id",
            new_name="external_project_id",
        ),
        migrations.AddConstraint(
            model_name="project",
            constraint=models.UniqueConstraint(
                condition=models.Q(external_project_id__isnull=False),
                fields=("datasource", "external_project_id"),
                name="ingestion_project_ds_external_id_uniq",
            ),
        ),
    ]
