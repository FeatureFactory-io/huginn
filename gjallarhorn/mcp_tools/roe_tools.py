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
