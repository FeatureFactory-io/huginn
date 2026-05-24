"""Rules of Engagement domain logic — list helpers and versioned persistence."""

from __future__ import annotations

from datetime import timedelta
from typing import Any

from django.db import transaction
from django.db.models import Count, Exists, Max, OuterRef, Subquery
from django.utils import timezone
from django.utils.text import slugify

from roe.models import RulesOfEngagement, RulesOfEngagementVariable, RulesOfEngagementVersion


def roe_queryset_for_list():
    latest_ver = Subquery(
        RulesOfEngagementVersion.objects.filter(roe_id=OuterRef("pk"))
        .order_by("-version_number")
        .values("version_number")[:1],
    )
    latest_at = Subquery(
        RulesOfEngagementVersion.objects.filter(roe_id=OuterRef("pk"))
        .order_by("-version_number")
        .values("created_at")[:1],
    )
    return RulesOfEngagement.objects.annotate(
        latest_version_number=latest_ver,
        latest_snapshot_at=latest_at,
    ).annotate(used_by_count=Count("assigned_projects", distinct=True))


def apply_roe_list_filters(qs, *, author: str, used_by: str, updated_within: str):
    author = (author or "").strip()
    used_by = (used_by or "").strip().lower()
    updated_within = (updated_within or "").strip()

    if author:
        qs = qs.filter(created_by__email__icontains=author)
    if used_by == "yes":
        qs = qs.filter(used_by_count__gt=0)
    elif used_by == "no":
        qs = qs.filter(used_by_count=0)

    if updated_within == "7":
        cutoff = timezone.now() - timedelta(days=7)
        qs = qs.filter(
            Exists(
                RulesOfEngagementVersion.objects.filter(roe_id=OuterRef("pk"), created_at__gte=cutoff),
            ),
        )
    elif updated_within == "30":
        cutoff = timezone.now() - timedelta(days=30)
        qs = qs.filter(
            Exists(
                RulesOfEngagementVersion.objects.filter(roe_id=OuterRef("pk"), created_at__gte=cutoff),
            ),
        )
    return qs


def unique_roe_slug(name: str) -> str:
    base = slugify(name.strip()) or "roe"
    slug = base
    n = 0
    while RulesOfEngagement.objects.filter(slug=slug).exists():
        n += 1
        slug = f"{base}-{n}"
    return slug


def parse_variables_from_post(post: Any) -> tuple[list[dict[str, Any]], list[str]]:
    errors: list[str] = []
    rows: list[dict[str, Any]] = []
    i = 0
    while i < 64:
        prefix = f"var_{i}_"
        name = (post.get(prefix + "name") or "").strip()
        if not name:
            i += 1
            continue
        abbrev = (post.get(prefix + "abbrev") or "").strip()
        if not abbrev:
            errors.append(f"Variable row {len(rows) + 1}: Abbrev is required.")
        rows.append(
            {
                "sort_order": len(rows),
                "name": name,
                "abbrev": abbrev,
                "calculating": (post.get(prefix + "calculating") or "").strip(),
                "interpreting": (post.get(prefix + "interpreting") or "").strip(),
                "hover": (post.get(prefix + "hover") or "").strip(),
            },
        )
        i += 1
    return rows, errors


def _persist_variable_rows(version: RulesOfEngagementVersion, rows: list[dict[str, Any]]) -> None:
    RulesOfEngagementVariable.objects.filter(roe_version=version).delete()
    if not rows:
        return
    RulesOfEngagementVariable.objects.bulk_create(
        [RulesOfEngagementVariable(roe_version=version, **row) for row in rows],
    )


def editor_snapshot_from_version(version: RulesOfEngagementVersion | None) -> dict[str, Any]:
    if version is None:
        return {
            "name": "",
            "description": "",
            "workflow_md": "",
            "variables": [],
        }
    roe = version.roe
    var_rows = list(
        version.variables.order_by("sort_order").values(
            "name",
            "abbrev",
            "calculating",
            "interpreting",
            "hover",
        ),
    )
    return {
        "name": roe.name,
        "description": roe.description,
        "workflow_md": version.workflow_md,
        "variables": var_rows,
    }


@transaction.atomic
def create_roe_with_version(
    *,
    user,
    name: str,
    description: str,
    workflow_md: str,
    variables: list[dict[str, Any]],
) -> RulesOfEngagement:
    slug = unique_roe_slug(name)
    roe = RulesOfEngagement.objects.create(
        name=name.strip(),
        slug=slug,
        description=(description or "").strip(),
        created_by=user if getattr(user, "is_authenticated", False) else None,
    )
    ver = RulesOfEngagementVersion.objects.create(
        roe=roe,
        version_number=1,
        workflow_md=workflow_md or "",
        change_summary="Initial version",
        created_by=user if getattr(user, "is_authenticated", False) else None,
    )
    _persist_variable_rows(ver, variables)
    return roe


@transaction.atomic
def append_roe_version(
    *,
    roe: RulesOfEngagement,
    user,
    change_summary: str,
    name: str,
    description: str,
    workflow_md: str,
    variables: list[dict[str, Any]],
) -> RulesOfEngagementVersion:
    next_n = (roe.versions.aggregate(m=Max("version_number"))["m"] or 0) + 1
    roe.name = name.strip()
    roe.description = (description or "").strip()
    roe.save(update_fields=["name", "description", "updated_at"])
    ver = RulesOfEngagementVersion.objects.create(
        roe=roe,
        version_number=next_n,
        workflow_md=workflow_md or "",
        change_summary=(change_summary or "").strip(),
        created_by=user if getattr(user, "is_authenticated", False) else None,
    )
    _persist_variable_rows(ver, variables)
    return ver


def delete_roe_if_allowed(roe_id: int) -> tuple[bool, str]:
    roe = (
        RulesOfEngagement.objects.filter(pk=roe_id)
        .annotate(used_by_count=Count("assigned_projects", distinct=True))
        .first()
    )
    if roe is None:
        return False, "Rules of Engagement not found."
    if roe.is_system_seed:
        return False, "Cannot delete the system seed Rules of Engagement."
    if roe.used_by_count > 0:
        return False, "Rules of Engagement is assigned to one or more projects."
    roe.delete()
    return True, ""
