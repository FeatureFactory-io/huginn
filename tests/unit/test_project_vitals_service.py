import pytest

from tests.factories import ProjectFactory
from ui.services.project_vitals_service import ProjectVitalsService


@pytest.mark.django_db
def test_latest_increment_occurred_at_none_for_project_without_commits():
    project = ProjectFactory()
    assert ProjectVitalsService().latest_increment_occurred_at(project.pk) is None
