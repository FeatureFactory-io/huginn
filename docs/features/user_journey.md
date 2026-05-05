# Huginn — User Journey

> ESM Activity 02 artifact. Companion to `docs/ideation/vision.md`.

---

## System Architecture Notes

**Screen ID convention**: every screen is identified by `{ENTITY}-{OPERATION}-{VERSION}` (e.g., `PROJECTS-LIST+FIND-1`). Used in this document, in screen-flow diagrams, in feature files, and as HTML comments / hidden divs in templates for grep-able traceability.

**Gjallarhorn** — the AI component. Two surfaces:
1. **Background**: generates SitReps after each successful sync, evaluating Variables against the active Playbook expectations.
2. **Chat**: interactive surface (Act 8) that exposes platform CRUDL via `services.py` / `tool_executor.py`. `find_*` tools provide full-text search; list operations support pagination, page size, filters.

**Jira / GitLab / etc.** — systems of record for raw work data. Huginn ingests via DataSources. **Huginn writes one thing back to Jira: issues created from accepted Decisions, tagged `HUGINN`.** No comment write-back, no annotation write-back.

**Project lifecycle**: Projects are **import-only**. They are never created from a blank form — only by selecting from the list of projects a connected DataSource's token can see.

**Playbook lifecycle**: Playbooks are versioned. A Project auto-tracks the latest version of its assigned Playbook unless explicitly pinned to a specific version. Editing a Playbook creates a new version; Projects on auto-track receive the new expectations on their next SitRep. (In the future version you can import Playbook/Worklfow from Mimir Server.)

**DataSource credentials**: PATs (GitLab) are user-set and may have an expiry; Jira API tokens generally don't. Huginn tracks an `expires_at` per DataSource and surfaces a warning before expiry. No automatic refresh — the API doesn't support it for PATs.

**Non-standard screen patterns** (extensions to CRUDLF, established here per Activity 01):
- `IMPORT` — Project: select-from-source instead of CREATE form
- `VIEW` only — SitRep, Variables, Contributors (generated/computed)
- `VIEW + EDIT` only — SituationalAwareness (one instance per Project)
- `LIST+FIND + VIEW` only — Action Stations (Jira-owned lifecycle, read-only display)
- `CHAT` — Gjallarhorn (conversational, single-screen surface)

---

## Persona

### Commander Donland

**Role**: Project Manager / Commander. Bears the consequences of every Decision.

**Typical day**:
- 09:00 — opens Huginn, scans the **Projects Dashboard** for red/orange health indicators
- For any red Project — reads the SitRep, calibrates expectations via FRAGOs, drills into Variables, queries Gjallarhorn
- Makes Decisions. Each Decision branches into one of three concrete outcomes: a new FRAGO, an extension of SituationalAwareness, or a `HUGINN`-tagged Jira issue
- Reviews Contributors' day-by-day activity
- Checks Action Stations to confirm the `HUGINN`-tagged tasks landed in Jira correctly

---

## Acts

The journey divides into three phases. Inception is one-time per install (or per new Project). Calibration and Action repeat daily.

### INCEPTION — bring data in, set expectations

| Act | Surface | Pattern | Primary Screen |
|-----|---------|---------|----------------|
| 0 | Authentication | Login | `AUTH-LOGIN-1` |
| 1 | DataSource | CRUDLF | `DATASOURCES-LIST+FIND-1` |
| 2 | Project Import | LIST+FIND + IMPORT + VIEW + ARCHIVE | `PROJECTS-LIST+FIND-1` |
| 3 | Playbook | CRUDLF (versioned) | `PLAYBOOKS-LIST+FIND-1` |

### CALIBRATION — read the situation, tune expectations

| Act | Surface | Pattern | Primary Screen |
|-----|---------|---------|----------------|
| 4 | Projects Dashboard | Landing — color-coded health | `DASHBOARD-PROJECTS-1` |
| 5 | SitRep / Status Report | LIST+FIND + VIEW (per Project) | `SITREP-LIST+FIND-1` |
| 6 | FRAGO | CRUDLF (Playbook adjustment) | `FRAGOS-LIST+FIND-1` |
| 7 | Variables Deep-Dive | VIEW with filters | `VARIABLES-VIEW-1` |
| 8 | Gjallarhorn Chat | CHAT | `CHAT-1` |

### ACTION — decide, execute, observe

