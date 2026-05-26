.DEFAULT_GOAL := help
# Local dev: project venv. CI jobs use make ci-lint / make ci-test (ephemeral .ci-venv-*).
PYTHON        := .venv/bin/python
PIP           := .venv/bin/pip
PYTEST        := .venv/bin/pytest
RUFF          := .venv/bin/ruff

##@ General

.PHONY: help
help: ## Show this help
	@awk 'BEGIN {FS = ":.*##"; printf "\nUsage:\n  make \033[36m<target>\033[0m\n"} /^[a-zA-Z_0-9-]+:.*?##/ { printf "  \033[36m%-22s\033[0m %s\n", $$1, $$2 } /^##@/ { printf "\n\033[1m%s\033[0m\n", substr($$0, 5) } ' $(MAKEFILE_LIST)

##@ Provision

.PHONY: provision
provision: ## Install all prerequisites and dependencies (app + CDK)
	@echo "Creating virtual environment..."
	python3 -m venv .venv
	$(PIP) install --upgrade pip -q
	$(PIP) install -r requirements.txt -q
	python3 -m venv infra/.venv
	infra/.venv/bin/pip install -r infra/requirements.txt -q
	@cp -n .env.example .env 2>/dev/null && echo "Created .env from .env.example — fill in your values" || echo ".env already exists"
	@echo "✅ Provision complete. Run 'make run' to start."

##@ Development

.PHONY: run
run: ## Start all services via Docker Compose
	docker compose up

.PHONY: run-d
run-d: ## Start all services in background
	docker compose up -d

.PHONY: stop
stop: ## Stop all containers
	docker compose stop

.PHONY: shell
shell: ## Open Django shell in web container
	docker compose exec web python manage.py shell

.PHONY: migrate
migrate: ## Run Django migrations in web container
	docker compose exec web python manage.py migrate

.PHONY: makemigrations
makemigrations: ## Create new migrations in web container
	docker compose exec web python manage.py makemigrations

.PHONY: createsuperuser
createsuperuser: ## Create Django superuser
	docker compose exec web python manage.py createsuperuser

.PHONY: logs
logs: ## Tail all container logs
	docker compose logs -f

##@ Testing

# Default SECRET_KEY so pytest-django can import settings without a local .env (matches CI test job).
export SECRET_KEY ?= ci-test-secret-key-not-used-in-prod

.PHONY: test
test: export PYTHONPATH := .
test: ## Run all tests
	$(PYTEST)

.PHONY: test-unit
test-unit: ## Run unit tests only
	$(PYTEST) tests/unit/

.PHONY: test-integration
test-integration: ## Run integration tests only
	$(PYTEST) tests/integration/

##@ Code Quality

.PHONY: lint
lint: ## Run ruff linter + format check (mirrors make ci-lint)
	$(RUFF) check .
	$(RUFF) format --check .

.PHONY: format
format: ## Auto-format code with ruff
	$(RUFF) format .

.PHONY: lint-fix
lint-fix: ## Run ruff linter with auto-fix
	$(RUFF) check --fix .

##@ Database

# Local Docker Postgres (matches docker-compose defaults). Override if your .env differs.
POSTGRES_DB ?= huginn
POSTGRES_USER ?= huginn

.PHONY: db-reset-dev
db-reset-dev: ## DROP local DB and migrate (destroys data; fixes inconsistent migration history)
	docker compose exec -T db psql -U $(POSTGRES_USER) -d postgres -v ON_ERROR_STOP=1 -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = '$(POSTGRES_DB)' AND pid <> pg_backend_pid();"
	docker compose exec -T db psql -U $(POSTGRES_USER) -d postgres -v ON_ERROR_STOP=1 -c "DROP DATABASE IF EXISTS $(POSTGRES_DB);"
	docker compose exec -T db psql -U $(POSTGRES_USER) -d postgres -v ON_ERROR_STOP=1 -c "CREATE DATABASE $(POSTGRES_DB) OWNER $(POSTGRES_USER);"
	$(PYTHON) manage.py migrate --noinput

.PHONY: backup
backup: ## Dump PostgreSQL to S3 (set S3_BUCKET env var)
	docker compose exec db pg_dump -U huginn huginn | aws s3 cp - s3://$(S3_BUCKET)/huginn-$(shell date +%Y%m%d-%H%M%S).sql

.PHONY: db-shell
db-shell: ## Open psql in db container
	docker compose exec db psql -U huginn huginn

##@ Infrastructure (CDK)

CDK_VENV := infra/.venv/bin

