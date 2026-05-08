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

**Playbook lifecycle**: Playbooks are versioned. A Playbook is metadata + a Workflow (markdown) + an ordered list of `PlaybookVariable` (structured). A Project auto-tracks the latest version of its assigned Playbook unless explicitly pinned to a specific version. Editing a Playbook (Workflow markdown OR any PlaybookVariable) creates a new version; Projects on auto-track receive the new expectations on their next SitRep. (In the future version you can import Playbook/Workflow from Mimir Server.)

**Project view tabs**: tabs on the Project view are **system-defined**, not Playbook-derived:
- **Vitals** — hardcoded, present on every Project. Contains: Identity / Playbook / Sync metadata cards; a hardcoded **Transparency** card; and the **informer bar** — one colored dot per `PlaybookVariable` on the active PlaybookVersion (in declared order), showing `name (abbrev)` with value and color on hover.
- **Variables** — one diagram per `PlaybookVariable` on the active PlaybookVersion, showing `VariableDatapoint` history for the selected period. Fixed period filter: today / yesterday / this week / previous week / 30 days.
- **Adapter-driven tabs** — one tab per registered ingestion adapter. Today: the **Increments** tab, contributed by `ingestion/adapters/gitlab_commits.py`. New adapters add new tabs as they land.

**DataSource credentials**: PATs (GitLab) are user-set and may have an expiry; Jira API tokens generally don't. Huginn tracks an `expires_at` per DataSource and surfaces a warning before expiry. No automatic refresh — the API doesn't support it for PATs.

**Non-standard screen patterns** (extensions to CRUDLF, established here per Activity 01):
- `IMPORT` — Project: select-from-source instead of CREATE form
- `VIEW` only — SitRep, Variables, Contributors (generated/computed)
- `VIEW + EDIT` only — Situational Awareness (**workspace-global**: one capsule for the Commander / installation, not scoped per Project)
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
| 12 | Situational Awareness | VIEW + EDIT (workspace-global) | `SITAWARENESS-VIEW-1` |

---

# INCEPTION

The one-time setup: connect a data source, import the projects you care about, write the Playbook that defines what "good" looks like for each project. By the end of Inception, Huginn has data flowing in and Gjallarhorn has produced its first SitRep.

---

## Act 0: Authentication

**Context**: Donland opens Huginn at `/`. He has an account (created by admin; self-signup is out of scope for MVP). After login he lands on the Projects Dashboard (Act 4) — empty on first run.

#### Screen: AUTH-LOGIN-1

**Layout**:
- **Header**: Huginn wordmark + tagline "Human-AI Command Composite"
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
  - Name | DataSource | Playbook (name + version) | Last sync | Status
  - No visible **Actions** column; each row ends with a single overflow menu (⋯) for secondary commands (see `docs/ux/IA_guidelines.md` §5.2 — LIST+FIND Table).
- **Row navigation**:
  - **Name** links to `PROJECTS-VIEW_PROJECT-1`
  - Overflow menu: **Edit project** → `PROJECTS-EDIT_PROJECT-1` | **Archive** → `PROJECTS-ARCHIVE_PROJECT-1`
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

**Layout** — tabbed page. Tabs are **system-defined** (not Playbook-derived).

- **Header**: Project name + status badge + DataSource
- **Vitals tab** (hardcoded, present on every Project):
  - **Identity**: source path, source URL, imported on, imported by
  - **Playbook**: name + version (or "Not assigned" — link to assign)
  - **Sync**: last sync time, next scheduled, current status (idle / syncing / error)
  - **Transparency card**: hardcoded system-wide health signal — how stale are updates? (See `ingestion/adapters/` for the metric definition.)
  - **Informer bar**: one colored dot per `PlaybookVariable` on the active PlaybookVersion, in declared order. Hover shows `name (abbrev): value`. When no Playbook is assigned, the bar is empty.
- **Variables tab**:
  - One diagram per `PlaybookVariable` on the active PlaybookVersion, showing `VariableDatapoint` history.
  - **Period selector** (top-right, persistent): today / yesterday / this week / previous week / 30 days.
  - Each diagram: Variable name + abbrev as title; Y-axis = value; X-axis = time. Color of each data point reflects the `interpreting` rule at that time.
  - Per-card affordances: [View in Chat] (Act 8) with Variable + period pre-loaded | [Create FRAGO from this] → `FRAGOS-CREATE_FRAGO-1` with Variable pre-selected | reasoning-trace drilldown (click a data point to open a right-rail panel showing the originating `VariableDatapoint` row + SitRep + `AgentInvocation`, collapsed by default).
  - Empty states: no Playbook assigned → "No Playbook assigned. Assign one in the Project view." | Playbook has no Variables → "This Playbook defines no Variables." | Variable has no history yet → "No SitReps yet" in place of the chart.
