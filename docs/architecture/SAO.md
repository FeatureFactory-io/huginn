# Huginn: System Architecture Overview

> *Last updated: April 2026 — CloudFront + ACM + CDK `HuginnCdn` deployed; Route53 CNAME via idempotent custom resource; **HSTS** (`max-age=3600; includeSubDomains`) added at CloudFront via `ResponseHeadersPolicy`*

---

## Executive Summary

Huginn is a Human-AI OODA composite for engineering PMs. It ingests development signals from external sources on an hourly schedule, computes Master Variables (TRANSPARENCY, THROUGHPUT, CYCLE TIME, REWORK, QUALITY, COMPLEXITY, CONTRIBUTION), and produces a SitRep at the morning daily planning session. The PM conducts Observe-Orient (OO) with Gjallarhorn AI, then makes Decisions and defines Actions (DA).

**Key architectural decisions:**
- Django MTV + Celery hybrid: web UI and async ingestion in one monorepo
- PostgreSQL + Django ORM — relational model sufficient, no graph DB needed
- Docker Compose everywhere — dev/prod parity, no K8s complexity
- HTMX partial updates + Apache ECharts — server-rendered, testable UI
- AWS Elastic Beanstalk + GitLab CI — simple managed deploy for Docker Compose, Kaniko for daemonless image builds
- Blue/green deployment via `eb swap` — two EB environments (`huginn-blue` / `huginn-green`); `huginn-prod` EB CNAME rotates between them. Public DNS `huginn.featurefactory.io` → **CloudFront** (origin = `huginn-prod` EB CNAME); swap does not require Route53 or CloudFront changes
- AWS RDS (PostgreSQL) in production — no containerised DB on EB; local dev retains the `db` Compose service

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
- Iconography: Font Awesome Pro — loaded via kit script (CDN)
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
├── infra/               # AWS CDK (Python) — stacks, Lambda for Route53 upsert
│   ├── app.py
│   ├── cdk.json
│   ├── stacks/
│   └── lambda/
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

**Makefile targets:** `make test`, `make test-unit`, `make test-integration`. **CDK stack tests:** `tests/infra/` synthesise CDK stacks and assert on CloudFormation templates (no AWS calls); included in `make test` once `infra/requirements.txt` is installed (pulled via root `requirements.txt`).

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
- Static assets: WhiteNoise (served by Django). **CloudFront** terminates TLS for the public hostname and proxies to EB; it is not a separate static-asset CDN (cache policy is disabled for the app)

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

**Services (local dev):**
```yaml
services:
  web:     # Django (runserver + debugpy on :8000)
  worker:  # Celery worker
  beat:    # Celery beat (DatabaseScheduler — django_celery_beat)
  redis:   # Broker + cache (redis:7-alpine)
  db:      # PostgreSQL 16 (local only — replaced by RDS in prod)
```

**Services (production — `docker-compose.prod.yml`):**
```yaml
services:
  web:     # gunicorn, runs migrate --noinput on startup, mapped :8080→:8000
  worker:  # Celery worker, concurrency=2
  beat:    # Celery beat (DatabaseScheduler)
  redis:   # redis:7-alpine with healthcheck
  # no db  — uses RDS
```

**Local dev:** `make run` starts all services via `docker compose up`. `.env` file provides local config. Django `runserver` runs locally (outside Docker) with F5 / Cursor debugpy launch config; only `db` and `redis` run in Compose containers.

**Production AWS components:**

