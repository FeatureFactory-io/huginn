# Blueprint — T-REG-01-impl: DEBUG gate on login + register-route guard

## Summary

Turn the 3 RED tests from T-REG-01 GREEN. Add a DEBUG-conditional "Create an account"
link to the login screen and a `RegisterView` skeleton that (a) redirects to login with
a flash banner when `DEBUG=False`, and (b) renders an empty form stub when `DEBUG=True`.
**`post()` is a `NotImplementedError` stub** — implementation lands in T-REG-02-impl.

## Context

- Plan §Task T-REG-01-impl
- System blueprint §Template contract — `ui/templates/ui/auth/login.html` and §`RegisterView`
- Source-of-truth feature scenarios: AUTH-REG-LOGIN-01 / 02 / 03

## Design

### 1. `ui/views/auth/login_view.py` — extend `_context()`

```python
def _context(self, request: HttpRequest) -> dict:
    return {"debug_mode": settings.DEBUG}
```

### 2. `ui/templates/ui/auth/login.html` — conditional + messages render

(a) **At the top of `.card-body`** (before existing `{% if login_error %}` block), render Django messages so the redirect banner from `RegisterView` shows up:

```html
{% if messages %}
  {% for message in messages %}
    <div class="alert alert-{{ message.tags|default:'warning' }} alert-dismissible fade show"
         role="alert" data-testid="login-flash-banner">
      {{ message }}
      <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    </div>
  {% endfor %}
{% endif %}
```

(b) **Replace the existing Forgot-password block** (currently a `<button class="disabled" disabled>`):

```html
<div class="d-flex justify-content-between align-items-center mt-3">
  {% if debug_mode %}
    <a href="{% url 'auth-register' %}" class="btn btn-link btn-sm px-0"
       data-testid="login-register-link">Create an account</a>
  {% else %}
    <span class="text-muted small" data-testid="login-signup-disabled">
      Need an account? Contact your admin.
    </span>
  {% endif %}
  <a href="#" class="btn btn-link btn-sm px-0" data-testid="forgot-password">Forgot password?</a>
</div>
```

The Forgot-password link loses its `disabled` attr and `<button>` wrapper (becomes plain `<a href="#">`); behavior is unchanged (still a no-op), but the conditional create-account block reads cleanly and the existing `test_auth_login_08_forgot_password_disabled_with_admin_tooltip` continues to pass because (i) the `login-submit` button still has `disabled`, and (ii) "Contact your admin" is now in the `login-signup-disabled` span. Verify by running the full suite.

### 3. `ui/views/auth/register_view.py` — NEW skeleton

```python
"""REGISTER screen — AUTH-REGISTER-1 (DEBUG-gated)."""

from django.conf import settings
from django.contrib import messages
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.cache import never_cache


@method_decorator(never_cache, name="dispatch")
class RegisterView(View):
    """Self-signup for DEBUG-only installs (sandbox / local dev)."""

    template_name = "ui/auth/register.html"

    def dispatch(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        if not settings.DEBUG:
            messages.warning(
                request,
                "Registration is disabled on this Huginn install. "
                "Contact your admin to request an account.",
            )
            return redirect(reverse("auth-login"))
        return super().dispatch(request, *args, **kwargs)

    def get(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        return render(request, self.template_name, {})

    def post(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        raise NotImplementedError  # implemented in T-REG-02-impl
```

### 4. `ui/templates/ui/auth/register.html` — NEW (minimal stub)

T-REG-02-impl will fully port the mockup. This task only needs enough for `GET` to render successfully when DEBUG=True (so test 03's `follow=True` doesn't trip on the GET):

```html
{% extends "base.html" %}
{% load static %}

{% block title %}Create account · Huginn{% endblock %}
{% block navbar %}{% endblock navbar %}

{% block content %}
{% include "ui/mockups/_screen_anchor.html" with screen_id="AUTH-REGISTER-1" screen_testid="auth-register-loaded" %}
<div class="row justify-content-center align-items-center" style="min-height:calc(100vh - 4rem)">
  <div class="col-md-10 col-lg-6 col-xl-5 col-xxl-4 text-center">
    <h2 class="hg-page-title">Create your account</h2>
    <p class="text-muted">Registration form will land in the next task.</p>
  </div>
</div>
{% endblock %}
```

T-REG-02-impl rewrites this file.

### 5. `ui/urls.py` — register the route

```python
from .views.auth.register_view import RegisterView
# ... existing imports ...

# In urlpatterns, alongside auth-login / auth-logout:
path("accounts/register/", RegisterView.as_view(), name="auth-register"),
```

## Files to touch

```
ui/views/auth/login_view.py             (modify — debug_mode in _context)
ui/templates/ui/auth/login.html         (modify — messages block + conditional)
ui/views/auth/register_view.py          (NEW)
ui/templates/ui/auth/register.html      (NEW — minimal stub)
ui/urls.py                              (modify — register URL)
```

## Interfaces / contracts

- URL name `auth-register` → `/accounts/register/` (T-REG-02 will reverse this).
- Template variable `debug_mode` available in `login.html` (set by `LoginScreenView._context()`).
- Flash banner text **must match verbatim** (AUTH-REG-LOGIN-03):
  `"Registration is disabled on this Huginn install. Contact your admin to request an account."`

## Risks

- `test_auth_login_08_forgot_password_disabled_with_admin_tooltip`
  ([`tests/integration/test_auth_login_layout.py`](../../tests/integration/test_auth_login_layout.py) line 32)
  asserts `"disabled" in body` and `"Contact your admin" in body`. Both still True after our
  changes (login-submit retains `disabled`; "Contact your admin" appears in `login-signup-disabled`
  span under DEBUG=False). **Run the full suite to confirm.** If it fails, narrow the test to
  the actual contract (e.g. `'data-testid="forgot-password"' in body`) — call it out in the
  Result block's `out_of_scope_changes:` note.
- Django messages middleware is already in `MIDDLEWARE` (default Django setup). Verify with
  `rg "messages" huginn/settings/base.py` if uncertain.

## Rollback / feature flags

Revert this single commit. The conditional is opt-in via `settings.DEBUG` — production
installs (DEBUG=False) see no behaviour change beyond an unenabled "Forgot password?" link.

## Smoke / verification

```bash
ruff check ui/ --fix
.venv/bin/python -m pytest tests/integration/test_auth_reg_login_debug_gate.py -v
# expect: 3 passed.

.venv/bin/python -m pytest tests/ -x
# expect: full suite green (no regressions).
```