- **Increments tab** (contributed by `ingestion/adapters/gitlab_commits.py`): system-defined view of ingested commit/increment data. Layout and content defined by the adapter. Further adapter-driven tabs will appear here as new adapters land.
- Deep-link: `?tab=vitals` | `?tab=variables` | `?tab=increments` (or the adapter slug).
- Sync engine behavior (beat, idempotency, error states) is specified in `docs/features/act-2-projects/projects-sync-engine.feature`; architecture in `docs/architecture/SAO.md` §1 (Ingestion sync engine), §4, §7.
- **Top Actions**: [Edit] | [Sync Now] | [Archive] | [Open SitReps] (→ Act 5)

#### Screen: PROJECTS-EDIT_PROJECT-1

Editable fields:
- Display name (Huginn-side label; source path is immutable)
- Assigned Playbook (dropdown of Playbooks; can also pick a specific version, default is "auto-track latest")
- Sync schedule: `daily | hourly | minutely`, each with a pattern (e.g. `daily 08:00`, `hourly :30`, `every 5m from :00`). Default: `hourly :00`.
- SitRep cadence: defaults to "match sync"; may be set to a coarser cadence (≥ hourly) when sync runs minutely, to bound LLM cost. *(Open question — see vision.md.)*
- [Save Changes] | [Cancel]

#### Screen: PROJECTS-ARCHIVE_PROJECT-1

Confirmation modal:
- "Archive 'company-gitlab/atlas-backend'?"
- "Syncs will stop. Ingested history is retained and can be browsed. Project will not appear on the Projects Dashboard."
- [Archive] (warning) | [Cancel]

---

## Act 3: Playbook — CRUDLF (versioned)

**Context**: While the initial sync is running, Donland writes a Playbook. A Playbook is **metadata** (name, description) + a **Workflow** (free-form markdown describing the OO/DA narrative — roles, who is who, what to look for) + an ordered list of **PlaybookVariables** (structured: `name`, `abbreviation`, `calculating`, `interpreting`, `hover`). **One Playbook can be assigned to many Projects.** Each Project pins a (Playbook, version); auto-tracks the latest version by default. Editing the Workflow OR any Variable creates a new version.

**Seed Playbook** (`FeatureFactory Playbook`): Huginn ships a default seed Playbook named **FeatureFactory Playbook**, pre-populated with:
- **Seven starter Variables** (Transparency, Throughput, Cycle & Lead Time, Rework, Quality, Complexity, Contribution), each with default `calculating`, `interpreting`, and `hover`.

Cloning **FeatureFactory Playbook** is the recommended starting point.

**Pattern**: CRUDLF, with version history per Playbook.

#### Screen: PLAYBOOKS-LIST+FIND-1

Donland clicks **Playbooks** in the main nav.

**Layout**:
- **Header**: "Playbooks" with count badge
- **Top Actions**: **[Import from Mimir]** (secondary outline, Mimir icon, disabled — MVP stub; IA toolbar) | **[+ New Playbook]** (primary → CREATE)
- **Filter**: Author | Used by Project (yes / no) | Updated within
- **Table**:
  - Name | Author | Latest version | Used by N projects | Updated
  - No visible **Actions** column; each row ends with a single overflow menu (⋯) for secondary commands (see `docs/ux/IA_guidelines.md` §5.2 — LIST+FIND Table).
- **Row navigation**:
  - **Name** links to `PLAYBOOKS-VIEW_PLAYBOOK-1`
  - Overflow menu: **Edit** → `PLAYBOOKS-EDIT_PLAYBOOK-1` (creates a new version on save) | **Clone to new Playbook** → `PLAYBOOKS-CREATE_PLAYBOOK-1` pre-filled | **Delete** → `PLAYBOOKS-DELETE_PLAYBOOK-1` when unused (disabled with reason when any Project uses this Playbook)
- **Empty State**: "No Playbooks yet. Write one to define expectations for your Projects."

#### Screen: PLAYBOOKS-CREATE_PLAYBOOK-1

**Layout** — three regions, top to bottom:

- **Header**: "New Playbook" | [Clone from seed Playbook] (shortcut)

