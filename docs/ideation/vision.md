# The Composite: Huginn - Human-AI OODA for  PM

> *Saved from conversation — April 13, 2026*

---

## Seed: On Command and Composite Cognition

**Command as equation-solving:** Human + AI composite: identify the variables, solve the system, implement — ruthlessly or sneakily, whatever the topology of the problem demands. Boyd's OODA, Clausewitz's Schwerpunkt, implicit guidance and control — all variations of the same idea.

**The Composite framing** (Cheris/Jedao as archetype):
- Shared problem representation
- Asymmetric capabilities mapped to subproblems
- A trust/authority protocol that evolves as the mission unfolds
- Neither component can solve the problem alone — the composite is load-bearing


**Why do we need this? Loop tempo -> operation tempo: outthink the enemy**

The side cycling faster wins. The composite  multiplies your tempo giving you an advantage: find bottlenecs & design tasks to be handed to people/agents.

---

## Composite Cognition — Applied Science Foundation

**Distributed cognition** (Hutchins, *Cognition in the Wild*, 1995): cognition is distributed across people, artifacts, and representations. A navigation team isn't six people thinking — it's one cognitive system with six nodes.

**Extended mind theory** (Clark & Chalmers, 1998): cognitive processes can extend into tools. The boundary of "mind" is functional, not anatomical.

**Transactive memory systems** (Kozlowski et al.): high-performing teams don't share all knowledge — they share *knowledge about knowledge*, and route problems accordingly. Maps directly to human+AI composites.

**Empirical signal** (Noy & Zhang, MIT/QJE, 2023): AI assistance didn't just speed up writing — it changed cognitive strategy. Workers offloaded different parts of the problem than expected. That's cognitive restructuring, not tool use.

### Known failure modes
- **Automation bias** — humans over-trust AI under cognitive load; composite becomes less capable than either alone (Parasuraman & Manzey)
- **Skill atrophy** — AI consistently handling a subproblem causes human capability loss; composite degrades in ways neither component would alone
- **Representation mismatch** — human and AI solving slightly different problems because internal representations diverged; invisible until catastrophic

### What a well-functioning composite requires
- Shared problem representation — both nodes working on the same formulation
- Explicit uncertainty signaling — AI communicates confidence, not just answers
- Dynamic authority allocation — who leads on which subproblem shifts as the problem evolves
- Productive friction — a composite that never disagrees has silenced one node

---

## OODA Decomposition for the PM

### The decomposition

| Phase | Owner | Rationale |
|-------|-------|-----------|
| **O1 — Observe** | AI primary | Sensor fusion, pattern detection, recall without fatigue. Human doing first-O alone is slower and noisier. |
| **O2 — Orient** | Composite | Destruction and reconstruction of mental models. AI brings pattern libraries and consistency; human brings contextual judgment, stakes awareness, skin-in-the-game heuristics. |
| **D — Decide** | Human | Requires someone who bears the consequences. Fog is thickest here. Human judgment least replaceable. |
| **A-prep** | AI | Planning, dependency mapping, scenario modeling. |
| **A-exec** | Human | Execution is yours - create Jira issues for me in the managerial backlog. But AI observes in real time, feeds directly into next O1, including failure to act. |



---

## Personas

### Commander Donland — the PM running the loop

**Role**: Project Manager / Commander. Bears the consequences. Final call on Decisions.

**A day in the life**:

