# GitLab issues — Act-0 Auth (paste into `dp2580/huginn`)

**MCP/GitLab API authentication was not available from this session.** Create six issues manually (or via `glab issue create`) using the blocks below. Suggested labels: `Feature`, `Scenario`, `priority::medium` (adjust to project convention).

Shared inline sections for **every** issue body (BPE-01):

---

## Context Map

| File | Lines | Note |
|------|-------|------|
| `docs/architecture/SAO.md` | §1–3, §5, §11, §13 | Server-rendered UI; session auth; pytest; structured logs; CSRF |
| `docs/features/act-0-auth/auth-login.feature` | full | BDD — 13 scenarios |
| `accounts/models.py` | full | `AbstractBaseUser` + `PermissionsMixin`, email `USERNAME_FIELD` |
| `accounts/managers.py` | full | `UserManager`, `get_by_natural_key` iexact |
| `ui/services/authentication_service.py` | full | `authenticate` + `login`, logging `huginn.auth` |
| `ui/views/auth/login_view.py` | full | `never_cache`, connectivity `OperationalError` |
| `ui/views/auth/logout_view.py` | full | POST-only logout |
| `ui/templates/ui/auth/login.html` | full | Canonical login (mockup port) |
| `templates/base.html` | full | `hg-navbar` shell, `{% block navbar %}` |
| `static/css/huginn.css`, `static/js/login_form.js` | full | Design system + submit enablement |

## Do Not Do

- Do NOT use Django’s default `User` model — `get_user_model()` only.
- Do NOT add SSO/OAuth/MVP REST auth — Django views + session only.
- Do NOT edit `ui/templates/ui/mockups/**` (reference only).
- Do NOT introduce `FOB-*` screen IDs.
- Do NOT disable CSRF on login POST or bypass `AuthenticationService` from views.
- Do NOT log passwords or full credentials.

## SAO.md Sections That Apply

- §1 Application Blocks, §2 Integration & API Design, §3 Code Organization, §4 Data Architecture, §5 Test Strategy, §11 Observability, §13 Security

---

### Issue 1 — `feat(accounts): custom AbstractBaseUser + AUTH_USER_MODEL`

**Phase:** 1 (parallel)

**Implementation Plan:** Add `accounts` app; `User` + `UserManager`; `AUTH_USER_MODEL`; reset/regenerate `ingestion` migrations with `makemigrations`; register admin; `commander_user` fixture uses `create_user(email=..., full_name=...)`; unit tests `tests/unit/test_user_model.py`, `tests/unit/test_user_manager.py`.

**Checkpoint:** `pytest tests/unit/test_user_model.py tests/unit/test_user_manager.py tests/ -x -q`

**Acceptance:** Checkpoint green; no default `User` imports.

---

### Issue 2 — `feat(ui): promote design system into base.html + huginn.css`

**Phase:** 1 (parallel)

**Implementation Plan:** Extract mockup CSS to `static/css/huginn.css`; rebuild `templates/base.html` (Montserrat, Bootstrap 5.3.8, FA, `hg-navbar`, real routes: `projects-list`, `datasources-list`, `welcome`); `{% block navbar %}`, `{% block body_class %}`; point `templates/base_mockups.html` at `huginn.css`; regression test `tests/integration/test_base_shell.py`.

**Checkpoint:** `pytest tests/ -x -q`

---

### Issue 3 — `feat(auth): AuthenticationService + unit tests`

**Phase:** 2 (after Issue 1)

**Implementation Plan:** `authenticate()` + `login()`; strip email; blank email/password → `(None, None)`; failure → `"Invalid email or password"`; `logger` `huginn.auth`; `logout_user`; `tests/unit/test_authentication_service.py` (RequestFactory + `AnonymousUser` on request).

**Checkpoint:** `pytest tests/unit/test_authentication_service.py -x -q`

---

### Issue 4 — `feat(auth): LoginScreenView, LogoutScreenView, credential integration tests`

**Phase:** 2 (after Issue 1)

**Implementation Plan:** `@method_decorator(never_cache)` on `LoginScreenView`; try/except `OperationalError`/`ConnectionError` → connectivity banner; blank credential branch without false “Invalid…” ; `LogoutScreenView` POST-only (`405` GET); `tests/integration/test_auth_login_credentials.py` (AUTH-LOGIN-01..04, 10–11).

**Checkpoint:** `pytest tests/integration/test_auth_login_credentials.py -x -q`

---

### Issue 5 — `feat(auth): login template port + login_form.js + layout tests`

**Phase:** 2 (after Issue 1+2)

**Implementation Plan:** Port `ui/templates/ui/mockups/auth/login.html` to `ui/templates/ui/auth/login.html` (extends `base.html`, empty navbar block); `static/js/login_form.js`; `tests/integration/test_auth_login_layout.py`, `test_auth_login_form.py` (AUTH-LOGIN-05..09, 12–13 structural).

**Checkpoint:** `pytest tests/integration/test_auth_login_layout.py tests/integration/test_auth_login_form.py -x -q`

---

### Issue 6 — `test(auth): scenario sweep + ruff + docs`

**Phase:** 3

**Implementation Plan:** Map scenarios 01–13 to tests in `docs/plans/F01_auth_login_FULL_IMPLEMENTATION_PLAN.md`; remove stale `test_auth_login.py` if split; `ruff check` + `ruff format --check`; full `pytest tests/`.

**Checkpoint:** `pytest tests/ -x -q && ruff check . && ruff format --check .`

---

**Suggested dependency note in GitLab:** Issues 3–5 depend on 1; Issue 5 depends on 2; Issue 6 depends on 3–5.
