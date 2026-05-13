# ACT0-REG-01 — Registration (DEBUG-only, no email verification)

**Milestone:** Registration (GitLab IID 7427525)
**Feature file:** `docs/features/act-0-auth/registration.feature`
**Mockups:** `ui/templates/ui/mockups/auth/login.html`, `ui/templates/ui/mockups/auth/register.html`

---

## Sprint Goal

Implement the minimum viable self-signup path for developer / sandbox installs:

1. When `settings.DEBUG = True`, the login screen shows a **"Create an account"** link.
2. The register form accepts name + email + password + confirm-password.
3. On valid submit: `User` row created with `is_active = True`, user is immediately signed in,
   redirected to the Tactical Plot.
4. When `settings.DEBUG = False`, the `/accounts/register/` route redirects to login with a banner.

No email verification, no admin approval queue, no SES dependency — those ship in a later milestone.

---

## Scenarios in scope

| Scenario ID | Description |
|-------------|-------------|
| AUTH-REG-LOGIN-01 | DEBUG shows Create account link on login |
| AUTH-REG-LOGIN-02 | Production (`DEBUG=False`) hides Create account link |
| AUTH-REG-LOGIN-03 | Direct `/accounts/register/` redirects to login with banner when DEBUG disabled |
| AUTH-REGISTER-01 | Successful submit → User created `is_active=True` → auto-login → Tactical Plot |
| AUTH-REGISTER-02 | Submit button disabled while any required field is empty (client-side) |
| AUTH-REGISTER-03 | Password ≠ confirm shows mismatch helper on confirm field |
| AUTH-REGISTER-04 | Server rejects weak password with inline validation error |
| AUTH-REGISTER-05 | "Sign in" link on register form navigates back to login |
| AUTH-REGISTER-08 | Already-active email returns generic success (enumeration protection) |
| ACCESS-REG-01 | Tab order: name → email → password → confirm → submit |

---

## Context Map

| File | Lines | Note |
|------|-------|------|
| `ui/views/auth/login_view.py` | 1–66 | Follow this exact class-based view pattern; pass `debug_mode` in `_context()` |
| `ui/services/authentication_service.py` | 1–46 | Follow this service pattern for `RegistrationService`; thin service, call ORM directly |
| `ui/templates/ui/auth/login.html` | 1–57 | Production template to extend with conditional register link |
| `ui/templates/ui/mockups/auth/register.html` | 1–65 | Mockup to port to production template (same structure, add `method="post"`, `{% csrf_token %}`) |
| `tests/integration/test_auth_login_credentials.py` | 1–86 | Follow this exact test pattern for new integration tests |

---

## Do Not Do

- Do NOT add an `account_status` field or enum to `accounts.User` — `is_active=True` is the entire approval state for this sprint.
- Do NOT send any email in this sprint — no SES, no `django.core.mail`, no verification token.
- Do NOT create an `EmailVerificationToken` model or any token model.
- Do NOT add async or Celery tasks.
- Do NOT add a new Django app — registration lives in `ui/views/auth/` and `ui/services/`.
- Do NOT add a manager/repository layer — services call ORM directly.
- Do NOT use `UserCreationForm` from `django.contrib.auth.forms` — write a plain Django `Form` following the `EmailUserCreationForm` pattern in `accounts/admin.py`.
- Do NOT implement the forgot-password flow — out of scope for this milestone.

---

## SAO.md Sections That Apply

- **§Authentication** (line ~548): session-based, username + password, `django.contrib.auth.login()`.
- **§accounts/ app** (line ~30, ~102): custom `AUTH_USER_MODEL`; `UserManager._create_user` is the canonical way to create users.
- **§Services Layer**: shared by MCP and Web UI; no MCP-specific logic in services.

---

## Implementation Plan

### Branch

```bash
git checkout -b feature/act0-registration-debug
```

---

### Task T-REG-01: Step definitions for AUTH-REG-LOGIN-* scenarios

