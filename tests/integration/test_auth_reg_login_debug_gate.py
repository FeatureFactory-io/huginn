"""Integration tests for AUTH-REG-LOGIN-01/02/03 — DEBUG-gated registration link.

These tests are intentionally RED today; they will turn GREEN after
``T-REG-01-impl`` ships the production view + template changes.

Scenarios are translated verbatim from
``docs/features/act-0-auth/registration.feature`` (lines 20–35):

* **AUTH-REG-LOGIN-01** — DEV (``DEBUG=True``) shows a "Create account" link
  on the login page with ``data-testid="login-register-link"``.
* **AUTH-REG-LOGIN-02** — Production (``DEBUG=False``) hides the link and
  surfaces the muted helper text
  ``"Need an account? Contact your admin."``
* **AUTH-REG-LOGIN-03** — A direct ``GET /accounts/register/`` with
  ``DEBUG=False`` 302-redirects to the login page and shows a dismissable
  banner containing
  ``"Registration is disabled on this Huginn install. Contact your admin to
  request an account."``

Per ``factory/tasks/T-REG-01.md``, the canonical testid is
``login-register-link`` (matching the feature file). The earlier plan draft
used a different testid name; ignore it.

No production code is written here — that is the responsibility of
``T-REG-01-impl``.
"""

import pytest
from django.test import Client, override_settings
from django.urls import reverse


@pytest.mark.django_db
@override_settings(DEBUG=True)
def test_auth_reg_login_01_dev_shows_create_account_link_on_login_page(db):
    client = Client()
    r = client.get(reverse("auth-login"))
    assert r.status_code == 200
    body = r.content.decode()
    assert 'data-testid="login-register-link"' in body


@pytest.mark.django_db
@override_settings(DEBUG=False)
def test_auth_reg_login_02_production_hides_link_and_shows_helper_text(db):
    client = Client()
    r = client.get(reverse("auth-login"))
    assert r.status_code == 200
    body = r.content.decode()
    assert 'data-testid="login-register-link"' not in body
    assert "Need an account? Contact your admin." in body


@pytest.mark.django_db
@override_settings(DEBUG=False)
def test_auth_reg_login_03_direct_register_url_redirects_to_login_with_banner(db):
    client = Client()

    r = client.get("/accounts/register/", follow=False)
    assert r.status_code == 302
    assert reverse("auth-login") in (r.headers.get("Location") or "")

    r = client.get("/accounts/register/", follow=True)
    assert r.status_code == 200
    body = r.content.decode()
    banner_copy = "Registration is disabled on this Huginn install. Contact your admin to request an account."
    assert banner_copy in body
