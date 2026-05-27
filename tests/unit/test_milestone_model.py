"""Milestone model tests."""

import pytest
from django.db import IntegrityError

from tests.factories import MilestoneFactory, ProjectFactory


@pytest.mark.django_db
def test_milestone_unique_per_project_external_id() -> None:
    project = ProjectFactory()
    MilestoneFactory(project=project, external_id="7")
    with pytest.raises(IntegrityError):
        MilestoneFactory(project=project, external_id="7")