- **09:00 — Projects Dashboard.** Donland lands on the Projects Dashboard. Each Project is a status card colored red / orange / yellow / green, derived from the latest SitRep's overall assessment vs. its assigned Playbook. He scans for trouble in seconds — anything red or orange gets opened first.
- **Reading a SitRep.** For each problem Project he opens the latest SitRep: situation assessment narrative, Variables snapshot, proposed Decisions. When the assessment surprises him in a legitimate way — *"Active Bug Count = 0 — but Friday afternoons routinely run 1–2"* — he creates a **FRAGO** to override the Playbook expectation in flight: *"belay that on Fridays, ≤3 OK"*. FRAGOs are short markdown bodies with optional time/scope filters; Gjallarhorn reads them alongside the Playbook on the next SitRep.
- **Querying Gjallarhorn.** When the SitRep doesn't answer the question he has, he opens the chat. Gjallarhorn has CRUDL access to platform entities and can search, list, and inspect anything in his context.
- **Making Decisions.** Each accepted Decision branches into exactly one of three mutually-exclusive outcomes: a new FRAGO, an extension of Situational Awareness, or a `HUGINN`-tagged Jira issue created via the Jira API.
- **Verifying.** He glances at Action Stations — a read-only sync of `HUGINN`-tagged Jira issues — to confirm what landed. Resolution happens in Jira itself; Huginn does not edit Jira beyond creating these issues.

**Implications for the product** (to carry into ESM):
- Primary landing surface is the **Projects Dashboard** (color-coded health), not a generic dashboard or a single-Project SitRep.
- **Playbook** is the user-authored guidance for what good looks like. Composed of metadata + a Workflow markdown body + a structured list of PlaybookVariables. Versioned. Shared: one Playbook can be assigned to many Projects. Each Project pins a (Playbook, version), auto-tracking the latest version by default.
- **FRAGO** is a per-Project markdown override of Playbook expectations with optional scope (day-of-week, date range, Sprint/Milestone) and an optional `PlaybookVariable` tag. May retune a variable's `interpreting` for a window; cannot introduce new variables. Not a watcher with triggers — it modifies how SitReps are produced.
- **Decision** has a 3-branch acceptance flow (FRAGO / Situational Awareness extension / `HUGINN`-tagged Jira issue), mutually exclusive per Decision.
- **Action Stations** is a read-only mirror of `HUGINN`-tagged Jira issues. The only Huginn → Jira write is the issue creation from Decision Branch C. No annotation, no comment write-back.
- **Jira / GitLab / etc.** are systems of record for raw work data. Huginn ingests via DataSources; the only thing it writes back to Jira is `HUGINN`-tagged issues from accepted Decisions.

---

## Key Entities

Huginn's domain is organized into four concerns: the **canonical work model** (what we analyze), **command & doctrine** (how we decide and act), **measurement & events** (what we observe), and **identity & configuration** (who and where).

**Ingestion principle**: the analytical layer operates on canonical types (`UnitOfWork`, `Milestone`, `Sprint`, `Increment`). Adapters translate source-system concepts at the edge:

- Jira Issue / GitLab Issue / GitHub Issue / Linear Ticket → **UnitOfWork**
- Jira Version / GitLab Milestone / GitHub Milestone / Linear Project → **Milestone** *(the planning container — mutable scope, due date, burndown target)*
- Jira Sprint / GitLab Iteration → **Sprint**
- *(post-MVP)* GitLab Release / GitHub Release / Jira Version with `released=true` → **Release** *(the artifact — immutable, tag-anchored, realizes one or more Milestones)*

GitLab and GitHub separate the planning container (Milestone) from the shipped artifact (Release). Jira conflates them into a single Version entity that flips a `released` flag. The canonical model treats them as two distinct types so OODA-relevant signals (burndown, scope drift, commitment) attach to the Milestone, while artifact-shaped questions (what shipped, regression baseline) attach to the Release. MVP only ingests Milestone; Release is reserved for a later iteration.

For synchronized surfaces (Action Stations), the upstream tool remains system of record. For analytics, the canonical projection is authoritative.

### Canonical Work Model