| Component | Detail |
|---|---|
| Platform | AWS Elastic Beanstalk — *Docker running on 64bit Amazon Linux 2023* |
| EB application | `huginn` |
| EB environments | `huginn-blue`, `huginn-green` (blue/green pair) |
| CNAME for prod | `huginn-prod.us-east-1.elasticbeanstalk.com` — rotates between envs via `eb swap` |
| CNAME for staging | `huginn-staging.us-east-1.elasticbeanstalk.com` — always the inactive env |
| DNS | Route53 CNAME `huginn.featurefactory.io` → **CloudFront** distribution domain. **Origin** (in CDK): `huginn-prod.us-east-1.elasticbeanstalk.com` — stable; `eb swap` rotates which EB env backs that name. CNAME record is applied by CDK (`HuginnCdn` stack) via a **Lambda-backed custom resource**: if the record already matches the CloudFront domain it no-ops; otherwise it UPSERTs (avoids duplicate-record failures when migrating from a direct EB CNAME) |
| Container registry | AWS ECR — `411113550285.dkr.ecr.us-east-1.amazonaws.com/huginn` — tagged by short SHA and `:latest` |
| Database | AWS RDS — PostgreSQL 16, credentials injected as EB environment properties |
| Secrets | AWS SSM Parameter Store — `SECRET_KEY`, DB credentials fetched and promoted to EB env properties |
| Deploy bundle S3 | `s3://elasticbeanstalk-us-east-1-411113550285/huginn/<sha>.zip` |
| Nginx fix | `.ebextensions/01_nginx_proxy.config` — systemd oneshot service patches EB's auto-generated nginx upstream from the unreachable Compose-network IP to `127.0.0.1:8080` (stable `docker-proxy` port) |
| Web container port | `8080:8000` — host 8080 → gunicorn 8000. Required because EB's nginx config template uses the mapped host port. |

**No Kubernetes** — internal tool, team of 2–5, Compose complexity is sufficient.

**Infrastructure as Code:** `infra/` directory contains a Python CDK project with four stacks:

| Stack | Resources | Deploy phase |
|---|---|---|
| `HuginnCdn` (CDK) | ACM cert (`featurefactory.io` + `*.featurefactory.io`, us-east-1), CloudFront (viewer HTTPS → origin HTTP, `CachingDisabled`, `AllViewer` origin policy, **response headers policy** for `Strict-Transport-Security` 1h + `includeSubDomains`), Lambda + custom resource for **idempotent** Route53 CNAME to CloudFront | Phase 1 — **deployed** (CloudFormation stack `HuginnCdn`) |
| `HuginnNetworkStack` | VPC (`10.0.0.0/16`), 2-AZ public/private subnets, NAT gateway, EB SG, RDS SG | Phase 3 |
| `HuginnDataStack` | RDS PostgreSQL 16 (private subnet, encrypted), SSM parameter stubs | Phase 3 |
| `HuginnAppStack` | ECR repo, EB application + blue/green environments (L1), IAM roles, CloudWatch alarms | Phase 4 |

Existing resources (ECR, RDS, EB, IAM) will be brought under CDK management via `cdk import` in phases 2–4. See `infra/` for full stack definitions.

**CDK CLI:** use `npx aws-cdk@2` from the `infra/` directory (Node.js required), or install `aws-cdk` globally. `infra/cdk.json` sets `"app": ".venv/bin/python app.py"` — run `pip install -r requirements.txt` (includes `-r infra/requirements.txt`) so the app venv has `aws-cdk-lib`. **Bootstrap:** the account/region must be CDK-bootstrapped once (`cdk bootstrap aws://<account>/us-east-1`); this creates the `CDKToolkit` stack used for deployments.

---

## 9. CI/CD Pipeline

**Platform:** GitLab CI (`.gitlab-ci.yml`). Repository: `gitlab.com/dp2580/huginn`.

**Pipeline stages (app):**
```
lint (ruff) → test (pytest + CDK stack tests) → infra (child pipeline, main + infra/** only) → build (kaniko→ECR) → deploy (scripts/deploy.sh) → swap (manual)
```

**Infra pipeline:** `infra/gitlab-ci.yml` — triggered as a **child pipeline** when `infra/**` changes on `main`. Stages: CDK assertion tests (`tests/infra/`), `cdk diff` (non-blocking), manual `cdk deploy` (stack selectable via `CDK_STACK`). Requires same AWS GitLab CI variables as deploy.

**Stage details:**

