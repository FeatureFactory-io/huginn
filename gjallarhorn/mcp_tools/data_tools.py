"""Data tools — commit, contributor, and work-item queries scoped to a project."""

from django.db.models import Count, Q

from ingestion.models import Increment, Milestone, UnitOfWork


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


def _serialize_uow(uow: UnitOfWork) -> dict:
    payload = uow.payload or {}
    return {
        "external_id": uow.external_id,
        "iid": uow.iid,
        "kind": uow.kind,
        "title": uow.title,
        "state": uow.state,
        "milestone_title": uow.milestone.title if uow.milestone_id else None,
        "assignee_email": uow.assignee.email if uow.assignee_id else None,
        "labels": list(uow.labels or []),
        "updated_at": uow.updated_at.isoformat() if uow.updated_at else None,
        "closed_at": uow.closed_at.isoformat() if uow.closed_at else None,
        "web_url": payload.get("web_url"),
    }


def list_issues(project_id: int, from_dt, to_dt, limit: int = 200) -> list[dict]:
    """Return issues whose updated_at or closed_at falls in [from_dt, to_dt)."""
    qs = (
        UnitOfWork.objects.filter(project_id=project_id, kind=UnitOfWork.Kind.ISSUE)
        .filter(Q(updated_at__gte=from_dt, updated_at__lt=to_dt) | Q(closed_at__gte=from_dt, closed_at__lt=to_dt))
        .select_related("milestone", "assignee")
        .order_by("-updated_at")[:limit]
    )
    return [_serialize_uow(uow) for uow in qs]


def list_merge_requests(project_id: int, from_dt, to_dt, limit: int = 200) -> list[dict]:
    """Return merge requests updated or closed in [from_dt, to_dt)."""
    qs = (
        UnitOfWork.objects.filter(project_id=project_id, kind=UnitOfWork.Kind.MERGE_REQUEST)
        .filter(Q(updated_at__gte=from_dt, updated_at__lt=to_dt) | Q(closed_at__gte=from_dt, closed_at__lt=to_dt))
        .select_related("milestone", "assignee")
        .order_by("-updated_at")[:limit]
    )
    return [_serialize_uow(uow) for uow in qs]


def list_milestones(project_id: int, at_dt=None, limit: int = 50) -> list[dict]:
    """Return milestones for the project (active and recently updated)."""
    qs = Milestone.objects.filter(project_id=project_id)
    if at_dt is not None:
        qs = qs.filter(updated_at__lte=at_dt)
    qs = qs.order_by("-updated_at")[:limit]
    return [
        {
            "external_id": ms.external_id,
            "title": ms.title,
            "state": ms.state,
            "due_date": ms.due_date.isoformat() if ms.due_date else None,
            "updated_at": ms.updated_at.isoformat() if ms.updated_at else None,
            "web_url": (ms.payload or {}).get("web_url"),
        }
        for ms in qs
    ]