| Entity | Source of truth | Notes |
|--------|----------------|-------|
| **UnitOfWork** | Upstream tool (Jira etc.), mirrored | The atom of trackable work. UoWs created via Decision Branch C are tagged `HUGINN` in Jira; Action Stations is the read-only mirror of these. Otherwise UoWs are normal engineering work flowing to Milestones. |
| **Milestone** | Upstream tool, mirrored | The planning target — a forward-looking, scope-mutable container with a due date. UoWs commit to it; Sprints target it; burndown is computed against it. (GitLab/GitHub Milestone, Jira Version, Linear Project.) |
| **Sprint** | Upstream tool, mirrored | Time-boxed cohort of UoWs targeting a Milestone. Sprint burndown is the short-cycle view; Milestone burndown is the long-cycle view. |
| **Release** *(post-MVP)* | Upstream tool, mirrored | The shipped artifact — immutable, tag-anchored, references the Milestone(s) it realizes. Surfaces artifact-shaped signals (deployed scope, regression baseline). Not in MVP scope; placeholder so the rename is intentional rather than ambiguous. |

### Command & Doctrine

| Entity | Source of truth | Notes |
|--------|----------------|-------|
| **SitRep** | Huginn | Generated per Project after a successful sync (subject to SitRep cadence, which may be coarser than sync cadence). **Generation contract**: Gjallarhorn receives `(SituationalAwareness, active Playbook workflow + variables, enabled in-window FRAGOs, data: {...} for the period under assessment)` and returns a situation assessment narrative + proposed Decisions + `variables: [{name, abbrev, value, color, hover}, …]`. The variables output is stored as the embedded `variables_snapshot` JSON (canonical, immutable record of what Gjallarhorn saw at time T against PlaybookVersion V with active FRAGOs applied) and denormalized to `VariableDatapoint` rows for trend queries. Read-only once finalized. |
| **Decision** | Huginn | DA-loop primitive. Proposed by Gjallarhorn in each SitRep, accepted/rejected by Commander with rationale. **Accepting branches into exactly one of three mutually-exclusive outcomes**: (a) create a new FRAGO, (b) append an entry to the **workspace** Situational Awareness capsule, or (c) create a `HUGINN`-tagged Jira issue via the Jira API. Full history is the DA-loop log. |
| **FRAGO** | Huginn | Per-Project, in-flight override of Playbook expectations. Free-form markdown body with optional scope (day-of-week, date range, Sprint/Milestone) and an optional `PlaybookVariable` tag. **May retune the `interpreting` of an existing PlaybookVariable for its effective window; cannot introduce new variables.** Has an `enabled` flag the Commander toggles from the list/detail view — disabled FRAGOs are excluded by Gjallarhorn at SitRep generation regardless of their effective window, useful for short-term suspension. Gjallarhorn reads enabled, in-window FRAGOs alongside the Playbook when generating a SitRep. Soft-delete (revoke) preserves history; revoked FRAGOs cannot be re-enabled. Not a watcher — does not trigger; modifies how SitReps are produced. |
| **SituationalAwareness** | Huginn | **Workspace-global** durable narrative memory (one versioned capsule per tenant/workspace, not keyed by Project). Extended via Decision Branch B; read by Gjallarhorn **for every** SitRep alongside that Project's Playbook and FRAGOs. |
| **Playbook** | Huginn | What good looks like for a project. Composed of (a) **metadata** — name, description; (b) a **Workflow** — free-form markdown describing the OO/DA narrative for this Project, who is who, what to look for; (c) an ordered list of **PlaybookVariables** (structured). Workflow can be typed inline, uploaded as MD, or pulled from Mimir Server (post-MVP). Shared: one Playbook can be assigned to many Projects. Distinct from the OO/DA *procedures* run internally by Gjallarhorn. |
| **PlaybookVersion** | Huginn | Immutable snapshot of a Playbook. Created on every Playbook edit. Has version number, change summary, author, `workflow_markdown`, and a snapshot of the PlaybookVariables defined at that version. A Project pins a (Playbook, version) — auto-tracks latest by default; can be pinned explicitly to keep an older version. |
| **PlaybookVariable** | Huginn | Per-PlaybookVersion definition of one measurement. Fields: `name` (e.g. "Cycle Time"), `abbreviation` ("CT"), `calculating` (free text — may be a JQL query, a count/ratio expression, or a natural-language prompt; the Agent decides how to apply), `interpreting` (rules mapping value → color, e.g. "<5d & not climbing → green; climbing → orange; >5d → red"), `hover` (tooltip text shown on the project card and in the SitRep snapshot). FRAGOs may retune `interpreting` for a window. |

