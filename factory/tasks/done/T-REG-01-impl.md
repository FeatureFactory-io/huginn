# Blocked

reason: reason:status: field 'status' is empty

---

---
id: T-REG-01-impl
role: feature-builder
attempt: 1
depends_on: [T-REG-01]
gitlab_issue: 69
branch: factory/T-REG-01-impl-debug-gate
tools:
  - git
  - glab
  - python
  - pytest
  - ruff
  - python manage.py
files_in_scope:
  - ui/views/auth/login_view.py
  - ui/templates/ui/auth/login.html
  - ui/views/auth/register_view.py
  - ui/templates/ui/auth/register.html
  - ui/urls.py
---

# Task T-REG-01-impl — DEBUG gate on login screen + register-route guard

## Goal

Turn the 3 RED tests from T-REG-01 GREEN. Add a DEBUG-conditional "Create an
account" affordance to the login screen and a `RegisterView` skeleton that
(a) flashes a banner + redirects to login when `DEBUG=False`, and
(b) renders an empty form stub when `DEBUG=True`.
**`post()` raises `NotImplementedError`** — body lands in T-REG-02-impl.

## Blueprint

See [`factory/blueprints/T-REG-01-impl.md`](../../blueprints/T-REG-01-impl.md).
Read it before you start — it has the exact code for the view, the template
fragments, and the messages-banner change in `login.html`.

## System context

[`factory/blueprints/system.md`](../../blueprints/system.md) §Template contract — login.html, §`RegisterView`, §Existing code workers must read.

## Acceptance criteria (GREEN)

After your change:

```
.venv/bin/python -m pytest tests/integration/test_auth_reg_login_debug_gate.py -v
```

must show **3 passed** for AUTH-REG-LOGIN-01 / 02 / 03 (the file authored in T-REG-01).

```
.venv/bin/python -m pytest tests/ -x
```

must show **no regressions** anywhere.

`ruff check ui/` must be clean.

## Files in scope

```
ui/views/auth/login_view.py            (modify — add "debug_mode" to _context())
ui/templates/ui/auth/login.html        (modify — messages render + conditional Create-account block)
ui/views/auth/register_view.py         (NEW)
ui/templates/ui/auth/register.html     (NEW — minimal stub; T-REG-02-impl rewrites it)
ui/urls.py                             (modify — register the auth-register URL)
```

Out-of-scope changes (services/, models, migrations, settings, JS) are
blockers. If you find a hidden regression — for example
`tests/integration/test_auth_login_layout.py::test_auth_login_08_forgot_password_disabled_with_admin_tooltip`
asserts wording that conflicts with the new `<a href="#">` design — narrow
that one test to the actual contract (`'data-testid="forgot-password"' in body`,
no `disabled` substring requirement) and call it out in your `# Result` block
under `out_of_scope_changes:`.

## Step-by-step

1. Read [`factory/blueprints/T-REG-01-impl.md`](../../blueprints/T-REG-01-impl.md) in full.
2. Read [`ui/views/auth/login_view.py`](../../../ui/views/auth/login_view.py) (66 lines) — extend `_context()`, that's the only function you touch in this file.
3. Read [`ui/templates/ui/auth/login.html`](../../../ui/templates/ui/auth/login.html) (57 lines) — splice the messages block at the top of `.card-body`, replace the Forgot-password block at the bottom.
4. Read [`ui/views/auth/register_view.py`](../../../ui/views/auth/register_view.py) (does not exist yet) — create it from the blueprint's class skeleton.
5. Read [`ui/templates/ui/mockups/auth/register.html`](../../../ui/templates/ui/mockups/auth/register.html) — note its structure; **do not port it fully** (that's T-REG-02-impl). Just create a minimal stub per the blueprint.
6. Read [`ui/urls.py`](../../../ui/urls.py) — add `path("accounts/register/", RegisterView.as_view(), name="auth-register")` and the import.
7. Verify Django messages middleware is enabled: `rg "django.contrib.messages.middleware.MessageMiddleware" huginn/settings/base.py`. If absent, that's a real blocker — file `--blocked` rather than guess.
8. Run the targeted test file: `.venv/bin/python -m pytest tests/integration/test_auth_reg_login_debug_gate.py -v`. Iterate until 3 passed.
9. Run the full suite: `.venv/bin/python -m pytest tests/ -x`. Fix any regression you caused (and only those).
10. `ruff check ui/ --fix && ruff check ui/`.
11. Stage, commit, push, open MR.

## Branch & MR

```bash
cd .worktrees/feature-builder
git fetch origin
git checkout main && git reset --hard origin/main
git checkout -b factory/T-REG-01-impl-debug-gate

# … make changes …

.venv/bin/python -m pytest tests/integration/test_auth_reg_login_debug_gate.py -v
.venv/bin/python -m pytest tests/ -x
ruff check ui/

git add ui/views/auth/login_view.py \
        ui/templates/ui/auth/login.html \
        ui/views/auth/register_view.py \
        ui/templates/ui/auth/register.html \
        ui/urls.py
git commit -m "feat(auth): debug-gate register link on login screen + register route guard"
git push -u origin factory/T-REG-01-impl-debug-gate

glab mr create \
  --source-branch factory/T-REG-01-impl-debug-gate \
  --target-branch main \
  --title "feat(auth): debug-gate register link + register route guard" \
  --description "$(printf 'Turns T-REG-01 RED tests (AUTH-REG-LOGIN-01/02/03) GREEN.\n\n- LoginScreenView._context() exposes debug_mode\n- login.html renders {%% messages %%} + conditional Create-account / Contact-admin block\n- RegisterView skeleton: dispatch() guards on settings.DEBUG; get() renders stub; post() = NotImplementedError\n- Minimal stub register.html (T-REG-02-impl rewrites)\n- auth-register URL wired at /accounts/register/\n\nCloses #69\n')" \
  --yes
```

## Checkpoint

```bash
.venv/bin/python -m pytest tests/integration/test_auth_reg_login_debug_gate.py -v
# expect: 3 passed.

.venv/bin/python -m pytest tests/ -x
# expect: full suite green.

ruff check ui/
# expect: clean.
```

## Do not

- Do NOT implement `post()` — `NotImplementedError` only.
- Do NOT add `RegistrationService` (T-REG-02-impl).
- Do NOT change `AUTH_PASSWORD_VALIDATORS`, `MIDDLEWARE`, or any settings file.
- Do NOT create any new app, model, migration, or admin form.
- Do NOT use `django.contrib.auth.forms.UserCreationForm`.
- Do NOT modify the mockup at `ui/templates/ui/mockups/auth/register.html`.
- Do NOT change `data-testid="login-register-link"` to a different name (feature file is authoritative).

## Result

<!-- Worker fills in after completion. Required for verify-result.sh to accept. -->

# Result

status: passed
branch: "factory/T-REG-01-impl-debug-gate"
mr: "20"
commit_sha: "c4ad47e"
