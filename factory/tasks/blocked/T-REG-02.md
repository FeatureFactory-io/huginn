# Blocked

reason: reason:status: field 'status' is empty

---

---
id: T-REG-02
role: step-def-writer
attempt: 1
depends_on: [T-REG-01-impl]
gitlab_issue: 70
branch: factory/T-REG-02-register-form-steps
tools:
  - git
  - glab
  - python
  - pytest
  - ruff
files_in_scope:
  - tests/integration/test_auth_register.py
---

# Task T-REG-02 — Step defs: AUTH-REGISTER-* registration form scenarios

## Goal

Write **5 RED** pytest integration tests for **AUTH-REGISTER-01 / 03 / 04 / 05 / 08**:
happy path, password mismatch, weak password, sign-in link, and the duplicate-active-email
enumeration-protection contract. No production code.

## Blueprint

See [`factory/blueprints/T-REG-02.md`](../../blueprints/T-REG-02.md). It contains the
exact assertions for each scenario plus an important plan-vs-feature deviation you must
follow:

> The feature file says duplicate-active-email lands on AUTH-AWAIT_VERIFICATION-1
> (out of sprint scope). **LE decision: in-sprint contract = same 302 to Tactical Plot
> as a successful registration** (enumeration protection at the redirect level).
> Assert against the **plan**, not the AUTH-AWAIT_VERIFICATION-1 line in the feature.

## System context

[`factory/blueprints/system.md`](../../blueprints/system.md) §Key interfaces, §Test conventions.

## Acceptance criteria (RED)

`docs/features/act-0-auth/registration.feature` scenarios — write one test per scenario,
named after the scenario ID:

| Test name | Scenario | Key assertions |
|---|---|---|
| `test_auth_register_01_happy_path_creates_active_user_and_logs_in` | AUTH-REGISTER-01 | 302 → tactical-plot, `User.is_active=True`, `_auth_user_id` in session |
| `test_auth_register_03_password_mismatch_re_renders_with_inline_error` | AUTH-REGISTER-03 | 200, mismatch text in body, no user created |
| `test_auth_register_04_weak_password_re_renders_with_validator_error` | AUTH-REGISTER-04 | 200, password-validator copy in body, no user created |
| `test_auth_register_05_get_renders_sign_in_link` | AUTH-REGISTER-05 | 200, `register-sign-in-link` testid + auth-login URL in body |
| `test_auth_register_08_duplicate_active_email_returns_same_redirect_without_creating_dup_or_changing_password` | AUTH-REGISTER-08 | 302 → tactical-plot, no duplicate row, existing user's password unchanged, NOT logged in |

Verbatim test code (with imports + decorators) is in the blueprint. Copy it.

## Files in scope

Exactly one new file:

- `tests/integration/test_auth_register.py`

Do not touch any other file. If a test needs a fixture, write it inline (the
existing `commander_user` is too restrictive — pre-create users with `User.objects.create_user(...)`
directly inside the relevant test).

## Step-by-step

1. Read [`factory/blueprints/T-REG-02.md`](../../blueprints/T-REG-02.md) in full.
2. Open [`docs/features/act-0-auth/registration.feature`](../../../docs/features/act-0-auth/registration.feature) lines 80–141 (AUTH-REGISTER-01/02/03/04/05/06/07/08).
3. Open [`tests/integration/test_auth_login_credentials.py`](../../../tests/integration/test_auth_login_credentials.py) — Client + reverse + override_settings pattern.
4. `User = get_user_model()` at the top of the new file.
5. All 5 tests `@pytest.mark.django_db` + `@override_settings(DEBUG=True)`.
6. Run new file — expect 5 failures (NotImplementedError from `post()`, missing testid in GET).
7. Run full suite — expect green-except-new-file.
8. `ruff check tests/integration/test_auth_register.py` — clean.
9. Stage, commit, push, MR.

## Branch & MR

```bash
cd .worktrees/step-def-writer
git fetch origin
git checkout main && git reset --hard origin/main
git checkout -b factory/T-REG-02-register-form-steps

# … write the file …

.venv/bin/python -m pytest tests/integration/test_auth_register.py -v  # expect 5 RED
.venv/bin/python -m pytest tests/ -x --ignore=tests/integration/test_auth_register.py  # green
ruff check tests/integration/test_auth_register.py

git add tests/integration/test_auth_register.py
git commit -m "test(auth): RED tests for AUTH-REGISTER-01/03/04/05/08 registration form"
git push -u origin factory/T-REG-02-register-form-steps

glab mr create \
  --source-branch factory/T-REG-02-register-form-steps \
  --target-branch main \
  --title "test(auth): RED tests for AUTH-REGISTER-01/03/04/05/08" \
  --description "$(printf 'RED step defs for the in-scope AUTH-REGISTER scenarios (T-REG-02 in sprint Registration).\n\nThese tests are intentionally failing — T-REG-02-impl will turn them GREEN.\n\nClassroom note: AUTH-REGISTER-08 asserts the LE in-sprint contract (302 to Tactical Plot for duplicate-active-email) — not the AUTH-AWAIT_VERIFICATION-1 line in the .feature, which is out of sprint scope.\n\nCloses #70\n')" \
  --yes
```

## Checkpoint

```bash
.venv/bin/python -m pytest tests/integration/test_auth_register.py -v
# expect: 5 failed/errored (RED).

.venv/bin/python -m pytest tests/ -x --ignore=tests/integration/test_auth_register.py
# expect: 0 failures.

ruff check tests/integration/test_auth_register.py
# expect: clean.
```

## Do not

- Do NOT modify any production code (no `ui/`, no `accounts/`, no settings).
- Do NOT make the tests pass.
- Do NOT assert against AUTH-AWAIT_VERIFICATION-1 — that screen is out of sprint.
- Do NOT use Selenium / Playwright.
- Do NOT bypass `User.objects.create_user(...)` when seeding the duplicate user (test 08).

## Result

<!-- Worker fills in after completion. Required for verify-result.sh to accept. -->

# Result

status:
branch: ""
mr: ""
commit_sha: ""
