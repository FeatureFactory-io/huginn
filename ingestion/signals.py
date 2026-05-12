"""Ingestion Django signals."""

from django.dispatch import Signal

sync_project_completed = Signal()
"""Sent after a successful project sync.

Keyword arguments:
    project (Project): The project that was synced.
    to_dt (datetime): The sync completion timestamp (UTC).
"""
