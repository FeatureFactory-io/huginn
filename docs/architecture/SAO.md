# Huginn: System Architecture Overview

> *Last updated: April 2026 — initial DTA pass*

---

## Executive Summary

Huginn is a Human-AI OODA composite for engineering PMs. It ingests development signals from external sources on an hourly schedule, computes Master Variables (TRANSPARENCY, THROUGHPUT, CYCLE TIME, REWORK, QUALITY, COMPLEXITY, CONTRIBUTION), and produces a SitRep at the morning daily planning session. The PM conducts Observe-Orient (OO) with Gjallarhorn AI, then makes Decisions and defines Actions (DA).

**Key architectural decisions:**
- Django MTV + Celery hybrid: web UI and async ingestion in one monorepo
- PostgreSQL + Django ORM — relational model sufficient, no graph DB needed
- Docker Compose everywhere — dev/prod parity, no K8s complexity
- HTMX partial updates + Apache ECharts — server-rendered, testable UI
- AWS Elastic Beanstalk + GitHub Actions — simple deploy target for internal tool

---

## 1. Application Blocks

**Pattern:** Hybrid — Django MTV for web UI, Celery event-driven for async ingestion.

**Django apps:**

| App | Responsibility |
|---|---|
| `ingestion/` | Extraction jobs per source (GitLab, Jira, …). Celery tasks, connector clients, raw data models. |
| `analytics/` | Master Variable computation (THROUGHPUT, CYCLE TIME, REWORK, QUALITY, COMPLEXITY, CONTRIBUTION). Reads from ingested data, writes computed metrics. |
| `sitrep/` | SitRep generation, FRAGO store, Situational Awareness snapshots. |
| `ui/` | Django views, HTMX responses, ECharts JSON endpoints, templates. |
| `gjallarhorn/` | FastMCP wrapper exposing Huginn data to AI. Gjallarhorn AI interface. |

**UI architecture:**
- Rendering: server-rendered Django templates
- Interaction: HTMX partial updates (no full page reloads for dashboard interactions)
- Layout: multi-panel (navigation + dashboard + detail/chat)
- Design system: Bootstrap 5 — base component library, grid, typography, utilities (CDN)
- Charts: Apache ECharts — data served as JSON from Django views, chart rendered client-side (CDN)

**Dependency rules:**
- `analytics/` → reads from `ingestion/` models
- `sitrep/` → reads from `analytics/` + `ingestion/`
- `ui/` → reads from all apps, no business logic
- `gjallarhorn/` → reads from `sitrep/` and `analytics/`
- `ingestion/` → no internal dependencies

---

## 2. Integration & API Design

**Web UI:** Django views only — no REST API for v1. All UI interactions are HTMX swaps against Django views.

**AI interface:** FastMCP wrapper (`gjallarhorn/`) exposing Huginn data as MCP tools to Gjallarhorn AI.

**Inter-service communication:** Redis + Celery queue (async). Django web process enqueues tasks; Celery workers consume them.

**External source connectors — v1:**

| Source | Library | Version | Notes |
|---|---|---|---|
| GitLab | `python-gitlab` | 8.x | Full REST API coverage: commits, MRs, branches, members |
| Jira | `jira` (pycontribs) | latest | Better Jira-specific coverage than `atlassian-python-api` |

**External source connectors — TBD (resolve before respective sprint):**

| Source | Library |
|---|---|
| Zoom Notes | TBD |
| Slack / email | TBD |
| XRay (test state) | TBD |

**Ingestion cadence:** hourly Celery beat schedule per source. OODA loop runs daily at morning planning session.

**Contract approach:** no formal REST contract for v1 (single consumer: the web UI). MCP tools documented inline in `gjallarhorn/`.

---

## 3. Code Organization

**Repository:** monorepo — single repo, all code together.

**Top-level layout:**
```
huginn/
├── ingestion/
│   ├── models/
│   ├── services/        # connector clients, extraction logic
│   ├── tasks.py         # Celery tasks
│   └── tests/
├── analytics/
│   ├── models/
│   ├── services/        # Master Variable computation
│   └── tests/
├── sitrep/
│   ├── models/
│   ├── services/        # SitRep generation, FRAGO logic
│   └── tests/
├── ui/
│   ├── views/
│   ├── templates/
│   └── tests/
├── gjallarhorn/
│   ├── mcp_tools/       # FastMCP tool definitions
│   └── tests/
├── huginn/              # Django project settings
│   ├── settings/
│   │   ├── base.py
│   │   ├── local.py
│   │   └── production.py
│   ├── urls.py
│   └── celery.py
├── docs/
│   └── architecture/
│       ├── SAO.md
│       └── ADRs/
├── docker-compose.yml
├── Makefile
├── pyproject.toml
└── manage.py
```

