"""SitRep tools — get_active_situational_awareness and list_active_fragos."""

from django.db.models import Q

from sitrep.models import Frago, SituationalAwareness


def get_active_situational_awareness() -> dict:
    """Get the active Situational Awareness capsule.

    Returns:
        Dict with standing_md, active_md, version_number, or {} if no SA
    """
    try:
        sa = SituationalAwareness.objects.first()
    except SituationalAwareness.DoesNotExist:
        return {}

    if not sa:
        return {}

    latest_version = sa.versions.first()
    if not latest_version:
        return {}

    return {
        "standing_md": latest_version.standing_md,
        "active_md": latest_version.active_md,
        "version_number": latest_version.version_number,
    }


def list_active_fragos(project_id: int, at_dt) -> list[dict]:
    """List active FRAGOs for a project at a specific date.

    Args:
        project_id: Project ID to filter by
        at_dt: Date to check FRAGO active window

    Returns:
        List of active FRAGO dicts with id, title, body_md
    """
    fragos = Frago.objects.filter(
        project_id=project_id,
        enabled=True,
        effective_from__lte=at_dt,
    ).filter(Q(effective_to__isnull=True) | Q(effective_to__gt=at_dt))

    return [{"id": frago.id, "title": frago.title, "body_md": frago.body_md} for frago in fragos]
