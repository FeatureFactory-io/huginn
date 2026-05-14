"""Gjallarhorn Celery tasks."""

from gjallarhorn.tasks.plan_tasks import execute_plan

__all__ = ["execute_plan"]
