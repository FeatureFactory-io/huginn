"""FRAGO list queryset filtering — mirrors row-level status/effect semantics in the ORM."""

from __future__ import annotations

from datetime import date

from django.db.models import Q
from django.http import HttpRequest

from ingestion.models import Project
from sitrep.models import Frago


def frago_list_queryset(project: Project | None):
    qs = Frago.objects.select_related("project", "affected_variable").order_by("-updated_at", "-pk")
    if project is not None:
        qs = qs.filter(project=project)
    return qs


def apply_frago_list_filters(qs, request: HttpRequest):
    """Apply GET filters using the same rules as ``_frago_row`` / detail status ordering."""
    today = date.today()

    variable = (request.GET.get("variable") or "").strip()
    if variable:
        qs = qs.filter(affected_variable__abbrev=variable)

    if request.GET.get("in_effect") == "1":
        qs = qs.filter(
            Q(revoked_at__isnull=True, enabled=True)
            & (Q(effective_from__isnull=True) | Q(effective_from__lte=today))
            & (Q(effective_to__isnull=True) | Q(effective_to__gte=today)),
        )

    status = (request.GET.get("status") or "").strip()
    if status and status != "All":
        revoked = Q(revoked_at__isnull=False)
        inactive = Q(revoked_at__isnull=True, enabled=False)
        scheduled = Q(
            revoked_at__isnull=True,
            enabled=True,
            effective_from__isnull=False,
            effective_from__gt=today,
        )
        expired = (
            Q(revoked_at__isnull=True, enabled=True)
            & ~(Q(effective_from__isnull=False) & Q(effective_from__gt=today))
            & Q(effective_to__isnull=False, effective_to__lt=today)
        )
        active = (
            Q(revoked_at__isnull=True, enabled=True)
            & ~(Q(effective_from__isnull=False) & Q(effective_from__gt=today))
            & ~(Q(effective_to__isnull=False) & Q(effective_to__lt=today))
        )
        lookup = {
            "Revoked": revoked,
            "Inactive": inactive,
            "Scheduled": scheduled,
            "Expired": expired,
            "Active": active,
        }
        q = lookup.get(status)
        if q is not None:
            qs = qs.filter(q)
        else:
            qs = qs.none()

    return qs
