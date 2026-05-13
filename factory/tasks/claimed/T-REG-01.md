---
id: T-REG-01
role: step-def-writer
attempt: 1
depends_on: []
gitlab_issue: 68
branch: factory/T-REG-01-debug-gate-steps
tools:
  - git
  - glab
  - python
  - pytest
  - ruff
files_in_scope:
  - tests/integration/test_auth_reg_login_debug_gate.py
---

# Task T-REG-01 — Step defs: AUTH-REG-LOGIN-* debug-gate scenarios

## Goal

Write **3 RED** pytest integration tests for **AUTH-REG-LOGIN-01 / 02 / 03**
(the DEBUG-gated "Create an account" link on login + the production redirect
from `/accounts/register/`). No production code. The tests must fail today
and pass after T-REG-01-impl lands.

## Blueprint

See [`factory/blueprints/T-REG-01.md`](../../blueprints/T-REG-01.md).
Read it in full before you start — it spells out every assertion verbatim and
flags one **testid contract** you must follow (`login-register-link`, per the
feature file — the plan uses a different testid name; ignore the plan on this point).

## System context

[`factory/blueprints/system.md`](../../blueprints/system.md) §Test conventions, §Existing code workers must read.

## Acceptance criteria (RED)

`docs/features/act-0-auth/registration.feature` scenarios:

### AUTH-REG-LOGIN-01 — DEV shows Create account and navigates to register

```gherkin
Given settings DEBUG is enabled
And I am on the Huginn login page at "/"
Then I see a link with data-testid "login-register-link"
```

→ Test: `@override_settings(DEBUG=True)`; `GET reverse("auth-login")`; assert
`'data-testid="login-register-link"' in body`.

### AUTH-REG-LOGIN-02 — Production hides Create account link

```gherkin
Given settings DEBUG is disabled
And I am on the Huginn login page at "/"
Then I do not see a link with data-testid "login-register-link"
And I see the muted helper text containing "Need an account? Contact your admin."
```

→ Test: `@override_settings(DEBUG=False)`; `GET reverse("auth-login")`; assert testid
absent AND `"Need an account? Contact your admin." in body`.

### AUTH-REG-LOGIN-03 — Direct register URL redirects when signup disabled

```gherkin
Given settings DEBUG is disabled
When I open the registration URL "AUTH-REGISTER-1"
Then I am redirected to "AUTH-LOGIN-1"
And I see a dismissable banner containing
  "Registration is disabled on this Huginn install. Contact your admin to request an account."
```

→ Test: `@override_settings(DEBUG=False)`; `client.get("/accounts/register/", follow=False)`
asserts 302 to login; then `follow=True` asserts the banner copy verbatim in body.

## Files in scope

Exactly one new file:

- `tests/integration/test_auth_reg_login_debug_gate.py`

Do **not** modify any other file. If you find yourself needing to touch
`ui/`, `huginn/`, `accounts/`, or any other production code, **stop** — that's
T-REG-01-impl's job. Touch only the new test file.

## Step-by-step

1. Read [`factory/blueprints/T-REG-01.md`](../../blueprints/T-REG-01.md) (whole file, ~80 lines).
2. Open [`docs/features/act-0-auth/registration.feature`](../../../docs/features/act-0-auth/registration.feature) lines 20–35 — copy assertion text verbatim.
3. Open [`tests/integration/test_auth_login_credentials.py`](../../../tests/integration/test_auth_login_credentials.py) — copy the pytest-django + Client + reverse pattern.
4. Open [`tests/integration/conftest.py`](../../../tests/integration/conftest.py) — note `commander_user`, `commander_client` fixtures (not needed here — anonymous client paths only).
5. Open [`huginn/settings/test.py`](../../../huginn/settings/test.py) — confirm default `DEBUG = False`; use `@override_settings` to toggle per test.
6. Write the 3 tests in `tests/integration/test_auth_reg_login_debug_gate.py`. Use module-level docstring and `import` block matching the existing file style.
7. Run the new file: `.venv/bin/python -m pytest tests/integration/test_auth_reg_login_debug_gate.py -v`. Expect 3 failures or errors (RED).
8. Run the full suite: `.venv/bin/python -m pytest tests/ -x`. Expect no regressions — only the new file fails.
9. `ruff check tests/integration/test_auth_reg_login_debug_gate.py` — clean.
10. Stage, commit, push the branch, open MR targeting `main`.

## Branch & MR

```bash
cd .worktrees/step-def-writer
git fetch origin
git checkout main && git reset --hard origin/main
git checkout -b factory/T-REG-01-debug-gate-steps

# … write the file …

.venv/bin/python -m pytest tests/integration/test_auth_reg_login_debug_gate.py -v  # expect RED
.venv/bin/python -m pytest tests/ -x                                                # expect green-except-new-file
ruff check tests/integration/test_auth_reg_login_debug_gate.py

git add tests/integration/test_auth_reg_login_debug_gate.py
git commit -m "test(auth): RED tests for AUTH-REG-LOGIN-01/02/03 debug gate"
git push -u origin factory/T-REG-01-debug-gate-steps

glab mr create \
  --source-branch factory/T-REG-01-debug-gate-steps \
  --target-branch main \
  --title "test(auth): RED tests for AUTH-REG-LOGIN-01/02/03 debug gate" \
  --description "$(printf 'RED step defs for AUTH-REG-LOGIN-01/02/03 (T-REG-01 in sprint Registration).\n\nThese tests are intentionally failing — T-REG-01-impl will turn them GREEN.\n\nCloses #68\n')" \
  --yes
```

## Checkpoint

```bash
.venv/bin/python -m pytest tests/integration/test_auth_reg_login_debug_gate.py -v
# expect: 3 failed (or errored) — RED state.

.venv/bin/python -m pytest tests/ -x --ignore=tests/integration/test_auth_reg_login_debug_gate.py
# expect: 0 failed — no regression elsewhere.

ruff check tests/integration/test_auth_reg_login_debug_gate.py
# expect: clean.
```

## Do not

- Do NOT modify any file under `ui/`, `huginn/`, `accounts/`, `analytics/`, `ingestion/`, `sitrep/`, `gjallarhorn/`, `playbooks/`, or `static/`. Tests only.
- Do NOT use Selenium / Playwright — Django test client + `reverse()` only.
- Do NOT make the tests pass — they must be RED.
- Do NOT use `data-testid="login-create-account"` — that's a plan typo. Use `login-register-link` per feature file.
- Do NOT skip the full-suite run; out-of-scope regressions are blockers.

## Result

<!-- Worker fills in after completion. Required for verify-result.sh to accept. -->

# Result

status:
branch: ""
mr: ""
commit_sha: ""