- **1. Metadata**:
  - Name (required)
  - Description (one line, optional)

- **2. Workflow** (markdown):
  - Markdown editor (full-height, monospace) with side-by-side rendered preview
  - Describes the OO/DA narrative for projects on this Playbook — who is who, what good looks like, what to look out for
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

#### Screen: PLAYBOOKS-VIEW_PLAYBOOK-1

**Layout** (matches Project detail tab pattern — `hg-detail-tabs-card` + `nav-tabs card-header-tabs`):

- **Tabs**
  - **Playbook** — read-only snapshot for the version in focus (default: **latest**): Metadata, Workflow (rendered markdown), Variables table, **Used by** (Projects + tracking indicator with links to `PROJECTS-VIEW_PROJECT-1`).
  - **Versions** — immutable version log: vN, date, author, change summary (newest first); **[Compare with current]** when wired (diff across Workflow and Variables). Selecting a prior version to hydrate the Playbook tab is product wiring (navigation may use query params or in-page state).

- **Top Actions** (header toolbar): **[Clone]** | **[Edit]**

#### Screen: PLAYBOOKS-EDIT_PLAYBOOK-1

Same three-region form as CREATE (Metadata, Workflow, Variables), pre-populated with the latest version's content. Adds:
- "Change summary" field (required) — shown in version log
- [Save as v(N+1)] — never overwrites; always creates a new version

Editing semantics:
- Workflow markdown edits are tracked diff-style.
- Variables edits (add / remove / reorder / change any field) all contribute to the new version. The Variables snapshot for v(N+1) is the full edited list.

On save:
- New version becomes "latest"
- Projects auto-tracking this Playbook will use the new Variables and Workflow on their **next SitRep generation** (does not re-run past SitReps; existing SitReps keep their `variables_snapshot`)
- Pinned Projects keep their pinned version
- Removing a Variable does **not** delete its existing `VariableDatapoint` history — the trend is preserved for audit but the Variable simply stops appearing on new SitReps and on the Variables tab.

#### Screen: PLAYBOOKS-DELETE_PLAYBOOK-1

Confirmation modal:
- "Delete 'FeatureFactory Playbook'?"
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
    - **Variables mini-strip**: N dots, one per PlaybookVariable on the active Playbook (worst color first, then declared order). Hover a dot for `name (abbrev): value`.
    - **Last sync**: timestamp + sync status icon (OK / syncing / error — token expired etc.)
    - **Playbook**: name + version (auto-tracking ⟳ or pinned 📌 indicator)
- **Color semantics**:
  - **Red**: ≥1 PlaybookVariable's `interpreting` rule yielded red at the latest SitRep (with active FRAGOs applied), OR Project has no SitRep yet (initial sync incomplete or no Playbook assigned)
  - **Orange**: ≥1 PlaybookVariable's `interpreting` yielded orange at the latest SitRep, no red
  - **Yellow**: ≥1 PlaybookVariable's `interpreting` yielded yellow at the latest SitRep, no orange/red
  - **Green**: all monitored expectations met
- **Card click** → `SITREP-VIEW_SITREP-1` for that Project's latest SitRep
- **Empty state** (no Projects imported): big CTA → "Import projects to start" → links to Act 2

**Side panel** (collapsible right rail):
- **Data connection issues** — list of DataSources with errors or expiring tokens (links to Act 1 to fix)
- **Triggered FRAGOs since last visit** — quick visibility (links to Act 6)

---

## Act 5: SitRep / Status Report

**Context**: A SitRep is what Gjallarhorn produces after every sync (or on-demand). It is **per Project, per moment in time**. SitReps are read-only once finalized — they are a frozen record of what Gjallarhorn saw at time T against Playbook version V.

**Generation contract**: Gjallarhorn assembles `(SituationalAwareness, active Playbook workflow + variables, enabled in-window FRAGOs, data: {...} for the period under assessment)` and calls the AI once. The AI returns a situation assessment narrative + proposed Decisions + `variables: [{name, abbrev, value, color, hover}, …]`. The variables output is written into `SitRep.variables_snapshot` (canonical, immutable) and denormalized to `VariableDatapoint` rows (used by the Variables tab for trend diagrams).

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
  - One row per PlaybookVariable on the evaluated PlaybookVersion, rendered from the SitRep's embedded `variables_snapshot` JSON (canonical, immutable record of what Gjallarhorn saw at generation time).
  - Columns: **Name (abbrev)** | **Value** | **Color** (traffic light) | **Hover** | Δ vs. previous SitRep
  - When a Variable's value could not be computed by the Agent, the row renders with `value = —` and `color = grey`.
  - Each row links to `VARIABLES-VIEW-1` (Act 7 / Variables tab) filtered to that Variable.

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

