"""Drop per-project scoping from SituationalAwareness — make it a workspace singleton."""

from django.db import migrations


def consolidate_to_singleton(apps, schema_editor):
    """Keep the first SA record (by pk); delete the rest."""
    SituationalAwareness = apps.get_model("sitrep", "SituationalAwareness")
    records = list(SituationalAwareness.objects.order_by("pk"))
    for r in records[1:]:
        r.delete()


class Migration(migrations.Migration):
    dependencies = [
        ("sitrep", "0004_situational_awareness_entries"),
    ]

    operations = [
        migrations.RunPython(consolidate_to_singleton, migrations.RunPython.noop),
        migrations.RemoveField(
            model_name="situationalawareness",
            name="project",
        ),
    ]