**Role:** step-def-writer
**File:** `tests/integration/test_auth_reg_login_debug_gate.py`
**Depends on:** nothing

Write RED pytest tests for AUTH-REG-LOGIN-01, -02, -03 using `pytest.mark.django_db` and `django.test.Client`. Tests should fail (`ImportError` or `NoReverseMatch`) until the implementation task lands.

Steps for each scenario:

**AUTH-REG-LOGIN-01** (DEBUG → link visible):
```python
# Override settings.DEBUG = True
# GET /accounts/login/
# Assert 'data-testid="login-create-account"' in response body
```

**AUTH-REG-LOGIN-02** (DEBUG=False → link absent):
```python
# Override settings.DEBUG = False
# GET /accounts/login/
# Assert 'data-testid="login-create-account"' NOT in response body
# Assert "Contact your admin" in response body
```

**AUTH-REG-LOGIN-03** (DEBUG=False → register route redirects):
```python
# Override settings.DEBUG = False
# GET /accounts/register/
# Assert 302 → /accounts/login/
# Follow redirect, assert banner text present
```

**Acceptance:** `pytest tests/integration/test_auth_reg_login_debug_gate.py -x` exits non-zero (RED).

---

### Task T-REG-01-impl: DEBUG gate on login screen + register route guard

**Role:** feature-builder
**Depends on:** T-REG-01 (step definitions must be RED before starting)

#### 1. `ui/views/auth/login_view.py`
- In `_context()`, add `"debug_mode": settings.DEBUG`.

#### 2. `ui/templates/ui/auth/login.html`
Port the conditional block from the mockup:
```html
{% if debug_mode %}
  <a href="{% url 'auth-register' %}" class="btn btn-link btn-sm px-0"
     data-testid="login-create-account">Create an account</a>
{% else %}
  <span class="text-muted small" data-testid="login-signup-disabled">
    Need an account? Contact your admin.
  </span>
{% endif %}
```
Also wire the **Forgot password?** button (currently `disabled`) to `{% url 'auth-forgot-password' %}` as a proper link — stub view is acceptable for now (404 is fine; link must be present and enabled).

#### 3. `ui/views/auth/register_view.py` — skeleton + DEBUG guard only
```python
class RegisterView(View):
    template_name = "ui/auth/register.html"

    def dispatch(self, request, *args, **kwargs):
        if not settings.DEBUG:
            messages.warning(request,
                "Registration is disabled on this Huginn install. "
                "Contact your admin to request an account.")
            return redirect(reverse("auth-login"))
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name, {})

    def post(self, request, *args, **kwargs):
        raise NotImplementedError  # implemented in T-REG-02-impl
```

#### 4. `ui/urls.py`
```python
path("accounts/register/", RegisterView.as_view(), name="auth-register"),
```

#### 5. Tests
Make `tests/integration/test_auth_reg_login_debug_gate.py` **GREEN**.

**Commit:** `feat(auth): debug-gate register link on login screen`

---

### Task T-REG-02: Step definitions for AUTH-REGISTER-* scenarios

**Role:** step-def-writer
**File:** `tests/integration/test_auth_register.py`
**Depends on:** T-REG-01-impl (URL `auth-register` must resolve)

Write RED pytest tests for AUTH-REGISTER-01, -03, -04, -05, -08 (ACCESS-REG-01 and AUTH-REGISTER-02 are client-side only; cover them with layout/template assertions).

**AUTH-REGISTER-01** (happy path → active user + session + redirect):
```python
# settings.DEBUG = True; no prior user
# POST /accounts/register/ {name, email, password, password_confirm}
# Assert 302 → /plot/ (tactical plot)
# Assert User.objects.get(email=...).is_active is True
# Assert "_auth_user_id" in session
```

**AUTH-REGISTER-03** (password mismatch → stays on form with error):
```python
# POST with mismatched passwords
# Assert 200, template re-rendered
# Assert 'register-password-confirm' in body
# Assert mismatch error text in body
```

