# Huginn — User Journey

> ESM Activity 02 artifact. Companion to `docs/ideation/vision.md`.

---

## System Architecture Notes

**Screen ID convention**: every screen is identified by `{ENTITY}-{OPERATION}-{VERSION}` (e.g., `PROJECTS-LIST+FIND-1`). Used in this document, in screen-flow diagrams, in feature files, and as HTML comments / hidden divs in templates for grep-able traceability.

**Gjallarhorn** — the AI component. Three surfaces:
1. **Background**: event-driven — fires on `Sync Complete` (generates SitRep, evaluating Variables against the active RoE + FRAGOs + Situational Awareness). In **Autonomous** mode, approved **Outcomes** for auto-generated Decisions execute via the SitRep / `execute_decision_outcome` Celery chain. **Semi-Auto** Commander approvals **do not enqueue that path** — **calibration** and **dispatch** Outcomes run **synchronously inside the Decision review HTTP request** (SAO §17.8 / §18 / Flow C). Plan creation and final narrative synthesis use the **planning model** (Opus); per-Variable execution steps use the **execution model** (Sonnet); plan success/failure notifications use the **notification model** (Haiku) — see SAO §17.3 Model Assignment Policy.
2. **Chat — full-screen** (`CHAT-FULLSCREEN-1`, Act 8): two-pane interactive surface that exposes platform CRUDL via `services.py` / `tool_executor.py`. `find_*` tools provide full-text search; list operations support pagination, page size, filters.
3. **Chat — sidebar** (`CHAT-SIDEBAR-1`): collapsible right rail mounted in the global layout, visible on every screen. **One Conversation per authenticated user + Project** — navigation switches threads when the anchored Project changes; the context chip auto-updates from the current screen within that scope. `[Expand to full screen]` opens `CHAT-FULLSCREEN-1` preserving the active Project conversation and pinned context (`docs/architecture/SAO.md` §17.11).

**Operating mode** (per-Project, persisted as `Project.gjallarhorn_mode`):
- **Semi-Autonomous** (default): Gjallarhorn generates SitReps and proposes **Decisions with Outcome options** (calibrations or dispatches). The Commander reviews each Decision: **Approve** executes one **Outcome** **synchronously in the Decision review POST**. **Reject** declines the proposed option but **may still** capture vigilance calibrations (FRAGO / Sit-Awareness) or a reject note—or dismiss entirely with no artefacts (see Act 9).
- **Autonomous**: Gjallarhorn auto-approves its own Decisions (with machine-generated Reasoning attributed to `"Gjallarhorn"`) and executes Outcomes. The Commander observes via audit log.
- Toggle is a pill `[Semi-Auto | Auto]` on the `PROJECTS-VIEW_PROJECT-1` top action bar.

**Decisions Logic FRAGO** (per-Project, system-managed): **one dedicated FRAGO** per Project (`kind = decisions_logic`) — Donland maintains **judgment memory in that single body**: the system **contributes structured lines by default from most Completed reviews** (**Approved**, **Auto-approved**, and materially recorded **Rejected** — see Act 9); exceptions include e.g. a **bare dismiss** with nothing to remember. Commander **extends**, **modifies**, or **removes** bullets via **`FRAGOS-EDIT_FRAGO-1`**. Automatic contributions use the **canonical markdown-bullet template** in SAO §17.8 (` · `-separated inline fields — one bullet per qualifying review). Auto-created when the **first** such line lands. Not revocable, not toggleable, always Active. The Rules of Engagement stays the canonical definition of **what good looks like**; this FRAGO captures **how reasoning has evolved** for that Project. Gjallarhorn reads its current body when proposing new Decisions.

**Commander profile** (per-User, system-managed): behavioral priors — *how this Commander tends to decide* (e.g. tolerance for red Variables, typical delay before acting). **Distinct from Decisions Logic FRAGO** (project explicit judgment). Updated on Decision resolve via persisted signals; Gjallarhorn reads profile during Orient/Decide. MVP: signal persistence only (`variable_abbrev`, `color`, `action_taken`, `delay_hours`); profile VIEW/EDIT UI deferred (see Open product decisions). See SAO §18.5 and [`docs/ideation/vision.md`](../ideation/vision.md) — Vocabulary.

**Plans**: Gjallarhorn's internal async execution engine. When any multi-step task is needed — primarily SitRep generation (translating the RoE Workflow into concrete tool calls: get commits, assess Variable, assign color, save Datapoint…) or occasionally a complex Decision implementation — Gjallarhorn creates an `ExecutionPlan` and runs it step-by-step via Celery. Plans are **visible in the Chat** as a collapsible `PlanProgressCard` (goal + progress bar + live step list). Each step records pre-execution reasoning (`why needed`, `expected outcome`) and post-execution reflection (`actual result`, `outcome assessment`), and stores the `model_used` field from `LLMResponse.model` so the model used for each step is auditable. Plans always start automatically — there is no Commander approval gate on a Plan. The Commander only gates the *Decisions* that a SitRep Plan produces (in Semi-Auto mode). On permanent step failure, Gjallarhorn posts a recovery analysis message in Chat with partial results and next-step options (see PlanProgressCard spec in Act 8). On transient failure (Claude 429), the step pauses for exponential-backoff retry (30 s → 60 s → 120 s) before resuming — completed steps are never re-executed.

**Jira / GitLab / etc.** — systems of record for raw work data. Huginn ingests via DataSources. **Huginn writes one thing back to Jira: issues created from approved dispatch Outcomes, tagged `HUGINN`.** No comment write-back, no annotation write-back.

**Project lifecycle**: Projects are **import-only**. They are never created from a blank form — only by selecting from the list of projects a connected DataSource's token can see.

**RoE lifecycle**: Rules of Engagement are versioned. An RoE is metadata + a Workflow (markdown) + an ordered list of `RulesOfEngagementVariable` (structured). A Project auto-tracks the latest version of its assigned RoE unless explicitly pinned to a specific version. Editing an RoE (Workflow markdown OR any RulesOfEngagementVariable) creates a new version; Projects on auto-track receive the new expectations on their next SitRep. (In the future version you can import RoE/Workflow from Mimir Server.)

**Time period granularity (systemwide)**: periods in Huginn span hours or days, not just calendar days. Sync can run as frequently as every hour; SitReps can cover sub-day windows ("last 2 hours", "last 4 hours", "today"). Period selectors throughout the UI offer both day-level and hour-level presets. Custom periods use datetime pickers (`from_date` / `to_date`) resolved to the minute. All timestamps and period bounds are stored and displayed in the user's local timezone.

