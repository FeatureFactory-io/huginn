"""Unit tests for accounts.models.User."""

import pytest
from django.contrib.auth import get_user_model
from django.db import IntegrityError


@pytest.mark.django_db
def test_user_str_returns_email():
    user_model = get_user_model()
    u = user_model.objects.create_user("ops@example.com", "x")
    assert str(u) == "ops@example.com"


@pytest.mark.django_db
def test_email_unique_constraint_enforced():
    user_model = get_user_model()
    user_model.objects.create_user("same@example.com", "p1")
    with pytest.raises(IntegrityError):
        user_model.objects.create_user("same@example.com", "p2")


@pytest.mark.django_db
def test_get_full_name_prefers_full_name():
    user_model = get_user_model()
    u = user_model.objects.create_user("u@example.com", "x", full_name="Donland")
    assert u.get_full_name() == "Donland"
    assert u.get_short_name() == "Donland"


@pytest.mark.django_db
def test_get_full_name_fallback_to_email():
    user_model = get_user_model()
    u = user_model.objects.create_user("only@example.com", "x")
    assert u.get_full_name() == "only@example.com"
