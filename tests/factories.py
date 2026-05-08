"""factory_boy factories for tests."""

import factory
from django.utils import timezone
from factory.django import DjangoModelFactory

from accounts.models import User
from ingestion.domain.increments import ContributorDTO
from ingestion.models import Contributor, DataSource, Increment, IngestionRun, Project
from playbooks.models import Playbook, PlaybookVariable, PlaybookVersion
from sitrep.models import Frago, SituationalAwareness, SituationalAwarenessVersion


class UserFactory(DjangoModelFactory):
    class Meta:
        model = User

    email = factory.Sequence(lambda n: f"user{n}@example.com")


class PlaybookFactory(DjangoModelFactory):
    class Meta:
        model = Playbook

    name = factory.Sequence(lambda n: f"Playbook {n}")
    slug = factory.Sequence(lambda n: f"playbook-{n}")
    description = ""
    is_system_seed = False


class PlaybookVersionFactory(DjangoModelFactory):
    class Meta:
        model = PlaybookVersion

    playbook = factory.SubFactory(PlaybookFactory)
    version_number = 1
    workflow_md = ""
    change_summary = ""


class PlaybookVariableFactory(DjangoModelFactory):
    class Meta:
        model = PlaybookVariable

    playbook_version = factory.SubFactory(PlaybookVersionFactory)
    sort_order = factory.Sequence(lambda n: n)
    name = factory.Sequence(lambda n: f"Variable {n}")
    abbrev = factory.Sequence(lambda n: f"V{n}")


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
    sync_state = Project.SyncState.ACTIVE


class FragoFactory(DjangoModelFactory):
    class Meta:
        model = Frago

    project = factory.SubFactory(ProjectFactory)
    title = factory.Sequence(lambda n: f"Frago {n}")
    body_md = ""
    enabled = True


class SituationalAwarenessFactory(DjangoModelFactory):
    class Meta:
        model = SituationalAwareness


class SituationalAwarenessVersionFactory(DjangoModelFactory):
    class Meta:
        model = SituationalAwarenessVersion

    awareness = factory.SubFactory(SituationalAwarenessFactory)
    version_number = 1
    standing_md = ""
    active_md = ""
    change_summary = ""


class ContributorFactory(DjangoModelFactory):
    class Meta:
        model = Contributor

    datasource = factory.SubFactory(DataSourceFactory)
    email = factory.Sequence(lambda n: f"dev{n}@example.com")
    name = factory.Sequence(lambda n: f"Dev {n}")


class IncrementFactory(DjangoModelFactory):
    class Meta:
        model = Increment

    project = factory.SubFactory(ProjectFactory)
    datasource = factory.LazyAttribute(lambda o: o.project.datasource)
    kind = Increment.Kind.COMMIT
    external_id = factory.Sequence(lambda n: f"{n:040x}")
    occurred_at = factory.LazyFunction(timezone.now)
    summary = factory.Faker("sentence", nb_words=4)
    payload = factory.LazyFunction(dict)


class IngestionRunFactory(DjangoModelFactory):
    class Meta:
        model = IngestionRun

    project = factory.SubFactory(ProjectFactory)
    status = IngestionRun.Status.RUNNING


class ContributorDTOFactory(factory.Factory):
    class Meta:
        model = ContributorDTO

    source = "gitlab"
    email = "alice@example.com"
    name = "Alice"
    handle = None