**AUTH-REGISTER-04** (weak password → server error):
```python
# POST with password "12345" (too short)
# Assert 200, template re-rendered
# Assert password validation error in body
```

**AUTH-REGISTER-05** (sign-in link present):
```python
# GET /accounts/register/ (DEBUG=True)
# Assert 'data-testid="register-sign-in-link"' in body
# Assert href contains /accounts/login/ or name 'auth-login'
```

**AUTH-REGISTER-08** (duplicate active email → same 302, no new user):
```python
# Pre-create active user with same email
# POST /accounts/register/ with that email
# Assert 302 → /plot/
# Assert User.objects.filter(email=...).count() == 1  (no duplicate)
```

**Acceptance:** `pytest tests/integration/test_auth_register.py -x` exits non-zero (RED).

---

### Task T-REG-02-impl: Registration service + view + template

**Role:** feature-builder
**Depends on:** T-REG-02 (step defs RED), T-REG-01-impl (route + guard in place)

#### 1. `ui/services/registration_service.py` (new file)

```python
class RegistrationService:
    def register(self, email: str, full_name: str, password: str, request) -> tuple[User | None, str | None]:
        """
        Create an active user and bind their session.

        Returns (user, None) on success.
        Returns (None, error_message) on validation failure.
        Returns (None, None) on duplicate email (enumeration protection —
            caller must show the same success UI regardless).
        """
```

Logic:
- Normalize email (lowercase strip).
- Run Django's built-in password validators (`validate_password(password, user=None)`).
  On failure, return `(None, first_validator_message)`.
- Check `User.objects.filter(email__iexact=email).exists()`.
  If True: **do nothing, return `(None, None)`** (enumeration protection — no error, no new row).
- `User.objects.create_user(email=email, password=password, full_name=full_name)` — `is_active=True` by default.
- Call `login(request, user)` to bind the session.
- Return `(user, None)`.

#### 2. `ui/views/auth/register_view.py` — complete `post()` method

```python
def post(self, request, *args, **kwargs):
    name = request.POST.get("name", "").strip()
    email = request.POST.get("email", "").strip()
    password = request.POST.get("password", "")
    confirm = request.POST.get("password_confirm", "")

    ctx = {"field_name": name, "field_email": email}

    if password != confirm:
        ctx["password_error"] = "Passwords do not match."
        return render(request, self.template_name, ctx)

    user, error = RegistrationService().register(email, name, password, request)
    if error:
        ctx["password_error"] = error
        return render(request, self.template_name, ctx)

    # success OR silent duplicate — always redirect to plot
    return redirect(reverse("tactical-plot"))
```

#### 3. `ui/templates/ui/auth/register.html` (new file)

Port `ui/templates/ui/mockups/auth/register.html` to production:
- Replace `{% extends "base_mockups.html" %}` → `{% extends "base.html" %}`
- Add `method="post"` and `{% csrf_token %}` to the form
- Wire field `name` attributes: `name="name"`, `name="email"`, `name="password"`, `name="password_confirm"`
- Keep all `data-testid` attributes identical to the mockup
- Render `{{ password_error }}` as `alert-danger` above the form when present
- Keep "Sign in" link (`data-testid="register-sign-in-link"`) → `{% url 'auth-login' %}`
- Screen anchor: `AUTH-REGISTER-1` / `auth-register-loaded`

#### 4. Tests

Make `tests/integration/test_auth_register.py` **GREEN**.

**Commit:** `feat(auth): registration view and service — DEBUG-only auto-approved signup`

---

## Acceptance criteria (sprint done when ALL pass)

```bash
pytest tests/integration/test_auth_reg_login_debug_gate.py tests/integration/test_auth_register.py -v
```
exits 0 with no failures.

```bash
pytest tests/ -x
```
exits 0 — no regressions.