**Project view tabs**: tabs on the Project view are **system-defined**, not RoE-derived:
- **Vitals** — hardcoded, present on every Project. Contains: Identity / RoE / Sync metadata cards; a hardcoded **Transparency** card; and the **informer bar** — one colored dot per `RulesOfEngagementVariable` on the active RoE version (in declared order), value and color sourced from the **latest `VariableDatapoint`** for each Variable (hover shows `name (abbrev): value`; grey dot when no datapoint exists).
- **Variables** — one diagram per `RulesOfEngagementVariable` on the active RoE version, showing all `VariableDatapoint` rows for the selected period as a time-series chart (Y-axis = `y_axis_label` from the datapoint; color of each point reflects the `color` field from Gjallarhorn's assessment). Period filter supports both hour-level and day-level presets plus a custom datetime range.
- **Adapter-driven tabs** — one tab per registered ingestion adapter. Today: the **Increments** tab, contributed by `ingestion/adapters/gitlab_commits.py`. New adapters add new tabs as they land.

**DataSource credentials**: PATs (GitLab) are user-set and may have an expiry; Jira API tokens generally don't. Huginn tracks an `expires_at` per DataSource and surfaces a warning before expiry. No automatic refresh — the API doesn't support it for PATs.

**User account lifecycle**: Huginn supports **self-signup with admin moderation**. A `User` record progresses through four logical states (exact model field names are implementation details left to the build phase):

- `pending_email_verification` — account just created via registration form; `is_active = False`; cannot log in. A single-use verification link (24-hour TTL) has been issued and emailed.
- `pending_admin_approval` — email verification succeeded; `is_active = False` still; cannot log in. Visible to staff in the Django admin moderation queue (`/admin/`).
- `active` — admin approved; `is_active = True`; login enabled. Lands on `DASHBOARD-PROJECTS-1` after sign-in.
- `rejected` — admin declined the application; `is_active = False` permanent. Login attempts surface the rejection message (no enumeration of details). Optional admin-supplied rejection reason stored and included in the outbound notification email; not re-attemptable without admin intervention.

State transitions are one-directional except for `pending_email_verification → pending_email_verification` (resend issues a new link and invalidates the previous one).

**Transactional email** (outbound, system-sent): all Act 0 notifications (verify your email, awaiting approval, account approved, account rejected, password reset link, password changed) are delivered through **Amazon SES** via Django's email framework — production deployments configure SES SMTP or API credentials (a candidate dependency is `django-ses`; final choice deferred to BSP). Local dev / test use Django's console / locmem backends. SES is a **new infrastructure dependency** introduced by Act 0 — it must be provisioned (verified sender identity + IAM credentials in EB env vars) before registration can ship to staging. See `docs/architecture/SAO.md` (to be extended) for the deployment-side specifics.

**Self-signup gating (`settings.DEBUG`)**: `AUTH-REGISTER-1` and its companion routes (`AUTH-AWAIT_VERIFICATION-1`, `AUTH-VERIFY_EMAIL-1`, `AUTH-AWAIT_APPROVAL-1`) are available **only when `settings.DEBUG = True`** — i.e., on local developer machines and the sandbox. In production (`DEBUG = False`) the self-signup routes return a redirect to `AUTH-LOGIN-1` carrying a banner — *"Registration is disabled on this Huginn install. Contact your admin to request an account."* — and the **Create an account** link on `AUTH-LOGIN-1` is **not rendered**. Production accounts are provisioned by an operator via the Django admin or a management command (out-of-MVP UI; CLI flow is the operator's MVP path). Password reset (`AUTH-FORGOT_PASSWORD-1` / `AUTH-RESET_PASSWORD-1`) is **always available regardless of `DEBUG`** — operators in production still need their users to be able to recover access. This policy ties signup to the existing Django flag rather than introducing a new env variable: no toggle to forget, and the production posture is the safe default automatically.

**Session mechanism**: Huginn uses Django's standard **cookie-based session authentication** (`SESSION_ENGINE = django.contrib.sessions.backends.db`). Login calls `django.contrib.auth.login()`, logout calls `django.contrib.auth.logout()`. There is no DRF token, no JWT, no custom `auth_token` field. Email verification tokens and password-reset tokens are **implementation details** left to the build phase — the journey spec intentionally does not prescribe whether they are DB rows or Django's built-in signed-HMAC generator (`PasswordResetTokenGenerator`). The `account_status` enum, `EmailVerificationToken`, and `PasswordResetToken` concepts in this spec describe **logical states and flows**, not literal model names.

**Non-standard screen patterns** (extensions to CRUDLF, established here per Activity 01):
- `IMPORT` — Project: select-from-source instead of CREATE form
- `VIEW` only — SitRep, Variables, Contributors (generated/computed)
- `VIEW + EDIT` only — Situational Awareness (**workspace-global**: one capsule for the Commander / installation, not scoped per Project)
- `LIST+FIND + VIEW` only — Action Stations (**station records** — dispatch mirror; Jira-owned lifecycle, read-only display)
- `REGISTER` / `VERIFY_EMAIL` / `AWAIT_VERIFICATION` / `AWAIT_APPROVAL` — Act 0 self-signup workflow screens (anonymous-accessible; not a CRUDLF pattern)
- `CHAT-FULLSCREEN` — Gjallarhorn full-screen conversational surface (Act 8)
- `CHAT-SIDEBAR` — Gjallarhorn collapsible global rail (persistent across all screens)

---

## Persona

### Commander Donland

**Role**: Project Manager / Commander. Bears the consequences of every Decision.

**Typical day**:
- 09:00 — opens Huginn, scans the **Tactical Plot** for red/orange health indicators
- For any red Project — reads the SitRep, calibrates expectations via FRAGOs, drills into Variables, queries Gjallarhorn
- Makes Decisions. Each approved Decision executes exactly one **Outcome** — a **calibration** (FRAGO or SA) or a **dispatch** (`HUGINN`-tagged Jira issue)
- Reviews Contributors' day-by-day activity
- Checks Action Stations (**station records**) to confirm **dispatches** landed in Jira correctly

### Admin (workspace operator)

**Role**: Huginn installation operator. A Django user with `is_staff = True`. May be the same person as Donland in a small team, or a separate IT/Ops contact in a larger one — Huginn assumes **at least one** active staff user exists at install time (seeded via Django management command, see SAO §0 if/when documented).

**Responsibilities** (Act 0 scope):
- Moderates new self-signups: reviews each `pending_admin_approval` account in the **Django admin** (`/admin/`) and runs the **Approve** or **Reject** admin action.
- Receives no Huginn product email about pending applications in MVP — staff check the Django admin on cadence.

Out of MVP scope: password resets on behalf of users, role / permission management, deactivating active accounts. For now the admin's only Act 0 affordance is approve/reject of pending registrations.

---

## Acts

The journey divides into three phases. Inception is one-time per install (or per new Project). Calibration and Action repeat daily.

### INCEPTION — bring data in, set expectations

| Act | Surface | Pattern | Primary Screen |
|-----|---------|---------|----------------|
| 0 | Authentication | Register + Verify + Admin-gated Login | `AUTH-LOGIN-1` |
| 1 | DataSource | CRUDLF | `DATASOURCES-LIST+FIND-1` |
| 2 | Project Import | LIST+FIND + IMPORT + VIEW + ARCHIVE | `PROJECTS-LIST+FIND-1` |
| 3 | Rules of Engagement | CRUDLF (versioned) | `ROE-LIST+FIND-1` |

### CALIBRATION — read the situation, tune expectations

| Act | Surface | Pattern | Primary Screen |
|-----|---------|---------|----------------|
| 4 | Projects Dashboard (Tactical Plot) | Landing — color-coded health | `DASHBOARD-PROJECTS-1` |
| 5 | SitRep / Status Report | LIST+FIND + VIEW (per Project) | `SITREP-LIST+FIND-1` |
| 6 | FRAGO | CRUDLF (RoE adjustment) | `FRAGOS-LIST+FIND-1` |
| 7 | Variables Deep-Dive | VIEW with filters | `VARIABLES-VIEW-1` |
| 8 | Gjallarhorn Chat | CHAT-FULLSCREEN + CHAT-SIDEBAR | `CHAT-FULLSCREEN-1` / `CHAT-SIDEBAR-1` |

### ACTION — decide, execute, observe

| Act | Surface | Pattern | Primary Screen |
|-----|---------|---------|----------------|
| 9 | Decisions | LIST+FIND + VIEW (Outcome chooser) | `DECISIONS-LIST+FIND-1` |
| 10 | Contributors | LIST+FIND + VIEW (day-by-day) | `CONTRIBUTORS-LIST+FIND-1` |
| 11 | Action Stations | LIST+FIND — station records (dispatch mirror) | `ACTIONSTATIONS-LIST+FIND-1` |
| 12 | Situational Awareness | VIEW + EDIT (workspace-global) | `SITAWARENESS-VIEW-1` |

---

# INCEPTION

The one-time setup: connect a data source, import the projects you care about, write the Rules of Engagement that defines what "good" looks like for each project. By the end of Inception, Huginn has data flowing in and Gjallarhorn has produced its first SitRep.

---

## Act 0: Authentication

**Context**: Donland opens Huginn at `/`. If this is his first visit **and** the install runs with `settings.DEBUG = True` (dev / sandbox), he **self-signs up** (Register → email verification → admin approval); in production (`DEBUG = False`) self-signup is disabled and an operator provisions his account out-of-band — he simply signs in. After a successful sign-in he lands on the **Tactical Plot** (`DASHBOARD-PROJECTS-1`, Act 4) — empty on first run. A workspace **Admin** (`is_staff = True`) uses the same login screen and, after authenticating, manages pending registrations via the **Django admin** (`/admin/`) — there is no custom moderation UI in Huginn MVP. **Forgot password** is a separate side-flow available on every install (regardless of `DEBUG`) and is specified at the end of this Act.

**End-to-end registration flow** (the path a new Commander walks from cold start to a working login):

1. **Register** — clicks **Create an account** on `AUTH-LOGIN-1` → fills name / email / password on `AUTH-REGISTER-1`. Submitting creates a `User` row with `is_active = False`, issues a single-use verification link (24h TTL), and sends **Email 1 — Verify your email** via SES.
2. **Check email** — Huginn shows `AUTH-AWAIT_VERIFICATION-1` ("We sent a verification link to {email}…") with a **[Resend email]** affordance (rate-limited).
3. **Verify** — clicks the link in Email 1 → lands on `AUTH-VERIFY_EMAIL-1`, which consumes the token, transitions the row to `pending_admin_approval`, and sends **Email 2 — Awaiting admin approval** to the user. The screen confirms verification succeeded and explains that an admin must approve next.
4. **Wait for admin** — `AUTH-AWAIT_APPROVAL-1` is the holding state; if the user returns to `/` and tries to log in while still pending, the login form surfaces the same status inline (no enumeration leak — see AUTH-LOGIN-1 flow).
5. **Admin moderates** — in the **Django admin** (`/admin/`), the admin filters the User list by `pending_admin_approval` status, selects the user, and runs the **Approve** or **Reject** admin action. On approve: row transitions to `active`, `is_active = True`, and **Email 3 — Account approved** is sent (with a sign-in link). On reject: row transitions to `rejected`, `is_active` stays `False`, and **Email 4 — Account not approved** is sent (with the optional reason verbatim).
6. **Login** — the approved user clicks the link in Email 3 → `AUTH-LOGIN-1` → signs in with the credentials chosen at step 1 → `DASHBOARD-PROJECTS-1`.

**Failure / edge paths** (each detailed in the relevant screen below):
- Expired verification token (>24h) — `AUTH-VERIFY_EMAIL-1` shows an error with a [Resend email] CTA; no state transition.
- Login while `pending_email_verification` / `pending_admin_approval` / `rejected` — message rendered on `AUTH-LOGIN-1`, **no** password-vs-status enumeration disclosed: invalid credentials always fail the same way; status messages only appear when credentials match.
- Email already registered — `AUTH-REGISTER-1` returns a soft message and **always sends an email to that address** (either a verification re-send if pending, or a "you already have an account" note if active) to avoid leaking account existence.
- Self-signup hit on a production install (`DEBUG = False`) — `AUTH-REGISTER-1` and its companion routes redirect to `AUTH-LOGIN-1` with a banner: *"Registration is disabled on this Huginn install. Contact your admin to request an account."* No row is created, no email is sent.

**Security notes**:
- Email verification links are single-use with a 24h TTL. Resending a new link invalidates the previous one. Token storage and signing mechanism are implementation details (see session-mechanism note above).
- All Act 0 endpoints are rate-limited per IP and per email (e.g., 5 / hour / email for verification re-sends; 10 / hour / IP for register + login).
- Passwords are stored using Django's default PBKDF2 hasher (no plain text, never logged).

#### Screen: AUTH-LOGIN-1

**Layout**:
- **Header**: Huginn wordmark + tagline "Human-AI Command Composite"
- **Form** (centered, single column):
  - Email (`data-testid="login-email"`)
  - Password (`data-testid="login-password"`)
  - [Sign In] button (primary, full-width)
- **Below the form** (secondary affordances):
  - **Create an account** link (`data-testid="login-register-link"`) → `AUTH-REGISTER-1` — rendered **only when `settings.DEBUG = True`**. In production (`DEBUG = False`) this link is **omitted entirely** and replaced by static muted copy: *"Need an account? Contact your admin."* (no link, no tooltip).
- **Footer**:
  - **Forgot password?** link (`data-testid="login-forgot-password-link"`) → `AUTH-FORGOT_PASSWORD-1` — always rendered, always functional, regardless of `DEBUG`.

**Optional inbound banner** (above the form, dismissable):
- When the user was redirected here from a disabled self-signup route on a production install: *"Registration is disabled on this Huginn install. Contact your admin to request an account."*
- When the user just successfully reset their password (`AUTH-RESET_PASSWORD-1` → here): *"Password updated. Sign in with your new password."*
- When the user just clicked the link in Email 3 (account approved): *"Your account is approved — welcome to Huginn. Sign in to get started."*

**Flow** (credentials check happens first; status-based messaging only fires when credentials are valid, to prevent account-existence enumeration):
- Credentials valid AND account `active` → **Tactical Plot** `DASHBOARD-PROJECTS-1` (Act 4)
- Credentials valid AND account `pending_email_verification` → stays on the login page; inline notice: *"Your email isn't verified yet. We sent a verification link to {email}."* with a **[Resend verification email]** button (rate-limited)
- Credentials valid AND account `pending_admin_approval` → stays on login; inline notice: *"Your account is verified and waiting for admin approval. You'll receive an email once it's reviewed."*
- Credentials valid AND account `rejected` → stays on login; inline notice: *"Your account application was not approved. Please contact your admin if you believe this is an error."* (no rejection reason shown here — it was delivered in Email 4)
- Credentials invalid → inline error "Invalid email or password" (same message for unknown email and wrong password — no enumeration)
- Network error → "Unable to reach Huginn. Check your connection."

**Already-authenticated** users navigating to `/` are redirected to `DASHBOARD-PROJECTS-1`. Logging out clears the session and returns here.

---

#### Screen: AUTH-REGISTER-1

**Context**: The new Commander clicks **Create an account** on `AUTH-LOGIN-1` and lands here. This screen is anonymously accessible — but only on installs running with `settings.DEBUG = True`.

**`DEBUG` gating** (production posture): when `settings.DEBUG = False`, every entry-point to this screen (the route, direct URL access, deep links from old emails) returns an HTTP redirect to `AUTH-LOGIN-1` with the banner *"Registration is disabled on this Huginn install. Contact your admin to request an account."* No row is created, no token is issued, no email is sent. Server-side this is enforced by a single guard at the top of the registration view + URL conf — there is no client-side toggle to bypass, and no env variable to forget to flip. Operators provision production accounts through the Django admin or a management command (e.g. `manage.py createuser_active`, to be added during BSP).

The rest of this section assumes the install is in dev / sandbox mode (`DEBUG = True`).

**Layout**:
- **Header**: Huginn wordmark + tagline + sub-header "Create your Huginn account"
- **Form** (centered, single column):
  - Full name (`data-testid="register-name"`, required, free text)
  - Email (`data-testid="register-email"`, required, email format)
  - Password (`data-testid="register-password"`, required, masked, minimum strength per Django `AUTH_PASSWORD_VALIDATORS` — length, common-password block, numeric-only block)
  - Confirm password (`data-testid="register-password-confirm"`, required, must equal Password)
  - [Create account] button (`data-testid="register-submit"`, primary, full-width; disabled until all four fields validate)
- **Below the form**:
  - "Already have an account? **Sign in**" link → `AUTH-LOGIN-1`

**Inline validation**:
- Email format: client-side check + server re-check on submit
- Password strength: live indicator (weak / acceptable / strong) as the user types
- Password mismatch: red helper text under Confirm password

**Flow**:
- **Submit, new email** → server creates a `User` row with `is_active = False`, issues a single-use verification link (24h TTL), sends **Email 1 — Verify your email** to the address, redirects to `AUTH-AWAIT_VERIFICATION-1` carrying `{email}` for display.
- **Submit, email already in `pending_email_verification`** → re-issues the token, re-sends Email 1, redirects to `AUTH-AWAIT_VERIFICATION-1` with the same UX (no enumeration: looks identical to a brand-new signup).
- **Submit, email already in `pending_admin_approval` / `active` / `rejected`** → does **not** create a duplicate row; sends a context-appropriate "you already have an account" email to that address, then redirects to `AUTH-AWAIT_VERIFICATION-1` showing the same generic success copy (no enumeration). Real status is communicated only by the email Huginn just sent.
- **Validation error** (server-side: e.g., password too weak) → re-render the form with errors inline; no email is sent.
- **Network / server error** → top-of-form banner "Unable to create account right now. Please try again." Form retains entered values except passwords.

**Post-submit screen**: `AUTH-AWAIT_VERIFICATION-1`.

---

#### Screen: AUTH-AWAIT_VERIFICATION-1

**Context**: Immediately after `AUTH-REGISTER-1` submit succeeds (or any of its enumeration-blocking equivalents above). The User row is in `pending_email_verification`; login is not yet possible.

**Layout** (centered card, single column):
- **Header**: Huginn wordmark
- **Icon / illustration**: an envelope or "mail sent" cue
- **Title**: "Check your email"
- **Body**: "We sent a verification link to **{email}**. Click the link in the email to verify your address — the link is valid for **24 hours**."
- **Actions**:
  - **[Resend email]** button (`data-testid="resend-verification"`) — issues a new verification link (invalidating the previous one) and re-sends Email 1; rate-limited (5 / hour / email; gentle on-screen counter after click: "Sent. You can resend in 60s.")
  - **[Back to sign in]** secondary link → `AUTH-LOGIN-1`
- **Footer help**: "Didn't get the email? Check spam, or contact your admin."

**No automatic redirect**: this screen does not poll for verification — the user moves on by clicking the link in their inbox, which routes them to `AUTH-VERIFY_EMAIL-1`. Re-visiting this URL directly without an active pending registration redirects to `AUTH-LOGIN-1`.

---

#### Screen: AUTH-VERIFY_EMAIL-1

**Context**: The user clicks the verification link in Email 1, which routes to `/auth/verify/?token=…`. This screen consumes the token server-side **before** rendering.

**Server-side outcomes** (rendered states):

- **Success** (link valid + user is in `pending_email_verification` state + not expired):
  - Activate the account for admin review (`is_active` stays `False` until admin approves); **send Email 2 — Awaiting admin approval** to the user.
  - Render: title "Email verified", body "Thanks — we've confirmed your email. Your account now needs to be approved by an admin. We'll email you the moment that happens." + [Back to sign in] link → `AUTH-LOGIN-1`.
  - Optionally, after a brief delay (e.g., 2s) auto-redirect to `AUTH-AWAIT_APPROVAL-1`; manual click also goes there via the CTA.
- **Already verified** (link matches a user who already passed verification):
  - No state change, no second Email 2.
  - Render: title "Already verified", body "This email has already been verified. {status-appropriate one-liner: 'It's waiting for admin approval' / 'You can sign in now' / 'Please contact your admin.'}." + [Go to sign in] CTA.
- **Expired link** (>24h since issued):
  - Render: title "Link expired", body "This verification link has expired. Request a new one to verify your email." + **[Resend verification email]** form (one-field: email address; submitting issues a new link and sends Email 1; the user is then sent to `AUTH-AWAIT_VERIFICATION-1`).
- **Invalid / unknown link**:
  - Render: title "Link not recognised", body "We couldn't verify this link. It may have been used already or copied incorrectly. You can request a new link from the sign-in page." + [Go to sign in] CTA. No state change.

**No login side-effect**: verifying does **not** log the user in. They will sign in normally once admin approval lands.

---

#### Screen: AUTH-AWAIT_APPROVAL-1

**Context**: Reached automatically (or via the CTA on `AUTH-VERIFY_EMAIL-1`) once the User row is in `pending_admin_approval`. Anonymous-accessible — no session is required; users typically arrive here once and then close the tab.

**Layout** (centered card, single column):
- **Header**: Huginn wordmark
- **Icon / illustration**: a "stand by" or hourglass cue
- **Title**: "Hold tight — admin approval pending"
- **Body**: "Your email is verified. A workspace admin will review your application shortly. We'll email you (**{email}**) the moment your account is approved — you don't need to keep this page open."
- **Actions**:
  - **[Back to sign in]** link → `AUTH-LOGIN-1`
- **Footer help**: "Approvals are typically handled within one business day. Contact your admin directly if it's been longer."

**Behaviour**:
- This screen is static — no polling, no live status. The user's queue position is intentionally not surfaced to avoid leaking admin workload signals.
- Direct visits to this URL without a known pending session redirect to `AUTH-LOGIN-1`.

---

### Forgot password (Act 0 side-flow)

A standalone two-screen flow off `AUTH-LOGIN-1`. Available on **every install** regardless of `settings.DEBUG` — production users still need to be able to recover access when they forget their password. Password-reset links are single-use with a **1-hour TTL** (shorter than the 24h verification TTL) and are invalidated by a successful password change or by issuing a new reset for the same account. Storage and signing mechanism are implementation details. Like every other Act 0 endpoint, both screens are rate-limited per IP and per email.

**Build status**: screens specified here for completeness; implementation tracked as a follow-up sprint after the registration / approval flow ships. Until built, the **Forgot password?** link on `AUTH-LOGIN-1` may temporarily fall back to the legacy "Contact your admin" tooltip — but the canonical target is the spec below.

#### Screen: AUTH-FORGOT_PASSWORD-1

**Context**: The user clicks **Forgot password?** on `AUTH-LOGIN-1` and lands here. Anonymous-accessible.

**Layout** (centered card, single column):
- **Header**: Huginn wordmark + sub-header "Reset your password"
- **Form**:
  - Email (`data-testid="forgot-email"`, required, email format)
  - **[Send reset link]** button (`data-testid="forgot-submit"`, primary, full-width; disabled until email validates)
- **Below the form**:
  - "Remembered it? **Sign in**" link → `AUTH-LOGIN-1`

**Flow** (constant-time, enumeration-resistant — the UI behaviour is identical regardless of whether the email exists):
- **Submit** → server looks up the email:
  - If matched to an `active` user: issues a `PasswordResetToken`, invalidates any prior outstanding reset token for that user, sends **Email 5 — Password reset link**.
  - If matched to a `pending_email_verification` / `pending_admin_approval` / `rejected` user: does **not** issue a reset token; instead sends a context-appropriate variant of Email 5 explaining why the account can't be reset right now (verify your email first / awaiting admin approval / contact your admin) — the user still gets an email, just not one with a reset link.
  - If unmatched: sends **no** email; server logs the attempt for rate-limit accounting.
- **In all three cases** the screen transitions to a success state, identical copy: title *"Check your email"*, body *"If an account exists for **{email}**, we've sent a password-reset link. It will expire in 1 hour."* + **[Resend]** button (rate-limited; 5 / hour / email) + **[Back to sign in]** link.

The mismatch between "email always shown" and "real send only in some cases" is intentional — the only place a user can tell their account actually exists is the inbox of the email they just typed in. Combined with the enumeration-blocking behaviour on `AUTH-REGISTER-1` and `AUTH-LOGIN-1`, this keeps account existence opaque to bystanders.

**Edge cases**:
- Submitting the same email repeatedly within the rate-limit window: success state still renders, but no additional email is sent server-side; the rate-limit counter is decremented either way.
- Validation error (malformed email): inline error under the field; no submission, no email.
- Network / server error: top-of-form banner "Unable to send reset link right now. Please try again."

#### Screen: AUTH-RESET_PASSWORD-1

**Context**: The user clicks the link in Email 5 and lands here on `/auth/reset/?token=…`. Token validation happens server-side **before** rendering the form.

**Pre-render link check**:
- **Valid + within 1h TTL + not yet used** → render the form (below).
- **Expired** (>1h since issue): render an error state — title *"Reset link expired"*, body *"This password-reset link has expired. Request a new one from the sign-in page."* + **[Request new link]** CTA → `AUTH-FORGOT_PASSWORD-1`.
- **Already used**: render *"Link already used"* + same CTA.
- **Unknown / malformed link**: render *"Link not recognised"* + same CTA.
- **Link belongs to a non-`active` user** (account was rejected or reverted to pending after the link was issued): render *"This account can't be reset right now. Contact your admin."* — no form, no further action.

**Form layout** (centered card, single column):
- **Header**: Huginn wordmark + sub-header "Choose a new password"
- **Context line**: the email the reset is for (so the user knows which account they're changing): *"Resetting password for **{email}**."*
- **Fields**:
  - New password (`data-testid="reset-password"`, required, masked, same strength rules as `AUTH-REGISTER-1` — Django `AUTH_PASSWORD_VALIDATORS`)
  - Confirm new password (`data-testid="reset-password-confirm"`, required, must equal New password)
- **[Set new password]** button (`data-testid="reset-submit"`, primary, full-width; disabled until both fields validate)

**Flow on submit**:
- Server re-validates the link (defence in depth; handles race between page render and submit), then:
  - Sets the user's password to the new value (PBKDF2 hash).
  - Invalidates the reset link (single-use).
  - Invalidates other active sessions for that user so any previously logged-in browsers are signed out on their next request (Django's `update_session_auth_hash` keeps the resetting session intact; other sessions are revoked).
  - Sends **Email 6 — Password changed** to the user's email (security notification — *"Your Huginn password was changed at {timestamp}. If this wasn't you, contact your admin immediately."*).
  - Redirects to `AUTH-LOGIN-1` with the success banner: *"Password updated. Sign in with your new password."*
- Validation error (passwords don't match, password too weak): re-render the form with errors inline; the link is **not** invalidated (the user can retry).
- Network / server error: banner at top of form; link not invalidated.

**No auto-login**: completing reset returns the user to the login screen — they sign in fresh with their new password. This keeps the post-reset flow consistent with normal session creation and avoids edge cases where the reset link itself becomes a single-use sign-in mechanism.

---

### Admin moderation (Act 0)

The admin's role in Act 0 is narrow: approve or reject pending self-signups. There are **no custom product UI screens** for this — moderation is done entirely through the **Django admin** (`/admin/`), which is accessible only to users with `is_staff = True`.

**Implementation note**: The Django admin exposes the `User` model with a `pending_admin_approval` filter and custom admin actions:
- **Approve selected users** — transitions `account_status` to `active`, sets `is_active = True`, records `approved_by` + `approved_at`, and dispatches **Email 3 — Account approved**.
- **Reject selected users** — transitions `account_status` to `rejected`, keeps `is_active = False`, records `rejected_by` + `rejected_at`, and dispatches **Email 4 — Account not approved**.

The Django admin `User` change list is the moderation queue. No custom Huginn product navigation is added for this in MVP — the admin navigates to `/admin/` directly. Rejected rows are retained in the DB for audit; there is no DELETE in MVP.

---

### Transactional emails (Act 0)

All six emails are sent via Amazon SES (see the User account lifecycle architecture note). MVP uses simple HTML + plain-text multipart templates; subject lines are stable strings so they're easy to filter in inboxes.

| # | Trigger | Subject | Recipient | Key content |
|---|---------|---------|-----------|-------------|
| 1 | `AUTH-REGISTER-1` submit (new or re-send) | "Verify your email for Huginn" | Registrant | Greeting, verification link (`/auth/verify/?token=…`), TTL note (24h), small-print "if you didn't register, ignore this email" |
| 2 | `AUTH-VERIFY_EMAIL-1` success | "Your Huginn account is awaiting admin approval" | Registrant | Confirmation that email is verified, plain-language explanation that an admin must approve next, expectation-setting ("usually within one business day") |
| 3 | Django admin **Approve** action | "Your Huginn account is approved" | Approved user | Greeting using submitted full name, sign-in link to `/`, short "welcome to Huginn" line |
| 4 | Django admin **Reject** action | "Your Huginn account request" | Rejected user | Polite "your application was not approved", verbatim admin-supplied reason when present, contact-your-admin fallback line; **no** sign-in link |
| 5 | `AUTH-FORGOT_PASSWORD-1` submit (account matched) | "Reset your Huginn password" | Account holder | Reset link (`/auth/reset/?token=…`), TTL note (**1h**), security line "if you didn't request this, ignore this email and your password stays the same"; account-status variants for non-`active` rows omit the reset link and explain why (verify your email / awaiting approval / contact your admin) |
| 6 | `AUTH-RESET_PASSWORD-1` success | "Your Huginn password was changed" | Account holder | Security notification with timestamp; "if this wasn't you, contact your admin immediately"; no link |

Notes:
- **No email is sent** when `AUTH-FORGOT_PASSWORD-1` is submitted for an email Huginn doesn't recognise — server-side logs the attempt for rate-limit accounting; the UI behaves identically (account-existence enumeration is blocked at the UI layer, not the inbox).
- The admin **does not** receive a notification email when a new user reaches `pending_admin_approval` in MVP — they discover the queue through the **Pending users (N)** nav badge on next sign-in. (Out-of-band admin notifications are listed under Open product decisions.)

---

## Act 1: DataSource — CRUDLF

**Context**: Before Huginn can do anything, Donland connects a data source. MVP supports **GitLab and GitHub** (GitHub.com PAT only); Jira will come later. GitLab uses a base URL + Personal Access Token; GitHub uses a GitHub.com PAT (API base is fixed). After saving, the DataSource is the prerequisite for Act 2 (Project Import).

#### Screen: DATASOURCES-LIST+FIND-1

Donland clicks **Data Sources** in the main nav.

**Layout**:
- **Header**: "Data Sources" with count badge (e.g., "Data Sources (1)")
- **Top Actions**: [+ Add Data Source] button (primary)
- **Filter**: Type (GitLab / GitHub / Jira) | Status (Connected / Error / Token expiring)
- **Table** with columns:
  - Type | Name | Base URL | Token expires | Status | Last activity | Actions
- **Status badges**:
  - Connected (green)
  - Token expiring in N days (amber, ≤30 days from `expires_at`)
  - Token expired (red, sync stopped)
  - Connection error (red, hover for last error)
- **Row Actions** (dropdown):
  - [View] → `DATASOURCES-VIEW_DATASOURCE-1`
  - [Edit] → `DATASOURCES-EDIT_DATASOURCE-1`
  - [Delete] → `DATASOURCES-DELETE_DATASOURCE-1`
  - [Import Projects] → `PROJECTS-IMPORT-1` (Act 2) — shortcut, only enabled when status = Connected
- **Empty State**:
  - "No data sources connected"
  - "Add a GitLab or GitHub connection to start importing projects."
  - [+ Add Data Source]

**Example Data**:
- GitLab | "company-gitlab" | https://gitlab.example.com | 14 days | Token expiring | 5 min ago

#### Screen: DATASOURCES-CREATE_DATASOURCE-1

Donland clicks [+ Add Data Source].

**Layout**:
- **Step 1 — Type**: Two cards (GitLab / Jira). **GitLab** covers project import + commit sync. **Jira** is selectable when the workspace needs **Jira dispatch board** (dispatch Outcomes) + Action Stations read-sync — the same `DataSource(type=Jira)` stores PAT/API token + base URL (`docs/architecture/SAO.md` §2). Deep ingest of arbitrary Jira scopes beyond `HUGINN`-labelled mirrors may still roll out iteratively; connecting Jira here is still required before dispatch Outcomes succeed.
- **Step 2 — Connection form**:
  - Name (required) — Donland's label, e.g., "company-gitlab"
  - Base URL (required) — e.g., `https://gitlab.example.com`
  - Personal Access Token (required, masked input)
  - Token expires on (date picker, optional but encouraged) — informs the warning band
  - [Test Connection] button → inline result:
    - Success: "Connected as user@example.com — your token can see N projects"
    - Failure: error code + message (401, 404, network, etc.)
  - [Save Data Source] (disabled until Test Connection succeeds) | [Cancel]
- **Post-save**: redirect to `PROJECTS-IMPORT-1` (Act 2) with banner "Data source connected. Choose which projects to import."

#### Screen: DATASOURCES-VIEW_DATASOURCE-1

**Layout**:
- Type badge | Name | Base URL | Status
- Token: masked, last 4 chars; expiry date with countdown
- Authenticated as (user info from connection test)
- Sync activity log (last 20 sync runs across all imported Projects: timestamp, project, duration, records ingested, errors)
- [Edit] | [Test Connection Now] | [Delete]

#### Screen: DATASOURCES-EDIT_DATASOURCE-1

Same form as CREATE, pre-populated. Token field shows `••••••••` with [Replace Token] button. Editing the token re-runs Test Connection on save.

#### Screen: DATASOURCES-DELETE_DATASOURCE-1

Confirmation modal:
- "Disconnect 'company-gitlab'?"
- "N Project(s) currently use this data source. Disconnecting will stop syncs and mark them as orphaned."
- [Disconnect] (danger) | [Cancel]

---

## Act 2: Project Import — LIST+FIND + IMPORT + VIEW + ARCHIVE

**Context**: With a connected DataSource, Donland imports the specific projects he wants Huginn to analyze. Projects in Huginn are **never created from a blank form** — they are always imported from a DataSource that has access. He picks one, several, or all; each becomes a Project in Huginn and gets a Celery sync job submitted immediately.

**Pattern**: LIST+FIND (the Huginn-side list) + IMPORT (replaces CREATE) + VIEW + ARCHIVE (replaces DELETE — projects with ingested history are never hard-deleted).

#### Screen: PROJECTS-LIST+FIND-1

This is the **Huginn-side** Project list (different from the Tactical Plot in Act 4 — that is the daily landing). This screen is for management: assign RoE, archive, view sync status, and **see the latest SitRep headline + generated time** per row.

**Layout**:
- **Header**: "Projects" with count badge
- **Top Actions**:
  - **[Import Projects]** button (primary; download icon + label text `Import Projects`, no leading `+`) → `PROJECTS-IMPORT-1`
- **Filters**:
  - **Operational** list (`ui/templates/ui/projects/list.html`): Data source | Row status (Active / Archived / Orphaned) | RoE (search).
  - **HTML mock** (`ui/templates/ui/mockups/projects/list.html`): DataSource | Status — Rules of Engagement filter is omitted in the stub; columns still include RoE assignment per row.
- **Table** with columns:
  - Name | DataSource | RoE (name + version) | Last sync | **Last SitRep** (latest headline → link to `SITREP-VIEW_SITREP-1` when known) | **Last SitRep generated** (timestamp; **`—`** when none yet) | Status
  - No visible **Actions** column; each row ends with a single overflow menu (⋯) for secondary commands (see `docs/ux/IA_guidelines.md` §5.2 — LIST+FIND Table).
- **Row navigation**:
  - **Name** links to `PROJECTS-VIEW_PROJECT-1`
  - **Last SitRep** (when present) links to `SITREP-VIEW_SITREP-1` for the latest SitRep on that Project
  - Overflow menu: **Edit project** → `PROJECTS-EDIT_PROJECT-1` | **Archive** → `PROJECTS-ARCHIVE_PROJECT-1`
- **Empty State**:
  - "No projects imported yet"
  - "Import projects from a connected data source."
  - **[Import Projects]** (same label as toolbar)

#### Screen: PROJECTS-IMPORT-1

Donland clicks **[Import Projects]** (from this screen, Act 1's shortcut, or Act 0's empty-state CTA).

**Layout**:
- **Header**: "Import Projects from Data Source"
- **DataSource selector** (dropdown of Connected sources)
- After selection — Huginn calls the source API and lists what the token can see:
- **Available Projects table**:
  - Checkbox | Source name | Path/Slug | Description | Already imported? | Last activity (from source)
  - Search box: "Find project..."
  - Filter: Already imported (yes/no) | Activity (active in last 30 days)
- **Bulk action bar** (appears when ≥1 selected):
  - "N projects selected"
  - [Import Selected] (primary)
- **Post-import**:
  - For each imported Project:
    - Project record created in Huginn with status "Initial sync queued"
    - A Celery `initial_sync` job is dispatched
    - Default RoE = none (must be assigned in Act 3 / via Edit)
  - Banner on redirect: "N projects imported. Sync started. Assign a Rules of Engagement to receive SitReps."
  - Redirect → `PROJECTS-LIST+FIND-1`

**Re-import behavior**: Selecting an already-imported project is a no-op (checkbox disabled, "Already imported" badge shown).

#### Screen: PROJECTS-VIEW_PROJECT-1

**Layout** — tabbed page. Tabs are **system-defined** (not RoE-derived).

- **Header**: Project name + status badge + DataSource + **mode badge** (pill: `Semi-Auto` or `Auto`, matches the current `Project.gjallarhorn_mode`)
- **Vitals tab** (hardcoded, present on every Project):
  - **Identity**: source path, source URL, imported on, imported by
  - **RoE**: name + version (or "Not assigned" — link to assign)
  - **Sync**: last sync time, next scheduled, current status (idle / syncing / error); **Last SitRep generated**: timestamp + link to `SITREP-VIEW_SITREP-1` for the latest SitRep (shown as "—" when no SitRep exists yet). This is a separate line from "Last sync" — ingestion timing and AI evaluation timing are intentionally distinct.
  - **Transparency card**: hardcoded system-wide health signal — how stale are updates? (See `ingestion/adapters/` for the metric definition.)
  - **Informer bar**: one colored dot per `RulesOfEngagementVariable` on the active RoE version, in declared order. Value and color sourced from the **latest `VariableDatapoint`** for each Variable; hover shows `name (abbrev): value`. Grey dot when no datapoint exists for a Variable. When no RoE is assigned, the bar shows a placeholder ("No RoE assigned").
- **Variables tab**:
  - One diagram per `RulesOfEngagementVariable` on the active RoE version, showing all `VariableDatapoint` rows for the selected period.
  - **Period selector** (top-right, persistent): Last 2h / Last 4h / Last 8h / Today / Yesterday / This week / Previous week / 30 days / Custom datetime range. Default adapts to the project's sync cadence (see Act 7 for full spec).
  - Each diagram: Variable name + abbrev as title; Y-axis label = `y_axis_label` from the `VariableDatapoint` (set by Gjallarhorn at generation time, e.g. "increments", "commits"); X-axis = time over the selected period. Color of each data point reflects the `color` field from the `VariableDatapoint` (green / orange / red / grey).
  - Per-card affordances: [View in Chat] (Act 8) with Variable + period pre-loaded | [Create FRAGO from this] → `FRAGOS-CREATE_FRAGO-1` with Variable pre-selected | reasoning-trace drilldown (click a data point to open a right-rail panel showing the originating `VariableDatapoint` row + SitRep + originating **`PlanStep`** from the SitRep `ExecutionPlan`, collapsed by default).
  - Empty states: no RoE assigned → "No RoE assigned. Assign one in the Project view." | Rules of Engagement has no Variables → "This Rules of Engagement defines no Variables." | Variable has no history yet → "No SitReps yet" in place of the chart.
- **Increments tab** (contributed by `ingestion/adapters/gitlab_commits.py`): system-defined view of ingested commit/increment data. Layout and content defined by the adapter. Further adapter-driven tabs will appear here as new adapters land.
- Deep-link: `?tab=vitals` | `?tab=variables` | `?tab=increments` (or the adapter slug).
- Sync engine behavior (beat, idempotency, error states) is specified in `docs/features/act-2-projects/projects-sync-engine.feature`; architecture in `docs/architecture/SAO.md` §1 (Ingestion sync engine), §4, §7.
- **Top Actions**: [Edit] | [Sync Now] | [Generate SitRep ▾] | [Archive] | [Open SitReps] (→ Act 5) | **Mode toggle** — pill `[Semi-Auto | Auto]`, persists `Project.gjallarhorn_mode`. Tooltip on Auto: *"Gjallarhorn will execute Decisions without your approval."* Switching to Auto shows a confirmation modal: "Enable Autonomous mode? Gjallarhorn will auto-approve and execute Decisions for this project. You can switch back at any time."

  **[Generate SitRep ▾]** opens a small dropdown with period options:
  - **Since last SitRep** (default, pre-selected): covers `last_sitrep.generated_at → now`. Label shows the computed window, e.g. "Since last SitRep (3h 20m ago)". Disabled with tooltip "No previous SitRep — use a custom period" when none exists.
  - **Last 2 hours** | **Last 4 hours** | **Today** | **Yesterday** | **Custom…**
  - **Custom…** opens an inline datetime picker: `From` (date + time) and `To` (date + time, defaults to now). Both fields resolved to the minute.
  - Clicking any preset or confirming a custom range fires a `POST /projects/{slug}/sitreps/generate/` request. A toast appears: "SitRep generation started — this may take a moment." On completion the Vitals "Last SitRep generated" line updates and a notification links to the new SitRep.

#### Screen: PROJECTS-EDIT_PROJECT-1

Editable fields:
- Display name (Huginn-side label; source path is immutable)
- Assigned RoE (dropdown of Rules of Engagement; can also pick a specific version, default is "auto-track latest")
- Sync schedule: **`hourly` | `every 6h` | `daily`** — matches `Project.sync_schedule` in code (Celery fan-out every 15 minutes checks whether the project is due). Default: **hourly**.
- SitRep cadence: defaults to "match sync"; may be set to a coarser cadence when LLM cost must be bounded. *(Open question — see vision.md.)*
- [Save Changes] | [Cancel]

#### Screen: PROJECTS-ARCHIVE_PROJECT-1

Confirmation modal:
- "Archive 'company-gitlab/atlas-backend'?"
- "Syncs will stop. Ingested history is retained and can be browsed. Project will not appear on the Tactical Plot."
- [Archive] (warning) | [Cancel]

---

## Act 3: Rules of Engagement — CRUDLF (versioned)

**Context**: While the initial sync is running, Donland writes a Rules of Engagement. An RoE is **metadata** (name, description) + a **Workflow** (free-form markdown describing the OO/DA narrative — roles, who is who, what to look for) + an ordered list of **RulesOfEngagementVariables** (structured: `name`, `abbreviation`, `calculating`, `interpreting`, `hover`). **One Rules of Engagement can be assigned to many Projects.** Each Project pins a (Rules of Engagement, version); auto-tracks the latest version by default. Editing the Workflow OR any Variable creates a new version.

**Seed Rules of Engagement** (`FeatureFactory Rules of Engagement`): Huginn ships a default seed Rules of Engagement named **FeatureFactory Rules of Engagement**, pre-populated with:
- **Seven starter Variables** (Transparency, Throughput, Cycle & Lead Time, Rework, Quality, Complexity, Contribution), each with default `calculating`, `interpreting`, and `hover`.

Cloning **FeatureFactory Rules of Engagement** is the recommended starting point.

**Decisions Logic FRAGO relationship**: the Rules of Engagement defines what "good" looks like (authoritative expectations, Workflow, Variables). The per-Project **`Decisions Logic` FRAGO** (Act 6) is **one living document**: **most** Resolved Decisions (**Approved**, **Auto-approved**, **Rejected** where memory is warranted) deposit a structured line by default; Donland routinely **extends, merges, rewrites, or deletes** entries in that same FRAGO so future proposals reflect curated judgment—not a frozen append-only log. Rules of Engagement stays the stable template; Decisions Logic is **mutable** Commander–Gjallarhorn memory.

**Pattern**: CRUDLF, with version history per Rules of Engagement.

#### Screen: ROE-LIST+FIND-1

Donland clicks **Rules of Engagement** in the main nav.

**Layout**:
- **Header**: "Rules of Engagement" with count badge
- **Top Actions**: **[Import from Mimir]** (secondary outline, Mimir icon, disabled — MVP stub; IA toolbar) | **[+ New Rules of Engagement]** (primary → CREATE)
- **Filter**: Author | Used by Project (yes / no) | Updated within
- **Table**:
  - Name | Author | Latest version | Used by N projects | Updated
  - No visible **Actions** column; each row ends with a single overflow menu (⋯) for secondary commands (see `docs/ux/IA_guidelines.md` §5.2 — LIST+FIND Table).
- **Row navigation**:
  - **Name** links to `ROE-VIEW_ROE-1`
  - Overflow menu: **Edit** → `ROE-EDIT_ROE-1` (creates a new version on save) | **Clone to new Rules of Engagement** → `ROE-CREATE_ROE-1` pre-filled | **Delete** → `ROE-DELETE_ROE-1` when unused (disabled with reason when any Project uses this Rules of Engagement)
- **Empty State**: "No Rules of Engagement yet. Write one to define expectations for your Projects."

#### Screen: ROE-CREATE_ROE-1

**Layout** — three regions, top to bottom:

- **Header**: "New Rules of Engagement" | [Clone from seed Rules of Engagement] (shortcut)

- **1. Metadata**:
  - Name (required)
  - Description (one line, optional)

- **2. Workflow** (markdown):
  - Markdown editor (full-height, monospace) with side-by-side rendered preview
  - Describes the OO/DA narrative for projects on this Rules of Engagement — who is who, what good looks like, what to look out for
  - Read by Gjallarhorn alongside the structured Variables when generating SitReps
  - **Future**: [Import from Mimir] (out of MVP)

- **3. Variables** (structured, ordered list):
  - Editable table with columns: drag-handle | **Name** | **Abbrev** | **Calculating** | **Interpreting** | **Hover** | row actions
    - **Name**: e.g., "Cycle Time"
    - **Abbrev**: e.g., "CT"
    - **Calculating**: free-text — JQL, count/ratio expression, or natural-language prompt; the Agent decides how to apply
    - **Interpreting**: free-text mapping value → color, e.g. *"<5d & not climbing → green; climbing → orange; >5d → red"*
    - **Hover**: tooltip text shown on the project card and SitRep snapshot
  - [+ Add Variable] button (primary, below the table)
  - Row actions: [Duplicate] | [Remove]
  - Drag-handle reorders rows; order is preserved on save and determines the order Variables appear in the informer bar and on the Variables tab.

- **Top Actions**: [Save as v1] (primary) | [Cancel]

#### Screen: ROE-VIEW_ROE-1

**Layout** (matches Project detail tab pattern — `hg-detail-tabs-card` + `nav-tabs card-header-tabs`):

- **Tabs**
  - **Rules of Engagement** — read-only snapshot for the version in focus (default: **latest**): Metadata, Workflow (rendered markdown), Variables table, **Used by** (Projects + tracking indicator with links to `PROJECTS-VIEW_PROJECT-1`).
  - **Versions** — immutable version log: vN, date, author, change summary (newest first); **[Compare with current]** when wired (diff across Workflow and Variables). Selecting a prior version to hydrate the Rules of Engagement tab is product wiring (navigation may use query params or in-page state).

- **Top Actions** (header toolbar): **[Clone]** | **[Edit]**

#### Screen: ROE-EDIT_ROE-1

Same three-region form as CREATE (Metadata, Workflow, Variables), pre-populated with the latest version's content. Adds:
- "Change summary" field (required) — shown in version log
- [Save as v(N+1)] — never overwrites; always creates a new version

Editing semantics:
- Workflow markdown edits are tracked diff-style.
- Variables edits (add / remove / reorder / change any field) all contribute to the new version. The Variables snapshot for v(N+1) is the full edited list.

On save:
- New version becomes "latest"
- Projects auto-tracking this Rules of Engagement will use the new Variables and Workflow on their **next SitRep generation** (does not re-run past SitReps; existing SitReps keep their `variables_snapshot`)
- Pinned Projects keep their pinned version
- Removing a Variable does **not** delete its existing `VariableDatapoint` history — the trend is preserved for audit but the Variable simply stops appearing on new SitReps and on the Variables tab.

#### Screen: ROE-DELETE_ROE-1

Confirmation modal:
- "Delete 'FeatureFactory Rules of Engagement'?"
- If used by 0 Projects: [Delete] available
- If used by N Projects: "Used by N project(s). Reassign or archive those projects first." (Delete disabled)

---

## End of Inception

After Inception:
- ≥1 DataSource connected
- ≥1 Project imported and synced (initial dump complete)
- ≥1 Rules of Engagement authored and assigned to each Project
- **Trigger**: when a Project's initial sync completes AND it has a Rules of Engagement assigned, Gjallarhorn fires its first SitRep generation. The Project is now ready for Calibration (Act 4 onward).

---

# CALIBRATION

The daily loop. Donland opens Huginn, scans the **Tactical Plot**, drills into anything red or orange. He reads the SitRep, adjusts expectations via FRAGOs when reality and Rules of Engagement diverge for legitimate reasons, browses Variables to understand the trend, and questions Gjallarhorn directly when he needs an answer the SitRep didn't provide.

---

## Act 4: Projects Dashboard (Tactical Plot)

**Context**: This is the **daily landing screen** after login. Donland sees every active Project at a glance: dominant **health** colour, latest **SitRep** access, variable strip, and sync/RoE footers. **Two presentations exist today:**
- **HTML mock** (`ui/templates/ui/mockups/dashboard/projects.html`): title **Tactical Plot**; **card grid** (main) + **right sidebar** (Situational Awareness list, FRAGOs in effect, **Manage projects →**). Specified in `docs/features/act-4-dashboard/dashboard-projects.feature`.
- **Operational Tactical Plot** (`ui/templates/ui/dashboard/projects.html`): **four-column** xl layout (Situational Awareness | FRAGOs | compact **Projects** list | Decisions/Tasks stubs). Card-grid affordances below are the **target** for per-project richness on the shipped plot as parity improves.

**Pattern**: Single-screen dashboard. Read-only aggregate view; all detail lives one click away.

#### Screen: DASHBOARD-PROJECTS-1

**Layout — Tactical Plot header (mock + intent)**:
- **Title**: **Tactical Plot** (not "Projects"; that name is reserved for Act 2 management list).
- **Subcopy**: last refreshed / sync freshness (mock uses static example copy; operational uses `naturaltime` on latest sync).
- **Summary strip**: counts by **health** colour (red / orange / yellow / green), e.g. `N red · N orange · …` (mock renders from `summary_strip`; semi-auto vs auto mode counts are **not** on the mock cards today).
- **Toolbar**: refresh control (icon button; may be disabled stub on operational).

**Layout — project cards (HTML mock; target for rich plot cells)**:
- **Colour bar** (top edge, full-width): same hue as dominant health.
- **Title row**: **Project name** + DataSource icon(s) + **health badge** pill (capitalised label: Red / Orange / Yellow / Green — dominant assessment from latest SitRep / variables). *(Gjallarhorn **Semi-Auto / Auto** mode pill is not shown on the current mock card.)*
- **Headline**: one line under the title (latest SitRep narrative summary, e.g. "All monitored expectations met").
- **SitRep micro-subcard** (`data-testid="project-card-{id}-sitrep-pill"`): compact **list-item style** block — left **primary accent** bar, soft **icon tile** (`fa-display-chart-up-circle-currency`), stacked **title** (latest SitRep headline as link → `SITREP-VIEW_SITREP-1`) and **meta row** (“Last SitRep” kicker + generation time). `z-2` above the card stretched link so the title link stays clickable. When none: muted icon tile + **No SitRep yet** (no link).
- **Variables mini-strip**: abbreviations + coloured dots (tooltips); mock uses master-variable keys Tr, Tp, C, R, Q, X, Co.
- **Footer**: last sync line (icon OK/warn) + RoE name + auto-track ⟳ vs pinned 📌 icon.

**Navigation**:
- **Card stretched link** (mock): opens `PROJECTS-VIEW_PROJECT-1` for that project (whole card except intractable inner controls).
- **SitRep headline link** (inside the subcard): opens `SITREP-VIEW_SITREP-1` for that SitRep (overrides card link).

**Right column (mock only)**:
- **Situational Awareness** — short global event list (links to SA view).
- **FRAGOs** — in-effect list with scope labels.
- **Manage projects →** → `PROJECTS-LIST+FIND-1`.

**Future / operational rails** (not in the HTML card mock): aggregated **DataSource connection issues** and **FRAGOs triggered since last visit** may appear on the shipped Tactical Plot or global workspace chrome as those surfaces land.

**Colour semantics** (unchanged intent):
- **Red**: ≥1 RulesOfEngagementVariable's `interpreting` rule yielded red at the latest SitRep (with active FRAGOs applied), OR Project has no SitRep yet (initial sync incomplete or no Rules of Engagement assigned)
- **Orange**: ≥1 RulesOfEngagementVariable's `interpreting` yielded orange at the latest SitRep, no red
- **Yellow**: ≥1 RulesOfEngagementVariable's `interpreting` yielded yellow at the latest SitRep, no orange/red
- **Green**: all monitored expectations met

**Empty state** (no Projects imported): CTA toward Act 2 import (wording may differ mock vs operational).

**Operational-only note**: the shipped Tactical Plot **Projects** column is currently a **list-group** of rows (name, path, sync badge, GitLab description), not the rich `hg-card` grid — reconcile UX by evolving the list toward the mock card contract above.

---

## Act 5: SitRep / Status Report

**Context**: A SitRep is what Gjallarhorn produces after a sync completes or when requested manually. It is **per Project, per assessed period**. SitReps are read-only once finalized — they are a frozen record of what Gjallarhorn saw over `period: [from_dt, to_dt]` against Rules of Engagement version V.

**Generation triggers**:
- **Automatic**: fired by the `Sync Complete` event after each successful ingestion run, using a default period of `last_sitrep.generated_at → sync_completed_at` (i.e., everything new since the previous SitRep). If no prior SitRep exists, the default period is the full ingestion history.
- **Manual**: Commander clicks [Generate SitRep ▾] on `PROJECTS-VIEW_PROJECT-1` and selects a period — either the "Since last SitRep" default or a custom `from_dt → to_dt` window (supports hour-level granularity: "last 2 hours", "last 4 hours", "today", "yesterday", or a custom datetime range).

**Generation contract**: Gjallarhorn assembles `(SituationalAwareness, active Rules of Engagement workflow + variables, enabled in-window FRAGOs, data: {period: [from_dt, to_dt], …})` and runs a **multi-step `ExecutionPlan`**. The plan structure is:
1. **Data-collection steps** — fetch commits, contributor activity, active FRAGOs, Situational Awareness (tool calls, no LLM; execution model used where applicable).
2. **Per-Variable assessment steps** — one LLM step per `RulesOfEngagementVariable` using the **execution model** (Sonnet): applies the Variable's `calculating` + `interpreting` rules to the gathered data and produces a `value` (string) and traffic-light `color` (`green` / `orange` / `red` / `grey` — `grey` means the variable could not be computed, e.g. data unavailable).
3. **Narrative-composition step** — uses the **planning model** (Opus): synthesises headline, situation assessment, notable activity, and aggregates the computed datapoints.

The full output emitted by the narrative-composition step:
```json
{
  "headline": "…",
  "situation_assessment": "…",
  "notable_activity": […],
  "datapoints": [
    { "variable_name": "Throughput", "y_axis_label": "increments", "value": "15", "color": "green" },
    { "variable_name": "Commits",    "y_axis_label": "commits",    "value": "12", "color": "orange" }
  ]
}
```

The `datapoints` array is written into `SitRep.variables_snapshot` (canonical, immutable JSON — the frozen record of what Gjallarhorn computed at generation time) and denormalized into `VariableDatapoint` rows — one row per `RulesOfEngagementVariable` per SitRep — which power the Variables tab trend charts and the Vitals informer bar. Each `VariableDatapoint` stores `variable_name`, `y_axis_label`, `value`, `color`, `from_dt`, `to_dt` (period boundaries from the SitRep), and a FK to its producing **`PlanStep`** for full reasoning traceability. Within a plan run, tool results are cached by argument hash so the same data source (e.g. `list_commits`) is fetched only once across all steps (SAO §17.6).

**Pattern**: LIST+FIND + VIEW. No user-initiated CREATE form (generation is triggered via [Generate SitRep] on the Project view), no EDIT (frozen), no DELETE (audit log).

#### Screen: SITREP-LIST+FIND-1

Donland clicks a Project card on the Dashboard, or **SitReps** from the Project view.

**Layout**:
- **Header**: "SitReps — atlas-backend"
- **Top Actions**: **[Generate SitRep ▾]** — same period-picker dropdown as on `PROJECTS-VIEW_PROJECT-1` (see Act 2). Provides a shortcut so the Commander can trigger generation without navigating away from the SitRep list.
- **History table** (newest first by default; there is **no** separate pinned "latest SitRep" card — the first row is the latest):
  - Columns: Generated at | Assessed period | Trigger (Auto / Manual) | Status | **Variables** (colored dot strip from `variables_snapshot` — one dot per RoE Variable, tooltip shows `name (abbrev): value`) | Headline | Decisions proposed | Decisions accepted | Rules of Engagement version | Actions
  - Filter: status, date range, Rules of Engagement version, trigger type
  - **Generating row** — when an `ExecutionPlan` for this project has `sitrep_from_dt` set and `status ∈ {pending, running, waiting_retry}` and no corresponding `SitRep` exists yet, a row floats at the top of the table (above completed rows): `Generated at = "—"`, assessed period from `sitrep_from_dt → sitrep_to_dt`, Trigger badge, **Status = amber spinner badge "Generating… (N/M steps)"** where N/M come from `progress_current/progress_total`, `Headline = "—"`. No View action — generation is in progress.
  - **Failed row** — when a plan terminates with `status=failed` and no `SitRep` was written, the row remains in the table: `Generated at = plan.created_at`, period from `sitrep_from_dt → sitrep_to_dt`, Trigger badge, **Status = red "Failed" badge**, error reason from `ExecutionPlan.last_error` truncated to ~80 chars in the Headline cell. **Row Actions = [View in Chat]** linking to that plan's `Conversation` (where `_notify_ai_of_plan_failure` posted the recovery analysis with partial results and next-step options).
  - **Completed SitRep row** — the normal case once a `SitRep` record exists: all columns populated. **Row Actions = [View]** → `SITREP-VIEW_SITREP-1`.
- **Empty State**: "No SitReps yet. Gjallarhorn generates the first SitRep when initial sync completes and a Rules of Engagement is assigned. You can also generate one manually using [Generate SitRep ▾] above."

#### Screen: SITREP-VIEW_SITREP-1

Donland opens a SitRep from the list (headline link or row **View**), or follows **Open SitRep** from another screen (for example the Project view).

**Layout** (read-only document, multi-section):

- **Header**:
  - Project | Date generated | **Assessed period** (`from_dt → to_dt`, displayed in local timezone; e.g., "Mon 09:00 → 13:15" for a 4-hour window, or "2026-04-19 09:00 → 2026-04-20 09:00" for a daily window) | **Trigger** badge (Auto / Manual) | Rules of Engagement version evaluated against | Overall status badge | **Mode at generation** indicator (Semi-Auto / Auto — records which mode was active when Gjallarhorn ran; explains whether Decisions were proposed or already auto-approved)
  - [Open Decisions] (primary, jumps to Decisions section) | [Open Variables] (jumps to Variables section) | [Generate SitRep for another period ▾] (secondary — same period picker, pre-selects "Since this SitRep")

- **Section 1 — Situation Assessment**:
  - Overall status (red/orange/yellow/green) with one-paragraph narrative
  - Example: *"RED — Milestone v1.21 supposed to ship Monday, but still 3 critical bugs open. Rules of Engagement expects Active Bug Count = 0 at all times; current value is 3."*
  - Key breaches list: each shows Variable name → expected vs. actual → severity badge → link to Variable deep-dive (Act 7)

- **Section 2 — Variables Snapshot**:
  - One row per `RulesOfEngagementVariable` on the evaluated RoE version, rendered from `SitRep.variables_snapshot` (canonical, immutable JSON — the exact `datapoints` array Gjallarhorn emitted at generation time; not re-computed on read).
  - Columns: **Name (abbrev)** | **Y-axis label** | **Value** | **Color** (traffic-light: green / orange / red / grey) | Δ vs. previous SitRep
  - When a Variable's value could not be computed (`color = grey`), the row renders `value = —`.
  - Each row links to `VARIABLES-VIEW-1` (Act 7 / Variables tab) filtered to that Variable.

- **Section 3 — Decisions**:
  - List of Decisions Gjallarhorn generated based on the assessment. In Semi-Auto these are `Proposed`; in Autonomous mode they may already be `Auto-approved` and executed by the time the SitRep is viewed.
  - Each Decision shown as a card: title + status badge (`Proposed` / `Auto-approved`) + Owner attribution + rationale (2–4 sentences) + **Outcome options** as a radio list (2–N proposed calibrations/dispatches + **Type your own**) + [Review →] button
  - [Review] → `DECISIONS-VIEW_DECISION-1` (Act 9) where the Outcome chooser and approval flow live

- **Section 4 — FRAGOs applied**:
  - Which FRAGOs Gjallarhorn applied to this evaluation (i.e., enabled and in effective window at generation time; e.g., "Active Bug Count expected to be 0 — belay on Fridays, ≤3 OK")
  - Helps explain why the assessment is what it is — and conversely, deactivated/expired FRAGOs are *not* listed here, which makes "what changed when I toggled X" easy to verify
  - Links to Act 6

- **Section 5 — Notable activity since last SitRep** (optional):
  - "Who did what" summary: Increments, closed UoWs, state changes worth noting
  - Anomalies (e.g., "Anton: 0 commits — first time in 14 days")

**Top-right utility**:
- [Open Chat about this SitRep] → `CHAT-FULLSCREEN-1` (Act 8) with this SitRep pre-loaded as context

---

## Act 6: FRAGO — CRUDLF (Rules of Engagement adjustment)

**Context**: A FRAGO is an **in-flight adjustment to the Rules of Engagement** that the active Rules of Engagement version doesn't capture. When reality and Rules of Engagement disagree for a legitimate reason, Donland creates a FRAGO instead of editing the Rules of Engagement itself. Examples:
- *"Active Bug Count expected to be 0 — belay that on Fridays; up to 3 bugs OK on Fri."*
- *"Disregard broken builds tomorrow — known infra outage."*
- *"Cycle time threshold ≤ 5 days suspended for Sprint 47 (holiday week)."*

A FRAGO is **a short markdown body** scoped to one Project, with an optional time/scope filter (day-of-week, date range, Sprint/Milestone) and an optional **Affects** designation (Narrative or Variable(s)). When set to Variable(s), the FRAGO retunes that Variable's `interpreting` rule for the effective window; it cannot introduce new variables. When Gjallarhorn generates a SitRep, it reads **enabled FRAGOs that are currently in their effective window** alongside the Rules of Engagement (Workflow + Variables) and reconciles them in the assessment — both human-authored, both natural language.

**Activate / Deactivate**: each FRAGO has an `enabled` flag the Commander can toggle from the list or detail screen. **Deactivated FRAGOs are not consumed by Gjallarhorn** when producing SitReps, regardless of their effective window. Useful for short-term suspension without losing the FRAGO's context — re-enable to resume. Distinct from **Revoke** (which is soft-delete; revoked FRAGOs cannot be re-enabled).

**Pattern**: CRUDLF + Activate/Deactivate. FRAGOs are user-created, editable, enable/disable-toggleable, and revocable (soft-delete, history preserved).

**"Decisions Logic" FRAGO (special, system-managed)**: **Exactly one** per Project (`kind = decisions_logic`). Created automatically when the **first** qualifying Decision review produces a structured line (**Approved**, **Auto-approved**, **Rejected** with material to record — Act 9; **bare** reject skips). Not user-creatable as a duplicate, not revocable, not toggleable — always Active. The **markdown body** holds judgment memory **read verbatim** by Gjallarhorn on the next invocation.

- **Title** is fixed: *"Decisions Logic — {project name}"*.
- **Body** — primarily **structured lines**, one markdown bullet **in most cases** (canonical template documented in SAO §17.8 — fields inline with ` · ` separators). Example: `- **2026-05-11 14:03** · Decision: *Coverage gate* · Owner: **Donland** · **Approved** · Reasoning: *Ship quality bar before refactor* · Dispatch: Jira **HUGINN-302**`. Exceptions: omit line when nothing should be preserved (Act 9). Commander **maintains one document**: add free-form preamble, consolidate several bullets into one summary, rewrite wording, drop obsolete noise — **`FRAGOS-EDIT_FRAGO-1`**; edits surface in **`django-simple-history`** like any other FRAGO.
- **Prompt caching**: the Decisions Logic FRAGO body is part of the cached context Gjallarhorn keeps for the Project, meaning changes land on the very next SitRep without any extra cost.
- Visually pinned at the top of `FRAGOS-LIST+FIND-1` with a distinct icon (e.g., a brain or logic node); toggle column and `[Revoke]` row action are absent for this row.

**Project scope (mandatory in the UI)**
Every FRAGO belongs to exactly one **Project**. Operational screens **must not** infer project from session cookies, navbar memory, or implicit defaults.

- **Explicit context**: Any template that renders FRAGO links receives `project_slug` / `?project=` from **that screen's view** when linking from a scoped surface (Project view, SitRep, filtered list, etc.).
- **Create FRAGO**: **New FRAGO** opens the create screen. Deep links may append `?project=…` to **pre-select** Project; the create form always exposes a **required Project** control so the Commander can confirm or change the target before save. Visiting create **without** `?project=` still shows the form (no redirect solely for a missing query param).
- **Main nav → FRAGOs** lands on the list in **all-projects** mode until a Project filter narrows the table; deep links from elsewhere carry `?project=<slug>` where applicable.

#### Screen: FRAGOS-LIST+FIND-1

Donland clicks **FRAGOs** in the main nav (or [+ New FRAGO from this expectation] from a SitRep breach card — SitRep supplies `project`; or **Add FRAGO** from `PROJECTS-VIEW_PROJECT-1`).

**Layout**:
- **Header**: "FRAGOs — &lt;project name&gt;" when filtered by one Project; **"FRAGOs — All projects"** when unscoped
- **Top Actions**: **[+ New FRAGO]** → create screen; when the list is scoped with `?project=…`, the same parameter is appended for convenience so Project is pre-selected on the form
- **Filter**: Project | Timing (In Effect, Scheduled, Past) | Status (Active, Disabled, Revoked) | Affects (Narrative, Variable(s)); operational list may add query-backed filters separately
- **Pinned row — "Decisions Logic"**: when the list is scoped to a single Project and that Project has a Decisions Logic FRAGO, this row always appears first, visually distinct (brain/logic icon, shaded background). It has no toggle switch (always Active) and no `[Revoke]` action. Row Actions are limited to **[View]** and **[Edit]**. Not selectable for bulk actions.
- **Table** (remaining rows):
  - Toggle | Title | Affects | Effective window | Status | Actions
- **Toggle column** (leftmost): per-row enable/disable switch (`data-testid="frago-toggle-{id}"`). Click flips the `enabled` flag — no confirmation modal (action is reversible). On flip:
  - Status badge updates immediately
  - Toast confirmation: "Deactivated 'Belay Active Bug Count = 0 on Fridays' — Gjallarhorn will skip this FRAGO on the next SitRep."
  - Toggle is disabled for Revoked rows (cannot re-enable a revoked FRAGO)
- **Status badges** (computed):
  - **Active** (green) — `enabled AND in effective window` — Gjallarhorn applies it
  - **Inactive** (grey, dimmed) — `enabled = false` — Gjallarhorn skips it
  - **Scheduled** (blue) — `enabled AND start_date in future` — Gjallarhorn skips until window opens
  - **Expired** (grey) — `enabled AND end_date in past` — Gjallarhorn skips
  - **Revoked** (grey strikethrough) — soft-deleted; no longer in evaluation
- **Bulk actions** (appear when ≥1 row selected via checkbox):
  - [Activate selected] | [Deactivate selected] | [Revoke selected]
- **Row Actions** (dropdown):
  - [View] → `FRAGOS-VIEW_FRAGO-1`
  - [Edit] → `FRAGOS-EDIT_FRAGO-1`
  - [Activate] / [Deactivate] (mirrors the toggle, redundant for accessibility / keyboard users)
  - [Revoke] → `FRAGOS-REVOKE_FRAGO-1` (labelled Revoke, not Delete; soft-delete)
- **Empty State**: "No FRAGOs. Create one to override Rules of Engagement expectations for known temporary conditions."

#### Screen: FRAGOS-CREATE_FRAGO-1

Donland opens **New FRAGO** from the list or another surface. Links often include `?project=…` to **pre-select** Project (scoped FRAGO list, Project **Add FRAGO**, SitRep, Decision). The Commander **always picks or confirms Project on this form**; SitRep / Decision flows may still pre-fill other fields (e.g. Affects).

Note: the **"Decisions Logic"** FRAGO (`kind = decisions_logic`) is system-managed and cannot be user-created through this form. It appears when the Project's **first qualifying structured line** is recorded (Act 9). This create form always creates a `kind = general` FRAGO.

**Layout**:
- **Header**: "New FRAGO"
- **Form**:
  - **Project** (required, **dropdown**) — choose target Project; pre-filled when `?project=` is present
  - Title (required) — e.g., "Belay Active Bug Count = 0 on Fridays"
  - **Body** (markdown) — the FRAGO content. Free-form natural language. Gjallarhorn reads this alongside the Rules of Engagement when generating SitReps.
  - **Affects** (optional, single-select): **Narrative** — global context override, Gjallarhorn reads it alongside the Workflow; **Variable(s)** — retunes the interpreting rule for one or more Rules of Engagement Variables for the effective window.
  - **Scope filter** (optional):
    - Day-of-week: any combination of Mon–Sun
    - Date range: from / to (either or both optional)
    - Sprint / Milestone: dropdown
  - [Save FRAGO] | [Cancel]

#### Screen: FRAGOS-VIEW_FRAGO-1

**Layout**:
- Title | Status badge | Affects (if any)
- **Enable toggle** (header, prominent): switch labelled "Enabled" / "Disabled". Same semantics as the list toggle — flipping it changes whether Gjallarhorn applies the FRAGO on the next SitRep. Disabled when status = Revoked.
- Body (rendered markdown)
- Effective window
- **Application history**: list of SitReps where this FRAGO was applied (date, link to SitRep). Useful to verify activation/deactivation took effect — a deactivated FRAGO will not appear in subsequent SitReps' history.
- **State change log**: chronological log of toggles and edits (timestamp, action, actor) — backed by **`django-simple-history`** on the FRAGO model (diff-friendly)
- [Edit] | [Revoke]

#### Screen: FRAGOS-EDIT_FRAGO-1

Same form as CREATE, pre-populated. Editing is allowed — change is timestamped in history. [Save Changes] | [Cancel].

#### Screen: FRAGOS-REVOKE_FRAGO-1

Confirmation modal:
- "Revoke 'Belay Active Bug Count = 0 on Fridays'?"
- "Future SitReps will evaluate the underlying Rules of Engagement expectation as written. Existing SitReps that referenced this FRAGO are unchanged."
- [Revoke] (warning) | [Cancel]

---

## Act 7: Variables Tab

**Context**: The Variables tab lives on `PROJECTS-VIEW_PROJECT-1` (Act 2). Donland arrives here from a SitRep breach link, from the informer bar on Vitals, or directly by clicking the Variables tab on a Project. This tab shows every RulesOfEngagementVariable on the active RoE version as a time-series diagram derived from `VariableDatapoint` history. Read-only — values come from SitReps, history from VariableDatapoint rows.

**Pattern**: VIEW with period filter. No CREATE/EDIT/DELETE. Screen ID `VARIABLES-VIEW-1` is retained for cross-references.

#### Screen: VARIABLES-VIEW-1

**Layout**:
- **Header**: "Variables" (within the Project page header — "Variables — atlas-backend") + active RoE version indicator
- **Period selector** (top-right, persistent):
  - **Sub-day**: Last 2 hours | Last 4 hours | Last 8 hours
  - **Day-level**: Today | Yesterday | This week | Previous week | 30 days
  - **Custom…**: datetime range picker (`from_dt` / `to_dt`, resolved to the minute)
  - Default: Today (switches automatically to **Last 4 hours** when the project sync cadence is **hourly** so sub-day resolution stays meaningful — `every 6h`/daily presets still favor day-scale windows unless the Commander picks sub-day manually)
- **Variable diagrams** (grid, one card per RulesOfEngagementVariable on the active RoE version, in declared order):
  - **Card header**: Name (abbrev) + latest value (from most recent `VariableDatapoint` in the selected period) + color band (`green` / `orange` / `red` / `grey`)
  - **Diagram**: line chart — Y-axis label = `y_axis_label` from `VariableDatapoint`; X-axis = time over the selected period; color of each data point = `VariableDatapoint.color` (green / orange / red / grey)
  - **Calculating** (collapsed by default): the Variable's `calculating` text — JQL, expression, or prompt
  - **Interpreting**: the Variable's `interpreting` rules, with overlay showing any FRAGO overrides currently in effect
- **Per-card affordances**:
  - Click a data point → drill-down panel (right rail) showing that datapoint's `VariableDatapoint` row (with its `from_dt → to_dt` period) + the originating SitRep + the originating **`PlanStep`** (collapsed by default; expands to pre/post reasoning + tool trace for that SitRep execution step)
  - [View in Chat] → opens `CHAT-FULLSCREEN-1` with the Variable + period pre-loaded as context
  - [Create FRAGO from this] → `FRAGOS-CREATE_FRAGO-1` with this RulesOfEngagementVariable pre-selected as the tag
- **Variable-level affordances**:
  - "Edit Variable in Rules of Engagement" link → `ROE-EDIT_ROE-1` (or pin warning if Project pins an old version)
- **Empty states**:
  - Project has no assigned Rules of Engagement → "No Rules of Engagement assigned. Assign one in the Project view."
  - Rules of Engagement has no Variables → "This Rules of Engagement defines no Variables. Add some in `ROE-EDIT_ROE-1`."
  - A Variable has no VariableDatapoint history yet → diagram area shows "No SitReps yet" instead of an empty chart.

---

## Act 8: Gjallarhorn Chat

**Context**: When the SitRep doesn't answer Donland's question, he opens the chat. Gjallarhorn has CRUDL access to the platform via `services.py` / `tool_executor.py` and can search, list, and inspect any entity in the user's context. Chat is available in two modes: a persistent collapsible sidebar on every screen, and a full-screen surface for richer exploration.

**Pattern**: CHAT (conversational). Non-CRUDLF. Two screen IDs: `CHAT-SIDEBAR-1` (global rail) and `CHAT-FULLSCREEN-1` (two-pane dedicated surface).

#### Screen: CHAT-SIDEBAR-1

**Context**: A collapsible right rail, part of the global layout. Available on every screen. Default state is collapsed. Within the Commander's workspace, **messages live in separate threads per `(user, Project)` pair** — the rail always displays the Conversation for whichever Project navigation most recently anchored context (explicit Project selector overrides when needed). Persisted pinned context survives navigation **within that same Project**.

**Layout** (single-pane, narrow):
- **Header bar**: "Gjallarhorn" + [Expand ↗] button (opens `CHAT-FULLSCREEN-1`) + [×] collapse button
- **Context chip** (top of thread): auto-updates to reflect the current screen — e.g., "Viewing: SitRep 2026-04-20 09:15 · atlas-backend". Clicking the chip opens the referenced entity in its own screen. Pinned context items (manually attached by the user) appear below the auto-chip and persist across navigation.
- **Message thread** (scrollable):
  - User messages (right-aligned)
  - Gjallarhorn messages (left-aligned, AI badge)
  - Tool-call traces collapsed by default (one-line summary: "Used `list_uows` → 14 results")
  - **PlanProgressCard** (when Gjallarhorn is running a multi-step Plan): collapsible card embedded in the thread showing the Plan goal, progress bar (`3 / 9 steps`), and live step list. Each step: status icon (○ pending / ⟳ running / ✓ done / ✗ failed / ⏸ waiting) + action description + pre-execution reasoning (pending/running steps) or result summary (completed steps) or error (failed/waiting steps). Card collapses to a one-line summary when minimised. Updates live via SSE stream as steps complete (`plan_step_update` events on the conversation stream).
    - **Rate-limit retry** (`⏸ waiting`): if Claude returns 429 during a step, the step shows `⏸ waiting (retry in 30s)` and a status message appears in the thread below the card: *"Hmm, I'm thinking… Give me 30 seconds to gather my thoughts."* Gjallarhorn retries with exponential backoff (30 s → 60 s → 120 s at the LLM level; up to 5 Celery-level task retries). Completed steps are never re-executed — execution resumes from the paused step. When the retry succeeds the card resumes normally; if all retries are exhausted the step transitions to `✗ failed` and the permanent-failure flow kicks in.
    - **Permanent step failure** (e.g. GitLab data not yet available, tool error): the failed step shows `✗ failed` + error text. The card's overall state changes to `Failed`. Gjallarhorn immediately posts a **recovery message** in the thread below the card containing: how many steps completed before the failure, what the failing step was trying to do, and a concrete proposal — e.g. *"I couldn't fetch commits — the GitLab sync may not have run yet. Options: (1) wait for the next sync and re-trigger the SitRep, (2) I can generate a partial SitRep from the data I already collected."* The Commander responds in Chat; Gjallarhorn may create a revised Plan if needed.
  - Citations render as clickable chips
- **Input box** at bottom: textarea + [Send] + [Attach context] (pin a SitRep, FRAGO, Variable, etc.)

**Behavior**:
- Opening the sidebar from any screen restores the Conversation for **the Project currently in focus**; the context chip updates with the routed screen.
- `[Expand ↗]` opens `CHAT-FULLSCREEN-1` in the same tab, carrying **the active Project conversation** plus all pinned context.
- Same tool inventory and citation behavior as full-screen.

#### Screen: CHAT-FULLSCREEN-1

**Context**: Full-screen two-pane chat surface. Donland arrives here from `[Expand ↗]` on the sidebar, from "Open Chat about this SitRep" on a SitRep, or from "View in Chat" on a Variable card. Context (SitRep, Variable + period) is pre-loaded when arriving from another screen.

**Layout** (two-pane):

**Left — Conversation**:
- Project selector at top (defaults to last-viewed Project)
- Pre-loaded context chip (when arriving from another screen): e.g., "SitRep 2026-04-20 09:15" or "Variable: Active Bug Count, Last 2 weeks" — clickable to open
- Message thread:
  - User messages (right-aligned)
  - Gjallarhorn messages (left-aligned, AI badge)
  - **Tool-call traces** (collapsible) below each Gjallarhorn message that used tools — shows which tool(s) were called, their args, and result counts. Donland can expand to inspect.
  - **PlanProgressCard** (when Gjallarhorn is running a multi-step Plan): collapsible card embedded in the thread showing the Plan goal, progress bar (`3 / 9 steps`), and live step list. Each step: status icon (○ pending / ⟳ running / ✓ done / ✗ failed / ⏸ waiting) + action description + pre-execution reasoning (pending/running steps) or result summary (completed steps) or error (failed/waiting steps). Card collapses to a one-line summary when minimised. Updates live via SSE stream as steps complete (`plan_step_update` events on the conversation stream).
    - **Rate-limit retry** (`⏸ waiting`): if Claude returns 429 during a step, the step shows `⏸ waiting (retry in 30s)` and a status message appears in the thread below the card: *"Hmm, I'm thinking… Give me 30 seconds to gather my thoughts."* Gjallarhorn retries with exponential backoff (30 s → 60 s → 120 s at the LLM level; up to 5 Celery-level task retries). Completed steps are never re-executed — execution resumes from the paused step. When the retry succeeds the card resumes normally; if all retries are exhausted the step transitions to `✗ failed` and the permanent-failure flow kicks in.
    - **Permanent step failure** (e.g. GitLab data not yet available, tool error): the failed step shows `✗ failed` + error text. The card's overall state changes to `Failed`. Gjallarhorn immediately posts a **recovery message** in the thread below the card containing: how many steps completed before the failure, what the failing step was trying to do, and a concrete proposal — e.g. *"I couldn't fetch commits — the GitLab sync may not have run yet. Options: (1) wait for the next sync and re-trigger the SitRep, (2) I can generate a partial SitRep from the data I already collected."* The Commander responds in Chat; Gjallarhorn may create a revised Plan if needed.
  - Citations: when Gjallarhorn references entities (UoW, Contributor, SitRep, Variable datapoint), they render as clickable chips → open the entity's view screen
- Input box at bottom: textarea + [Send] button + [Attach context] dropdown (manually pin a SitRep, FRAGO, etc. as additional context)

**Right — Context panel** (collapsible):
- **Active Project**: name, status, Rules of Engagement
- **Pinned context**: items the user attached (SitRep, Variable view, etc.)
- **Recent entities seen in this conversation** (auto-tracked) — quick-jump links
- **Tool inventory** — list of tools available to Gjallarhorn (collapsible reference) so Donland understands what's possible. Examples: `list_uows`, `find_uows` (full-text), `get_contributor`, `list_increments`, `get_sitrep`, `list_decisions`, `find_artifacts`, etc.

**Behavior notes**:
- Lists in tool results support pagination (page size, page number) and filters — Gjallarhorn passes through to the user when results are large
- `find_*` tools are full-text search across the relevant entity
- Read-only by default in MVP; if/when write tools are exposed (e.g., create FRAGO from chat) they require explicit user confirmation in the chat (confirmation card with [Confirm] / [Cancel])

**Example exchange** (illustrative):
- Donland: "What happens to the open bug trend over the last 2 weeks? Do we close at the same rate as we open?"
- Gjallarhorn (uses `list_uows(filter='bug', date_range='last_2_weeks')` and `list_increments(...)`):
  *"Over the last 2 weeks, you opened 28 bugs and closed 26. Same-day close rate is 78%. The 2-bug carry is concentrated in Friday afternoon (5 of 6 carries opened after 15:00 on Fridays, closed Mondays)."*

---

# ACTION

Donland has read the situation, calibrated expectations, and asked his questions. Now he decides. Each SitRep proposes **Decisions with Outcome options** (**calibrations** or **dispatches**). On **Approve**, he selects one option (or types his own) and Huginn executes exactly one **Outcome**. On **Reject**, he is *not* endorsing Gjallarhorn's proposed option — but he may still record **vigilance calibrations**: optional **reject note** and/or watch FRAGO or Sit-Awareness entry (e.g. *"Keep an eye on code quality; if Radon drops below B−, let me know"*). No **dispatch** is created from the Reject path in MVP. Gjallarhorn executes Outcomes — sometimes via a multi-step Plan visible in Chat. He then verifies **dispatches** (Contributors and Action Stations **station records**) and maintains global doctrine memory (Situational Awareness).

---

## Act 9: Decisions — LIST+FIND + VIEW (Outcome chooser; reject: optional vigilance)

**Context**: Each SitRep generates Decisions **with Outcome options**. In Semi-Auto mode they are `Proposed` and the Commander **approves** (Reasoning required) or **rejects** (**reject note optional** — skip for a frictionless dismiss). A reject **may still leave Gjallarhorn better informed**: optional **reject note** only, **or** a **vigilance calibration** (watch FRAGO or Sit-Awareness entry, e.g. *"Keep an eye on code quality; if Radon drops below B−, let me know"*), **or note + vigilance**. **Most** Resolved Decisions (**Approved**, **Auto-approved**, **Rejected**) **contribute a structured line by default** to the Project's **single** Decisions Logic FRAGO; **exceptions** — e.g. **bare dismiss** — record **no line**. Optional **Commander profile** signal may be appended on resolve. Commander **maintains that one FRAGO** (extend/modify/remove — Act 6).

**Pattern**: LIST+FIND + VIEW. Decisions are AI-generated (no user CREATE form). Semi-Auto centres on **review** — Outcome chooser with Approve (required Reasoning) or Reject (optional note and/or vigilance calibrations). In Autonomous mode the list is primarily an audit log.

**Decision status set**:
- `Proposed` (blue) — awaiting the Commander's review (Semi-Auto only)
- `Approved` (green) — human-approved; Commander provided Reasoning (required) and selected an Outcome option
- `Auto-approved` (teal) — Gjallarhorn approved itself in Autonomous mode; machine Reasoning attached; Outcome already executed
- `Rejected` (grey) — human-rejected in Semi-Auto; Commander **may** leave a reject note (optional); **may** attach vigilance calibrations (**dispatches are approve-only**)

#### Screen: DECISIONS-LIST+FIND-1

Donland clicks **Decisions** in the main nav (or [Open Decisions] from a SitRep).

**Layout**:
- **Header**: "Decisions — atlas-backend" + count badge
- **Filter**: Status (Proposed / Approved / Auto-approved / Rejected) | Owner (me / Gjallarhorn / all) | Mode (Semi-Auto / Auto) | Outcome type (**Calibration** / **Dispatch** / None / —) — for `Rejected`, **Outcome** reflects an optional vigilance calibration when created on reject | Date range | Source SitRep
- **Table**:
  - Date | Title | Status | Owner | Mode | Outcome | Source SitRep | Actions
- **Row Actions**: [Review] (when `Proposed`) / [View] → `DECISIONS-VIEW_DECISION-1`
- **Empty State**: "No Decisions yet. Decisions are generated by Gjallarhorn in each SitRep."

**Example Data**:
- 20 Apr 09:15 | "Belay Active Bug Count = 0 on Fridays" | Approved | Donland | Semi-Auto | Calibration (FRAGO) | sitrep #142
- 20 Apr 09:15 | "Investigate Friday bug-carry pattern" | Auto-approved | Gjallarhorn | Auto | Dispatch (Jira HUGINN-302) | sitrep #142
- 19 Apr 09:00 | "Refactor auth module immediately" | Rejected | Donland | Semi-Auto | — | sitrep #141 — plain dismiss
- 19 Apr 09:30 | "Tighten coverage to 95% now" | Rejected | Donland | Semi-Auto | Calibration (FRAGO watch Radon ≥ B−) | sitrep #141 — rejected the proposed remediation, opened a vigilance FRAGO instead

#### Screen: DECISIONS-VIEW_DECISION-1

The single most action-dense screen of the daily loop. Donland reviews each proposed Decision here. For `Auto-approved` Decisions the page is read-only on arrival — the Outcome has already been executed.

**Layout** (single-column, top-to-bottom flow):

- **Header**: Decision title + status badge + Owner + Mode badge + source SitRep link

- **Section 1 — Gjallarhorn's case**:
  - Rationale (full text, 1–4 paragraphs)
  - **Proposed Outcome options** (radio cards from SitRep — e.g. Monitor via FRAGO | Create Jira issue | Type your own)
  - Supporting evidence: Variables that triggered, FRAGOs in effect (including Decisions Logic FRAGO), related UoWs/Contributors (clickable chips)
  - Confidence indication

- **Section 2 — Decision** (when status = `Proposed`; hidden for terminal statuses):
  - **Two top-level actions**: [Approve] (primary, green) | [Reject] (secondary)
  - **Approve** — select an Outcome option (or custom) + **Reasoning** textarea (required): why you accepted Gjallarhorn's recommendation; opens **Section 3 — Outcome detail**. On successful Outcome execution, Decision → `Approved` (**dispatch failures keep `Proposed`** — SAO §17.8 / §18); the system **normally** appends **one markdown bullet line** per Act 6 / SAO template, including Reasoning, Owner, and outcome ref — Donland edits the **same** Decisions Logic FRAGO anytime (**extend**, **modify**, **remove** bullets).
  - **Reject** — **Reject note** textarea (optional): free text if you want Decisions Logic to capture *why not* — skip entirely for a bare dismiss below.
  - **Reject note without vigilance artefacts** → **normally** one structured line toward Decisions Logic; Donland later **modify/remove** rows in **`FRAGOS-EDIT_FRAGO-1`**.
  - After **[Reject]** (before confirm): optional **follow-up vigilance** (calibration forms only — pre-filled blanks, Commander writes the watch condition in natural language, e.g. *"Keep an eye on code quality; if Radon drops below B−, flag it."*):
    - **None** — bare reject: leave **reject note** empty **and** do not create vigilance artefacts → Decision → `Rejected`; **no line** contributed to Decisions Logic.
    - **Calibration — watch FRAGO** — same field set as approving a FRAGO calibration, but Decision stays **`Rejected`**; outcome ref = created FRAGO. Primary action e.g. **[Reject and create watch FRAGO]**. System **normally** adds `{status: Rejected, …}` line to Decisions Logic.
    - **Calibration — extend Situational Awareness** — same as approving an SA calibration, but Decision stays **`Rejected`**; outcome ref = SA entry. Primary action e.g. **[Reject and extend awareness]**. System **normally** adds the analogous line.
  - **[Confirm Rejection]** submits the chosen path (`Rejected` + optional artefacts).
  - Approval flow remainder: option selected + Reasoning filled → **Section 3**.

- **Section 3 — Outcome detail (when approving)**: Dynamic form for the **selected Outcome option** (+ execution). Exactly one Outcome executes:

  **Calibration — FRAGO**
  - Use when the Decision is "modify expectations going forward"
  - Pre-filled FRAGO form embedded inline (same fields as `FRAGOS-CREATE_FRAGO-1`):
    - **Project** (fixed from the SitRep's Project scope), title, body (pre-filled from Decision rationale), Affects, scope filter
  - [Approve and execute] → creates FRAGO, persists Outcome (`kind=calibration`), marks Decision `Approved`

  **Calibration — Extend Situational Awareness**
  - Use when the Decision is "remember this context for future evaluations"
  - Inline rich-text input with title + body
  - Preview shows: "This will be appended to **workspace** Situational Awareness (shared across all SitReps), dated today, attributed to you."
  - [Approve and execute] → appends SA entry, persists Outcome (`kind=calibration`), marks Decision `Approved`

  **Dispatch — Create Jira Issue (`HUGINN`-tagged)**
  - Uses the workspace's **`DataSource` row with type Jira** (connected PAT/API token — same ingestion primitive GitLab uses) for REST authentication + default project/issue metadata routing
  - Use when the Decision is "execute work in the team's tracker"
  - Inline form:
    - Summary (required)
    - Description (rich text, pre-filled from Decision rationale)
    - Issue type (Task / Bug / Story — sourced from Jira project's available types)
    - Assignee (Jira accounts list, optional)
    - Priority
    - The `HUGINN` label is **automatically applied and not editable** — this is the marker Action Stations syncs on
  - [Approve and Create Jira Issue] → calls Jira API **synchronously inside the approve request** (`OutcomeExecutor` / `ToolExecutor`); on success, Outcome persisted (`kind=dispatch`), Decision marked `Approved` with Jira key as ref; on failure, Decision **stays `Proposed`**, nothing is written to Decisions Logic for that attempt, and an inline/HTMX error explains the fault (timeouts must be surfaced clearly because the Commander blocks on this POST)

  **Type your own** — free-text option; Commander may pick executor explicitly when text does not match a proposed option (see Open product decisions).

  > When the Decision scope requires multi-step implementation, Gjallarhorn may execute it via a Plan internally. The Plan appears in the Chat thread as a `PlanProgressCard`. No Commander action required — the Plan runs automatically and reports results back through the conversation.

- **Section 4 — Outcome (when status = `Approved`, `Auto-approved`, or `Rejected`)**:
  - Decision is now read-only
  - **Reasoning** (approve / auto) or **Reject note** (reject, if any) displayed when present; machine Reasoning for `Auto-approved`
  - **Owner** and Mode at decision time
  - Shows the **Outcome** record with link to FRAGO / Sit-Awareness entry / Jira key **when one exists** (including `Rejected` + vigilance calibration)
  - For **dispatch** Outcomes: **[View in Action Stations →]** when station record is synced
  - For `Rejected` with **no** vigilance Outcome: omit outcome links — may still show reject note text **or** omit entire outcome block for a bare dismiss
  - For `Auto-approved`: informational banner — "This Decision was auto-approved by Gjallarhorn in Autonomous mode. [View Decisions Logic FRAGO →]"
  - **Decisions Logic FRAGO** — when **this Decision review contributed a structured line**, show *"[View Decisions Logic FRAGO →]."* **Bare rejects** omit. Banner does **not** imply the body is append-only — Donland edits one shared FRAGO.

> Plans surface exclusively as a `PlanProgressCard` in the Chat message thread (see Act 8 Chat). After a Plan completes, the SitRep it generated (or the Outcome it implemented) gains a "View execution plan →" link that deep-links to that message in the conversation history.

---

## Act 10: Contributors — LIST+FIND + VIEW (day-by-day)

**Context**: After making Decisions, Donland often wants to see what the team is actually doing this week — a sanity check on the picture Gjallarhorn painted. Contributors page shows day-by-day activity: how many UoWs each person closed, how many Increments they pushed, what kind. He also drills into one Contributor when a Variable analysis (Contribution profile) flagged an outlier.

**Pattern**: LIST+FIND + VIEW. Contributors are ingested, not user-created. No CREATE/DELETE.

#### Screen: CONTRIBUTORS-LIST+FIND-1

Donland clicks **Contributors** in the main nav.

**Layout**:
- **Header**: "Contributors — atlas-backend"
- **Time-range picker** (top-right, persistent): This week (default) | Previous week | Last 2 weeks | This month | Custom
- **Search & Filter**:
  - Search box: "Find contributor..." (full-text on name, email, source handles)
  - Filter: Active in range (yes/no) | Identity reconciliation status (reconciled / unmapped)
- **Table** with day-by-day breakdown for the selected range:
  - Contributor | Mon | Tue | Wed | Thu | Fri | (Sat) | (Sun) | Total
  - Each day cell shows two numbers: **Increments pushed** / **UoWs closed** (e.g., "5 / 2")
  - Hover on a cell → tooltip with breakdown by Increment type (fix/feat/docs/etc.)
- **Row Actions**: [View] → `CONTRIBUTORS-VIEW_CONTRIBUTOR-1`
- **Empty State**: "No contributors found in the selected range."

**Example Data**:
- Anton P. | 8/3 | 5/2 | 6/1 | 4/2 | 0/0 | — | — | 23/8
- Maria S. | 4/1 | 3/2 | 5/2 | 6/3 | 4/1 | — | — | 22/9

#### Screen: CONTRIBUTORS-VIEW_CONTRIBUTOR-1

**Layout**:
- **Header**: Name + reconciled identities (git emails, Jira account, Slack handle)
- **Identity panel**: source handles resolved to this Contributor; [Edit Mapping] (admin function — out of MVP if too complex)
- **Activity timeline** (selected range):
  - Daily strip: Increments stacked by type (fix/feat/docs/...) and UoWs closed
  - List of the underlying records: each Increment with sha + UoW link, each closed UoW with key + summary
- **UoWs currently assigned**: table of open UoWs assigned to this Contributor
- **Mentions in FRAGOs**: any FRAGO scoped to this person (e.g., "Watch Anton's commit cadence")

---

## Act 11: Action Stations — LIST+FIND (station records — dispatch mirror)

**Context**: Donland just approved Decisions whose **dispatch** Outcomes created `HUGINN`-tagged Jira issues. He wants to confirm they landed upstream. **Action Stations** lists **station records** — read-only mirrors of successful dispatches across connected Jira projects, kept in sync via [Sync] button or scheduled pull. **He does not edit, complete, or annotate here** — to act on an issue, he opens it in Jira. Station records are populated by sync (linked from `Outcome.ref`), not by the approve POST directly.

**Pattern**: LIST+FIND only. No CREATE (created by Act 9 dispatch Outcomes + sync), no EDIT (Jira is the system of record), no DELETE (Jira-side action).

#### Screen: ACTIONSTATIONS-LIST+FIND-1

Donland clicks **Action Stations** in the main nav.

**Layout**:
- **Header**: "Action Stations" + count badge
- **Top action**: [Sync] button — pulls latest from Jira; shows last sync timestamp next to it
- **Filter**: Project | Status (Open / In Progress / Done / All) | Assignee (me / all / specific) | Date created
- **Table** (read-only):
  - Jira Key | Summary | Status | Assignee | Project | Created | Updated
  - Jira Key links open Jira in a new tab
  - Status badge synced from Jira (current as of last Sync)
- **No row actions** — view in Jira to act on it
- **Empty State**: "No station records yet. **Dispatches** from approved Decisions appear here after sync."

**Sync semantics**:
- Clicking [Sync] runs a fresh pull from each connected Jira DataSource for issues with the `HUGINN` label
- Background scheduler also runs the same pull on the configured DataSource cadence
- Read-only: no writes back from this screen

---

## Act 12: Situational Awareness — VIEW + EDIT (workspace-global)

**Context**: Some Decisions produce **SA calibration** Outcomes — adding context that future evaluations should consider. This is **workspace-global narrative memory** for the Commander (single capsule per Huginn workspace / tenant): known constraints, ongoing situations ("GitLab outage all week — expect sync errors"), cross-cutting context — **not** keyed by Project. FRAGOs remain **per-Project** calibration (Act 6); SA is the shared story Gjallarhorn reads for **every** SitRep regardless of which Project it is for.

**Pattern**: VIEW + EDIT. One Situational Awareness capsule per workspace. No `?project=` routing — URLs are `/sitawareness/` (or equivalent). No separate CREATE screen (capsule exists implicitly); no DELETE in MVP.

#### Screen: SITAWARENESS-VIEW-1

Donland clicks **Situational Awareness** in the main nav (or arrives from a Decision **SA calibration** Outcome link).

**Layout** (two-pane):
- **Left — Document** (read-only in VIEW mode):
  - Sections (rendered):
    - **Standing context** — durable items: team composition, known constraints
    - **Active situations** — time-bounded items: outages, holidays, special conditions
    - **Recent entries** — chronological log of entries appended via **SA calibration** Outcomes
  - Each entry: title, body, date, author, source Decision (if applicable, linked)
- **Right — Versions panel**:
  - List of past versions: vN | date | author | change summary
  - Click to view a past version; [Compare with current] for diff view
- **Top Actions**: [Edit] → `SITAWARENESS-EDIT-1`

**Gjallarhorn behavior**: when generating **any** SitRep, Gjallarhorn reads this single active Situational Awareness alongside that Project's Rules of Engagement and **that Project's** FRAGOs. SitRep narratives may reference SA explicitly ("Per Situational Awareness 2026-04-19: GitLab outage in progress, sync gaps expected").

#### Screen: SITAWARENESS-EDIT-1

Same layout as VIEW but document is editable (rich text per section).

- "Change summary" field (required) — appears in version log
- [Save Version] (creates new version) | [Cancel]

---

## Open product decisions

The following are deliberately deferred — captured here so they aren't silently lost between this artefact and ESM Activity 04 / implementation:

1. **Seed Rules of Engagement starter Variables.** Exact `name / abbreviation / calculating / interpreting / hover` values for each of the seven starters (Transparency, Throughput, Cycle & Lead Time, Rework, Quality, Complexity, Contribution). Tracked in a separate doc: `docs/features/roe-seed.md` (to be authored).
2. **SitRep cadence vs sync cadence default policy.** **MVP ingestion sync** is capped at **`hourly` \| `every_6h` \| `daily`** (`Project.sync_schedule`). SitRep generation is still LLM-expensive; optional coarser-than-sync SitRep beats may be desirable. See `docs/ideation/vision.md` Open Questions about future finer-grained ingest cadences vs LLM budgets. *Partially resolved*: the **period model** is explicit — each SitRep stores `from_dt → to_dt`; manual on-demand generation with any period (including sub-day) is specified. What remains open is the **default automatic** SitRep throttle when/if sync becomes more frequent post-MVP.
3. **Per-Variable rich subchart enrichment.** The Variables tab renders one diagram per Variable (Y = value, X = time, fixed period filter). Richer auxiliary panels — burndown, churn quadrant, contributor scatter — don't fit the single-value-per-Variable model. Options: declare them as additional Variables on **FeatureFactory Rules of Engagement**; attach auxiliary chart specs to a `RulesOfEngagementVariable`; or move them to a dedicated post-MVP "Project Analytics" surface.
4. **RulesOfEngagementVariable.calculating typing.** Currently free text — the Agent decides whether to evaluate deterministically (JQL, count expression) or interpret + estimate. Open whether to add an explicit `calc_kind` hint to make Agent routing cheaper.
5. ~~**Situational Awareness scope — journey vs vision.**~~ **Resolved:** persistence and UI use one **workspace-global** SA capsule (singleton). FRAGOs stay per-Project. If `docs/ideation/vision.md` still mentions per-Project SA, treat it as superseded by Act 12 unless an ADR says otherwise.
6. **Chat sidebar keyboard shortcut.** Global keyboard shortcut to expand/collapse `CHAT-SIDEBAR-1` (e.g., `⌘+Shift+G`). Deferred — needs keybinding UX design and conflict resolution with browser shortcuts.
7. **Auto-approved Decision reversal.** In Autonomous mode, `Auto-approved` Decisions are audit-only in MVP — no UI to reverse the outcome after the fact. Post-MVP: define a "Revert Decision" flow that creates compensating artefacts (e.g., deactivate the auto-created FRAGO, reverse the Jira issue) and records a Reversal Reasoning. Deferred.
8. **Decisions Logic FRAGO pruning UX.** The Decisions Logic FRAGO body grows over time. Commander can edit it directly (`FRAGOS-EDIT_FRAGO-1`), but there is no structured pruning, archiving, or summarisation UI in MVP. Options: (a) manual curation in the edit form; (b) Gjallarhorn-assisted "summarise and compress" action; (c) versioned checkpoint with rollback. Deferred.
9. **Custom outcome routing.** Free-text "Type your own" — Gjallarhorn classifies to nearest executor vs Commander picks executor explicitly. MVP recommendation: explicit executor picker when custom text does not match a proposed Outcome option.
10. **Commander profile UX.** Signal persistence in MVP; profile VIEW/EDIT screen deferred. Minimum signals: `{variable_abbrev, color, action_taken, delay_hours}`. See SAO §18.5.
11. **DispatchBoard plugin contract.** Fields required for third-party boards (robot, Slack). Deferred implementation; interface documented in SAO §18 only.
12. **Admin notification on pending signups (Act 0).** MVP relies on the **Pending users (N)** nav badge to surface the queue; admins must visit Huginn to notice it. Out-of-band notifications (email digest, Slack/webhook, push) are deferred. Risk: a one-admin workspace where the admin is on vacation could leave a signup waiting indefinitely. Mitigation when wired: an env-configurable list of admin emails that receive a daily digest of `pending_admin_approval` rows.
13. **Account lifecycle actions beyond approve / reject and password reset (Act 0).** Admin-initiated deactivation of `active` users, re-considering a `rejected` row from the admin UI (today it's terminal), and role / permission management are all out of MVP. Forgot-password is **specified** in this document (`AUTH-FORGOT_PASSWORD-1` / `AUTH-RESET_PASSWORD-1` + Email 5 / Email 6) and uses the same SES + single-use-hashed-token machinery as email verification; its **implementation** is sequenced as a follow-up sprint after the registration / approval flow ships — the **Forgot password?** link on `AUTH-LOGIN-1` may temporarily fall back to the legacy "Contact your admin" tooltip in the interim.
14. ~~**Self-signup gating per install (Act 0).**~~ **Resolved**: self-signup is gated by `settings.DEBUG`. `AUTH-REGISTER-1` and companion routes are available only when `DEBUG = True` (dev / sandbox); production (`DEBUG = False`) redirects them to `AUTH-LOGIN-1` with a banner and omits the **Create an account** link. Production accounts are provisioned by an operator via Django admin or a management command. See the **Self-signup gating** architecture note.
