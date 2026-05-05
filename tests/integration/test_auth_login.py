"""Integration tests for AUTH-LOGIN-1."""

import pytest
from django.test import Client
from django.urls import reverse


@pytest.mark.django_db
def test_successful_login_redirects_to_projects_dashboard(commander_user):
    client = Client()
    r = client.post(
        reverse("auth-login"),
        {"email": "donland@example.com", "password": "s3cr3t"},
        follow=False,
    )
    assert r.status_code == 302
    assert r.headers["Location"] == "/projects/"


@pytest.mark.django_db
def test_wrong_password_returns_login_with_error(commander_user):
    client = Client()
    r = client.post(
        reverse("auth-login"),
        {"email": "donland@example.com", "password": "wrong-password"},
    )
    assert r.status_code == 200
    body = r.content.decode()
    assert "Invalid email or password" in body


@pytest.mark.django_db
def test_unknown_email_returns_login_with_error(db):
    client = Client()
    r = client.post(
        reverse("auth-login"),
        {"email": "nobody@example.com", "password": "anypassword"},
    )
    assert r.status_code == 200
    assert "Invalid email or password" in r.content.decode()


@pytest.mark.django_db
def test_logged_in_user_get_login_redirects_to_dashboard(commander_client):
    r = commander_client.get(reverse("auth-login"), follow=False)
    assert r.status_code == 302
    assert r.headers["Location"] == "/projects/"


@pytest.mark.django_db
def test_logout_clears_session(commander_client):
    r = commander_client.post(reverse("auth-logout"), follow=False)
    assert r.status_code in (302, 303)
    r2 = commander_client.get(reverse("projects-list"), follow=False)
    assert r2.status_code == 302
    assert reverse("auth-login") in (r2.headers.get("Location") or "")
