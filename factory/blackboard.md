# Blackboard — factory current state

<!-- LE edits this section in place -->

**Phase:** 0 — Preflight (ready to start Phase 1 Ingestion)

**Milestone:** Registration (GitLab IID 7427525)

**Sprint goal:** Self-signup flow (DEBUG-only): register → auto-verified + auto-approved → immediate login. No email verification, no admin moderation queue. Ships the minimum viable account creation path so a developer can sign up on a local/sandbox install.

**Branch base:** `main`

**Integration branch (to be created Phase 4):** `integration/registration`

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

## Test strategy

- Step-def workers write RED pytest-bdd tests first; impl workers make them GREEN.
- `settings.DEBUG = True` in test settings; gate tested by toggling the setting in parametrized tests.
- No email sending, no token models, no `account_status` field — see Do-Not-Do list in plan.
- Test DB: SQLite in-memory (default Django test runner).

---

## Do NOT do

- Send any email or touch `django.core.mail`
- Create email verification tokens or any new model
- Add an `account_status` / `is_approved` field to the User model
- Implement admin approval queue UI
- Show the register link when `DEBUG = False`

---

## Blocked / risks

- None identified at preflight.

---

## Open questions for human

_None._

---

# Event queue (LE)

- **PENDING:** —
- **CLAIMED:** —
- **Done worker tasks:** —

---

# Event log

<!-- Append-only: LE and workers add dated lines -->
- **2026-05-13 (LE)** Factory reset to Registration milestone. Previous sprint (AI → SitRep, IID 4) task queue cleared (T-68-release ghost removed from pending/ + claimed/). Preflight passed with `--allow-dirty`; working tree cleaned (.worktrees/ gitignored). Blackboard initialized for Registration Phase 0 → ready for Phase 1 ingestion.