**Project view tabs** are **system-defined**, not Playbook-derived:
- **Vitals** — hardcoded, system-wide for every Project. Contains: Identity / Playbook / Sync metadata cards; a hardcoded **Transparency** card; and the **informer bar** — one colored dot per `PlaybookVariable` on the active PlaybookVersion (in declared order), showing `name (abbrev)` with value and color on hover.
- **Variables** — one diagram per `PlaybookVariable` on the active PlaybookVersion, showing `VariableDatapoint` history for the selected period. Fixed period filter: today / yesterday / this week / previous week / 30 days. When no Playbook is assigned (or the Playbook has no Variables), this tab shows an empty state.
- **Adapter-driven tabs** — one tab per registered ingestion adapter, contributing system-defined views of ingested data. Today: the **Increments** tab, contributed by `ingestion/adapters/gitlab_commits.py`. New adapters add new tabs as they land; the tab set is determined by code, not by Playbook configuration.

### Measurement & Events (append-only)

| Entity | Source of truth | Notes |
|--------|----------------|-------|
| **UoWStateChange** | Huginn (ingested) | Transitions of a UoW (state, assignee, estimate, sprint). Each change *advances* the UoW through its lifecycle. Feeds cycle time, lead time, estimation drift. |
| **Increment** | Huginn (ingested) | A discrete contribution — commit, PR, review, doc update — attributed to a Contributor and linked to the UoW it advances. |
| **TestResult** | Huginn (ingested, XRay) | Red / green / gray; feeds Quality variable. Shown in the Canonical Work Model diagram (UoW ← verified by — TestResult) rather than Measurement, because the relationship is to the work item, not the Project aggregate. |
| **VariableDatapoint** | Huginn (computed) | Single (Project, PlaybookVariable, time T, value, color, agent_invocation_ref) row. Denormalized from `SitRep.variables_snapshot` so trend queries (Variables Deep-Dive, history charts) stay cheap. When the Agent cannot compute a value (insufficient data, tool failure), `color = 'grey'` and `value = null`. |

### Cross-cutting

| Entity | Source of truth | Notes |
|--------|----------------|-------|
| **Artifact** | Huginn (user-supplied or ingested) | PDFs, chat extracts, Confluence links, meeting notes. Attachable to UoWs, Decisions, and SitReps — spans all concerns. Cross-linking fabric. |

### Identity & Configuration

| Entity | Source of truth | Notes |
|--------|----------------|-------|
| **User** | Huginn | Huginn account. Roles: `Commander`, `Analyst` (TBD if distinct). |
| **Contributor** | Huginn (reconciled) | Developer identity unified across git author / Jira assignee / Slack handle. Derived profile: Pathfinder / Mastermind / Firefighter / Observer. |
| **Project** | Huginn (imported) | An imported project from a single DataSource (one upstream project = one Project; e.g., one GitLab project). Defines the analytical scope and pins a (Playbook, version) it is evaluated against. Has a **sync schedule** — `daily | hourly | minutely` — each with a pattern (e.g. `daily 08:00`, `hourly :30`, `every 5m from :00`). **SitRep cadence may be coarser than sync cadence** to bound LLM cost (see Open Questions). **Cannot be created from a blank form** — only via Project Import. |
| **DataSource** | Huginn config | Connection to GitLab / Jira / etc. (credentials, base URL, expiry tracking). Source of one or more Projects via import. |
| **Agent** | Huginn config | Reusable AI task definition. Fields: `name`, `model` (e.g. `claude-sonnet-4.6`), `base_prompt`, `embedding` (vector index handle, optional), `context_data` / `howto` (optional). Gjallarhorn's behaviors — compute a PlaybookVariable, draft a SitRep section, propose a Decision — are concrete Agent invocations. **Model id and prompt strings live here, not on Playbook or PlaybookVariable**, so swapping Claude for a local model is a config change. |
| **AgentInvocation** | Huginn (append-only) | One row per Agent run: `agent`, `inputs_hash`, `started_at`, `finished_at`, `status`, `output_ref` (e.g. SitRep section id, VariableDatapoint id). Lets us audit *why* a Variable got the value it did at time T, and replay against a different Agent if needed. |