| Stage | Image | Triggers | What it does |
|---|---|---|---|
| `lint` | `python:3.12-slim` | every push, every branch | `ruff check` + `ruff format --check` |
| `test` | `python:3.12-slim` + postgres + redis services | every push, every branch | `pip install` app + `infra/requirements.txt`; `PYTHONPATH=.`; `pytest --tb=short -q` (includes `tests/infra/` CDK template assertions) |
| `build` | `gcr.io/kaniko-project/executor:v1.23.2-debug` | `main` only | builds Docker image without daemon; pushes `:<sha>` and `:latest` to ECR |
| `deploy` | `python:3.12-slim` + AWS CLI v2 | `main` only, after build | runs `scripts/deploy.sh` — deploys to inactive EB env, waits, smoke-tests `/health/` |
| `swap` | `python:3.12-slim` + AWS CLI v2 | `main`, **manual click** | calls `eb swap` to rotate `huginn-prod` CNAME to the freshly deployed env |

**Why Kaniko:** GitLab shared runners are Alpine-based and lack a Docker daemon. Kaniko builds without DinD, resolves `aws-cli` Alpine incompatibilities.

**`scripts/deploy.sh` — deploy logic:**
1. Determine which EB env holds `huginn-prod` CNAME → that is `LIVE_ENV`, the other is `INACTIVE_ENV`.
2. `envsubst '${ECR_IMAGE}'` bakes the commit SHA image tag into `docker-compose.prod.yml` → `docker-compose.yml`.
3. Bundle `docker-compose.yml` + `.ebextensions/` into `deploy.zip`.
4. Upload zip to EB S3 bucket via `create-storage-location`.
5. Create idempotent EB application version (skip if SHA already exists).
6. `update-environment` on `INACTIVE_ENV`, wait until stable.
7. Smoke-test `http://<inactive-cname>/health/` — 10 retries × 10 s, `--retry-connrefused` (nginx startup lag).
8. Print prompt to manually trigger the `swap` job.

**GitLab CI variables (project-level secrets):**

| Variable | Purpose |
|---|---|
| `AWS_ACCESS_KEY_ID` | IAM deploy user |
| `AWS_SECRET_ACCESS_KEY` | IAM deploy user |
| `AWS_DEFAULT_REGION` | `us-east-1` |
| `ECR_REGISTRY` | `411113550285.dkr.ecr.us-east-1.amazonaws.com` |
| `EB_APP_NAME` | `huginn` |
| `EB_BLUE_ENV` | `huginn-blue` |
| `EB_GREEN_ENV` | `huginn-green` |

**Artifact registry:** AWS ECR — `411113550285.dkr.ecr.us-east-1.amazonaws.com/huginn`.

**Promotion flow:**
```
push to main
  → lint + test (automated gate)
  → infra (child pipeline, only if infra/** changed)
  → build (Kaniko → ECR)
  → deploy (→ inactive EB env, smoke test)
  → swap (manual click → eb swap → huginn-prod EB CNAME rotates; CloudFront origin unchanged)
```

**Branch strategy:** trunk-based — short-lived feature branches, merge to `main` via MR.

---

## 10. Release & Rollback

**Deployment strategy:** Blue/green via `eb swap`. Two EB environments (`huginn-blue`, `huginn-green`) are always running. Each deploy targets the *inactive* env; the `swap` job rotates the `huginn-prod` CNAME. **Application deploys do not change Route53** — the public hostname stays on CloudFront; only CDK infra changes (e.g. `HuginnCdn`) alter DNS.

**Version tagging:** Git short SHA (`CI_COMMIT_SHORT_SHA`) is the version label for EB application versions and the Docker image tag. Calendar versioning for human-facing releases if needed.

**Rollback:** trigger one more `eb swap` in GitLab CI (or manually via AWS console) to flip the CNAME back. The previously live environment is always running and ready. Target: < 2 minutes.

**Release cadence:** continuous — every merge to `main` auto-deploys to the inactive env and pauses at the manual `swap` gate.

**Hotfix:** direct merge to `main` with `[hotfix]` prefix in commit message; same pipeline applies.

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

