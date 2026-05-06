from datetime import timedelta

import pytest
from django.utils import timezone

from tests.factories import IncrementFactory, ProjectFactory
from ui.services.project_vitals_service import ProjectVitalsService


@pytest.mark.django_db
def test_latest_increment_occurred_at_none_for_project_without_commits():
    project = ProjectFactory()
    assert ProjectVitalsService().latest_increment_occurred_at(project.pk) is None


@pytest.mark.django_db
def test_latest_increment_occurred_at_returns_newest_timestamp():
    project = ProjectFactory()
    older = timezone.now() - timedelta(days=2)
    newer = timezone.now() - timedelta(hours=2)
    IncrementFactory(project=project, occurred_at=older)
    IncrementFactory(project=project, occurred_at=newer)
    result = ProjectVitalsService().latest_increment_occurred_at(project.pk)
    assert result is not None
    assert abs((result - newer).total_seconds()) < 1


@pytest.mark.django_db
def test_latest_increment_occurred_at_isolated_per_project():
    a = ProjectFactory()
    b = ProjectFactory()
    IncrementFactory(project=a, occurred_at=timezone.now())
    assert ProjectVitalsService().latest_increment_occurred_at(b.pk) is None
