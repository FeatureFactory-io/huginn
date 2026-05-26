"""Backfill variables_snapshot + VariableDatapoint rows from completed plan steps."""

from django.core.management.base import BaseCommand

from ui.services.sitrep_variables_service import backfill_all_empty_sitreps


class Command(BaseCommand):
    help = "Backfill SitRep variables_snapshot from completed variable assessment plan steps."

    def add_arguments(self, parser):
        parser.add_argument("--project", type=int, default=None, help="Limit to one project pk")

    def handle(self, *args, **options):
        project_id = options.get("project")
        results = backfill_all_empty_sitreps(project_id=project_id)
        if not results:
            self.stdout.write("No SitReps needed backfill.")
            return
        for row in results:
            self.stdout.write(f"SitRep {row['sitrep_id']}: {row['datapoints']} datapoint(s)")
