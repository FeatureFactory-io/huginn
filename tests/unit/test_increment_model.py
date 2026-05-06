"""Increment model."""

import pytest
from django.db import IntegrityError

from ingestion.models import Increment
from tests.factories import IncrementFactory, ProjectFactory


@pytest.mark.django_db
def test_increment_unique_project_kind_external_id() -> None:
    p = ProjectFactory()
    IncrementFactory(project=p, kind=Increment.Kind.COMMIT, external_id="sha1")
    with pytest.raises(IntegrityError):
        IncrementFactory(project=p, kind=Increment.Kind.COMMIT, external_id="sha1")