**Naming conventions:**
- Files: `snake_case.py`, templates: `kebab-case.html`
- Classes: PascalCase, functions/methods: snake_case
- Constants: UPPER_SNAKE_CASE
- URLs: kebab-case (`/sitrep/latest/`)

**Shared utilities:** `huginn/utils/` for cross-cutting concerns (logging helpers, decorators). All apps may import from `huginn/utils/`; no circular imports.

---

## 4. Data Architecture

**Database engine:** PostgreSQL 16+. Rationale: relational model is sufficient — status history as append-only table, aggregation queries via raw SQL where needed. No graph traversal requirements in v1.

**Schema strategy:**
- Django migrations (numbered, tracked in VCS)
- `factory_boy` + `Faker` for test data
- Expand-contract pattern for breaking schema changes

**Core model patterns:**

*UnitOfWork status history (append-only — no graph edges needed):*
```python
class IssueStatusEvent(Model):
    issue_id    = CharField()   # external ID (e.g. "ISS-1")
    status      = CharField()   # "backlog", "planned", "in_progress", "done"
    recorded_at = DateTimeField()
    source      = CharField()   # "jira", "gitlab"
```

**Data access:**
- Django ORM for all CRUD and simple queries
- Raw SQL (via `connection.execute()`) for complex aggregations: cycle time distributions, contribution quadrant coordinates, burndown series

**Caching:**
- Redis as Django cache backend
- Cache computed Master Variable results (TTL: 1 hour, invalidated on new ingestion run)
- Session storage: database-backed (default Django)

---

## 5. Test Strategy

**Frameworks:**
- `pytest` + `pytest-django` as test runner
- Django `TestCase` for unit/integration (DB isolation via transaction rollback)
- Django `LiveServerTestCase` for UI integration tests where needed
- `factory_boy` for test data generation
- `responses` library for mocking external HTTP calls (GitLab, Jira APIs)

**Test pyramid:**
- Unit: services, utilities, Master Variable computation logic
- Integration: Django views (test client), Celery task logic, DB queries
- No E2E (Playwright) for v1 — internal tool, overhead not justified

**ECharts testing approach:** ECharts data served from Django JSON views. Tests assert on the JSON response structure — no browser rendering needed.

**CI gate:** all tests must pass before merge to `main`.

**Makefile targets:** `make test`, `make test-unit`, `make test-integration`

---

## 6. Performance & Scalability

**Load profile:**
- Concurrent users: 2–5 (internal team)
- Daily burst: morning planning session (~9:00)
- Data volume: grows linearly with team size and sprint count
- Read-heavy: dashboards read far more than ingestion writes

**Async processing:**
- Celery Beat: one scheduled task per source, hourly
- Celery workers: 2 workers sufficient for v1
- Priority queues: not needed for v1 (all jobs equal priority)

**Caching:**
- Redis: Celery broker + Django cache
- Computed Master Variables cached for 1 hour
- Static assets: WhiteNoise (served by Django, no CDN for v1)

**Connection pooling:** Django default (persistent DB connections via `CONN_MAX_AGE`).

**Scaling:** vertical (larger EB instance) before horizontal. Re-evaluate at 10+ users.

---

## 7. Error Handling & Resilience

**Celery job failure policy:**
- Retry with exponential backoff (3 attempts, 60s / 120s / 240s)
- On exhaustion: log at ERROR level, skip this run, surface staleness via TRANSPARENCY Master Variable
- No dead-letter queue for v1 — staleness is visible to the PM, not a silent failure

**External API failure taxonomy:**

| Error type | Handling |
|---|---|
| Rate limit (429) | Retry after `Retry-After` header; count as stale if exhausted |
| Auth failure (401/403) | Log at ERROR, alert via CloudWatch, skip |
| Timeout / network error | Retry with backoff, skip on exhaustion |
| Partial data (200 but empty) | Log at WARNING, store what was received |

**Graceful degradation:** TRANSPARENCY Master Variable explicitly tracks data freshness. Stale sources are visible on the dashboard — the PM knows to check the source directly.

**Idempotency:** ingestion tasks are idempotent — upsert pattern on external IDs, safe to re-run.

---

## 8. Infrastructure

**Runtime:** Docker Compose everywhere — development and production.

**Services:**
```yaml
services:
  web:     # Django (gunicorn in prod, runserver in dev)
  worker:  # Celery worker
  beat:    # Celery beat scheduler
  redis:   # Broker + cache
  db:      # PostgreSQL 16
```

**Local dev:** `make run` starts all services via `docker-compose up`. `.env` file provides local config.

**Production:** Docker Compose on AWS Elastic Beanstalk (Multi-container Docker platform). EB manages the EC2 instance; Compose manages the containers.

