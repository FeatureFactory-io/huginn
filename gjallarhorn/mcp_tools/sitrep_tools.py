"""Sitrep tools — situational awareness and FRAGO queries."""

from django.db.models import Q

from sitrep.models import Frago, SituationalAwareness


def get_active_situational_awareness(project_id=None) -> dict:
    """Return the latest SA version, or {} if none exists.

    SA is workspace-wide; project_id is accepted but unused.
    """
    sa = SituationalAwareness.objects.prefetch_related("versions").first()
    if sa is None:
        return {}
    version = sa.versions.first()
    if version is None:
        return {}
    return {
        "standing_md": version.standing_md,
        "active_md": version.active_md,
        "version_number": version.version_number,
    }


def list_active_fragos(project_id: int, at_dt) -> list[dict]:
    """Return FRAGOs active at at_dt for the project."""
    qs = Frago.objects.filter(
        project_id=project_id,
        enabled=True,
        effective_from__lte=at_dt,
    ).filter(Q(effective_to__isnull=True) | Q(effective_to__gt=at_dt))
    return [{"id": f.id, "title": f.title, "body_md": f.body_md} for f in qs]
