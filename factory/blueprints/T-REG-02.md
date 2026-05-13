# Blueprint — T-REG-02: Step defs for AUTH-REGISTER-* registration form scenarios

## Summary

Write 5 **RED** pytest integration tests covering the in-scope AUTH-REGISTER scenarios
on the register form: happy path, password mismatch, weak password, sign-in link, and
duplicate-active-email enumeration protection. No production code in this task.

## Context

- Plan §Task T-REG-02
- Feature file scenarios **AUTH-REGISTER-01 / 03 / 04 / 05 / 08**
- System blueprint §Key interfaces, §Test conventions
- Pattern: [`tests/integration/test_auth_login_credentials.py`](../../tests/integration/test_auth_login_credentials.py)

## ⚠ Plan-vs-feature deviation (AUTH-REGISTER-08)

The feature file (line 137-140) says duplicate-active-email lands on **AUTH-AWAIT_VERIFICATION-1**
with "generic success copy". That whole screen is **out of sprint scope**.

**LE decision (logged in blackboard):** the in-sprint contract is what the plan says — the
duplicate path returns the **same 302 to Tactical Plot** as a successful registration
(enumeration protection at the redirect level). No `AUTH-AWAIT_VERIFICATION-1` screen
this sprint. Workers: assert against the **plan's** wording.

## Design

One new file: `tests/integration/test_auth_register.py`.

All tests `@pytest.mark.django_db` and `@override_settings(DEBUG=True)` unless noted.
Use raw `Client()`; for test 08 pre-create the user inline (no fixture needed).
URL helper: `reverse("auth-register")`. Redirect target: `reverse("tactical-plot")`.

### `test_auth_register_01_happy_path_creates_active_user_and_logs_in`

```
client.post(reverse("auth-register"), {
    "name": "Commander Casey",
    "email": "fresh@example.com",
    "password": "Abcd-valid-987",
    "password_confirm": "Abcd-valid-987",
}, follow=False)

assert r.status_code == 302
assert r.headers["Location"] == reverse("tactical-plot")

user = User.objects.get(email="fresh@example.com")
assert user.is_active is True
assert "_auth_user_id" in client.session
assert int(client.session["_auth_user_id"]) == user.pk
```

`User = get_user_model()` at top of file.

### `test_auth_register_03_password_mismatch_re_renders_with_inline_error`

```
client.post(reverse("auth-register"), {
    "name": "Commander Casey",
    "email": "fresh@example.com",
    "password": "Abcd-valid-987",
    "password_confirm": "different-password",
})

assert r.status_code == 200
body = r.content.decode()
assert 'data-testid="register-password-confirm"' in body
assert "do not match" in body.lower()
assert not User.objects.filter(email="fresh@example.com").exists()
```

### `test_auth_register_04_weak_password_re_renders_with_validator_error`

```
client.post(reverse("auth-register"), {
    "name": "Bad",
    "email": "pw@example.com",
    "password": "12345",
    "password_confirm": "12345",
})

assert r.status_code == 200
body = r.content.decode()
# Django's MinimumLengthValidator message: "This password is too short. It must contain at least 8 characters."
# CommonPasswordValidator may also fire on "12345" / NumericPasswordValidator on all-digits.
# Be loose: assert SOMETHING password-related is rendered.
assert "password" in body.lower()
assert ("too short" in body.lower()
        or "at least 8" in body
        or "too common" in body.lower()
        or "entirely numeric" in body.lower())
assert not User.objects.filter(email="pw@example.com").exists()
```

### `test_auth_register_05_get_renders_sign_in_link`

```
r = client.get(reverse("auth-register"))
assert r.status_code == 200
body = r.content.decode()
assert 'data-testid="register-sign-in-link"' in body
# Link href points to login (use reverse so a future URL rename doesn't lie).
assert reverse("auth-login") in body
```

### `test_auth_register_08_duplicate_active_email_returns_same_redirect_without_creating_dup_or_changing_password`

```
existing = User.objects.create_user(
    email="existing@example.com",
    password="Original-pw-12345",
    full_name="Existing User",
)

r = client.post(reverse("auth-register"), {
    "name": "Intruder",
    "email": "existing@example.com",
    "password": "Different-Abcd-987",
    "password_confirm": "Different-Abcd-987",
}, follow=False)

# Enumeration protection: same 302 → Tactical Plot as a fresh successful signup.
assert r.status_code == 302
assert r.headers["Location"] == reverse("tactical-plot")

# No duplicate row.
assert User.objects.filter(email__iexact="existing@example.com").count() == 1
# Existing user's password untouched.
existing.refresh_from_db()
assert existing.check_password("Original-pw-12345") is True
# Attacker is NOT logged in as the existing user (no session attached).
assert "_auth_user_id" not in client.session
```

## Files to touch

```
tests/integration/test_auth_register.py    (NEW — only file)
```

## Interfaces / contracts

- URL name `auth-register` (created in T-REG-01-impl).
- URL name `auth-login` (existing).
- URL name `tactical-plot` (existing; `/plot/`).
- POST field names: `name`, `email`, `password`, `password_confirm`.
- `data-testid` strings: `register-password-confirm`, `register-sign-in-link` (from mockup; preserved by T-REG-02-impl).

## Risks

- AUTH-REGISTER-04: tests use `"12345"` (5 chars, all-numeric). Three validators may fire
  (MinimumLength, NumericPassword, possibly CommonPassword). Assertion is OR-loose to
  accept any of them. **Do not** narrow to one specific validator message — Django's
  copy may shift across versions.
- AUTH-REGISTER-08: caller must NOT be auto-logged-in as the pre-existing user. The
  duplicate branch silently 302s; no session is bound. Test asserts `"_auth_user_id" not in session`.
- Until T-REG-02-impl lands, `RegisterView.post()` raises `NotImplementedError` — all 4
  POST tests will raise, satisfying RED. Test 05 (GET) will fail because the stub template
  doesn't yet render the sign-in link — also satisfying RED.

## Rollback / feature flags

Delete the new test file — no production impact.

## Smoke / verification

```bash
.venv/bin/python -m pytest tests/integration/test_auth_register.py -v
# expect: 5 failures or errors (RED). Exit code non-zero.

.venv/bin/python -m pytest tests/ -x
# expect: existing suite still green (only the new file fails).
```
