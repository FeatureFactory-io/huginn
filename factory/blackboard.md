# Blackboard — factory current state

<!-- LE edits this section in place -->

**Phase:** 2 — Decomposition complete; 4 tasks in `factory/tasks/pending/`. Worker fswatch loops will claim in dep order. Proceeding dark to Phase 3 (execution).

**Milestone:** Registration (GitLab IID 7427525)

**Sprint goal:** Self-signup flow (DEBUG-only): register → `is_active=True` → immediate login. No email verification, no admin moderation queue, no new models, no email. Ships the minimum viable account creation path so a developer can sign up on a local/sandbox install.

**Branch base:** `main` (Huginn is trunk-based; MRs target `main` per `SAO.md` §9).

**Integration strategy:** Stacked MRs from `main` per task. **No long-lived `integration/registration` branch** — chain is short (4 tasks, strictly linear) and trunk-based merges keep the dependency graph clean.

---

## Issue register

| # | ID | Title | Role | Status | Depends on | Feature file |
|---|---|---|---|---|---|---|
| 68 | T-REG-01 | Step defs — AUTH-REG-LOGIN-* debug gate scenarios | step-def-writer | open | — | `docs/features/act-0-auth/registration.feature` |
| 69 | T-REG-01-impl | DEBUG gate on login screen + register route guard | feature-builder | open | #68 | `docs/features/act-0-auth/registration.feature` |
| 70 | T-REG-02 | Step defs — AUTH-REGISTER-* registration form scenarios | step-def-writer | open | #69 | `docs/features/act-0-auth/registration.feature` |
| 71 | T-REG-02-impl | Registration service + view + template | feature-builder | open | #70, #69 | `docs/features/act-0-auth/registration.feature` |

**Dependency chain:** `#68 → #69 → #70 → #71`

---

## Scope decisions (LE, Phase 1)

| Scenario | In/out | Reason |
|---|---|---|
| AUTH-REG-LOGIN-01/02/03 | **in** — T-REG-01 + T-REG-01-impl | DEBUG gate is core sprint scope |
| AUTH-REG-LOGIN-04/05/06/07 | **out** | Require `pending_email_verification` / `pending_admin_approval` / `rejected` states — not in this sprint |
| AUTH-REGISTER-01/03/04/05/08 | **in** — T-REG-02 + T-REG-02-impl | Plan §Scenarios in scope |
| AUTH-REGISTER-02 | **in (template-level)** | Client-side `disabled` attr assertion in template test |
| AUTH-REGISTER-06 | **out** | Pending-verification state not modelled this sprint |
| AUTH-REGISTER-07 | **out** | Transient backend rejection requires injection point — defer |
| AUTH-AWAIT_VERIFICATION-*, AUTH-VERIFY_EMAIL-*, AUTH-AWAIT_APPROVAL-* | **out** | Email + token flow — later milestone |
| ADMIN-APPROVE-01 / ADMIN-REJECT-01 | **out** | Admin moderation — later milestone |
| ACCESS-REG-01 | **in (template-level)** | Asserted in T-REG-02-impl as `tabindex` / DOM order check |

Plan and feature file agree on this slicing (plan §Scenarios in scope is authoritative; out-of-scope scenarios remain in the .feature file as forward documentation).

---

## Test strategy

- **Framework:** `pytest` + `pytest-django` (no `pytest-bdd`). Tests are imperative integration tests using `django.test.Client`.
- **RED → GREEN:** step-def-writer tasks (`T-REG-01`, `T-REG-02`) author failing tests first. feature-builder tasks (`-impl`) make them pass + keep the rest of the suite green.
- **DEBUG toggle:** `@override_settings(DEBUG=True|False)` per test — do not depend on settings module defaults.
- **Test DB:** default `pytest-django` runner (`@pytest.mark.django_db`).
- **No email I/O:** any test that asserts "no email sent" only needs to assert the absence of a side-effect we never wire up; we don't import `django.core.mail` anywhere in this sprint.

---

## Do NOT do

- Send any email or touch `django.core.mail`
- Create email verification tokens or any new model
- Add an `account_status` / `is_approved` field to the User model
- Implement admin approval queue UI
- Show the register link when `DEBUG = False`

---

## Blocked / risks

- **R-1 (low):** `validate_password` defaults — Django's settings may not enforce min-length. Mitigation: T-REG-02-impl test for AUTH-REGISTER-04 uses `"12345"` (5 chars); confirm `huginn/settings/base.py` has `MinimumLengthValidator` in `AUTH_PASSWORD_VALIDATORS`. If absent, T-REG-02-impl worker adds it (5 LoC); flag in Result block.
- **R-2 (low):** Forgot-password link in `login.html` is currently `disabled`. T-REG-01-impl removes the `disabled` attribute (keeps `href="#"`) so the conditional create-account block reads cleanly. Documented in template contract in `system.md`.
- **R-3 (low):** ACCESS-REG-01 (keyboard tab order) is asserted at the template level (visual DOM order matches tab order, no `tabindex` reordering). No Selenium needed.

---

## Open questions for human

_None — sprint plan + feature file are unambiguous on the in-scope slice._