---

## Domain Model (Draft)

Read the **overview** first for the spine; then drill into the four focused views (each small enough to read without edge clutter).

### Overview

```mermaid
erDiagram
    DataSource ||--o{ Project : "imported from"
    Project ||--o{ UnitOfWork : contains
    Project ||--o{ Milestone : targets
    Project ||--o{ SitRep : produces
    Project ||--o{ FRAGO : "scoped to"
    Project }o--|| Playbook : assigned
    Playbook ||--o{ PlaybookVersion : versions
    PlaybookVersion ||--o{ PlaybookVariable : defines
    Sprint }o--|| Milestone : targets
    Sprint ||--o{ UnitOfWork : contains
    SitRep ||--o{ Decision : proposes
    User ||--o{ Decision : makes
    User ||--o{ FRAGO : issues
```

### Canonical Work Model

```mermaid
erDiagram
    Project ||--o{ Milestone : targets
    Project ||--o{ Sprint : runs
    Project ||--o{ UnitOfWork : contains
    Project ||--o{ Contributor : "team roster"
    Sprint }o--|| Milestone : targets
    Sprint ||--o{ UnitOfWork : contains
    UnitOfWork }o--o| Milestone : "commits to"
    UoWStateChange }o--|| UnitOfWork : advances
    Increment }o--|| UnitOfWork : "contributes to"
    Contributor ||--o{ UnitOfWork : "assigned to"
    Contributor ||--o{ Increment : authors
    UnitOfWork ||--o{ TestResult : "verified by"
```

### Command & Doctrine

```mermaid
erDiagram
    SituationalAwareness {
        bigint id PK
    }
    Project ||--o{ SitRep : produces
    Project ||--o{ FRAGO : "scoped to"
    %% One SA row per workspace — not FK-linked to Project (Act 12)
    Project }o--|| Playbook : assigned
    Project }o--o| PlaybookVersion : "pinned (else auto-tracks latest)"
    Playbook ||--o{ PlaybookVersion : versions
    PlaybookVersion ||--o{ PlaybookVariable : defines
    FRAGO }o--o| PlaybookVariable : "may override interpreting"
    User ||--o{ Decision : makes
    User ||--o{ FRAGO : issues
    SitRep ||--o{ Decision : proposes
    Decision }o--o| FRAGO : "may create"
    Decision }o--o| SituationalAwareness : "may extend"
    Decision }o--o| UnitOfWork : "may create HUGINN issue"
```

**Decision outcome semantics**: an accepted Decision creates **exactly one** of FRAGO / SituationalAwareness extension / `HUGINN`-tagged UoW. The mermaid `}o--o|` cardinalities show each as optional individually; XOR across the three is enforced at the application layer.

#### Agents

```mermaid
erDiagram
    Agent ||--o{ AgentInvocation : runs
    AgentInvocation }o--o| VariableDatapoint : "may produce"
    AgentInvocation }o--o| SitRep : "may produce"
```

`Agent` carries the model id, base prompt, and optional embedding/context. Every AI step in Gjallarhorn — computing a PlaybookVariable, drafting a SitRep section, proposing a Decision — is an `AgentInvocation`. This keeps doctrine entities (Playbook, PlaybookVariable, FRAGO) free of model/prompt strings.

### Measurement

