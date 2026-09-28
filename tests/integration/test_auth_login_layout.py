"""Layout / presence tests for AUTH-LOGIN (08–09, 13 fragments)."""

import pytest
from django.test import Client
from django.urls import reverse


@pytest.mark.django_db
def test_auth_login_08_login_page_shows_brand_mark_tagline_and_form_elements(db):
    client = Client()
    r = client.get(reverse("auth-login"))
    assert r.status_code == 200
    body = r.content.decode()
    assert 'data-testid="login-brand-mark"' in body
    assert "Human-AI Command Composite" in body
    assert 'data-testid="login-email"' in body
    assert 'data-testid="login-password"' in body
    assert 'data-testid="login-submit"' in body
    assert "csrfmiddlewaretoken" in body


@pytest.mark.django_db
def test_auth_login_09_password_input_has_type_password(db):
    client = Client()
    r = client.get(reverse("auth-login"))
    body = r.content.decode()
    assert 'data-testid="login-password"' in body
    assert 'type="password"' in body


@pytest.mark.django_db
def test_auth_login_08_forgot_password_disabled_with_admin_tooltip(db):
    client = Client()
    r = client.get(reverse("auth-login"))
    body = r.content.decode()
    assert 'data-testid="forgot-password"' in body
    assert "disabled" in body
    assert "Contact your admin" in body


@pytest.mark.django_db
def test_auth_login_13_email_and_password_have_associated_labels(db):
    client = Client()
    r = client.get(reverse("auth-login"))
    body = r.content.decode()
    assert 'for="login-email"' in body
    assert 'for="login-password"' in body
    assert ">Sign In<" in body or "Sign In" in body


@pytest.mark.django_db
def test_login_page_loads_screen_anchor_for_auth_login_1(db):
    client = Client()
    r = client.get(reverse("auth-login"))
    body = r.content.decode()
    assert 'data-testid="auth-login-loaded"' in body
    assert "AUTH-LOGIN-1" in body
    assert 'data-testid="realm-navbar"' not in body
    assert 'data-testid="app-sidebar"' not in body