**Local:** `.env` file (gitignored) loaded via `envFile` in `.vscode/launch.json`. Django dev server runs locally; only `db` and `redis` run in Docker. `POSTGRES_HOST=localhost` in `.env` (overrides the Docker service name `db`). `REDIS_URL=redis://localhost:6379/0`.

**Production:** AWS EB environment properties (set via EB console or `eb setenv`). EB exports these as shell env vars before running Docker Compose; `docker-compose.prod.yml` uses `${VAR}` substitution to pass them into containers. *(Note: `env_file:` directive does not work on AL2023 — explicit `environment:` blocks required.)*

**Secrets storage:** AWS SSM Parameter Store. Credentials are fetched and set as EB environment properties. GitLab CI credentials (`AWS_ACCESS_KEY_ID`, etc.) are GitLab project-level CI variables.

**Required env vars:**

| Variable | Description | Source (prod) |
|---|---|---|
| `SECRET_KEY` | Django secret key | SSM → EB env property |
| `DJANGO_SETTINGS_MODULE` | `huginn.settings.production` | EB env property |
| `ALLOWED_HOSTS` | e.g. `huginn.featurefactory.io,...` | EB env property |
| `POSTGRES_HOST` | RDS endpoint | EB env property |
| `POSTGRES_DB` | Database name | EB env property |
| `POSTGRES_USER` | DB user | SSM → EB env property |
| `POSTGRES_PASSWORD` | DB password | SSM → EB env property |
| `REDIS_URL` | `redis://localhost:6379/0` (Redis runs in same Compose stack) | EB env property |
| `GITLAB_URL` | GitLab instance URL | EB env property |
| `GITLAB_TOKEN` | GitLab personal access token | SSM → EB env property |
| `JIRA_URL` | Jira instance URL | EB env property |
| `JIRA_USER` | Jira username/email | EB env property |
| `JIRA_TOKEN` | Jira API token | SSM → EB env property |
| `LLM_API_KEY` | LLM API key for Gjallarhorn | SSM → EB env property |
| `DEBUG` | `False` in prod | EB env property |

**Feature flags:** not needed for v1.

---

## 13. Security

**Authentication:** Django session-based auth. Username + password. Small team — no SSO/OAuth for v1.

**Authorization:** single-role (all authenticated users have full access). No RBAC needed for v1.

