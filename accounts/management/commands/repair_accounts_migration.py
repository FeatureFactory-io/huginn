"""Repair inconsistent history when admin ran before accounts.0001_initial existed."""

from __future__ import annotations

from django.apps import apps
from django.core.management.base import BaseCommand, CommandError
from django.db import connection
from django.utils import timezone


class Command(BaseCommand):
    help = (
        "If accounts_user is missing but django_migrations skipped accounts.0001_initial, "
        "create the User schema and record the migration so migrate can run."
    )

    def handle(self, *args, **options) -> None:
        User = apps.get_model("accounts", "User")
        table = User._meta.db_table

        table_exists = table in connection.introspection.table_names()

        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT EXISTS (
                  SELECT 1 FROM django_migrations
                  WHERE app = %s AND name = %s
                )
                """,
                ["accounts", "0001_initial"],
            )
            recorded = cursor.fetchone()[0]

        if table_exists and recorded:
            return

        if recorded and not table_exists:
            raise CommandError(
                f"django_migrations lists accounts.0001_initial but {table} is missing — needs manual DB repair."
            )

        if table_exists and not recorded:
            self.stdout.write(f"Recording accounts.0001_initial ({table} already exists).")
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO django_migrations (app, name, applied)
                    VALUES (%s, %s, %s)
                    """,
                    ["accounts", "0001_initial", timezone.now()],
                )
            return

        self.stdout.write(f"Creating {table} and related tables; recording accounts.0001_initial.")
        with connection.schema_editor() as editor:
            editor.create_model(User)
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO django_migrations (app, name, applied)
                VALUES (%s, %s, %s)
                """,
                ["accounts", "0001_initial", timezone.now()],
            )