.PHONY: infra-synth
infra-synth: ## Synthesise all CDK stacks — validates templates, no AWS calls
	cd infra && $(CDK_VENV)/cdk synth

.PHONY: infra-diff
infra-diff: ## Show diff between CDK definition and currently deployed state
	cd infra && $(CDK_VENV)/cdk diff

.PHONY: infra-deploy-cdn
infra-deploy-cdn: ## Deploy HuginnCdn (ACM + CloudFront + Route53 CNAME) — Phase 1
	cd infra && $(CDK_VENV)/cdk deploy HuginnCdn

.PHONY: infra
infra: ## Deploy all CDK stacks (use with caution on existing infra)
	cd infra && $(CDK_VENV)/cdk deploy --all

##@ Deploy (AWS EB)

# Same scripts as GitLab CI. Requires AWS CLI, EB_* and ECR_REGISTRY (see GitLab project variables / SAO).
# The ECR image huginn:$(CI_COMMIT_SHORT_SHA) must already exist before staging succeeds.
#
# Staging only — which *revision* to deploy to the inactive EB:
#   (1) CI_COMMIT_SHORT_SHA if set (CI), else (2) BRANCH=… (any git ref), else (3) HEAD.
# GNU Make: use `make staging BRANCH=release/0.0.6` (not `--branch=`).
#
# swap / promote: **no BRANCH**. Promotes **whatever is on staging now**
# (after you tested on staging; bugfix loop = redeploy staging, then swap). Optional CI_COMMIT_SHORT_SHA
# must match inactive VersionLabel or the script aborts (GitLab sets it to the pipeline SHA).
# Prod smoke compares /health/ revision from staging (release tag), not the EB VersionLabel.

.PHONY: staging
staging: ## Deploy chosen revision to inactive EB (staging smoke). Optional BRANCH=git-ref; default HEAD. CI sets CI_COMMIT_SHORT_SHA.
	@set -e; \
	if [ -n "$$CI_COMMIT_SHORT_SHA" ]; then sha="$$CI_COMMIT_SHORT_SHA"; \
	elif [ -n "$(BRANCH)" ]; then sha=$$(git rev-parse --short "$(BRANCH)"); \
	else sha=$$(git rev-parse --short HEAD); fi; \
	if [ -n "$(BRANCH)" ]; then echo "Using ECR/huginn:$$sha (from ref $(BRANCH))"; else echo "Using ECR/huginn:$$sha (HEAD)"; fi; \
	CI_COMMIT_SHORT_SHA="$$sha" bash scripts/deploy-staging.sh

.PHONY: swap
swap: ## Promote **current staging** (inactive EB) to prod — not HEAD/BRANCH. SHA guard on VersionLabel; prod smoke vs staging /health/ revision.
	bash scripts/promote-prod.sh

##@ CI glue (GitLab)

# .gitlab-ci.yml is thin glue: install `make`, then call these targets. Kaniko and GitLab
# release-cli images have no Make — those jobs invoke the same scripts as `make ci-build`
# / `make gitlab-release` (see comments in .gitlab-ci.yml).
#
# To ship: git tag x.y.z && git push origin x.y.z  (or: glab release create x.y.z)
# Pipeline triggers on the tag: lint → test → build → staging → GitLab Release → manual promote.

.PHONY: ci-lint
ci-lint: ## [CI] Ruff check + format via ephemeral venv (same rules as make lint)
	bash scripts/ci-lint.sh

.PHONY: ci-test
ci-test: ## [CI] pytest with Node.js for CDK/jsii (same suite as make test)
	bash scripts/ci-test.sh

.PHONY: ci-prepare-aws
ci-prepare-aws: ## [CI] Install AWS CLI v2 for EB deploy/promote jobs
	bash scripts/ci-prepare-aws.sh

.PHONY: ci-build
ci-build: ## [CI] Kaniko → ECR (requires /kaniko/executor; GitLab build job)
	sh scripts/ci-kaniko-build.sh

.PHONY: gitlab-release
gitlab-release: ## [CI] GitLab Release via release-cli (GitLab release stage)
	bash scripts/ci-create-gitlab-release.sh

.PHONY: ci-staging-deploy
ci-staging-deploy: ci-prepare-aws staging ## [CI] AWS CLI + deploy to inactive EB (staging smoke)

.PHONY: ci-promote
ci-promote: ci-prepare-aws swap ## [CI] AWS CLI + swap prod CNAME + smoke prod

##@ Cleanup

.PHONY: clean
clean: ## Stop containers and remove volumes
	docker compose down -v

.PHONY: clean-pyc
clean-pyc: ## Remove Python bytecode files
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
