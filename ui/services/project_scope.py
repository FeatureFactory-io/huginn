"""Resolve optional `?project=` scope from HTTP requests (FRAGO, SA, etc.)."""

from __future__ import annotations

from django.http import HttpRequest

from ingestion.models import Project


def optional_project_from_request(request: HttpRequest) -> tuple[Project | None, str]:
    """Return ``(project, slug)`` when ``project`` query param is set.

    * Empty/missing slug → ``(None, "")`` (unscoped).
    * Non-empty slug with no matching :class:`~ingestion.models.Project`
      → ``(None, slug)`` — callers treat as unknown slug (do **not** 404 list views).

    Matching slug → ``(project, slug)``.
    """
    slug = (request.GET.get("project") or "").strip()
    if not slug:
        return None, ""
    project = Project.objects.filter(slug=slug).first()
    return project, slug
