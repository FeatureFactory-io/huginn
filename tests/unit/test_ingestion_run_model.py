"""IngestionRun model."""

import pytest

from ingestion.models import IngestionRun
from tests.factories import IngestionRunFactory, ProjectFactory


@pytest.mark.django_db
def test_ingestion_run_defaults() -> None:
    p = ProjectFactory()
    run = IngestionRunFactory(project=p, status=IngestionRun.Status.PENDING, finished_at=None)
    assert run.increments_ingested == 0
    assert run.contributors_touched == 0
    assert run.error_message == ""
