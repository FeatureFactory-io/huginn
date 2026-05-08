from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("playbooks", "0002_seed_featurefactory_playbook"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="playbookvariable",
            name="dimensions",
        ),
        migrations.DeleteModel(
            name="PlaybookTable",
        ),
    ]
