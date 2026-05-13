# Blueprint — T-REG-02-impl: Registration service + view post() + register template

## Summary

Turn the 5 RED tests from T-REG-02 GREEN. Implement `RegistrationService`, fill in
`RegisterView.post()`, and port the register form template from the mockup. After this
task, the sprint's entire happy path works: signup → active user → auto-login → tactical plot.

## Context

- Plan §Task T-REG-02-impl
- System blueprint §Key interfaces, §Template contract — `ui/templates/ui/auth/register.html`
- Mockup source: [`ui/templates/ui/mockups/auth/register.html`](../../ui/templates/ui/mockups/auth/register.html)
- Service pattern: [`ui/services/authentication_service.py`](../../ui/services/authentication_service.py)
- User model: [`accounts/models.py`](../../accounts/models.py), [`accounts/managers.py`](../../accounts/managers.py)

## Design

### 1. `ui/services/registration_service.py` — NEW

```python
"""Register and auto-login a new account (DEBUG-only sprint)."""

from __future__ import annotations

import logging
from typing import Any

from django.contrib.auth import get_user_model, login
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError

logger = logging.getLogger("huginn.registration")

User = get_user_model()


class RegistrationService:
    """Create a new active account and bind the session."""

    def register(
        self, email: str, full_name: str, password: str, request
    ) -> tuple[Any, str | None]:
        """Create user and log in on success.

        Returns ``(user, None)``       on successful create + login.
        Returns ``(None, None)``       on duplicate email — enumeration protection
                                       (caller must redirect the same as success).
        Returns ``(None, error_msg)``  on password-validator failure or blank input.
        """
        email = (email or "").strip().lower()
        full_name = (full_name or "").strip()

        if not email or not password:
            return None, "Please complete all required fields."

        try:
            validate_password(password, user=None)
        except ValidationError as exc:
            # Surface the first validator message; Django bundles them per validator.
            return None, exc.messages[0]

        if User.objects.filter(email__iexact=email).exists():
            logger.info('"event":"register_duplicate_silent"')
            return None, None

        user = User.objects.create_user(
            email=email, password=password, full_name=full_name
        )
        login(request, user)
        logger.info('"event":"register_success","user_id":%s', user.pk)
        return user, None
```

Notes:
- `User.objects.create_user(...)` uses the manager which calls `set_password(password)`
  internally; `is_active=True` is the model default.
- Never log the password or full email; log only `user_id` after creation.
- The duplicate branch deliberately does **not** call `login()` — an attacker who
  guesses an existing email must not be signed in as the legitimate owner.

### 2. `ui/views/auth/register_view.py` — implement `post()`

Replace the `NotImplementedError` body with:

```python
def post(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
    name = request.POST.get("name", "").strip()
    email = request.POST.get("email", "").strip()
    password = request.POST.get("password", "")
    confirm = request.POST.get("password_confirm", "")

    # Repopulate non-secret fields on validation failure.
    ctx: dict = {"field_name": name, "field_email": email}

    if password != confirm:
        ctx["password_error"] = "Passwords do not match."
        return render(request, self.template_name, ctx)

    _user, error = RegistrationService().register(email, name, password, request)
    if error:
        ctx["password_error"] = error
        return render(request, self.template_name, ctx)

    # Success OR silent-duplicate — both redirect identically (enumeration protection).
    return redirect(reverse("tactical-plot"))
```

Add the import at top of `register_view.py`:
```python
from ui.services.registration_service import RegistrationService
```

### 3. `ui/templates/ui/auth/register.html` — full port from mockup

Rewrite the stub (created in T-REG-01-impl) with the production version. Take the
mockup at `ui/templates/ui/mockups/auth/register.html` as the structural source of
truth — **preserve every `data-testid` from it verbatim** — and apply these production
adaptations:

| Change | From mockup | Production |
|---|---|---|
| Base | `{% extends "base_mockups.html" %}` | `{% extends "base.html" %}` |
| Form | `<form … data-testid="register-form">` (no `method`, no CSRF) | add `method="post"` and `{% csrf_token %}` as first child |
| Field names | (no `name=` attrs) | `name="name"`, `name="email"`, `name="password"`, `name="password_confirm"` |
| Value repopulation | n/a | `value="{{ field_name|default:'' }}"` on name, `value="{{ field_email|default:'' }}"` on email. **No `value=` on password fields.** |
| Inline error | n/a | Above the form: `{% if password_error %}<div class="alert alert-danger" role="alert" data-testid="register-error">{{ password_error }}</div>{% endif %}` |
| Sign-in link href | `{% url 'mockup-auth-login' %}` | `{% url 'auth-login' %}` |
| "Browse mockups" link | present (mockup-only) | **remove** |
| Screen anchor | `screen_id="AUTH-REGISTER-1" screen_testid="auth-register-loaded"` | keep verbatim |

Required `data-testid`s in production template (verify after port):
- `register-brand-mark`, `register-form`, `register-name`, `register-email`,
  `register-password`, `register-password-confirm`, `register-submit`,
  `register-sign-in-link`
- And the screen anchor's `auth-register-loaded`.

## Files to touch

```
ui/services/registration_service.py    (NEW)
ui/views/auth/register_view.py         (modify — implement post(), add import)
ui/templates/ui/auth/register.html     (REWRITE — port from mockup, drop the T-REG-01-impl stub)
```

## Interfaces / contracts

`RegistrationService.register(email, full_name, password, request) -> (user|None, error|None)`:

| Return | Meaning | Caller action |
|---|---|---|
| `(user, None)` | New user created + session bound | redirect to tactical-plot |
| `(None, None)` | Duplicate email — silent | redirect to tactical-plot (SAME) |
| `(None, "msg")` | Validator failure / blank input | re-render form with `password_error="msg"` |

Email normalization: `(email or "").strip().lower()` — must match `User.objects.filter(email__iexact=…)` in test 08.

## Risks

- **R-1 (CLEARED):** `MinimumLengthValidator` is already in `AUTH_PASSWORD_VALIDATORS`
  (`huginn/settings/base.py` line 96). Test 04 (`"12345"`) will trip at least one validator.
- **Logger leakage:** never log the password or full email. Only `user_id` after success.
- **`ValidationError.messages[0]`:** if Django raises with an empty `.messages` list (it doesn't,
  but defensive note), this would IndexError. The validators in use all produce at least one
  message — confirmed by manual smoke.
- **Stub template:** T-REG-01-impl created a placeholder `register.html`. This task REWRITES
  it; don't append.
- **MR target branch:** target `main` directly (the previous task's MR will already be merged
  to main before this task is claimed — claim.sh gates on `done/T-REG-02.md`).

## Rollback / feature flags

Single-commit revert. `RegisterView.dispatch()` still 302s under `DEBUG=False`, so production
installs are untouched even if the rest of the work regresses.

## Smoke / verification

```bash
ruff check ui/services/registration_service.py ui/views/auth/register_view.py

.venv/bin/python -m pytest tests/integration/test_auth_register.py -v
# expect: 5 passed.

.venv/bin/python -m pytest tests/integration/test_auth_reg_login_debug_gate.py tests/integration/test_auth_register.py -v
# expect: 8 passed (3 from T-REG-01 + 5 here).

.venv/bin/python -m pytest tests/ -x
# expect: full suite green (no regressions).
```