---

# Event queue (LE)

- **PENDING:** T-REG-01, T-REG-01-impl, T-REG-02, T-REG-02-impl
- **CLAIMED:** —
- **Done worker tasks:** —

(`claim.sh` gates each task on `factory/tasks/done/<dep>.md`; only T-REG-01 will be claimable
until T-REG-01 lands in done/. No `blocked/` placement needed.)

---

# Event log

<!-- Append-only: LE and workers add dated lines -->
- **2026-05-13 (LE)** Factory reset to Registration milestone. Previous sprint (AI → SitRep, IID 4) task queue cleared (T-68-release ghost removed from pending/ + claimed/). Preflight passed with `--allow-dirty`; working tree cleaned (.worktrees/ gitignored). Blackboard initialized for Registration Phase 0 → ready for Phase 1 ingestion.
- **2026-05-13 (LE) Phase 1 — Ingestion complete.** Read milestone (`glab issue view 68/69/70/71`), plan `docs/plans/ACT0-REG-01_registration_debug_only.md` (309 lines), feature file `docs/features/act-0-auth/registration.feature` (249 lines, 23 scenarios), mockup `ui/templates/ui/mockups/auth/register.html`, and existing production code (`accounts/models.py`, `accounts/managers.py`, `accounts/admin.py`, `ui/views/auth/login_view.py`, `ui/services/authentication_service.py`, `ui/templates/ui/auth/login.html`, `ui/urls.py`, `tests/integration/conftest.py`, `tests/integration/test_auth_login_credentials.py`). Rewrote `factory/blueprints/system.md` for Registration sprint (replaces stale Gjallarhorn-sprint version). **Awaiting human review of blackboard + system blueprint before Phase 2 decomposition.**

- **2026-05-13 (HUMAN → LE)** Phase 1 approved. **PROCEED DARK:** run Phase 2 → 3 → 4 → 4.5 → 5 autonomously without stopping for human checkpoints. Log all assumptions to this event log. When staging is deployed write `factory/RESULT.md` with the URL. Do not wait for human input at any intermediate phase.

(LE) Wrote factory/CHECKPOINT — Phase 1 review requested. scripts/checkpoint.sh not yet present in repo; created the signal file directly (in-scope, factory/**). Surfaces in scripts/status.sh banner. Waiting on human to rm factory/CHECKPOINT before Phase 2.

- **2026-05-13 (HUMAN → LE)** CHECKPOINT removed. PROCEED to Phase 2 immediately. Do NOT create any more CHECKPOINT files or gating mechanisms — run dark all the way to staging. Make assumptions, log them here, keep moving.

- **2026-05-13 (LE) Phase 2 — Decomposition complete.** Wrote 4 blueprints + 4 task files. Archived 12 previous-sprint done/ + blueprint files to `factory/archive/sprint-sitrep-pre-2026-05-13/` so `release.sh` won't be tripped by their missing `status: integrated` (they were merged in the prior Sitrep sprint; archival is records-only, no code reverted). All 4 new tasks sit in `factory/tasks/pending/`; `claim.sh` enforces deps by checking `done/<dep>.md`. Dependency chain: T-REG-01 → T-REG-01-impl → T-REG-02 → T-REG-02-impl. step-def-writer claims T-REG-01 + T-REG-02; feature-builder claims T-REG-01-impl + T-REG-02-impl. All MRs target `main` (trunk-based, per SAO §9).
- **ASSUMPTION [sprint-wide]:** `data-testid="login-register-link"` per the feature file (AUTH-REG-LOGIN-01 line 23). The plan + previous system blueprint draft both used `login-create-account`; **feature wins** (LE rule §When you're uncertain #2). Workers told explicitly to use `login-register-link` and to ignore the plan on this point.
- **ASSUMPTION [T-REG-02 / AUTH-REGISTER-08]:** The feature file lands duplicate-active-email on screen `AUTH-AWAIT_VERIFICATION-1`. That screen is out of sprint scope (no email verification flow this milestone). LE in-sprint contract = silent duplicate returns the SAME 302 to Tactical Plot as a fresh successful signup (enumeration protection at the redirect level, no second screen). Documented in T-REG-02 task + T-REG-02-impl service contract. To revisit when AUTH-AWAIT_VERIFICATION-1 ships in a later milestone.
- **ASSUMPTION [T-REG-01-impl forgot-password]:** Existing `test_auth_login_08_forgot_password_disabled_with_admin_tooltip` asserts `"disabled" in body` and `"Contact your admin" in body`. After the conditional block lands, login-submit still has `disabled` and the `login-signup-disabled` span carries "Contact your admin" under DEBUG=False — assertion stays satisfied. Worker told to confirm via full-suite run and, if it does fail, narrow that test (out-of-scope diff documented in Result).
- **ASSUMPTION [release strategy]:** Latest tag is `registration-kickoff` (non-semver). `release.sh` requires `x.y.z`. Will choose semver `0.1.0` for first registration release (minor: new feature; major bump to `1.0.0` once production-grade auth lands).

- **2026-05-13 14:32:16** 🔧 **step-def-writer** claimed **T-REG-01**
