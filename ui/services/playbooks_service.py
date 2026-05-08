"""Playbooks domain logic — list helpers and versioned persistence."""

from __future__ import annotations

from datetime import timedelta
from typing import Any

from django.db import transaction
from django.db.models import Count, Exists, Max, OuterRef, Subquery
from django.utils import timezone
from django.utils.text import slugify

from playbooks.models import Playbook, PlaybookVariable, PlaybookVersion


def playbook_queryset_for_list():
    latest_ver = Subquery(
        PlaybookVersion.objects.filter(playbook_id=OuterRef("pk"))
        .order_by("-version_number")
        .values("version_number")[:1],
    )
    latest_at = Subquery(
        PlaybookVersion.objects.filter(playbook_id=OuterRef("pk")).order_by("-version_number").values("created_at")[:1],
    )
    return Playbook.objects.annotate(
        latest_version_number=latest_ver,
        latest_snapshot_at=latest_at,
    ).annotate(used_by_count=Count("assigned_projects", distinct=True))


def apply_playbook_list_filters(qs, *, author: str, used_by: str, updated_within: str):
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
                PlaybookVersion.objects.filter(playbook_id=OuterRef("pk"), created_at__gte=cutoff),
            ),
        )
    elif updated_within == "30":
        cutoff = timezone.now() - timedelta(days=30)
        qs = qs.filter(
            Exists(
                PlaybookVersion.objects.filter(playbook_id=OuterRef("pk"), created_at__gte=cutoff),
            ),
        )
    return qs


def unique_playbook_slug(name: str) -> str:
    base = slugify(name.strip()) or "playbook"
    slug = base
    n = 0
    while Playbook.objects.filter(slug=slug).exists():
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


def _persist_variable_rows(version: PlaybookVersion, rows: list[dict[str, Any]]) -> None:
    PlaybookVariable.objects.filter(playbook_version=version).delete()
    if not rows:
        return
    PlaybookVariable.objects.bulk_create(
        [PlaybookVariable(playbook_version=version, **row) for row in rows],
    )


def editor_snapshot_from_version(version: PlaybookVersion | None) -> dict[str, Any]:
    if version is None:
        return {
            "name": "",
            "description": "",
            "workflow_md": "",
            "variables": [],
        }
    pb = version.playbook
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
        "name": pb.name,
        "description": pb.description,
        "workflow_md": version.workflow_md,
        "variables": var_rows,
    }


@transaction.atomic
def create_playbook_with_version(
    *,
    user,
    name: str,
    description: str,
    workflow_md: str,
    variables: list[dict[str, Any]],
) -> Playbook:
    slug = unique_playbook_slug(name)
    pb = Playbook.objects.create(
        name=name.strip(),
        slug=slug,
        description=(description or "").strip(),
        created_by=user if getattr(user, "is_authenticated", False) else None,
    )
    ver = PlaybookVersion.objects.create(
        playbook=pb,
        version_number=1,
        workflow_md=workflow_md or "",
        change_summary="Initial version",
        created_by=user if getattr(user, "is_authenticated", False) else None,
    )
    _persist_variable_rows(ver, variables)
    return pb


@transaction.atomic
def append_playbook_version(
    *,
    playbook: Playbook,
    user,
    change_summary: str,
    name: str,
    description: str,
    workflow_md: str,
    variables: list[dict[str, Any]],
) -> PlaybookVersion:
    next_n = (playbook.versions.aggregate(m=Max("version_number"))["m"] or 0) + 1
    playbook.name = name.strip()
    playbook.description = (description or "").strip()
    playbook.save(update_fields=["name", "description", "updated_at"])
    ver = PlaybookVersion.objects.create(
        playbook=playbook,
        version_number=next_n,
        workflow_md=workflow_md or "",
        change_summary=(change_summary or "").strip(),
        created_by=user if getattr(user, "is_authenticated", False) else None,
    )
    _persist_variable_rows(ver, variables)
    return ver


def delete_playbook_if_allowed(playbook_id: int) -> tuple[bool, str]:
    pb = (
        Playbook.objects.filter(pk=playbook_id)
        .annotate(used_by_count=Count("assigned_projects", distinct=True))
        .first()
    )
    if pb is None:
        return False, "Playbook not found."
    if pb.is_system_seed:
        return False, "Cannot delete the system seed playbook."
    if pb.used_by_count > 0:
        return False, "Playbook is assigned to one or more projects."
    pb.delete()
    return True, ""