**Production hardening:**
- `DEBUG=False`
- `SECURE_SSL_REDIRECT=True` — TLS terminated at CloudFront; `X-Forwarded-Proto: https` forwarded via AllViewer origin request policy
- `SESSION_COOKIE_SECURE=True`
- `CSRF_COOKIE_SECURE=True`
- `SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")`
- `CSRF_TRUSTED_ORIGINS = ["https://huginn.featurefactory.io"]`
- `SECURE_REDIRECT_EXEMPT = [r"^health/$"]` — allows CI smoke test to reach EB CNAME directly over HTTP
- `SECURE_HSTS_SECONDS = 3600` — increase to 31536000 after one week of stable HTTPS
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
| `make provision` | Install app deps + CDK deps (`infra/.venv` for `aws-cdk` CLI workflows) |
| `make run` | Start all services via Docker Compose |
| `make test` | Run full test suite (`SECRET_KEY` defaulted for pytest-django if unset) |
| `make test-unit` | Run unit tests only |
| `make lint` | Run ruff check |
| `make format` | Run ruff format |
| `make infra-synth` | `cdk synth` (from `infra/` via `.venv/bin/python` in `cdk.json`) |
| `make infra-diff` | `cdk diff` |
| `make infra-deploy-cdn` | `cdk deploy HuginnCdn` |
| `make infra` | `cdk deploy --all` (later phases — use with care) |
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
| CI/CD | GitLab CI | — | — | — | pipeline at `gitlab.com/dp2580/huginn` |
| Build (CI) | Kaniko | v1.23.2 | — | — | daemonless Docker build in CI |
| Deploy | AWS EB CLI | latest | `pip install awsebcli` | `pip install awsebcli` | `eb --version` |
| VCS | git | 2.x | `brew install git` | `apt install git` | `git --version` |
| Build | make | 4+ | bundled on macOS | `apt install make` | `make --version` |
| IaC | AWS CDK (Python) | 2.x | `pip install aws-cdk-lib` | `pip install aws-cdk-lib` | `cdk --version` |

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
| DB (local) | PostgreSQL 16 in Docker Compose | Dev/prod parity; simple to spin up |
| DB (prod) | AWS RDS PostgreSQL | Data survives EB instance replacement; managed backups |
| UI | Django + HTMX + ECharts | Server-rendered = testable; no SPA complexity; ECharts handles scatter/quadrant |
| Infra | Docker Compose on EB AL2023 | Internal tool; K8s overhead not justified; EB manages EC2 |
| Deploy strategy | Blue/green via `eb swap` | Zero-downtime; measurable cycle time; instant rollback by re-swapping |
| DNS | Route53 `huginn.featurefactory.io` → CloudFront; origin `huginn-prod.*` | Public name stable; EB prod CNAME is CloudFront origin and rotates via swap; no Route53 edit per deploy |
| CI platform | GitLab CI | Repo is on GitLab; native integration |
| CI builds | Kaniko | Shared runners are Alpine; Kaniko is daemonless, no glibc needed |
| Image registry | AWS ECR | Co-located with EB/IAM; no extra auth needed |
| Secrets | AWS SSM → EB env properties | Credentials never in git or image |
| Async | Celery + Redis + `django_celery_beat` | Hourly ingestion; DatabaseScheduler persists beat schedule in RDS |
| Connectors v1 | python-gitlab + jira (pycontribs) | Both actively maintained; `jira` preferred over `atlassian-python-api` for Jira-specific coverage |
| Testing | pytest + Django test client, no E2E | Internal tool; browser E2E overhead not justified; ECharts tested via JSON endpoints |
| Observability | AWS CloudWatch | Co-located with EB; no additional tooling needed |
| TLS | CloudFront + ACM | ACM in us-east-1 (`featurefactory.io` + `*.featurefactory.io`); CloudFront in front of EB `huginn-prod` origin; Django `SECURE_SSL_REDIRECT=True` + `SECURE_PROXY_SSL_HEADER` |
| IaC | AWS CDK (Python) | `infra/` — `HuginnCdn` stack deployed; Network/Data/App stacks + `cdk import` for legacy resources tracked as later phases |

---

## Discovered Patterns & Lessons Learned

### Critical Discoveries

**EB AL2023: `env_file:` does not work.**
`env_file: /opt/elasticbeanstalk/deployment/env` fails with "file not found" on Amazon Linux 2023. EB exports environment properties as shell env vars *before* running Docker Compose. The correct pattern is explicit `environment:` blocks with `${VAR}` substitution in `docker-compose.prod.yml`.

**EB nginx upstream points to unreachable container IP.**
EB's platform agent auto-generates `/etc/nginx/conf.d/elasticbeanstalk-nginx-docker-upstream.conf` with the container's Compose-network IP (e.g. `172.23.0.3:8000`), which is not routable from the EB host. The fix is a systemd oneshot service (`.ebextensions/01_nginx_proxy.config`) that sleeps 5 s after `nginx.service` starts and patches the upstream to `127.0.0.1:8080` — the stable `docker-proxy` host port. The `appdeploy/post` hook fires *before* nginx config is written, so it cannot be used for this fix.

**Web container must map port `8080:8000`.**
EB's nginx config template uses the host-mapped port. Port 80 is taken by nginx itself. The chain is: public :80 → nginx → `127.0.0.1:8080` (docker-proxy) → gunicorn :8000 inside the container.

**`django_celery_beat` must be in `INSTALLED_APPS`.**
The `beat` Celery container crashed at startup with `RuntimeError: Model class django_celery_beat.models.SolarSchedule doesn't declare an explicit app_label`. Fix: add `"django_celery_beat"` to `INSTALLED_APPS` in `huginn/settings/base.py`.

