"""Form behaviour structure tests for AUTH-LOGIN (05–07, 12)."""

import re

import pytest
from django.test import Client
from django.urls import reverse


@pytest.mark.django_db
def test_auth_login_05_submit_button_initially_disabled(db):
    client = Client()
    r = client.get(reverse("auth-login"))
    body = r.content.decode()
    assert 'data-testid="login-submit"' in body
    assert re.search(r"<button[^>]*data-testid=\"login-submit\"[^>]*disabled", body, re.I | re.DOTALL)


@pytest.mark.django_db
def test_auth_login_06_email_input_has_required_attribute(db):
    client = Client()
    r = client.get(reverse("auth-login"))
    body = r.content.decode()
    assert 'data-testid="login-email"' in body
    assert "required" in body


@pytest.mark.django_db
def test_auth_login_07_password_input_has_required_attribute(db):
    client = Client()
    r = client.get(reverse("auth-login"))
    body = r.content.decode()
    assert 'data-testid="login-password"' in body
    assert 'type="password"' in body and "required" in body


@pytest.mark.django_db
def test_login_form_includes_client_script(db):
    client = Client()
    r = client.get(reverse("auth-login"))
    body = r.content.decode()
    assert "login_form.js" in body


@pytest.mark.django_db
def test_auth_login_12_focus_order_email_password_submit_in_dom_order(db):
    client = Client()
    r = client.get(reverse("auth-login"))
    body = r.content.decode()
    pos_email = body.find('data-testid="login-email"')
    pos_password = body.find('data-testid="login-password"')
    pos_submit = body.find('data-testid="login-submit"')
    assert 0 < pos_email < pos_password < pos_submit
