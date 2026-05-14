# Blueprint — T-REG-01: Step defs for AUTH-REG-LOGIN-* debug-gate scenarios

## Summary

Write 3 **RED** pytest integration tests that pin the DEBUG-gated "Create an account"
affordance on the login screen and the production redirect from `/accounts/register/`.
No production code in this task.

## Context

- **Sprint plan:** [`docs/plans/ACT0-REG-01_registration_debug_only.md`](../../docs/plans/ACT0-REG-01_registration_debug_only.md) §Task T-REG-01
- **Feature file:** [`docs/features/act-0-auth/registration.feature`](../../docs/features/act-0-auth/registration.feature) scenarios **AUTH-REG-LOGIN-01 / 02 / 03**
- **System blueprint:** [`factory/blueprints/system.md`](system.md) §Template contract — login.html
- **Pattern to follow:** [`tests/integration/test_auth_login_credentials.py`](../../tests/integration/test_auth_login_credentials.py)
  and [`tests/integration/test_auth_login_layout.py`](../../tests/integration/test_auth_login_layout.py)
- **Fixtures:** [`tests/integration/conftest.py`](../../tests/integration/conftest.py) (`commander_user`, `commander_client`)

## ⚠ testid contract — feature file wins

The feature file (AUTH-REG-LOGIN-01, line 23) names the link `data-testid="login-register-link"`.
The plan section uses `login-create-account` — **ignore that**. Tests in this task use
**`login-register-link`** per the feature file (LE rule: featurefile beats plan).
T-REG-01-impl will produce a template with the same `login-register-link` testid.

## Design

One new file: `tests/integration/test_auth_reg_login_debug_gate.py`.

Three tests, each decorated with `@pytest.mark.django_db` and `@override_settings(DEBUG=…)`.
Use `from django.test.utils import override_settings` (or `from django.test import override_settings`).
Use raw `Client()` (no login fixture needed — anonymous user paths).

### `test_auth_reg_login_01_debug_true_shows_register_link`
```
@override_settings(DEBUG=True)
GET reverse("auth-login")
assert status_code == 200
assert 'data-testid="login-register-link"' in body
```

### `test_auth_reg_login_02_debug_false_hides_register_link_and_shows_admin_hint`
```
@override_settings(DEBUG=False)
GET reverse("auth-login")
assert status_code == 200
assert 'data-testid="login-register-link"' not in body
assert "Need an account? Contact your admin." in body
```

### `test_auth_reg_login_03_debug_false_register_url_redirects_to_login_with_banner`
```
@override_settings(DEBUG=False)
# Raw URL — auth-register URL name may not yet resolve (RED state allowed).
r = client.get("/accounts/register/", follow=False)
assert r.status_code == 302
assert r.headers["Location"].startswith(reverse("auth-login"))

r2 = client.get("/accounts/register/", follow=True)
body2 = r2.content.decode()
assert "Registration is disabled on this Huginn install." in body2
assert "Contact your admin to request an account." in body2
```

If `/accounts/register/` returns **404** in the RED state (because the URL isn't wired yet),
that's fine — the test will fail with `assert 404 == 302`, which is the desired RED.
**Do not** add `try/except` to mask the failure.

## Files to touch

```
tests/integration/test_auth_reg_login_debug_gate.py   (NEW — only file)
```

## Interfaces / contracts

None — pure test authoring. Pin assertions against the feature-file wording verbatim:

| Source line | Assertion |
|---|---|
| AUTH-REG-LOGIN-01 line 23 | `'data-testid="login-register-link"' in body` |
| AUTH-REG-LOGIN-02 line 28 | `'data-testid="login-register-link"' not in body` |
| AUTH-REG-LOGIN-02 line 29 | `"Need an account? Contact your admin." in body` |
| AUTH-REG-LOGIN-03 line 35 | `"Registration is disabled on this Huginn install. Contact your admin to request an account." in body` |

## Risks

- `MIDDLEWARE` includes Django messages middleware — but the redirect-then-banner only works
  if `login.html` renders `{% if messages %}…{% endfor %}`. Today `login.html` does **not**.
  That's T-REG-01-impl's problem; this task only writes the assertion.

## Rollback / feature flags

Delete the new test file — no production impact.

## Smoke / verification

```bash
.venv/bin/python -m pytest tests/integration/test_auth_reg_login_debug_gate.py -v
# expect: 3 failures or errors (RED). Exit code non-zero.

.venv/bin/python -m pytest tests/ -x
# expect: existing suite still passes (only the new file fails).
```
