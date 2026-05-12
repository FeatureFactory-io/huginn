"""Playbook tools — get_active_playbook."""

from ingestion.models import Project


def get_active_playbook(project_id: int) -> dict | None:
    """Get the active Playbook workflow for a project.

    Args:
        project_id: Project ID

    Returns:
        Dict with workflow_md, version_number, playbook_name, or None if no playbook
    """
    try:
        project = Project.objects.select_related("assigned_playbook").get(id=project_id)
    except Project.DoesNotExist:
        return None

    if not project.assigned_playbook:
        return None

    # Get latest version
    latest_version = project.assigned_playbook.versions.first()
    if not latest_version:
        return None

    return {
        "workflow_md": latest_version.workflow_md,
        "version_number": latest_version.version_number,
        "playbook_name": project.assigned_playbook.name,
    }
