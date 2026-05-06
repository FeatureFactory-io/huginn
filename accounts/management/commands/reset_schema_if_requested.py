"""DROP/CREATE the public schema when HUGINN_RESET_DB=1.

Safety net: only PostgreSQL backends and only when the env var is exactly "1".
Used as a one-shot to recover from inconsistent migration history. Run BEFORE
migrate so Django sees a clean django_migrations table.
"""

from __future__ import annotations

import os

from django.core.management.base import BaseCommand
from django.db import connection


class Command(BaseCommand):
    help = "Drop and recreate the public schema iff HUGINN_RESET_DB=1 (PostgreSQL only)."

    def handle(self, *args, **options) -> None:
        if os.environ.get("HUGINN_RESET_DB") != "1":
            return

        if connection.vendor != "postgresql":
            self.stderr.write(f"Refusing reset on non-postgres backend: {connection.vendor}")
            return

        self.stdout.write("HUGINN_RESET_DB=1 -> DROP SCHEMA public CASCADE; CREATE SCHEMA public;")
        with connection.cursor() as cursor:
            cursor.execute("DROP SCHEMA IF EXISTS public CASCADE;")
            cursor.execute("CREATE SCHEMA public;")
            cursor.execute("GRANT ALL ON SCHEMA public TO CURRENT_USER;")
            cursor.execute("GRANT ALL ON SCHEMA public TO PUBLIC;")
        self.stdout.write("Schema reset complete.")
