"""Playbooks domain logic — list helpers and versioned persistence."""

from __future__ import annotations

from datetime import timedelta
from typing import Any

from django.db import transaction
from django.db.models import Count, Exists, Max, OuterRef, Subquery
from django.utils import timezone
from django.utils.text import slugify

from playbooks.catalog import scan_version_for_drift, validate_table_row
from playbooks.models import Playbook, PlaybookTable, PlaybookVariable, PlaybookVersion


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


def _split_dimensions(raw: str) -> list[str]:
    parts = [p.strip() for p in (raw or "").split(",")]
    return [p for p in parts if p]


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
                "dimensions": _split_dimensions(post.get(prefix + "dimensions") or ""),
            },
        )
        i += 1
    return rows, errors


def parse_tables_from_post(post: Any) -> tuple[list[dict[str, Any]], list[str]]:
    errors: list[str] = []
    rows: list[dict[str, Any]] = []
    i = 0
    while i < 64:
        prefix = f"tbl_{i}_"
        entity = (post.get(prefix + "entity") or "").strip()
        if not entity:
            i += 1
            continue
        slicer = (post.get(prefix + "slicer") or "").strip()
        row_display = len(rows) + 1
        if not slicer:
            errors.append(f"Tables row {row_display}: Slicer is required.")
        msg = validate_table_row(entity=entity, slicer=slicer)
        if msg:
            errors.append(f"Tables row {row_display}: {msg}")
        rows.append(
            {
                "sort_order": len(rows),
                "entity": entity,
                "slicer": slicer,
                "dimensions": _split_dimensions(post.get(prefix + "dimensions") or ""),
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


def _persist_table_rows(version: PlaybookVersion, rows: list[dict[str, Any]]) -> None:
    PlaybookTable.objects.filter(playbook_version=version).delete()
    if not rows:
        return
    PlaybookTable.objects.bulk_create(
        [PlaybookTable(playbook_version=version, **row) for row in rows],
    )


def editor_snapshot_from_version(version: PlaybookVersion | None) -> dict[str, Any]:
    if version is None:
        return {
            "name": "",
            "description": "",
            "workflow_md": "",
            "variables": [],
            "tables": [],
        }
    pb = version.playbook
    vars_ = list(
        version.variables.order_by("sort_order").values(
            "name",
            "abbrev",
            "calculating",
            "interpreting",
            "hover",
            "dimensions",
        ),
    )
    tbls = list(
        version.tables.order_by("sort_order").values(
            "entity",
            "slicer",
            "dimensions",
        ),
    )
    var_rows = []
    for r in vars_:
        dims = r["dimensions"] if isinstance(r["dimensions"], list) else []
        var_rows.append({**r, "dimensions_display": ", ".join(dims)})
    tbl_rows = []
    for r in tbls:
        dims = r["dimensions"] if isinstance(r["dimensions"], list) else []
        tbl_rows.append({**r, "dimensions_display": ", ".join(dims)})
    return {
        "name": pb.name,
        "description": pb.description,
        "workflow_md": version.workflow_md,
        "variables": var_rows,
        "tables": tbl_rows,
    }


@transaction.atomic
def create_playbook_with_version(
    *,
    user,
    name: str,
    description: str,
    workflow_md: str,
    variables: list[dict[str, Any]],
    tables: list[dict[str, Any]],
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
    _persist_table_rows(ver, tables)
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
    tables: list[dict[str, Any]],
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
    _persist_table_rows(ver, tables)
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


def catalog_drift_messages_all_versions(playbook: Playbook) -> list[str]:
    out: list[str] = []
    for ver in playbook.versions.order_by("version_number"):
        for line in scan_version_for_drift(ver):
            out.append(f"v{ver.version_number}: {line}")
    return out
