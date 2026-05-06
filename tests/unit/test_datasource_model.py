"""Unit tests for DataSource model helpers."""

from datetime import timedelta

import pytest
from django.utils import timezone

from ingestion.models import DataSource


@pytest.mark.django_db
def test_computed_status_connected_no_expiry() -> None:
    ds = DataSource.objects.create(
        name="co-gitlab",
        base_url="https://gitlab.example.com/",
        status=DataSource.Status.CONNECTED,
    )
    assert ds.computed_status == DataSource.Status.CONNECTED


@pytest.mark.django_db
def test_computed_status_token_expiring_within_30_days() -> None:
    future = timezone.now() + timedelta(days=14)
    ds = DataSource.objects.create(
        name="exp-soon",
        base_url="https://gitlab.example.com/",
        token_expires_at=future,
        status=DataSource.Status.CONNECTED,
    )
    assert ds.computed_status == DataSource.Status.TOKEN_EXPIRING


@pytest.mark.django_db
def test_computed_status_token_expired() -> None:
    past = timezone.now() - timedelta(days=1)
    ds = DataSource.objects.create(
        name="exp-past",
        base_url="https://gitlab.example.com/",
        token_expires_at=past,
        status=DataSource.Status.CONNECTED,
    )
    assert ds.computed_status == DataSource.Status.TOKEN_EXPIRED


@pytest.mark.django_db
def test_token_expires_in_days_none() -> None:
    ds = DataSource.objects.create(name="no-exp", base_url="https://gitlab.example.com/")
    assert ds.token_expires_in_days is None


@pytest.mark.django_db
def test_token_expires_in_days_approximately_14() -> None:
    future = timezone.now() + timedelta(days=14)
    ds = DataSource.objects.create(
        name="in-14",
        base_url="https://gitlab.example.com/",
        token_expires_at=future,
    )
    assert 13 <= (ds.token_expires_in_days or 0) <= 14


@pytest.mark.django_db
def test_masked_token_empty() -> None:
    ds = DataSource.objects.create(name="t0", base_url="https://x/", encrypted_token_ciphertext="")
    assert ds.masked_token == "—"


@pytest.mark.django_db
def test_masked_token_short() -> None:
    ds = DataSource.objects.create(name="t1", base_url="https://x/", encrypted_token_ciphertext="abcd")
    assert ds.masked_token == "••••"


@pytest.mark.django_db
def test_masked_token_long() -> None:
    ds = DataSource.objects.create(
        name="t2",
        base_url="https://x/",
        encrypted_token_ciphertext="glpat-abcdefgh",
    )
    assert ds.masked_token.endswith("gh")
    assert "glpat" not in ds.masked_token
