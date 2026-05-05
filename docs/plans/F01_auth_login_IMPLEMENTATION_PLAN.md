# F01 AUTH-LOGIN-1 — Implementation Plan (BPE-01 skeleton)

Canonical route: **`/accounts/login/`** (`auth-login`). Feature background references `/`; follow-up iteration may add root redirect for anon vs authenticated per `LOGIN_REDIRECT_URL`.

## Context Map

| File | Lines | Note |
| --- | --- | --- |
| [docs/architecture/SAO.md](../../architecture/SAO.md) | 36–52 | UI is server-rendered templates; Django auth/session per project settings |
| [huginn/settings/base.py](../../huginn/settings/base.py) | INSTALLED_APPS | `django.contrib.auth` already enabled |
| [templates/base.html](../../templates/base.html) | full | Navbar + messages — extend for login shell |
| [docs/features/act-0-auth/auth-login.feature](../../features/act-0-auth/auth-login.feature) | full | BDD acceptance — skeleton defers credential success path |

## Do Not Do

- Do NOT introduce `FOB-*` screen IDs ([.cursor/rules/no-fob-screen-ids.mdc](.cursor/rules/no-fob-screen-ids.mdc)).
- Do NOT disable CSRF on login POST.
- Do NOT bypass `AuthenticationService` from the shell view — delegate credentials there.

## SAO.md Sections That Apply

- §2 Integration & API Design — Web UI Django views only for v1
- §3 Code Organization — `ui/` views + templates; thin controllers
- §16 Security (if present) — session + CSRF defaults

## Implementation Steps (skeleton)

1. Add `huginn.settings.test` (SQLite, locmem cache) for checkpoint pytest without Docker services.
2. Set `DJANGO_SETTINGS_MODULE` in `pyproject.toml` for pytest.
3. `ui.services.authentication_service.AuthenticationService` — `authenticate_user` / `logout_user` → `NotImplementedError`.
4. `LoginScreenView` — GET render `ui/auth/login.html`; POST call service and catch `NotImplementedError` with inline message (skeleton UX).
5. Wire `urls.py` → `accounts/login/`; template `login-email`, `login-password`, `login-submit` `data-testid` per feature.
6. Integration checkpoint: pytest proves service raises until MIT implements.

## Checkpoint

```bash
.venv/bin/python -m pytest tests/integration/test_auth_login.py -x -q
```

Expect: PASS (explicit `NotImplementedError` assertion on service skeleton).