A FRAGO is **a short markdown body** scoped to one Project, with an optional time/scope filter (day-of-week, date range, Sprint/Milestone) and an optional **Affects** designation (Narrative or Variable(s)). When set to Variable(s), the FRAGO retunes that Variable's `interpreting` rule for the effective window; it cannot introduce new variables. When Gjallarhorn generates a SitRep, it reads **enabled FRAGOs that are currently in their effective window** alongside the Playbook (Workflow + Variables) and reconciles them in the assessment — both human-authored, both natural language.

**Activate / Deactivate**: each FRAGO has an `enabled` flag the Commander can toggle from the list or detail screen. **Deactivated FRAGOs are not consumed by Gjallarhorn** when producing SitReps, regardless of their effective window. Useful for short-term suspension without losing the FRAGO's context — re-enable to resume. Distinct from **Revoke** (which is soft-delete; revoked FRAGOs cannot be re-enabled).

**Pattern**: CRUDLF + Activate/Deactivate. FRAGOs are user-created, editable, enable/disable-toggleable, and revocable (soft-delete, history preserved).

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
- **Table**:
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
- **Empty State**: "No FRAGOs. Create one to override Playbook expectations for known temporary conditions."

#### Screen: FRAGOS-CREATE_FRAGO-1

Donland opens **New FRAGO** from the list or another surface. Links often include `?project=…` to **pre-select** Project (scoped FRAGO list, Project **Add FRAGO**, SitRep, Decision). The Commander **always picks or confirms Project on this form**; SitRep / Decision flows may still pre-fill other fields (e.g. Affects).

**Layout**:
- **Header**: "New FRAGO"
- **Form**:
  - **Project** (required, **dropdown**) — choose target Project; pre-filled when `?project=` is present
  - Title (required) — e.g., "Belay Active Bug Count = 0 on Fridays"
  - **Body** (markdown) — the FRAGO content. Free-form natural language. Gjallarhorn reads this alongside the Playbook when generating SitReps.
  - **Affects** (optional, single-select): **Narrative** — global context override, Gjallarhorn reads it alongside the Workflow; **Variable(s)** — retunes the interpreting rule for one or more Playbook Variables for the effective window.
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

## Act 7: Variables Tab

**Context**: The Variables tab lives on `PROJECTS-VIEW_PROJECT-1` (Act 2). Donland arrives here from a SitRep breach link, from the informer bar on Vitals, or directly by clicking the Variables tab on a Project. This tab shows every PlaybookVariable on the active PlaybookVersion as a time-series diagram derived from `VariableDatapoint` history. Read-only — values come from SitReps, history from VariableDatapoint rows.

**Pattern**: VIEW with period filter. No CREATE/EDIT/DELETE. Screen ID `VARIABLES-VIEW-1` is retained for cross-references.

#### Screen: VARIABLES-VIEW-1

**Layout**:
- **Header**: "Variables" (within the Project page header — "Variables — atlas-backend") + active PlaybookVersion indicator
- **Period selector** (top-right, persistent):
  - Today | Yesterday | This week | Previous week | 30 days
  - Default: This week
- **Variable diagrams** (grid, one card per PlaybookVariable on the active PlaybookVersion, in declared order):
  - **Card header**: Name (abbrev) + current value + color band + status badge (with active FRAGO overrides applied)
  - **Diagram**: line chart — Y-axis = value, X-axis = time over the selected period; color of each data point reflects the `interpreting` rule at that time
  - **Calculating** (collapsed by default): the Variable's `calculating` text — JQL, expression, or prompt
  - **Interpreting**: the Variable's `interpreting` rules, with overlay showing any FRAGO overrides currently in effect
  - **Hover** preview
- **Per-card affordances**:
  - Click a data point → drill-down panel (right rail) showing that day's `VariableDatapoint` row + the originating SitRep + the `AgentInvocation` (collapsed by default; expand for the Agent's reasoning trace)
  - [View in Chat] → opens `CHAT-1` with the Variable + period pre-loaded as context
  - [Create FRAGO from this] → `FRAGOS-CREATE_FRAGO-1` with this PlaybookVariable pre-selected as the tag
