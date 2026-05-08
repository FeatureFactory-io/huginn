"""Integration tests for AUTH-LOGIN credential flows (01–04, 10–11)."""

from unittest.mock import patch

import pytest
from django.test import Client
from django.urls import reverse


@pytest.mark.django_db
def test_auth_login_01_successful_login_redirects_to_tactical_plot(commander_user):
    client = Client()
    r = client.post(
        reverse("auth-login"),
        {"email": "donland@example.com", "password": "s3cr3t"},
        follow=False,
    )
    assert r.status_code == 302
    assert r.headers["Location"] == reverse("tactical-plot")


@pytest.mark.django_db
def test_auth_login_02_wrong_password_returns_login_with_error_and_clears_password_field(commander_user):
    client = Client()
    r = client.post(
        reverse("auth-login"),
        {"email": "donland@example.com", "password": "wrong-password"},
    )
    assert r.status_code == 200
    body = r.content.decode()
    assert "Invalid email or password" in body
    assert 'data-testid="login-password"' in body
    assert 'data-testid="login-password" value=' not in body.replace(" ", "")


@pytest.mark.django_db
def test_auth_login_03_unknown_email_returns_login_with_error(db):
    client = Client()
    r = client.post(
        reverse("auth-login"),
        {"email": "nobody@example.com", "password": "anypassword"},
    )
    assert r.status_code == 200
    assert "Invalid email or password" in r.content.decode()


@pytest.mark.django_db
@patch("ui.services.authentication_service.authenticate")
def test_auth_login_04_database_unreachable_shows_connectivity_message(mock_authenticate, commander_user):
    from django.db import OperationalError

    mock_authenticate.side_effect = OperationalError("simulated")
    client = Client()
    r = client.post(
        reverse("auth-login"),
        {"email": "donland@example.com", "password": "s3cr3t"},
    )
    assert r.status_code == 200
    body = r.content.decode()
    assert "Unable to reach Huginn. Check your connection." in body
    assert 'data-testid="login-connectivity-error"' in body


@pytest.mark.django_db
def test_auth_login_10_logged_in_user_get_login_redirects_to_tactical_plot(commander_client):
    r = commander_client.get(reverse("auth-login"), follow=False)
    assert r.status_code == 302
    assert r.headers["Location"] == reverse("tactical-plot")


@pytest.mark.django_db
def test_auth_login_11_logout_post_clears_session_and_redirects_to_home(commander_client):
    r = commander_client.post(reverse("auth-logout"), follow=False)
    assert r.status_code in (302, 303)
    assert r.headers.get("Location") == reverse("home")
    r2 = commander_client.get(reverse("projects-list"), follow=False)
    assert r2.status_code == 302
    assert reverse("auth-login") in (r2.headers.get("Location") or "")


@pytest.mark.django_db
def test_logout_get_returns_405():
    client = Client()
    r = client.get(reverse("auth-logout"))
    assert r.status_code == 405