| Act | Surface | Pattern | Primary Screen |
|-----|---------|---------|----------------|
| 9 | Decisions | LIST+FIND + VIEW (3-branch accept) | `DECISIONS-LIST+FIND-1` |
| 10 | Contributors | LIST+FIND + VIEW (day-by-day) | `CONTRIBUTORS-LIST+FIND-1` |
| 11 | Action Stations | LIST+FIND only (read-only Jira sync) | `ACTIONSTATIONS-LIST+FIND-1` |
| 12 | Situational Awareness | VIEW + EDIT (per Project) | `SITAWARENESS-VIEW-1` |

---

# INCEPTION

The one-time setup: connect a data source, import the projects you care about, write the Playbook that defines what "good" looks like for each project. By the end of Inception, Huginn has data flowing in and Gjallarhorn has produced its first SitRep.

---

## Act 0: Authentication

**Context**: Donland opens Huginn at `/`. He has an account (created by admin; self-signup is out of scope for MVP). After login he lands on the Projects Dashboard (Act 4) — empty on first run.

#### Screen: AUTH-LOGIN-1

**Layout**:
- **Header**: Huginn wordmark + tagline "Human-AI OODA for PM"
- **Form** (centered, single column):
  - Email (`data-testid="login-email"`)
  - Password (`data-testid="login-password"`)
  - [Sign In] button (primary, full-width)
- **Footer**: "Forgot password?" — disabled with tooltip "Contact your admin" (out of MVP scope)

**Flow**:
- Valid credentials → `DASHBOARD-PROJECTS-1` (Act 4)
- Invalid → inline error "Invalid email or password"
- Network error → "Unable to reach Huginn. Check your connection."

---

## Act 1: DataSource — CRUDLF

**Context**: Before Huginn can do anything, Donland connects a data source. MVP supports GitLab; Jira will come later. He provides a base URL and a Personal Access Token. After saving, the DataSource is the prerequisite for Act 2 (Project Import).

#### Screen: DATASOURCES-LIST+FIND-1

Donland clicks **Data Sources** in the main nav.

**Layout**:
- **Header**: "Data Sources" with count badge (e.g., "Data Sources (1)")
- **Top Actions**: [+ Add Data Source] button (primary)
- **Filter**: Type (GitLab / Jira) | Status (Connected / Error / Token expiring)
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
  - "Add a GitLab connection to start importing projects."
  - [+ Add Data Source]

**Example Data**:
- GitLab | "company-gitlab" | https://gitlab.example.com | 14 days | Token expiring | 5 min ago

#### Screen: DATASOURCES-CREATE_DATASOURCE-1

Donland clicks [+ Add Data Source].

**Layout**:
- **Step 1 — Type**: Two cards (GitLab / Jira). Jira disabled with "Coming soon" tooltip in MVP.
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