**No Kubernetes** — internal tool, team of 2–5, Compose complexity is sufficient.

---

## 9. CI/CD Pipeline

**Platform:** GitHub + GitHub Actions.

**Pipeline stages:**
```
lint (ruff) → test (pytest) → build (docker build) → deploy (eb deploy)
```

**Triggers:**
- `lint` + `test`: every push and PR
- `build` + `deploy`: merge to `main` only

**Artifact registry:** GitHub Container Registry (GHCR) for Docker images.

**Promotion gates:**
- Automated: all tests pass, ruff clean
- No manual gate for v1 (internal tool, low risk)

**Branch strategy:** trunk-based — short-lived feature branches, merge to `main` via PR.

---

## 10. Release & Rollback

**Deployment strategy:** AWS Elastic Beanstalk rolling update (default). Single environment for v1 — no staging/prod split until team grows.

**Version tagging:** `YYYY.MM.DD` calendar versioning — simple, no semver overhead for an internal tool.

**Rollback:** EB "Deploy previous version" via AWS console or `eb deploy --version`. Target: < 5 minutes.

**Release cadence:** continuous — every merge to `main` deploys automatically.

**Hotfix:** direct merge to `main` with `[hotfix]` prefix in commit message.

---

## 11. Observability

**Logging:**
- Structured JSON logging to stdout
- AWS CloudWatch Logs collects from EB automatically
- Log levels: DEBUG (dev), INFO (prod default), WARNING/ERROR for job failures
- Never log API tokens, credentials, or PII

**Metrics via CloudWatch:**
- Celery job failure rate (CloudWatch alarm: > 2 failures/hour → notify)
- EB instance CPU/memory (standard EB metrics)
- No Prometheus/Grafana for v1 — CloudWatch is sufficient

**Correlation IDs:** Django middleware injects `X-Request-ID` header; included in all log entries.

**Alerting:** CloudWatch alarm → email notification to PM on Celery exhaustion.

---

## 12. Config & Secrets

**Config source:** environment variables everywhere.

**Local:** `.env` file (gitignored), loaded by `docker-compose.yml`.

**Production:** AWS EB environment properties (set via EB console or `eb setenv`).

**Required env vars:**

| Variable | Description |
|---|---|
| `SECRET_KEY` | Django secret key |
| `DATABASE_URL` | PostgreSQL connection string |
| `REDIS_URL` | Redis connection string |
| `GITLAB_URL` | GitLab instance URL |
| `GITLAB_TOKEN` | GitLab personal access token |
| `JIRA_URL` | Jira instance URL |
| `JIRA_USER` | Jira username/email |
| `JIRA_TOKEN` | Jira API token |
| `LLM_API_KEY` | LLM API key for Gjallarhorn |
| `ALLOWED_HOSTS` | Django ALLOWED_HOSTS |
| `DEBUG` | `True` locally, `False` in prod |

**Feature flags:** not needed for v1.

---

## 13. Security

**Authentication:** Django session-based auth. Username + password. Small team — no SSO/OAuth for v1.

**Authorization:** single-role (all authenticated users have full access). No RBAC needed for v1.

**Production hardening:**
- `DEBUG=False`
- `SECURE_SSL_REDIRECT=True`
- `SESSION_COOKIE_SECURE=True`
- `CSRF_COOKIE_SECURE=True`
- `ALLOWED_HOSTS` explicitly set

**CSRF:** Django built-in CSRF middleware (on by default). HTMX configured to send CSRF token.

**Input validation:** Django forms + model validation. No user-supplied data flows into raw SQL without parameterization.

**Dependency scanning:** `pip-audit` in CI pipeline. Block merge on critical CVEs.

---

## 14. Backup & Recovery

**Backup:** daily `pg_dump` to S3, triggered by Celery Beat task at 02:00.

**Retention:** 30 daily backups (1 month rolling window).

**RPO:** 24 hours — acceptable for internal analytics tool. If today's SitRep data is lost, re-ingestion from source systems restores it.

**RTO:** restore from S3 dump, `psql` restore, restart EB environment. Target: < 2 hours.

**Makefile targets:** `make backup`, `make restore BACKUP=<s3-key>`

---

## 15. Developer Experience

**IDE:** Cursor.

**Code quality:**
- Linter + formatter: `ruff` (replaces flake8 + black)
- Type checker: `mypy` (optional for v1, recommended)
- Pre-commit hooks: `ruff check`, `ruff format --check`
- Config: `pyproject.toml`

**Makefile targets:**

| Target | Action |
|---|---|
| `make provision` | Install all prerequisites (pip install) |
| `make run` | Start all services via Docker Compose |
| `make test` | Run full test suite |
| `make test-unit` | Run unit tests only |
| `make lint` | Run ruff check |
| `make format` | Run ruff format |
| `make backup` | Run pg_dump to S3 |
| `make shell` | Django shell in web container |