**`SECURE_SSL_REDIRECT=True` breaks HTTP-only EB.**
Enabling Django's SSL redirect on an EB environment without TLS causes an infinite redirect loop (HTTP 301 to a dead HTTPS endpoint). Enabled only after CloudFront + ACM cert is deployed. Exempt `/health/` via `SECURE_REDIRECT_EXEMPT` so the CI smoke test can still reach the EB CNAME directly over HTTP.

**CDK `from_lookup()` requires AWS credentials during `cdk synth`.**
`HostedZone.from_lookup()` in the CDN stack makes an AWS API call at synthesis time. Tests bypass this by passing a `hosted_zone` built with `HostedZone.from_hosted_zone_attributes()`. After first successful `cdk synth`, CDK can cache the lookup in `cdk.context.json` (optional to commit).

**Route53 CNAME already existed (direct EB) — `AWS::Route53::RecordSet` create failed.**
A second CNAME for `huginn.featurefactory.io` conflicts with the existing record. Fix: manage the record with a **Lambda custom resource** that compares the current CNAME target to the CloudFront domain — **no-op if already correct**, **UPSERT** if it still points at Elastic Beanstalk or anything else. Deployed as part of `HuginnCdn`.

**EB in default VPC (Phase 3 gap).**
Current infrastructure (EB, RDS) lives in the default AWS VPC (`vpc-a2af05df`, `172.31.0.0/16`). `HuginnNetworkStack` creates a dedicated VPC. RDS migration requires a snapshot restore; EB environment recreation requires a maintenance window. Tracked as Phase 3/4 of the CDK migration.

**Kaniko is required for ECR builds on GitLab shared runners.**
GitLab's shared runners are Alpine-based; `aws-cli` v2 binary is not compatible with Alpine (`glibc` missing). Switching the `build` stage to Kaniko (`gcr.io/kaniko-project/executor:v1.23.2-debug`) eliminates the Docker daemon requirement and the Alpine incompatibility.

**Blue/green swap direction must be verified before executing.**
`eb swap` is directional: swapping twice in the same direction returns to the original state, not the desired one. Always check which env holds the `huginn-prod` CNAME (`aws elasticbeanstalk describe-environments ... --query CNAME`) before triggering a swap.

**Font Awesome Pro Kit uses domain allowlisting.**
Icons loaded via `https://kit.fontawesome.com/<kit-id>.js` are silently blocked if the serving domain is not in the kit's allowed-domains list on fontawesome.com. Domains to add: `huginn.featurefactory.io`, `huginn-prod.us-east-1.elasticbeanstalk.com`, `huginn-staging.us-east-1.elasticbeanstalk.com`.

**`collectstatic` fails silently at Docker build time.**
`SECRET_KEY` is not available at build time. The `RUN python manage.py collectstatic --noinput 2>/dev/null || true` line in the `Dockerfile` silently skips if `SECRET_KEY` is missing. Static files are served by WhiteNoise from the source tree. *(Revisit if static assets are missing in prod.)*

**Local DNS caching masks correct DNS propagation.**
After Route53 changes, the local machine may serve stale records from its DNS cache. Flush with `sudo dscacheutil -flushcache && sudo killall -HUP mDNSResponder` (macOS) or temporarily add the entry to `/etc/hosts`.

**Local Django dev server vs Docker Compose hostname resolution.**
When running Django `runserver` locally (outside Docker), `POSTGRES_HOST=db` cannot be resolved — `db` is a Docker Compose service name. Override with `POSTGRES_HOST=localhost` in `.env` to reach the Docker-mapped port `5432`.

### Retrospective Updates

- **CI platform pivoted from GitHub Actions → GitLab CI** during execution; SAO initially specified GitHub Actions / GHCR.
- **Database pivoted from containerised Postgres → RDS** during execution; removes data loss risk on EB instance replacement.
- **Rolling → blue/green** adopted for zero-downtime deploys and measurable cycle time (deploy completes on inactive env; swap is the single atomic promotion event).
