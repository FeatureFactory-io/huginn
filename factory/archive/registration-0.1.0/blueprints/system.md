# System Blueprint — Huginn / Registration sprint

> **Canonical source:** `docs/architecture/SAO.md` (esp. §Authentication, §accounts/ app, §Services Layer).
> **Sprint plan:** `docs/plans/ACT0-REG-01_registration_debug_only.md`.
> **Feature file:** `docs/features/act-0-auth/registration.feature`.
> This file is a worker-readable digest. When in doubt, SAO.md and the plan win.

---

## Sprint scope (in / out)

| In scope (this sprint) | Out of scope (explicitly NOT this sprint) |
|---|---|
| AUTH-REG-LOGIN-01/02/03 (DEBUG gate on login + register guard) | AUTH-REG-LOGIN-04/05/06/07 (states `pending_email_verification`, `pending_admin_approval`, `rejected`) |
| AUTH-REGISTER-01/02/03/04/05/08 (form, mismatch, weak pw, sign-in link, enumeration protection) | AUTH-REGISTER-06/07 (verification re-send, transient backend) |
| ACCESS-REG-01 (keyboard tab order — assert by template) | AUTH-AWAIT_VERIFICATION-*, AUTH-VERIFY_EMAIL-*, AUTH-AWAIT_APPROVAL-* |
| | ADMIN-APPROVE-01, ADMIN-REJECT-01 |
| | Any email sending (no `django.core.mail`, no SES) |
| | Any new model or field on `accounts.User` |
| | Forgot-password flow |

`is_active=True` (Django default) **is** the entire approval state for this sprint. Other account states ship in a later milestone.

---

## Repository layout (relevant apps only)

```
huginn/
├── accounts/                          # custom AUTH_USER_MODEL
│   ├── models.py                      # User: AbstractBaseUser+PermissionsMixin, USERNAME_FIELD='email'
│   ├── managers.py                    # UserManager.create_user(email, password, **extra) — is_active=True default
│   ├── admin.py                       # EmailUserCreationForm pattern reference (do NOT subclass this)
│   └── migrations/                    # NO new migration this sprint
├── ui/
│   ├── views/auth/
│   │   ├── login_view.py              # MODIFY: add debug_mode=settings.DEBUG to _context()
│   │   ├── register_view.py           # NEW (T-REG-01-impl: skeleton + DEBUG guard; T-REG-02-impl: full POST)
│   │   └── logout_view.py             # untouched
│   ├── services/
│   │   ├── authentication_service.py  # PATTERN to follow for RegistrationService (thin, ORM-direct)
│   │   └── registration_service.py    # NEW (T-REG-02-impl)
│   ├── templates/ui/auth/
│   │   ├── login.html                 # MODIFY: conditional create-account link
│   │   └── register.html              # NEW: stub in T-REG-01-impl, full port in T-REG-02-impl
│   └── urls.py                        # MODIFY: add path('accounts/register/', name='auth-register')
├── ui/templates/ui/mockups/auth/
│   └── register.html                  # SOURCE OF TRUTH for production register.html layout & data-testids
└── tests/integration/
    ├── conftest.py                    # commander_user / commander_client fixtures
    ├── test_auth_login_credentials.py # PATTERN to follow for new tests
    ├── test_auth_reg_login_debug_gate.py  # NEW (T-REG-01)
    └── test_auth_register.py          # NEW (T-REG-02)
```

---

## Key interfaces (normative — do not deviate)

### `RegistrationService` (`ui/services/registration_service.py`) — T-REG-02-impl

```python
class RegistrationService:
    def register(
        self, email: str, full_name: str, password: str, request
    ) -> tuple[object | None, str | None]:
        """
        Returns (user, None)        on successful create + login.
        Returns (None, error_msg)   on password-validator failure.
        Returns (None, None)        on duplicate email — enumeration protection,
                                    caller must show the SAME success UI / redirect.
        """
```

Implementation rules:
- Normalize email: `(email or "").strip().lower()`.
- `validate_password(password)` from `django.contrib.auth.password_validation` — return `(None, exc.messages[0])` on failure.
- `User.objects.filter(email__iexact=email).exists()` → if True, return `(None, None)` silently (no log, no row).
- `User.objects.create_user(email=..., password=..., full_name=...)` — `is_active=True` by default.
- `login(request, user)` to bind session.

### `RegisterView` (`ui/views/auth/register_view.py`)

```python
@method_decorator(never_cache, name="dispatch")
class RegisterView(View):
    template_name = "ui/auth/register.html"

    def dispatch(self, request, *args, **kwargs):
        if not settings.DEBUG:
            messages.warning(request, "Registration is disabled on this Huginn install. "
                                      "Contact your admin to request an account.")
            return redirect(reverse("auth-login"))
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name, {})

    def post(self, request, *args, **kwargs):
        # T-REG-01-impl: raise NotImplementedError
        # T-REG-02-impl: full body — see blueprint T-REG-02-impl
        ...
```

### URL

```python
# ui/urls.py
from .views.auth.register_view import RegisterView
path("accounts/register/", RegisterView.as_view(), name="auth-register"),
```