**Hot reload:** `runserver` in dev container with volume mount.

**Time-to-first-feature target:** new developer running tests within 30 minutes of `git clone`.

---

## 16. Documentation Strategy

**ADRs:** stored in `docs/architecture/ADRs/`. Standard format:
```
# ADR-NNN: Title
Status: Accepted | Superseded | Deprecated
Context: ...
Decision: ...
Consequences: ...
```

Write an ADR for every significant technology or architecture choice. This SAO.md is the compiled result; ADRs are the audit trail.

**Living documentation:**
- Sphinx-format docstrings on all public methods (`:param:`, `:return:`, `:raises:`)
- Type hints on all public functions
- Comments explain *why*, not *what*
- README hierarchy: root README → per-app README for non-obvious modules

**Knowledge base:** `docs/` in repo. No external wiki.

---

## Technology Stack

| Layer | Tool | Version | Install (macOS) | Install (Linux) | Verify |
|---|---|---|---|---|---|
| Language | Python | 3.12+ | `brew install python@3.12` | `apt install python3.12` | `python3 --version` |
| Framework | Django | 5.x | `pip install django` | `pip install django` | `django-admin --version` |
| Async | Celery | 5.x | `pip install celery` | `pip install celery` | `celery --version` |
| Broker/Cache | Redis | 7.x | `brew install redis` | `apt install redis` | `redis-cli --version` |
| Database | PostgreSQL | 16+ | `brew install postgresql@16` | `apt install postgresql` | `psql --version` |
| Charts | Apache ECharts | 5.x | CDN — no install | CDN — no install | loaded in base template |
| Design system | Bootstrap | 5.x | CDN — no install | CDN — no install | loaded in base template |
| Connector | python-gitlab | 8.x | `pip install python-gitlab` | `pip install python-gitlab` | `pip show python-gitlab` |
| Connector | jira (pycontribs) | latest | `pip install jira` | `pip install jira` | `pip show jira` |
| AI interface | FastMCP | latest | `pip install fastmcp` | `pip install fastmcp` | `pip show fastmcp` |
| Test runner | pytest + pytest-django | 8.x | `pip install pytest pytest-django` | `pip install pytest pytest-django` | `pytest --version` |
| HTTP mocking | responses | latest | `pip install responses` | `pip install responses` | `pip show responses` |
| Test data | factory_boy | latest | `pip install factory_boy` | `pip install factory_boy` | `pip show factory_boy` |
| Linter | ruff | 0.6+ | `pip install ruff` | `pip install ruff` | `ruff --version` |
| Container | Docker Compose | 2.x | `brew install docker` | `apt install docker-compose` | `docker compose version` |
| CI/CD | GitHub Actions | — | — | — | — |
| Deploy | AWS EB CLI | latest | `pip install awsebcli` | `pip install awsebcli` | `eb --version` |
| VCS | git | 2.x | `brew install git` | `apt install git` | `git --version` |
| Build | make | 4+ | bundled on macOS | `apt install make` | `make --version` |

---

## Connector Libs — Remaining Sources (TBD)

The following sources are planned but connector libs not yet selected. Resolve before the respective sprint:

| Source | Signal type | Lib |
|---|---|---|
| Zoom Notes | MFUs → outstanding items, blockers, risks | TBD |
| Slack / email | Outstanding items, blockers, risks | TBD |
| XRay | Test state: red/green/gray | TBD |

---

## Key Decisions Summary

| Domain | Decision | Rationale |
|---|---|---|
| DB | PostgreSQL + Django ORM, no graph | Relational sufficient; state history as append-only table; simpler ops |
| UI | Django + HTMX + ECharts | Server-rendered = testable; no SPA complexity; ECharts handles scatter/quadrant |
| Infra | Docker Compose everywhere | Internal tool; K8s overhead not justified |
| Deploy | AWS Elastic Beanstalk | Simple managed deploy for Docker Compose; no container orchestration needed |
| Async | Celery + Redis | Hourly ingestion jobs; standard Django async stack |
| Connectors v1 | python-gitlab + jira (pycontribs) | Both actively maintained; `jira` preferred over `atlassian-python-api` for Jira-specific coverage |
| Testing | pytest + Django test client, no E2E | Internal tool; browser E2E overhead not justified; ECharts tested via JSON endpoints |
| Observability | AWS CloudWatch | Co-located with EB; no additional tooling needed |

---

## Discovered Patterns & Lessons Learned

*Reserved — populated during and after implementation.*

### Critical Discoveries
*(none yet)*

### Retrospective Updates
*(none yet)*
