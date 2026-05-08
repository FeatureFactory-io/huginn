"""Unit tests for SituationalAwareness models (ACT12-SA-01)."""

import pytest
from django.db import IntegrityError

from tests.factories import SituationalAwarenessFactory, SituationalAwarenessVersionFactory


@pytest.mark.django_db
def test_get_or_create_awareness_stable_singleton() -> None:
    from ui.services.situational_awareness_service import get_or_create_awareness

    a = get_or_create_awareness()
    b = get_or_create_awareness()
    assert a.pk == b.pk


@pytest.mark.django_db
def test_version_unique_per_awareness() -> None:
    awareness = SituationalAwarenessFactory()
    SituationalAwarenessVersionFactory(awareness=awareness, version_number=1)
    with pytest.raises(IntegrityError):
        SituationalAwarenessVersionFactory(awareness=awareness, version_number=1)


@pytest.mark.django_db
def test_head_version_query() -> None:
    awareness = SituationalAwarenessFactory()
    SituationalAwarenessVersionFactory(awareness=awareness, version_number=1)
    SituationalAwarenessVersionFactory(awareness=awareness, version_number=3)
    head = awareness.versions.order_by("-version_number").first()
    assert head is not None
    assert head.version_number == 3
