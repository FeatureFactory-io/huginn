# F01 AUTH-LOGIN-1 — Full implementation (Act-0 Auth)

**Status:** Implemented on branch `main` (see git history). Supersedes [F01_auth_login_IMPLEMENTATION_PLAN.md](F01_auth_login_IMPLEMENTATION_PLAN.md) skeleton.

## Scenario → test mapping (AUTH-LOGIN-01 … 13)

| Scenario | Test module | Notes |
|----------|----------------|-------|
| AUTH-LOGIN-01 | `tests/integration/test_auth_login_credentials.py` | POST redirect `/projects/` |
| AUTH-LOGIN-02 | `tests/integration/test_auth_login_credentials.py` | Inline error; password not echoed |
| AUTH-LOGIN-03 | `tests/integration/test_auth_login_credentials.py` | Same error message |
| AUTH-LOGIN-04 | `tests/integration/test_auth_login_credentials.py` | `OperationalError` via patched `authenticate` |
| AUTH-LOGIN-05 | `tests/integration/test_auth_login_form.py` | Submit `disabled` + `login_form.js` |
| AUTH-LOGIN-06 | `tests/integration/test_auth_login_form.py` | `required` on email |
| AUTH-LOGIN-07 | `tests/integration/test_auth_login_form.py` | `required` on password |
| AUTH-LOGIN-08 | `tests/integration/test_auth_login_layout.py` | Brand, tagline, forgot disabled + tooltip |
| AUTH-LOGIN-09 | `tests/integration/test_auth_login_layout.py` | `type="password"` |
| AUTH-LOGIN-10 | `tests/integration/test_auth_login_credentials.py` | GET redirect when authenticated |
| AUTH-LOGIN-11 | `tests/integration/test_auth_login_credentials.py` | POST logout; session cleared |
| AUTH-LOGIN-12 | `tests/integration/test_auth_login_form.py` | DOM order email → password → submit |
| AUTH-LOGIN-13 | `tests/integration/test_auth_login_layout.py` | Labels `for="login-email"` etc. |

## Checkpoints

```bash
DJANGO_SETTINGS_MODULE=huginn.settings.test .venv/bin/python -m pytest tests/integration/test_auth_login_credentials.py tests/integration/test_auth_login_layout.py tests/integration/test_auth_login_form.py -x -q
.venv/bin/python -m pytest tests/ -x -q
.venv/bin/ruff check . && .venv/bin/ruff format --check .
```

## Key artifacts

- **User model:** `accounts.User` (`AUTH_USER_MODEL`), `accounts/managers.py` (`get_by_natural_key` email `iexact`).
- **Auth service:** `ui/services/authentication_service.py` (`authenticate` + `login`, structured logging `huginn.auth`).
- **Views:** `ui/views/auth/login_view.py` (`never_cache`, connectivity handling), `ui/views/auth/logout_view.py` (POST-only).
- **UI:** `ui/templates/ui/auth/login.html`, `static/css/huginn.css`, `static/js/login_form.js`, `templates/base.html` (design system shell).

## GitLab issues (manual)

If not created via API, use the six-issue breakdown from the approved Act-0 plan (Phase 1–3) and paste inline Context Map / Do Not Do / SAO sections per BPE-01.
