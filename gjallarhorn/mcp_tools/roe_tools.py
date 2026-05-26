"""RoE tools — resolve the active Rules of Engagement for a project."""

from ingestion.models import Project


def get_active_roe(project_id: int) -> dict | None:
    """Return active Rules of Engagement data for the project, or None if none assigned."""
    project = Project.objects.select_related("assigned_roe").get(pk=project_id)
    roe = project.assigned_roe
    if roe is None:
        return None
    version = roe.versions.first()
    if version is None:
        return None
    return {
        "workflow_md": version.workflow_md,
        "version_number": version.version_number,
        "roe_name": roe.name,
    }


def get_roe_variables(project_id: int) -> list[dict] | None:
    """Return structured variables from the active RoE version, or None if no RoE/no variables.

    Returns list of dicts with: name, abbrev, y_axis_label, calculating, interpreting.
    Ordered by sort_order.
    """
    project = Project.objects.select_related("assigned_roe").get(pk=project_id)
    roe = project.assigned_roe
    if roe is None:
        return None

    version = roe.versions.first()
    if version is None:
        return None

    variables = version.variables.all()
    if not variables.exists():
        return None

    return [
        {
            "name": v.name,
            "abbrev": v.abbrev,
            "y_axis_label": v.y_axis_label,
            "calculating": v.calculating,
            "interpreting": v.interpreting,
        }
        for v in variables
    ]
