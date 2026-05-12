"""SitRep model tests — T-60."""

import pytest
from django.db import IntegrityError
from django.utils import timezone

from ingestion.models import Project
from sitrep.models import Frago, SitRep


@pytest.mark.django_db
class TestSitRepModel:
    def test_unique_constraint_project_to_dt(self):
        """Duplicate (project, to_dt) raises IntegrityError."""
        project = Project.objects.create(name="test-proj", slug="test-proj")
        to_dt = timezone.now()

        SitRep.objects.create(
            project=project,
            from_dt=timezone.now(),
            to_dt=to_dt,
            trigger="automatic",
            headline="First",
            situation_assessment="Test",
        )

        with pytest.raises(IntegrityError):
            SitRep.objects.create(
                project=project,
                from_dt=timezone.now(),
                to_dt=to_dt,
                trigger="manual",
                headline="Duplicate",
                situation_assessment="Should fail",
            )

    def test_ordering_descending(self):
        """Queryset first is most recent (ordering = ['-generated_at'])."""
        project = Project.objects.create(name="test-proj", slug="test-proj")

        sr1 = SitRep.objects.create(
            project=project,
            from_dt=timezone.now(),
            to_dt=timezone.now(),
            trigger="automatic",
            headline="Old",
            situation_assessment="Old",
        )
        sr2 = SitRep.objects.create(
            project=project,
            from_dt=timezone.now(),
            to_dt=timezone.now() + timezone.timedelta(hours=1),
            trigger="automatic",
            headline="New",
            situation_assessment="New",
        )

        qs = SitRep.objects.all()
        assert qs.first() == sr2
        assert qs.last() == sr1

    def test_notable_activity_defaults_to_list(self):
        """Missing notable_activity → defaults to []."""
        project = Project.objects.create(name="test-proj", slug="test-proj")

        sr = SitRep.objects.create(
            project=project,
            from_dt=timezone.now(),
            to_dt=timezone.now(),
            trigger="automatic",
            headline="Test",
            situation_assessment="Test",
        )

        assert sr.notable_activity == []

    def test_fragos_applied_m2m(self):
        """M2M attach/detach works."""
        project = Project.objects.create(name="test-proj", slug="test-proj")
        frago = Frago.objects.create(
            project=project,
            title="Test FRAGO",
            body_md="Test",
            enabled=True,
        )

        sr = SitRep.objects.create(
            project=project,
            from_dt=timezone.now(),
            to_dt=timezone.now(),
            trigger="automatic",
            headline="Test",
            situation_assessment="Test",
        )

        sr.fragos_applied.add(frago)
        assert sr.fragos_applied.count() == 1
        assert sr.fragos_applied.first() == frago

        sr.fragos_applied.remove(frago)
        assert sr.fragos_applied.count() == 0

    def test_source_plan_nullable(self):
        """source_plan=None is valid."""
        project = Project.objects.create(name="test-proj", slug="test-proj")

        sr = SitRep.objects.create(
            project=project,
            from_dt=timezone.now(),
            to_dt=timezone.now(),
            trigger="automatic",
            headline="Test",
            situation_assessment="Test",
            source_plan=None,
        )

        assert sr.source_plan is None