---

## Template contract — `ui/templates/ui/auth/register.html` (T-REG-02-impl)

Port the mockup at `ui/templates/ui/mockups/auth/register.html` to production:

1. `{% extends "base.html" %}` (not `base_mockups.html`).
2. `<form method="post" ...>` + `{% csrf_token %}`.
3. Input `name` attributes: `name="name"`, `name="email"`, `name="password"`, `name="password_confirm"`.
4. **Keep every `data-testid` from the mockup verbatim** — these are the scenario hooks.
5. Repopulate `value="{{ field_name|default:'' }}"` on name + email. **Never repopulate passwords.**
6. Above the form, render `password_error` (or other inline errors) as `alert alert-danger` with `data-testid="register-error"`.
7. "Sign in" link points to `{% url 'auth-login' %}` and keeps `data-testid="register-sign-in-link"`.
8. Screen anchor at top: `{% include "ui/mockups/_screen_anchor.html" with screen_id="AUTH-REGISTER-1" screen_testid="auth-register-loaded" %}`.

---

## Template contract — `ui/templates/ui/auth/login.html` (T-REG-01-impl)

Inside `.card-body` below the form, insert (replace the existing Forgot password block):

```html
<div class="d-flex justify-content-between align-items-center mt-3">
  {% if debug_mode %}
    <a href="{% url 'auth-register' %}" class="btn btn-link btn-sm px-0"
       data-testid="login-create-account">Create an account</a>
  {% else %}
    <span class="text-muted small" data-testid="login-signup-disabled">
      Need an account? Contact your admin.
    </span>
  {% endif %}
  <a href="#" class="btn btn-link btn-sm px-0" data-testid="forgot-password">Forgot password?</a>
</div>
```

Forgot password stays `href="#"` (out of scope) but loses the `disabled` attribute so it's still rendered & discoverable.

`LoginScreenView._context()` must include `"debug_mode": settings.DEBUG`.

---

## Test conventions (apply in every task)

- **Framework:** `pytest` + `pytest-django` (no `pytest-bdd`; tests are imperative integration tests against `django.test.Client`).
- **DEBUG toggle:** `@override_settings(DEBUG=True)` or `@override_settings(DEBUG=False)` per test. Do not rely on settings file default.
- **DB:** `@pytest.mark.django_db` (or seeded via existing fixtures).
- **User creation:** `User.objects.create_user(email=..., password=..., full_name=...)` — never bypass the manager.
- **Session check:** `assert "_auth_user_id" in client.session` to prove auto-login.
- **Redirect target:** `reverse("tactical-plot")` for the post-register destination.
- **RED → GREEN protocol:**
  - step-def-writer task: tests must collect and FAIL (or `NoReverseMatch`-skip) — `expected_exit_code: 1`.
  - feature-builder task: tests must PASS plus `pytest tests/ -x` no regression — `expected_exit_code: 0`.

---

## Existing code workers must read before touching

| File | Lines | Why |
|---|---|---|
| `ui/views/auth/login_view.py` | 1–66 | Class-based view pattern; where `debug_mode` lands |
| `ui/services/authentication_service.py` | 1–46 | Thin-service pattern — `RegistrationService` mirrors this exactly |
| `ui/templates/ui/auth/login.html` | 1–57 | Production login template; where to splice the conditional |
| `ui/templates/ui/mockups/auth/register.html` | 1–65 | Source-of-truth for register form layout + every `data-testid` |
| `tests/integration/test_auth_login_credentials.py` | 1–86 | Integration-test pattern (Client + reverse + override_settings) |
| `tests/integration/conftest.py` | 1–20 | Fixture pattern (`commander_user`, `commander_client`) |
| `accounts/models.py` | 1–44 | `User` model — is_active default True; no fields to add |
| `accounts/managers.py` | 1–46 | `UserManager.create_user` — canonical user creation path |
| `accounts/admin.py` | 17–40 | `EmailUserCreationForm` is **reference only** — do NOT subclass it in `RegistrationService` |
| `ui/urls.py` | 44–84 | Where to register the new path; URL name `auth-register` |
| `docs/plans/ACT0-REG-01_registration_debug_only.md` | full | Sprint plan — the contract |
| `docs/features/act-0-auth/registration.feature` | full | Scenarios — source of truth for acceptance |

---

## Hard prohibitions (apply across ALL tasks)

- Do NOT send any email, import `django.core.mail`, or stub SES.
- Do NOT create any new model, migration, or field. The `accounts.User` schema is frozen for this sprint.
- Do NOT add `account_status`, `is_approved`, `EmailVerificationToken`, or any token model.
- Do NOT add a new Django app.
- Do NOT use `django.contrib.auth.forms.UserCreationForm`.
- Do NOT add a repository/manager layer above ORM — service calls ORM directly.
- Do NOT add async or Celery tasks.
- Do NOT implement Forgot Password.
- Do NOT show the Create-account link when `DEBUG = False`.
- Do NOT distinguish duplicate-email failures from successful submits at the UI level (enumeration protection — both return the same redirect).
