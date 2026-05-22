"""Data tools — commit and contributor queries scoped to a project."""

from django.db.models import Count

from ingestion.models import Increment


def list_commits(project_id: int, from_dt, to_dt, limit: int = 200) -> list[dict]:
    """Return commits in [from_dt, to_dt) for the given project."""
    qs = (
        Increment.objects.filter(
            project_id=project_id,
            kind="commit",
            occurred_at__gte=from_dt,
            occurred_at__lt=to_dt,
        )
        .select_related("contributor")
        .order_by("-occurred_at")[:limit]
    )
    return [
        {
            "external_id": inc.external_id,
            "author_email": inc.contributor.email if inc.contributor else None,
            "message": inc.summary,
            "occurred_at": inc.occurred_at.isoformat() if inc.occurred_at else None,
        }
        for inc in qs
    ]


def get_contributor_activity(project_id: int, from_dt, to_dt) -> list[dict]:
    """Return per-contributor commit counts in [from_dt, to_dt), sorted descending."""
    rows = (
        Increment.objects.filter(
            project_id=project_id,
            kind="commit",
            occurred_at__gte=from_dt,
            occurred_at__lt=to_dt,
            contributor__isnull=False,
        )
        .values("contributor__email")
        .annotate(commit_count=Count("id"))
        .order_by("-commit_count")
    )
    return [{"email": row["contributor__email"], "commit_count": row["commit_count"]} for row in rows]
