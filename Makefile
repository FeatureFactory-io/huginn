.DEFAULT_GOAL := help
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
provision: ## Install all prerequisites and dependencies
	@echo "Creating virtual environment..."
	python3 -m venv .venv
	$(PIP) install --upgrade pip -q
	$(PIP) install -r requirements.txt -q
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

.PHONY: test
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
lint: ## Run ruff linter
	$(RUFF) check .

.PHONY: format
format: ## Auto-format code with ruff
	$(RUFF) format .

.PHONY: lint-fix
lint-fix: ## Run ruff linter with auto-fix
	$(RUFF) check --fix .

##@ Database

.PHONY: backup
backup: ## Dump PostgreSQL to S3 (set S3_BUCKET env var)
	docker compose exec db pg_dump -U huginn huginn | aws s3 cp - s3://$(S3_BUCKET)/huginn-$(shell date +%Y%m%d-%H%M%S).sql

.PHONY: db-shell
db-shell: ## Open psql in db container
	docker compose exec db psql -U huginn huginn

##@ Cleanup

.PHONY: clean
clean: ## Stop containers and remove volumes
	docker compose down -v

.PHONY: clean-pyc
clean-pyc: ## Remove Python bytecode files
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
