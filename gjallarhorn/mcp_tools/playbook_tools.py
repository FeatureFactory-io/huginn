"""Playbook tools — resolve the active playbook for a project."""

from ingestion.models import Project


def get_active_playbook(project_id: int) -> dict | None:
    """Return active playbook data for the project, or None if none assigned."""
    project = Project.objects.select_related("assigned_playbook").get(pk=project_id)
    playbook = project.assigned_playbook
    if playbook is None:
        return None
    version = playbook.versions.first()
    if version is None:
        return None
    return {
        "workflow_md": version.workflow_md,
        "version_number": version.version_number,
        "playbook_name": playbook.name,
    }
