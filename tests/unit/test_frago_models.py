"""Unit tests for sitrep Frago model (ACT6-FRAGO-01)."""

import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.utils import timezone

from sitrep.models import Frago
from tests.factories import FragoFactory, ProjectFactory, RulesOfEngagementVariableFactory


@pytest.mark.django_db
def test_frago_requires_project() -> None:
    with pytest.raises(IntegrityError):
        Frago.objects.create(title="orphan")


@pytest.mark.django_db
def test_frago_optional_affected_variable() -> None:
    project = ProjectFactory()
    FragoFactory(project=project, affected_variable=None)
    variable = RulesOfEngagementVariableFactory()
    frago = FragoFactory(project=project, affected_variable=variable)
    assert frago.affected_variable_id == variable.id


@pytest.mark.django_db
def test_frago_revoked_at_nullable() -> None:
    frago = FragoFactory(revoked_at=None)
    assert frago.revoked_at is None


@pytest.mark.django_db
def test_frago_revoked_cannot_remain_enabled() -> None:
    frago = FragoFactory.build(revoked_at=timezone.now(), enabled=True)
    with pytest.raises(ValidationError):
        frago.full_clean()


@pytest.mark.django_db
def test_frago_audit_event_linked() -> None:
    fr = FragoFactory()
    from sitrep.models import FragoAuditEvent

    FragoAuditEvent.objects.create(frago=fr, kind=FragoAuditEvent.Kind.CREATED.value, message="test")
    assert fr.audit_events.count() == 1
