# =========================================================================
# AI Dispatcher МЧС — task runner (Stage 16 §7).
# Platform-agnostic entry points for build, test, static analysis, migration
# checks and container builds. CI systems call these targets so the pipeline
# is NOT tied to any specific CI/CD product — the same commands run locally.
# =========================================================================
.DEFAULT_GOAL := help
PY ?= python
PIP ?= $(PY) -m pip
PYTEST ?= $(PY) -m pytest
RUFF ?= $(PY) -m ruff
IMAGE ?= dispatcher-api
TAG ?= latest

.PHONY: help install lint format test test-fast check migrate migrate-down \
        migrate-check build-image run stop loadtest verify-readiness ci clean

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
	 awk 'BEGIN{FS=":.*?## "}{printf "  \033[36m%-16s\033[0m %s\n",$$1,$$2}'

install: ## Install runtime + test dependencies
	$(PIP) install -r requirements.txt

lint: ## Static analysis (ruff)
	$(RUFF) check backend tests

format: ## Auto-format (ruff)
	$(RUFF) format backend tests
	$(RUFF) check --fix backend tests

test: ## Run the full test suite
	$(PYTEST)

test-fast: ## Run tests excluding PostgreSQL-backed ones
	$(PYTEST) -k "not _pg"

check: lint test ## Lint + test (pre-commit gate)

migrate: ## Apply all migrations
	alembic upgrade head

migrate-down: ## Roll back one migration
	alembic downgrade -1

migrate-check: ## Verify migrations round-trip and match models (§8)
	scripts/verify/check_migrations.sh

build-image: ## Build the backend container image
	docker build -t $(IMAGE):$(TAG) .

run: ## Bring up the local stack (db + api)
	docker compose up -d --build

stop: ## Tear down the local stack
	docker compose down

loadtest: ## Run the load/stress scenarios against a running instance (§9)
	$(PY) scripts/perf/loadtest.py $(ARGS)

verify-readiness: ## Run automated readiness checks (§13)
	scripts/verify/verify_readiness.sh

ci: install lint test migrate-check ## Full CI gate (build/test/analysis/migration)

clean: ## Remove caches and build artefacts
	find . -type d -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null || true
	rm -rf .pytest_cache .ruff_cache