```mermaid
erDiagram
    Project ||--o{ VariableDatapoint : measures
    PlaybookVariable ||--o{ VariableDatapoint : "shape of"
    SitRep ||--o{ VariableDatapoint : "snapshots (denormalized; embedded JSON is canonical)"
    AgentInvocation }o--o| VariableDatapoint : "may produce"
```

The embedded `SitRep.variables_snapshot` JSON is the canonical record of what Gjallarhorn saw at SitRep generation time. `VariableDatapoint` rows carry the same values denormalized for cheap trend queries (Variables Deep-Dive, history charts). FRAGOs may tag a `PlaybookVariable` and override its `interpreting` rules for a window, but never introduce new variables.

### Cross-cutting — Artifact Attachments

```mermaid
erDiagram
    UnitOfWork ||--o{ Artifact : attached
    Decision ||--o{ Artifact : attached
    SitRep ||--o{ Artifact : attached
```

### Work Flow DAG

How work originates and flows toward Milestone as the planning sink. Every path is directed and acyclic — Milestone has no outgoing edges within the analytical layer. The two paths UoW→Sprint→Milestone and UoW→Milestone (direct fix-version equivalent) form a diamond, not a cycle. *(Post-MVP: a Milestone is realized by a Release artifact; that edge is intentionally omitted from MVP analytics.)*

```mermaid
flowchart LR
    DataSource -->|ingests| Increment
    DataSource -->|ingests| UoWStateChange
    DataSource -->|ingests| TestResult
    Contributor -->|authors| Increment
    Contributor -->|"assigned to"| UoW
    Increment -->|"contributes to"| UoW
    UoWStateChange -->|advances| UoW
    UoW -->|"planned in"| Sprint
    Sprint -->|targets| Milestone
    UoW -->|"commits to"| Milestone
    UoW -->|"verified by"| TestResult
```

