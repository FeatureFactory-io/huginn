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


def _badge_active_q(today: date) -> Q:
    """Matches rows whose Status badge is Active (in window, enabled, not revoked)."""
    return (
        Q(revoked_at__isnull=True, enabled=True)
        & ~(Q(effective_from__isnull=False) & Q(effective_from__gt=today))
        & ~(Q(effective_to__isnull=False) & Q(effective_to__lt=today))
    )


def apply_frago_list_filters(qs, request: HttpRequest):
    """Apply GET filters using the same rules as ``_frago_row`` / detail status ordering."""
    today = date.today()

    variable = (request.GET.get("variable") or "").strip()
    if variable:
        qs = qs.filter(affected_variable__abbrev=variable)

    affects = (request.GET.get("affects") or "").strip().lower()
    if affects == "narrative":
        qs = qs.filter(affected_variable__isnull=True)
    elif affects in {"variables", "variable"}:
        qs = qs.filter(affected_variable__isnull=False)

    timing = (request.GET.get("timing") or "").strip().lower()
    if not timing and request.GET.get("in_effect") == "1":
        timing = "in_effect"

    if timing == "in_effect":
        qs = qs.filter(
            Q(revoked_at__isnull=True, enabled=True)
            & (Q(effective_from__isnull=True) | Q(effective_from__lte=today))
            & (Q(effective_to__isnull=True) | Q(effective_to__gte=today)),
        )
    elif timing == "scheduled":
        qs = qs.filter(
            revoked_at__isnull=True,
            enabled=True,
            effective_from__isnull=False,
            effective_from__gt=today,
        )
    elif timing == "past":
        qs = qs.filter(
            Q(revoked_at__isnull=False)
            | Q(
                revoked_at__isnull=True,
                enabled=True,
                effective_to__isnull=False,
                effective_to__lt=today,
            ),
        )

    status_raw = (request.GET.get("status") or "").strip()
    if status_raw and status_raw != "All":
        sk = status_raw.lower()
        if sk == "active":
            qs = qs.filter(_badge_active_q(today))
        elif sk in {"disabled", "inactive"}:
            qs = qs.filter(revoked_at__isnull=True, enabled=False)
        elif sk == "revoked":
            qs = qs.filter(revoked_at__isnull=False)
        else:
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
            active = _badge_active_q(today)
            lookup = {
                "Revoked": revoked,
                "Inactive": inactive,
                "Scheduled": scheduled,
                "Expired": expired,
                "Active": active,
            }
            q = lookup.get(status_raw)
            if q is not None:
                qs = qs.filter(q)
            else:
                qs = qs.none()

    return qs
