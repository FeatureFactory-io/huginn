"""Data tools — list_commits and get_contributor_activity."""

from django.db.models import Count

from ingestion.models import Increment


def list_commits(project_id: int, from_dt, to_dt, limit: int = 200) -> list[dict]:
    """List commits in the specified time window.

    Args:
        project_id: Project ID to filter by
        from_dt: Start of time window (inclusive)
        to_dt: End of time window (exclusive)
        limit: Maximum number of commits to return

    Returns:
        List of commit dictionaries with external_id, occurred_at, summary, contributor email
    """
    increments = (
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
            "occurred_at": inc.occurred_at.isoformat(),
            "summary": inc.summary,
            "contributor_email": inc.contributor.email if inc.contributor else None,
        }
        for inc in increments
    ]


def get_contributor_activity(project_id: int, from_dt, to_dt) -> list[dict]:
    """Aggregate commit counts by contributor email.

    Args:
        project_id: Project ID to filter by
        from_dt: Start of time window (inclusive)
        to_dt: End of time window (exclusive)

    Returns:
        List of contributor activity dicts, sorted by commit_count descending
    """
    activity = (
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

    return [{"email": item["contributor__email"], "commit_count": item["commit_count"]} for item in activity]