This is the **Huginn-side** Project list (different from the Projects Dashboard in Act 4 — that's the daily landing). This screen is for management: assign Playbook, archive, view sync status.

**Layout**:
- **Header**: "Projects" with count badge
- **Top Actions**:
  - [+ Import Projects] button (primary) → `PROJECTS-IMPORT-1`
- **Filter**: DataSource | Status (Active / Archived / Orphaned) | Playbook
- **Table** with columns:
  - Name | DataSource | Playbook (name + version) | Last sync | Status | Actions
- **Row Actions**:
  - [View] → `PROJECTS-VIEW_PROJECT-1`
  - [Edit] → `PROJECTS-EDIT_PROJECT-1` (assign Playbook, change pin, etc.)
  - [Archive] → `PROJECTS-ARCHIVE_PROJECT-1`
- **Empty State**:
  - "No projects imported yet"
  - "Import projects from a connected data source."
  - [+ Import Projects]

#### Screen: PROJECTS-IMPORT-1

Donland clicks [+ Import Projects] (from this screen, Act 1's shortcut, or Act 0's empty-state CTA).

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
    - Default Playbook = none (must be assigned in Act 3 / via Edit)
  - Banner on redirect: "N projects imported. Sync started. Assign a Playbook to receive SitReps."
  - Redirect → `PROJECTS-LIST+FIND-1`

**Re-import behavior**: Selecting an already-imported project is a no-op (checkbox disabled, "Already imported" badge shown).

#### Screen: PROJECTS-VIEW_PROJECT-1

**Layout**:
- **Header**: Project name + status badge + DataSource
- **Sections**:
  - **Identity**: source path, source URL, imported on, imported by
  - **Playbook**: name + version (or "Not assigned" — link to assign)
  - **Sync**: last sync time, next scheduled, current status (idle / syncing / error)
  - **Recent activity**: last N UoW state changes / Increments
- **Top Actions**: [Edit] | [Sync Now] | [Archive] | [Open SitReps] (→ Act 5)

#### Screen: PROJECTS-EDIT_PROJECT-1

Editable fields:
- Display name (Huginn-side label; source path is immutable)
- Assigned Playbook (dropdown of Playbooks; can also pick a specific version, default is "auto-track latest")
- Sync schedule: Hourly (default) / Every 6h / Daily
- [Save Changes] | [Cancel]

#### Screen: PROJECTS-ARCHIVE_PROJECT-1

Confirmation modal:
- "Archive 'company-gitlab/atlas-backend'?"
- "Syncs will stop. Ingested history is retained and can be browsed. Project will not appear on the Projects Dashboard."
- [Archive] (warning) | [Cancel]

---

## Act 3: Playbook — CRUDLF (versioned)

**Context**: While the initial sync is running, Donland writes a Playbook. A Playbook captures *what good looks like* for a project — roles ("who is who"), key Variables to watch, expected values and thresholds, what to look for. **One Playbook can be assigned to many Projects.** Each Project pins a (Playbook, version); auto-tracks the latest version by default. Editing a Playbook creates a new version. **MVP content is free-form markdown**; structured fields may be introduced in later versions.

**Pattern**: CRUDLF, with version history per Playbook.

#### Screen: PLAYBOOKS-LIST+FIND-1

Donland clicks **Playbooks** in the main nav.

**Layout**:
- **Header**: "Playbooks" with count badge
- **Top Actions**: [+ New Playbook] (primary)
- **Filter**: Author | Used by Project (yes / no) | Updated within
- **Table**:
  - Name | Latest version | Used by N projects | Updated | Actions
- **Row Actions**:
  - [View] → `PLAYBOOKS-VIEW_PLAYBOOK-1`
  - [Edit] → `PLAYBOOKS-EDIT_PLAYBOOK-1` (creates a new version on save)
  - [Clone] → opens CREATE pre-filled with current content as starting draft
  - [Delete] → `PLAYBOOKS-DELETE_PLAYBOOK-1` (only if used by 0 Projects)
- **Empty State**: "No Playbooks yet. Write one to define expectations for your Projects."

#### Screen: PLAYBOOKS-CREATE_PLAYBOOK-1

**Layout**:
- **Header**: "New Playbook"
- **Form**:
  - Name (required)
  - Description (one line, optional)
  - **Content**: markdown editor (full-height, monospace) with side-by-side rendered preview
    - Donland writes in plain markdown — describes how the project is supposed to be run, who is who, key Variables to watch, what good looks like, what to look out for
    - No structured schema in MVP; Gjallarhorn reads the markdown when generating SitReps
- **Top Actions**: [Save as v1] (primary) | [Cancel]
- **Future**: [Import from Mimir] (out of MVP); structured-fields layer (out of MVP)

#### Screen: PLAYBOOKS-VIEW_PLAYBOOK-1

**Layout** (two-column):
- **Left — current version content** (read-only): rendered markdown
- **Right — Versions panel**:
  - List of versions: vN | created on | author | change summary
  - Click version to view that version's content (left panel updates)
  - [Compare with current] (diff view)
- **Used by**: list of Projects assigned to this Playbook (each linked to `PROJECTS-VIEW_PROJECT-1`); for each Project, indicator whether it auto-tracks latest or pins a specific version
- **Top Actions**: [Edit] (creates new version) | [Clone]

#### Screen: PLAYBOOKS-EDIT_PLAYBOOK-1

Same form as CREATE, pre-populated with the latest version's content. Adds:
- "Change summary" field (required) — shown in version log
- [Save as v(N+1)] — never overwrites; always creates a new version

On save:
- New version becomes "latest"
- Projects auto-tracking this Playbook will use the new expectations on their **next SitRep generation** (does not re-run past SitReps)
- Pinned Projects keep their pinned version

#### Screen: PLAYBOOKS-DELETE_PLAYBOOK-1

Confirmation modal:
- "Delete 'Standard Engineering Playbook'?"
- If used by 0 Projects: [Delete] available
- If used by N Projects: "Used by N project(s). Reassign or archive those projects first." (Delete disabled)

---

## End of Inception

After Inception:
- ≥1 DataSource connected
- ≥1 Project imported and synced (initial dump complete)
- ≥1 Playbook authored and assigned to each Project
- **Trigger**: when a Project's initial sync completes AND it has a Playbook assigned, Gjallarhorn fires its first SitRep generation. The Project is now ready for Calibration (Act 4 onward).

---

# CALIBRATION

The daily loop. Donland opens Huginn, scans the Projects Dashboard, drills into anything red or orange. He reads the SitRep, adjusts expectations via FRAGOs when reality and Playbook diverge for legitimate reasons, browses Variables to understand the trend, and questions Gjallarhorn directly when he needs an answer the SitRep didn't provide.

---

## Act 4: Projects Dashboard

**Context**: This is the **daily landing screen**. After login, Donland sees every active Project as a status card with a single dominant color (red / orange / yellow / green). He scans for trouble in seconds, then clicks into the worst Project.

**Pattern**: Single-screen dashboard. Read-only aggregate view; all detail lives one click away.

#### Screen: DASHBOARD-PROJECTS-1

**Layout**:
- **Header**: "Projects" + last refresh timestamp + [Refresh] button
- **Summary strip** (top): counts by color — "2 red · 1 orange · 4 yellow · 6 green"
- **Project cards grid** (sorted by health: worst first):
  - Each card contains:
    - **Color bar** (top edge, full-width): red / orange / yellow / green
    - **Project name** + DataSource icon
    - **Last SitRep timestamp** + "View SitRep →" link → `SITREP-VIEW_SITREP-1` (Act 5) for the latest SitRep
    - **Headline assessment** (1 line, from latest SitRep): e.g., "Milestone v1.21 at risk: 3 critical bugs open"
    - **Master Variable mini-strip**: 7 dots, color per variable
    - **Last sync**: timestamp + sync status icon (OK / syncing / error — token expired etc.)
    - **Playbook**: name + version (auto-tracking ⟳ or pinned 📌 indicator)
- **Color semantics**:
  - **Red**: ≥1 red-severity Variable expectation breached, OR Project has no SitRep yet (initial sync incomplete or no Playbook assigned)
  - **Orange**: ≥1 orange-severity expectation breached, no red
  - **Yellow**: ≥1 yellow-severity expectation breached, no orange/red
  - **Green**: all monitored expectations met
- **Card click** → `SITREP-VIEW_SITREP-1` for that Project's latest SitRep
- **Empty state** (no Projects imported): big CTA → "Import projects to start" → links to Act 2

**Side panel** (collapsible right rail):
- **Data connection issues** — list of DataSources with errors or expiring tokens (links to Act 1 to fix)
- **Triggered FRAGOs since last visit** — quick visibility (links to Act 6)

---

## Act 5: SitRep / Status Report

**Context**: A SitRep is what Gjallarhorn produces after every sync (or on-demand). It is **per Project, per moment in time**. It evaluates current Variable values against the Project's active Playbook expectations, gives an overall RYG/orange assessment, narrates the situation, and proposes Decisions. SitReps are read-only once finalized — they are a frozen record of what Gjallarhorn saw at time T against Playbook version V.

**Pattern**: LIST+FIND + VIEW. No CREATE (auto-generated), no EDIT (frozen), no DELETE (audit log).

#### Screen: SITREP-LIST+FIND-1

Donland clicks a Project card on the Dashboard, or **SitReps** from the Project view.

**Layout**:
- **Header**: "SitReps — atlas-backend"
- **Latest SitRep card** (pinned, prominent):
  - Date + time generated
  - Overall status badge (red / orange / yellow / green)
  - Headline assessment (1–2 lines)
  - Pending Decisions count
  - [Open SitRep] (primary) → `SITREP-VIEW_SITREP-1`
- **History table** below:
  - Generated at | Status | Headline | Decisions proposed | Decisions accepted | Playbook version | Actions
  - Sort by date (default: newest first)
  - Filter: status, date range, Playbook version
- **Row Actions**: [View]
- **Empty State**: "No SitReps yet. Gjallarhorn generates the first SitRep when initial sync completes and a Playbook is assigned."

#### Screen: SITREP-VIEW_SITREP-1

Donland clicks [Open SitRep] or a row.

**Layout** (read-only document, multi-section):

- **Header**:
  - Project | Date generated | Playbook version evaluated against | Overall status badge
  - [Open Decisions] (primary, jumps to Decisions section) | [Open Variables] (jumps to Variables section)

- **Section 1 — Situation Assessment**:
  - Overall status (red/orange/yellow/green) with one-paragraph narrative
  - Example: *"RED — Milestone v1.21 supposed to ship Monday, but still 3 critical bugs open. Playbook expects Active Bug Count = 0 at all times; current value is 3."*
  - Key breaches list: each shows Variable name → expected vs. actual → severity badge → link to Variable deep-dive (Act 7)

- **Section 2 — Variables Snapshot**:
  - All 7 Master Variables with current values, deltas, traffic light vs. Playbook expectation
  - Each row links to `VARIABLES-VIEW-1` (Act 7) filtered to that variable

- **Section 3 — Proposed Decisions**:
  - List of Decisions Gjallarhorn proposes based on the assessment
  - Each Decision shown as a card: title + rationale (2–4 sentences) + [Review →] button
  - [Review] → `DECISIONS-VIEW_DECISION-1` (Act 9) where the 3-branch Accept flow lives

- **Section 4 — FRAGOs applied**:
  - Which FRAGOs Gjallarhorn applied to this evaluation (i.e., enabled and in effective window at generation time; e.g., "Active Bug Count expected to be 0 — belay on Fridays, ≤3 OK")
  - Helps explain why the assessment is what it is — and conversely, deactivated/expired FRAGOs are *not* listed here, which makes "what changed when I toggled X" easy to verify
  - Links to Act 6

- **Section 5 — Notable activity since last SitRep** (optional):
  - "Who did what" summary: Increments, closed UoWs, state changes worth noting
  - Anomalies (e.g., "Anton: 0 commits — first time in 14 days")

**Top-right utility**:
- [Open Chat about this SitRep] → `CHAT-1` (Act 8) with this SitRep pre-loaded as context

---

## Act 6: FRAGO — CRUDLF (Playbook adjustment)

**Context**: A FRAGO is an **in-flight adjustment to the Playbook** that the active Playbook version doesn't capture. When reality and Playbook disagree for a legitimate reason, Donland creates a FRAGO instead of editing the Playbook itself. Examples:
- *"Active Bug Count expected to be 0 — belay that on Fridays; up to 3 bugs OK on Fri."*
- *"Disregard broken builds tomorrow — known infra outage."*
- *"Cycle time threshold ≤ 5 days suspended for Sprint 47 (holiday week)."*

A FRAGO is **a short markdown body** scoped to one Project, with an optional time/scope filter (day-of-week, date range, Sprint/Milestone) and an optional Variable-section tag for filtering. When Gjallarhorn generates a SitRep, it reads **enabled FRAGOs that are currently in their effective window** alongside the Playbook markdown and reconciles them in the assessment — both human-authored, both natural language. There is no structured override schema in MVP.

**Activate / Deactivate**: each FRAGO has an `enabled` flag the Commander can toggle from the list or detail screen. **Deactivated FRAGOs are not consumed by Gjallarhorn** when producing SitReps, regardless of their effective window. Useful for short-term suspension without losing the FRAGO's context — re-enable to resume. Distinct from **Revoke** (which is soft-delete; revoked FRAGOs cannot be re-enabled).

**Pattern**: CRUDLF + Activate/Deactivate. FRAGOs are user-created, editable, enable/disable-toggleable, and revocable (soft-delete, history preserved).

#### Screen: FRAGOS-LIST+FIND-1

Donland clicks **FRAGOs** in the main nav (or [+ New FRAGO from this expectation] from a SitRep breach card).

**Layout**:
- **Header**: "FRAGOs — atlas-backend" with count badge
- **Top Actions**: [+ New FRAGO] (primary)
- **Filter**: Status (Active / Inactive / Scheduled / Expired / Revoked) | Variable tag | In effect now
- **Table**:
  - Toggle | Title | Variable tag | Effective window | Status | Actions
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
- **Empty State**: "No FRAGOs. Create one to override Playbook expectations for known temporary conditions."

#### Screen: FRAGOS-CREATE_FRAGO-1

Donland clicks [+ New FRAGO]. Or — when launched from a SitRep breach card or a Decision Branch A — the form opens with the relevant Variable tag pre-selected.

**Layout**:
- **Header**: "New FRAGO"
- **Form**:
  - Title (required) — e.g., "Belay Active Bug Count = 0 on Fridays"
  - **Body** (markdown) — the FRAGO content. Free-form natural language. Gjallarhorn reads this alongside the Playbook when generating SitReps.
  - **Variable tag** (optional, single-select) — one of the 7 Master Variable sections (Transparency / Throughput / Cycle & Lead Time / Rework / Quality / Complexity / Contribution). Used for filtering and to help Gjallarhorn associate the FRAGO with the right section of analysis. Doesn't enforce structure.
  - **Scope filter** (optional):
    - Day-of-week: any combination of Mon–Sun
    - Date range: from / to (either or both optional)
    - Sprint / Milestone: dropdown
  - [Save FRAGO] | [Cancel]

#### Screen: FRAGOS-VIEW_FRAGO-1

**Layout**:
- Title | Status badge | Variable tag (if any)
- **Enable toggle** (header, prominent): switch labelled "Enabled" / "Disabled". Same semantics as the list toggle — flipping it changes whether Gjallarhorn applies the FRAGO on the next SitRep. Disabled when status = Revoked.
- Body (rendered markdown)
- Effective window
- **Application history**: list of SitReps where this FRAGO was applied (date, link to SitRep). Useful to verify activation/deactivation took effect — a deactivated FRAGO will not appear in subsequent SitReps' history.
- **State change log**: chronological log of toggles and edits (timestamp, action, actor)
- [Edit] | [Revoke]

#### Screen: FRAGOS-EDIT_FRAGO-1

Same form as CREATE, pre-populated. Editing is allowed — change is timestamped in history. [Save Changes] | [Cancel].

#### Screen: FRAGOS-REVOKE_FRAGO-1

Confirmation modal:
- "Revoke 'Belay Active Bug Count = 0 on Fridays'?"
- "Future SitReps will evaluate the underlying Playbook expectation as written. Existing SitReps that referenced this FRAGO are unchanged."
- [Revoke] (warning) | [Cancel]

---

## Act 7: Variables Deep-Dive

**Context**: Donland sees a breach on the SitRep and wants to understand the trend behind it — or wants to wander through Variables to spot anomalies the SitRep didn't surface. This screen presents all 7 Master Variables grouped by section, each with daily-resolution graphs and time-range filters. Read-only — derived from ingested data.

**Pattern**: VIEW with filters. No CREATE/EDIT/DELETE. Open from main nav, from SitRep breach links, or from Project dashboard cards.

#### Screen: VARIABLES-VIEW-1

**Layout**:
- **Header**: "Variables — atlas-backend"
- **Time-range picker** (top-right, persistent):
  - This week | Previous week | Last 2 weeks | This month | Custom (date range)
  - Default: This week
- **Sections** (vertically stacked, each a panel; scroll or jump-link nav):

  **TRANSPARENCY** — do we have data, is it actual?
  - Sync freshness per DataSource (hours since last successful sync)
  - Stale Jira issues (no update in ≥7 days, with `HUGINN` tag breakdown)
  - Stale branches / PRs

  **THROUGHPUT**
  - Milestone burndown (line chart, daily — planned vs. actual)
  - Increment cadence (bar chart, daily — Increments per day, stacked by author)
  - Increment type distribution (stacked bar — fix / feat / docs / chore / refactor / test) per day

  **CYCLE & LEAD TIME**
  - UoW cycle time (median + p90, daily distribution)
  - Lead time (created → closed)
  - Engineering sub-cycle (in-progress → review → merged)

  **REWORK**
  - Churn rate per file
  - Reverts / amended commits
  - UoWs reopened after closure

  **QUALITY**
  - Test pass rate (daily)
  - Coverage trend
  - Active bug count (daily — central to many Playbook expectations)
  - Defects opened vs. closed (paired daily bars)

  **COMPLEXITY**
  - Maintainability index (Halstead + cyclomatic) trend
  - Hotspot files (highest complexity × highest churn)

  **CONTRIBUTION**
  - Increments by Contributor, daily
  - New code vs. churn quadrant (X = churn, Y = new code) — current period vs. prior

- **Per-graph affordances**:
  - Click a data point → drill-down panel (right rail) with the underlying records (UoWs, Increments, etc.) for that day
  - [View in Chat] → opens `CHAT-1` with the variable + range pre-loaded as context
  - [Create FRAGO from this] → `FRAGOS-CREATE_FRAGO-1` with the relevant Playbook expectation pre-selected

- **Variable-level affordances**:
  - Each section header shows the Playbook expectation in effect (with FRAGO overrides applied) and current status badge
  - "Edit expectation in Playbook" link → `PLAYBOOKS-EDIT_PLAYBOOK-1` (or pin warning if Project pins an old version)

---

## Act 8: Gjallarhorn Chat — CHAT

**Context**: When the SitRep doesn't answer Donland's question, he opens the chat. Gjallarhorn has CRUDL access to the platform via `services.py` / `tool_executor.py` and can search, list, and inspect any entity in the user's context. This is also where Donland often arrives from a SitRep ("Open Chat about this SitRep") or a Variable ("View in Chat") with context pre-loaded.

**Pattern**: CHAT (single screen, conversational). Non-CRUDLF.

#### Screen: CHAT-1

**Layout** (two-pane):

**Left — Conversation**:
- Project selector at top (defaults to last-viewed Project)
- Pre-loaded context chip (when arriving from another screen): e.g., "SitRep 2026-04-20 09:15" or "Variable: Active Bug Count, Last 2 weeks" — clickable to open
- Message thread:
  - User messages (right-aligned)
  - Gjallarhorn messages (left-aligned, AI badge)
  - **Tool-call traces** (collapsible) below each Gjallarhorn message that used tools — shows which tool(s) were called, their args, and result counts. Donland can expand to inspect.
  - Citations: when Gjallarhorn references entities (UoW, Contributor, SitRep, Variable datapoint), they render as clickable chips → open the entity's view screen
- Input box at bottom: textarea + [Send] button + [Attach context] dropdown (manually pin a SitRep, FRAGO, etc. as additional context)

**Right — Context panel** (collapsible):
- **Active Project**: name, status, Playbook
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

Donland has read the situation, calibrated expectations, and asked his questions. Now he decides. Each Decision branches into one of three concrete outcomes: a new FRAGO, an extension of Situational Awareness, or a `HUGINN`-tagged Jira issue. He then verifies what landed (Contributors and Action Stations) and writes back doctrine memory (Situational Awareness).

---

## Act 9: Decisions — LIST+FIND + VIEW (3-branch accept)

**Context**: Each SitRep proposes Decisions. Donland reviews them one at a time, accepts or rejects with rationale, and chooses the outcome. Decisions are also browseable as a per-Project log — the audit trail of what was decided, when, why, and what came of it.

**Pattern**: LIST+FIND + VIEW. Decisions are AI-proposed (no user CREATE form). Acceptance is the central action; it spawns one of three outcomes.

#### Screen: DECISIONS-LIST+FIND-1

Donland clicks **Decisions** in the main nav (or [Open Decisions] from a SitRep).

**Layout**:
- **Header**: "Decisions — atlas-backend" + count badge
- **Filter**: Status (Proposed / Accepted / Rejected) | Outcome type (FRAGO / Sit-Awareness / Jira issue / —) | Date range | Source SitRep
- **Table**:
  - Date | Title | Status | Outcome | Source SitRep | Actions
- **Status badges**: Proposed (blue) / Accepted (green) / Rejected (grey)
- **Row Actions**: [Review] / [View] → `DECISIONS-VIEW_DECISION-1`
- **Empty State**: "No Decisions yet. Decisions are proposed by Gjallarhorn in each SitRep."

**Example Data**:
- 20 Apr 09:15 | "Belay Active Bug Count = 0 on Fridays" | Accepted | FRAGO | sitrep #142
- 20 Apr 09:15 | "Investigate Friday bug-carry pattern" | Accepted | Jira (HUGINN-302) | sitrep #142
- 19 Apr 09:00 | "Refactor auth module immediately" | Rejected | — | sitrep #141

#### Screen: DECISIONS-VIEW_DECISION-1

The single most action-dense screen of the daily loop. Donland reviews each proposed Decision here.

**Layout** (single-column, top-to-bottom flow):

- **Header**: Decision title + status badge + source SitRep link

- **Section 1 — Gjallarhorn's case**:
  - Rationale (full text, 1–4 paragraphs)
  - Supporting evidence: Variables that triggered, FRAGOs in effect, related UoWs/Contributors (clickable chips)
  - Confidence indication

- **Section 2 — Decision** (when status = Proposed):
  - **Two top-level actions**: [Accept] (primary, green) | [Reject] (secondary)
  - Rejection flow: rationale text area → [Confirm Rejection]. Decision moves to status Rejected; outcome = none.
  - Acceptance flow: opens **3-branch outcome chooser** below.

- **Section 3 — Outcome (when accepting)**: three choices, mutually exclusive, presented as cards:

  **Branch A — Create FRAGO**
  - Use when the Decision is "modify expectations going forward"
  - Pre-filled FRAGO form embedded inline (same fields as `FRAGOS-CREATE_FRAGO-1`):
    - Title, body (pre-filled from Decision rationale), Variable tag, scope filter
  - [Accept and Create FRAGO] → creates FRAGO, marks Decision Accepted with outcome reference

  **Branch B — Extend Situational Awareness**
  - Use when the Decision is "remember this context for future evaluations"
  - Inline rich-text input with title + body
  - Preview shows: "This will be appended as a new entry in the Project's Situational Awareness, dated today, attributed to you."
  - [Accept and Extend Awareness] → appends entry, marks Decision Accepted with outcome reference

  **Branch C — Create Jira Issue (`HUGINN`-tagged)**
  - Use when the Decision is "execute work in the team's tracker"
  - Inline form:
    - Summary (required)
    - Description (rich text, pre-filled from Decision rationale)
    - Issue type (Task / Bug / Story — sourced from Jira project's available types)
    - Assignee (Jira accounts list, optional)
    - Priority
    - The `HUGINN` label is **automatically applied and not editable** — this is the marker Action Stations syncs on
  - [Accept and Create Jira Issue] → calls Jira API; on success, Decision marked Accepted with the Jira key as outcome reference; on failure, Decision stays Proposed and error is shown

- **Section 4 — Outcome (when status = Accepted/Rejected)**:
  - Decision is now read-only
  - Shows the outcome record with link to the created FRAGO / Sit-Awareness entry / Jira issue
  - Shows acceptance/rejection rationale and timestamp

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

## Act 11: Action Stations — LIST+FIND only (read-only Jira sync)

**Context**: Donland just accepted three Decisions that created `HUGINN`-tagged Jira issues. He wants to confirm they landed. Action Stations is the read-only mirror of all `HUGINN`-tagged issues across his connected Jira projects, kept in sync via [Sync] button or scheduled pull. **He does not edit, complete, or annotate here** — to act on an issue, he opens it in Jira.

**Pattern**: LIST+FIND only. No CREATE (created by Act 9 acceptance), no EDIT (Jira is the system of record), no DELETE (Jira-side action).

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
- **Empty State**: "No `HUGINN`-tagged issues yet. Issues created via accepted Decisions appear here."

**Sync semantics**:
- Clicking [Sync] runs a fresh pull from each connected Jira DataSource for issues with the `HUGINN` label
- Background scheduler also runs the same pull on the configured DataSource cadence
- Read-only: no writes back from this screen

---

## Act 12: Situational Awareness — VIEW + EDIT (per Project)

**Context**: Some Decisions extend Situational Awareness (Branch B in Act 9) — adding context that future SitReps should consider. This is **per-Project durable narrative memory**: known constraints, ongoing situations ("GitLab outage all week — expect sync errors"), team context, anything Donland wants Gjallarhorn to remember when generating future SitReps.

**Pattern**: VIEW + EDIT. One Situational Awareness instance per Project. No CREATE (created with Project), no DELETE (cleared on Project archive).

#### Screen: SITAWARENESS-VIEW-1

Donland clicks **Situational Awareness** in the main nav (or arrives from a Decision Branch B outcome link).

**Layout** (two-pane):
- **Left — Document** (read-only in VIEW mode):
  - Sections (rendered):
    - **Standing context** — durable items: team composition, known constraints
    - **Active situations** — time-bounded items: outages, holidays, special conditions
    - **Recent entries** — chronological log of entries appended via Decision Branch B
  - Each entry: title, body, date, author, source Decision (if applicable, linked)
- **Right — Versions panel**:
  - List of past versions: vN | date | author | change summary
  - Click to view a past version; [Compare with current] for diff view
- **Top Actions**: [Edit] → `SITAWARENESS-EDIT-1`

**Gjallarhorn behavior**: when generating SitReps, Gjallarhorn reads the active Situational Awareness for the Project as additional context alongside the Playbook. SitRep narratives may explicitly reference Situational Awareness entries ("Per Situational Awareness 2026-04-19: GitLab outage in progress, sync gaps expected").

#### Screen: SITAWARENESS-EDIT-1

Same layout as VIEW but document is editable (rich text per section).

- "Change summary" field (required) — appears in version log
- [Save Version] (creates new version) | [Cancel]

---
