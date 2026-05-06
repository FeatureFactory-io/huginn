"""factory_boy factories for tests."""

import factory
from factory.django import DjangoModelFactory

from ingestion.models import DataSource, Project


class DataSourceFactory(DjangoModelFactory):
    class Meta:
        model = DataSource

    name = factory.Sequence(lambda n: f"gitlab-{n}")
    datasource_type = DataSource.Type.GITLAB
    base_url = "https://gitlab.example.com/"
    status = DataSource.Status.CONNECTED


class ProjectFactory(DjangoModelFactory):
    class Meta:
        model = Project

    datasource = factory.SubFactory(DataSourceFactory)
    name = factory.Sequence(lambda n: f"project-{n}")
    slug = factory.Sequence(lambda n: f"project-{n}")
    status = Project.Status.ACTIVE