**Open questions** (to resolve before ESM Activity 04 formalizes this):
1. **UoW ↔ Milestone**: can a UoW commit directly to a Milestone without going through a Sprint? (Assumed yes — matches Jira's `fixVersion` without an active sprint.)
2. **Decision outcome XOR enforcement**: enforce mutual exclusion at DB level (CHECK constraint over three nullable FKs) or at application level only? Affects how loud failures are when invariants drift.
3. **PlaybookVersion content immutability**: confirmed immutable in MVP. Future question: rebase / cherry-pick across versions?
4. **Contributor reconciliation**: identity unification across git/Jira/Slack is a known-hard problem. MVP assumes manual mapping table.
5. **Single-Project MVP?**: the model supports N Projects, but MVP UI may treat the Projects Dashboard as the single landing surface and not expose Project-switching elsewhere. Affects navigation and scope-picker placement.
6. **SitRep cadence vs sync cadence**: sync can be `minutely`; SitRep generation is LLM-expensive. Likely SitReps run on a coarser beat (≥ hourly) even when sync is minutely; `VariableDatapoint` may still tick per-sync. To confirm before implementation.
7. **PlaybookVariable.calculating typing**: leave as free text and let the Agent route between deterministic evaluation (e.g. JQL, count expression) and LLM interpretation, or add an explicit `calc_kind: query | formula | prompt` hint? Current default: free text + Agent decides.

**Resolved** (no longer open):
- ~~Playbook scope~~: shared across Projects, versioned, Project pins (Playbook, version) with auto-track-latest as default. Composed of metadata + Workflow markdown + ordered list of `PlaybookVariable` (structured).
- ~~FRAGO trigger semantics~~: FRAGO is not a watcher. It is a markdown override of Playbook expectations consumed by Gjallarhorn at SitRep generation time. May retune `interpreting` of an existing PlaybookVariable for its window; cannot introduce new variables.
- ~~SitRep ↔ Variable storage~~: **embed in SitRep** (`variables_snapshot` JSON, canonical) **+ denormalized `VariableDatapoint` rows** for trend queries. Both written at SitRep generation time.
- ~~Variables as platform Master Variables~~: Variables are PlaybookVersion children (`PlaybookVariable`). The seven master variables (Transparency, Throughput, Cycle & Lead Time, Rework, Quality, Complexity, Contribution) become the **starter set on FeatureFactory Playbook** (the seed Playbook), not platform invariants. `MasterVariableDefinition` is removed.
- ~~AI model identity location~~: model id, base prompt, and embedding live on `Agent`, not on Playbook or PlaybookVariable. Every AI step is an `AgentInvocation` for audit.

---

## Data Foundation — What We Will Have

| Source | Signal type | Resolution |
|--------|------------|------------|
| GitLab/GitHub (no squash commits) | Work in progress, commit frequency, PR cycle time | Hours |
| Jira (issue-to-branch traceability) | Ticket state, flow efficiency, estimation drift | Daily |
| FastMCP wrapper | AI-queryable interface to Huginn | Real-time |
| Messaging (eg emails/Slack messages etc.) | outstanding items, blockers, risks
| Zoom Notes | MFUs -> outstanding items, blockers, risks
| Custom Artifacts | whatever PDF/MD files we can NER-extract info from & fit into our
| Test State | from XRay: red/green/gray
| Coverage | command like tools/existing reports in the repo structure - does green from test state means we are good or it means we have few tests?
[ To be extended later]

## How do we read data
These are dimensions we analyze through the OODA cycle: codebase, backlog, production cycle, release, [infra] environment, UX (user experience), DX (developer experience).

**Variables are user-defined per Playbook** (see `PlaybookVariable` in Command & Doctrine). The set below is the **starter pack** shipped with **FeatureFactory Playbook** (the seed Playbook); any Playbook may add, remove, or replace any of them. FRAGOs may retune a variable's `interpreting` for a window, but cannot introduce new variables.

The **seed Playbook** (**FeatureFactory Playbook**) ships with each starter Variable already defined — name, abbreviation, default `calculating`, default `interpreting`, and `hover`. Donland can clone or edit **FeatureFactory Playbook**. Project view tabs are system-defined (see *Project view tabs* above) and do not depend on Playbook configuration.

Default starter Variables:

TRANSPARENCY: do we know whats actually happening - do our systems contain enough fresh data to make decisions?
THROUGHPUT: WoW do we push more work or less, both as user-visible story points and hidden function-based complexity-adjusted pts?
CYCLE & LEAD TIME: WoW do we push units of work faster or slower? Because of engineering or no (cycle time for eng activities)?
REWORK: What % of what we are pushing is rework? What kind of rework - downstream fucked it up?
QUALITY: test success rate  & test coverage, number of Defects and "Mean Time to Evict"
COMPLEXITY: looking at the current project (lets assume 1 project is one repo; can be a collection of repos later) whats the maintanability index?
CONTRIBUTION: in terms of profile "Y for new code and X axis for churn in existing" who are pathfinders (new code mostly), masterminds (both new and churn - all over the system), firefighters (mostly churn existing codebase), observers (their contribution is too small to classify them eiether way)
[ To be extended later]

SitRep: momentary snapshot of the current values + AI performing first pass of analysis: hypotheses on why there are undesired deviations + suggested Actions to test hypotheses + Decisions to make → execute.

## OO Procedure (Gjallarhorn internal)

> *Note*: this is Gjallarhorn's internal procedure for producing a SitRep — system behavior, not the user-editable **Playbook** entity. The Playbook entity (Workflow markdown + ordered PlaybookVariables) is what good looks like for a specific Project; this procedure describes how Gjallarhorn evaluates against it.

**Single-call AI contract**: Gjallarhorn assembles `(SituationalAwareness, active Playbook workflow + variables, enabled in-window FRAGOs, data: {...} for the period under assessment)` and calls the AI once. The AI returns a situation assessment narrative + proposed Decisions + `variables: [{name, abbrev, value, color, hover}, …]`. The variables output is written into `SitRep.variables_snapshot` (canonical) and denormalized to `VariableDatapoint` rows (for trend queries on the Variables tab). The numbered steps below describe the doctrine Gjallarhorn follows when assembling that context and interpreting the response.

0. Load Situational Awareness / latest SitRep / active FRAGOs / pinned PlaybookVersion (Workflow + PlaybookVariables) — what we know from previous OODA passes, things to watch for per commander's overrides.
1. Check transparency — how stale are updates on Jira issues & pushes? Stale (not today) → flag first.
2. Reconstruct the flow: how Unit of Work travels into the Milestone. If we don't know — flag it.
3. Operate on Sprints → culminates in Milestone. Check burndown — burning down? scope expanding? no visible progress measured in closed stories?
4. Check quality of reqs: too big (root cause for no burndown). Bad → flag for improvement.
5. Assess quality of the pipeline. Unstable → flag for fix.
6. Assess architecture readiness — anything missing for the stories at hand? Missing → flag for action.
[ etc — full list to cover every PlaybookVariable in the active Playbook ]

Output: a **SitRep** with situation assessment ("how bad things are") and proposed **Decisions** ("how to set things straight").

## DA Procedure (Gjallarhorn internal)

> *Note*: this is the system behavior of the Decision-Action loop, not the user-editable Playbook.

1. Take a sitrep covering every PlaybookVariable in the active Playbook (think "Project Status Report").
2. Read problematic areas and propose Decisions: *"I agree with your assessment; my decision is that we need a Daily Increment pushed by every developer. We shall have a list of those who is listed among authors but haven't pushed anything today."*
3. Commander accepts / rejects each Decision. Acceptance branches into exactly one of three outcomes: **(a)** new FRAGO ("Disregard broken builds tomorrow"), **(b)** extension of Situational Awareness ("This is because of the GitLab outage — expect unsuccessful data dumps tomorrow"), or **(c)** new Jira issue tagged `HUGINN` ("Create a Task for the QA Architect to draft AI testing strategy").
4. Collect content of the OODA cycle and perform write-back: update Situational Awareness / extend/add/drop FRAGOs / save SitRep. *(The Playbook entity itself is edited deliberately and separately — it is doctrine, not session output.)*

Each AI step in the OO and DA procedures (compute a PlaybookVariable's value, draft a SitRep section, propose a Decision) is a named **Agent invocation** — see the Agents entity. Agents carry the model id, base prompt, and optional embedding; doctrine entities (Playbook, PlaybookVariable, FRAGO) carry no model or prompt strings, so the model+prompt mix can evolve independently.

# Stack

> Full architectural decisions in `docs/architecture/SAO.md`.

1. **Data**: PostgreSQL + Django ORM. State history as append-only tables (no graph DB). Redis for Celery broker + cache.
2. **Application**: Docker Compose deployment — `web` (Django), `worker` (Celery), `beat` (Celery scheduler), `redis`, `db` (PostgreSQL).
    - Django apps: `ingestion/`, `analytics/`, `sitrep/`, `ui/`, `gjallarhorn/`, `agents/`
    - `agents/` holds Agent definitions and the dispatch layer. Gjallarhorn calls into Agents rather than embedding model/prompt strings inline; every AI step (variable computation, SitRep section drafting, Decision proposal) is an `AgentInvocation` audit row.
    - Extraction jobs (Celery Beat) pull data from GitLab (`python-gitlab`), Jira (`jira`) on the per-Project sync schedule (`daily | hourly | minutely`); further sources TBD.
    - Gjallarhorn AI assesses situation per OO → SitRep (FastMCP interface)
    - Django + HTMX + Apache ECharts for the PM dashboard and DA chat
    - Configuration externalized as env vars: API tokens (Jira/GitLab), Anthropic key, base model id, and per-Agent prompt overrides — none of which live on Playbook entities.
3. **Deploy**: AWS Elastic Beanstalk + GitLab Pipelines. Docker Compose in prod.
