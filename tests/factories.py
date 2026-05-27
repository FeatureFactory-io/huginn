"""factory_boy factories for tests."""

from django.utils import timezone
from factory.django import DjangoModelFactory

import factory
from accounts.models import User
from ingestion.domain.increments import ContributorDTO
from ingestion.models import Contributor, DataSource, Increment, IngestionRun, Milestone, Project, UnitOfWork
from roe.models import RulesOfEngagement, RulesOfEngagementVariable, RulesOfEngagementVersion
from sitrep.models import Frago, SitRep, SituationalAwareness, SituationalAwarenessVersion, VariableDatapoint


class UserFactory(DjangoModelFactory):
    class Meta:
        model = User

    email = factory.Sequence(lambda n: f"user{n}@example.com")


class RulesOfEngagementFactory(DjangoModelFactory):
    class Meta:
        model = RulesOfEngagement

    name = factory.Sequence(lambda n: f"RoE {n}")
    slug = factory.Sequence(lambda n: f"roe-{n}")
    description = ""
    is_system_seed = False


class RulesOfEngagementVersionFactory(DjangoModelFactory):
    class Meta:
        model = RulesOfEngagementVersion

    roe = factory.SubFactory(RulesOfEngagementFactory)
    version_number = 1
    workflow_md = ""
    change_summary = ""


class RulesOfEngagementVariableFactory(DjangoModelFactory):
    class Meta:
        model = RulesOfEngagementVariable

    roe_version = factory.SubFactory(RulesOfEngagementVersionFactory)
    sort_order = factory.Sequence(lambda n: n)
    name = factory.Sequence(lambda n: f"Variable {n}")
    abbrev = factory.Sequence(lambda n: f"V{n}")
    y_axis_label = ""


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


class MilestoneFactory(DjangoModelFactory):
    class Meta:
        model = Milestone

    project = factory.SubFactory(ProjectFactory)
    datasource = factory.LazyAttribute(lambda o: o.project.datasource)
    external_id = factory.Sequence(lambda n: str(n + 100))
    title = factory.Sequence(lambda n: f"Milestone {n}")
    state = "active"
    updated_at = factory.LazyFunction(timezone.now)
    payload = factory.LazyFunction(dict)


class UnitOfWorkFactory(DjangoModelFactory):
    class Meta:
        model = UnitOfWork

    project = factory.SubFactory(ProjectFactory)
    datasource = factory.LazyAttribute(lambda o: o.project.datasource)
    kind = UnitOfWork.Kind.ISSUE
    external_id = factory.Sequence(lambda n: str(n + 1000))
    iid = factory.Sequence(lambda n: n + 1)
    title = factory.Sequence(lambda n: f"Issue {n}")
    state = "opened"
    labels = factory.LazyFunction(list)
    created_at = factory.LazyFunction(timezone.now)
    updated_at = factory.LazyFunction(timezone.now)
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


class SitRepFactory(DjangoModelFactory):
    class Meta:
        model = SitRep

    project = factory.SubFactory(ProjectFactory)
    from_dt = factory.LazyFunction(timezone.now)
    to_dt = factory.LazyFunction(timezone.now)
    trigger = "automatic"
    mode_at_generation = "semi_auto"
    headline = factory.Faker("sentence", nb_words=5)
    situation_assessment = factory.Faker("text")


class VariableDatapointFactory(DjangoModelFactory):
    class Meta:
        model = VariableDatapoint

    sitrep = factory.SubFactory(SitRepFactory)
    roe_variable = factory.SubFactory(RulesOfEngagementVariableFactory)
    variable_name = factory.LazyAttribute(lambda o: o.roe_variable.name if o.roe_variable else "Variable")
    y_axis_label = factory.LazyAttribute(lambda o: o.roe_variable.y_axis_label if o.roe_variable else "")
    value = "42"
    color = "green"
    from_dt = factory.LazyAttribute(lambda o: o.sitrep.from_dt)
    to_dt = factory.LazyAttribute(lambda o: o.sitrep.to_dt)
