"""Integration tests for AUTH-REGISTER scenarios (01, 03, 04, 05, 08).

These are intentionally RED — T-REG-02-impl will turn them GREEN by wiring
``RegistrationService`` + ``RegisterView.post()`` and porting the mockup template.

Note: AUTH-REGISTER-08 asserts the LE in-sprint contract (302 → Tactical Plot for
duplicate-active-email, for enumeration protection) rather than the
``AUTH-AWAIT_VERIFICATION-1`` line in the .feature, which is out of sprint scope.
"""

import pytest
from django.contrib.auth import get_user_model
from django.test import Client, override_settings
from django.urls import reverse

User = get_user_model()


@pytest.mark.django_db
@override_settings(DEBUG=True)
def test_auth_register_01_happy_path_creates_active_user_and_logs_in():
    client = Client()
    r = client.post(
        reverse("auth-register"),
        {
            "name": "Commander Casey",
            "email": "fresh@example.com",
            "password": "Abcd-valid-987",
            "password_confirm": "Abcd-valid-987",
        },
        follow=False,
    )

    assert r.status_code == 302
    assert r.headers["Location"] == reverse("tactical-plot")

    user = User.objects.get(email="fresh@example.com")
    assert user.is_active is True
    assert "_auth_user_id" in client.session
    assert int(client.session["_auth_user_id"]) == user.pk


@pytest.mark.django_db
@override_settings(DEBUG=True)
def test_auth_register_03_password_mismatch_re_renders_with_inline_error():
    client = Client()
    r = client.post(
        reverse("auth-register"),
        {
            "name": "Commander Casey",
            "email": "fresh@example.com",
            "password": "Abcd-valid-987",
            "password_confirm": "different-password",
        },
    )

    assert r.status_code == 200
    body = r.content.decode()
    assert 'data-testid="register-password-confirm"' in body
    assert "do not match" in body.lower()
    assert not User.objects.filter(email="fresh@example.com").exists()


@pytest.mark.django_db
@override_settings(DEBUG=True)
def test_auth_register_04_weak_password_re_renders_with_validator_error():
    client = Client()
    r = client.post(
        reverse("auth-register"),
        {
            "name": "Bad",
            "email": "pw@example.com",
            "password": "12345",
            "password_confirm": "12345",
        },
    )

    assert r.status_code == 200
    body = r.content.decode()
    # Django ships MinimumLengthValidator / NumericPasswordValidator / CommonPasswordValidator;
    # "12345" may trip any combination depending on settings. Stay loose — assert SOMETHING
    # password-related is rendered, then accept any of the validator messages.
    assert "password" in body.lower()
    assert (
        "too short" in body.lower()
        or "at least 8" in body
        or "too common" in body.lower()
        or "entirely numeric" in body.lower()
    )
    assert not User.objects.filter(email="pw@example.com").exists()


@pytest.mark.django_db
@override_settings(DEBUG=True)
def test_auth_register_05_get_renders_sign_in_link():
    client = Client()
    r = client.get(reverse("auth-register"))

    assert r.status_code == 200
    body = r.content.decode()
    assert 'data-testid="register-sign-in-link"' in body
    # Use reverse() so a future URL rename doesn't silently make this lie.
    assert reverse("auth-login") in body


@pytest.mark.django_db
@override_settings(DEBUG=True)
def test_auth_register_08_duplicate_active_email_returns_same_redirect_without_creating_dup_or_changing_password():
    existing = User.objects.create_user(
        email="existing@example.com",
        password="Original-pw-12345",
        full_name="Existing User",
    )

    client = Client()
    r = client.post(
        reverse("auth-register"),
        {
            "name": "Intruder",
            "email": "existing@example.com",
            "password": "Different-Abcd-987",
            "password_confirm": "Different-Abcd-987",
        },
        follow=False,
    )

    # Enumeration protection: identical 302 → Tactical Plot as a fresh successful signup.
    assert r.status_code == 302
    assert r.headers["Location"] == reverse("tactical-plot")

    assert User.objects.filter(email__iexact="existing@example.com").count() == 1
    existing.refresh_from_db()
    assert existing.check_password("Original-pw-12345") is True
    assert "_auth_user_id" not in client.session
