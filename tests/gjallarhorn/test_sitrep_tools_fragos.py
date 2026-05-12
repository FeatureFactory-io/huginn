"""list_active_fragos tool tests — T-65b."""

import pytest
from django.utils import timezone

from gjallarhorn.mcp_tools.sitrep_tools import list_active_fragos
from ingestion.models import Project
from sitrep.models import Frago


@pytest.mark.django_db
class TestListActiveFragos:
    def test_active_frago_in_window(self):
        """enabled FRAGO at at_dt → in result."""
        project = Project.objects.create(name="test-proj", slug="test-proj")
        at_dt = timezone.now().date()

        frago = Frago.objects.create(
            project=project,
            title="Active FRAGO",
            body_md="Test",
            enabled=True,
            effective_from=at_dt - timezone.timedelta(days=1),
            effective_to=None,
        )

        result = list_active_fragos(project_id=project.id, at_dt=at_dt)

        assert len(result) == 1
        assert result[0]["title"] == "Active FRAGO"
        assert result[0]["id"] == frago.id

    def test_disabled_frago_excluded(self):
        """enabled=False → excluded."""
        project = Project.objects.create(name="test-proj", slug="test-proj")
        at_dt = timezone.now().date()

        Frago.objects.create(
            project=project,
            title="Disabled FRAGO",
            body_md="Test",
            enabled=False,
            effective_from=at_dt - timezone.timedelta(days=1),
        )

        result = list_active_fragos(project_id=project.id, at_dt=at_dt)

        assert len(result) == 0

    def test_frago_expired_excluded(self):
        """effective_to < at_dt → excluded."""
        project = Project.objects.create(name="test-proj", slug="test-proj")
        at_dt = timezone.now().date()

        Frago.objects.create(
            project=project,
            title="Expired FRAGO",
            body_md="Test",
            enabled=True,
            effective_from=at_dt - timezone.timedelta(days=10),
            effective_to=at_dt - timezone.timedelta(days=1),
        )

        result = list_active_fragos(project_id=project.id, at_dt=at_dt)

        assert len(result) == 0

    def test_frago_not_yet_active_excluded(self):
        """effective_from > at_dt → excluded."""
        project = Project.objects.create(name="test-proj", slug="test-proj")
        at_dt = timezone.now().date()

        Frago.objects.create(
            project=project,
            title="Future FRAGO",
            body_md="Test",
            enabled=True,
            effective_from=at_dt + timezone.timedelta(days=1),
        )

        result = list_active_fragos(project_id=project.id, at_dt=at_dt)

        assert len(result) == 0