- **Variable-level affordances**:
  - "Edit Variable in Playbook" link → `PLAYBOOKS-EDIT_PLAYBOOK-1` (or pin warning if Project pins an old version)
- **Empty states**:
  - Project has no assigned Playbook → "No Playbook assigned. Assign one in the Project view."
  - Playbook has no Variables → "This Playbook defines no Variables. Add some in `PLAYBOOKS-EDIT_PLAYBOOK-1`."
  - A Variable has no VariableDatapoint history yet → diagram area shows "No SitReps yet" instead of an empty chart.

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

Donland has read the situation, calibrated expectations, and asked his questions. Now he decides. Each Decision branches into one of three concrete outcomes: a new **project-scoped** FRAGO, an extension of **workspace** Situational Awareness, or a `HUGINN`-tagged Jira issue. He then verifies what landed (Contributors and Action Stations) and maintains global doctrine memory (Situational Awareness).

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
    - **Project** (fixed from the SitRep's Project scope), title, body (pre-filled from Decision rationale), Affects, scope filter
  - [Accept and Create FRAGO] → creates FRAGO, marks Decision Accepted with outcome reference

  **Branch B — Extend Situational Awareness**
  - Use when the Decision is "remember this context for future evaluations"
  - Inline rich-text input with title + body
  - Preview shows: "This will be appended to **workspace** Situational Awareness (shared across all SitReps), dated today, attributed to you."
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

## Act 12: Situational Awareness — VIEW + EDIT (workspace-global)

**Context**: Some Decisions extend Situational Awareness (Branch B in Act 9) — adding context that future evaluations should consider. This is **workspace-global narrative memory** for the Commander (single capsule per Huginn workspace / tenant): known constraints, ongoing situations ("GitLab outage all week — expect sync errors"), cross-cutting context — **not** keyed by Project. FRAGOs remain **per-Project** calibration (Act 6); SA is the shared story Gjallarhorn reads for **every** SitRep regardless of which Project it is for.

**Pattern**: VIEW + EDIT. One Situational Awareness capsule per workspace. No `?project=` routing — URLs are `/sitawareness/` (or equivalent). No separate CREATE screen (capsule exists implicitly); no DELETE in MVP.

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

**Gjallarhorn behavior**: when generating **any** SitRep, Gjallarhorn reads this single active Situational Awareness alongside that Project's Playbook and **that Project's** FRAGOs. SitRep narratives may reference SA explicitly ("Per Situational Awareness 2026-04-19: GitLab outage in progress, sync gaps expected").

#### Screen: SITAWARENESS-EDIT-1

Same layout as VIEW but document is editable (rich text per section).

- "Change summary" field (required) — appears in version log
- [Save Version] (creates new version) | [Cancel]

---

## Open product decisions

The following are deliberately deferred — captured here so they aren't silently lost between this artefact and ESM Activity 04 / implementation:

1. **Seed Playbook starter Variables.** Exact `name / abbreviation / calculating / interpreting / hover` values for each of the seven starters (Transparency, Throughput, Cycle & Lead Time, Rework, Quality, Complexity, Contribution). Tracked in a separate doc: `docs/features/playbooks-seed.md` (to be authored).
2. **SitRep cadence vs sync cadence default policy.** Sync may be `minutely`; SitRep generation is LLM-expensive. Default is "match sync"; minutely sync likely needs an explicit coarser SitRep beat (≥ hourly) to bound cost. See `docs/ideation/vision.md` Open Questions.
3. **Per-Variable rich subchart enrichment.** The Variables tab renders one diagram per Variable (Y = value, X = time, fixed period filter). Richer auxiliary panels — burndown, churn quadrant, contributor scatter — don't fit the single-value-per-Variable model. Options: declare them as additional Variables on **FeatureFactory Playbook**; attach auxiliary chart specs to a `PlaybookVariable`; or move them to a dedicated post-MVP "Project Analytics" surface.
4. **PlaybookVariable.calculating typing.** Currently free text — the Agent decides whether to evaluate deterministically (JQL, count expression) or interpret + estimate. Open whether to add an explicit `calc_kind` hint to make Agent routing cheaper.
5. **Situational Awareness scope — journey vs vision.** This journey treats Situational Awareness as **workspace-global** (Act 12). `docs/ideation/vision.md` still documents a per-Project SA relationship in places — reconcile domain model, persistence, and MCP/SitRep wiring in a dedicated ADR before implementation diverges.
