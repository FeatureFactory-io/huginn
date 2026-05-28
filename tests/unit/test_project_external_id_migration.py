"""Project external_project_id model tests."""

import pytest
from django.db import IntegrityError

from ingestion.models import DataSource
from tests.factories import DataSourceFactory, ProjectFactory


@pytest.mark.django_db
def test_datasource_includes_github_type() -> None:
    assert DataSource.Type.GITHUB == "github"
    ds = DataSourceFactory(datasource_type=DataSource.Type.GITHUB, base_url="https://api.github.com")
    assert ds.get_datasource_type_display() == "GitHub"


@pytest.mark.django_db
def test_unique_external_project_id_per_datasource() -> None:
    ds = DataSourceFactory()
    ProjectFactory(datasource=ds, external_project_id=42, slug="proj-a")
    with pytest.raises(IntegrityError):
        ProjectFactory(datasource=ds, external_project_id=42, slug="proj-b")
