"""Unit tests for accounts.managers.UserManager."""

import pytest
from django.contrib.auth import get_user_model


@pytest.mark.django_db
def test_create_user_persists_normalized_email():
    user_model = get_user_model()
    u = user_model.objects.create_user("  Commander@Example.COM  ", "pw")
    assert u.email == "commander@example.com"


@pytest.mark.django_db
def test_create_user_hashes_password():
    user_model = get_user_model()
    u = user_model.objects.create_user("a@b.com", "secret")
    assert u.password
    assert u.password.startswith("pbkdf2_")
    assert u.check_password("secret")


@pytest.mark.django_db
def test_create_user_rejects_blank_email():
    user_model = get_user_model()
    with pytest.raises(ValueError, match="Email"):
        user_model.objects.create_user("", "pw")
    with pytest.raises(ValueError, match="Email"):
        user_model.objects.create_user("   ", "pw")


@pytest.mark.django_db
def test_create_superuser_sets_staff_and_superuser_flags():
    user_model = get_user_model()
    u = user_model.objects.create_superuser("admin@example.com", "pw")
    assert u.is_staff is True
    assert u.is_superuser is True


@pytest.mark.django_db
def test_create_superuser_rejects_non_staff():
    user_model = get_user_model()
    with pytest.raises(ValueError, match="is_staff"):
        user_model.objects.create_superuser("a@b.com", "pw", is_staff=False)


@pytest.mark.django_db
def test_create_superuser_rejects_non_superuser():
    user_model = get_user_model()
    with pytest.raises(ValueError, match="is_superuser"):
        user_model.objects.create_superuser("a@b.com", "pw", is_superuser=False)
