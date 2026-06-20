SHELL := /usr/bin/env bash

PYTHON ?= python
VENV := .venv
UV_VERSION := 0.11.22
UV := $(VENV)/bin/uv
PNPM_VERSION := 11.8.0
PNPM ?= npx --yes pnpm@$(PNPM_VERSION)

.PHONY: bootstrap bootstrap-python bootstrap-node doctor db-up wait-db db-down db-logs migrate-up migrate-down seed-catalogs load-fixtures check-db-schema health validate-governance validate-catalogs validate-contracts validate-prototype-parity validate-github-governance validate-governance-consistency validate-v5-production-readiness-sync generate-development-status-artifacts validate-development-status-artifacts generate-risk-control-artifacts validate-risk-control-artifacts generate-clean-room-release validate-clean-room-release generate-release-artifacts validate-release-artifacts validate-scale-benchmark-smoke validate-scale-benchmark-operator validate-scale-browser-benchmark validate-soak-smoke secret-scan copy-lint lint typecheck test test-unit test-integration test-e2e test-e2e-live verify verify-g1 verify-g2-db dev-api dev-web clean-local

$(UV):
	$(PYTHON) -m venv $(VENV)
	$(VENV)/bin/python -m pip install --upgrade pip
	$(VENV)/bin/python -m pip install uv==$(UV_VERSION)

bootstrap-python: $(UV)
	$(UV) sync --extra dev

bootstrap-node:
	if [[ -f pnpm-lock.yaml ]]; then $(PNPM) install --frozen-lockfile; else $(PNPM) install; fi

bootstrap: bootstrap-python bootstrap-node

doctor:
	if [[ -f .env ]]; then set -a; source .env; set +a; fi; $(UV) run python scripts/env_doctor.py

db-up:
	command -v docker >/dev/null || { echo "ERROR: docker is required for PostgreSQL verification"; exit 1; }
	docker compose up -d postgres
	$(MAKE) wait-db

wait-db:
	if [[ -f .env ]]; then set -a; source .env; set +a; fi; $(UV) run python scripts/wait_for_database.py --timeout 90

db-down:
	command -v docker >/dev/null || { echo "WARN: docker is not installed"; exit 0; }
	docker compose down

db-logs:
	command -v docker >/dev/null || { echo "ERROR: docker is required for db-logs"; exit 1; }
	docker compose logs --tail=120 postgres

migrate-up:
	if [[ -f .env ]]; then set -a; source .env; set +a; fi; $(UV) run python scripts/migrate.py upgrade

migrate-down:
	if [[ -f .env ]]; then set -a; source .env; set +a; fi; $(UV) run python scripts/migrate.py downgrade --all

seed-catalogs:
	if [[ -f .env ]]; then set -a; source .env; set +a; fi; $(UV) run python scripts/load_seed_catalogs.py

load-fixtures:
	if [[ -f .env ]]; then set -a; source .env; set +a; fi; $(UV) run python scripts/load_synthetic_fixtures.py

check-db-schema:
	if [[ -f .env ]]; then set -a; source .env; set +a; fi; $(UV) run python scripts/check_database_schema.py --expect-seeds --expect-fixtures

health:
	if [[ -f .env ]]; then set -a; source .env; set +a; fi; $(UV) run python -m apps.api.app.healthcheck

validate-governance:
	$(UV) run python scripts/validate_task_pack.py

validate-catalogs:
	$(UV) run python scripts/validate_catalog_integrity.py

validate-contracts:
	$(UV) run python scripts/validate_contracts.py

validate-prototype-parity:
	$(UV) run python scripts/validate_prototype_parity.py

validate-github-governance:
	$(UV) run python scripts/validate_github_governance.py

validate-governance-consistency:
	$(UV) run python scripts/validate_governance_consistency.py

validate-v5-production-readiness-sync:
	$(UV) run python scripts/validate_v5_production_readiness_sync.py

generate-development-status-artifacts:
	$(UV) run python scripts/manage_development_status_artifacts.py generate

validate-development-status-artifacts:
	$(UV) run python scripts/manage_development_status_artifacts.py validate

generate-risk-control-artifacts:
	$(UV) run python scripts/manage_risk_control_artifacts.py generate

validate-risk-control-artifacts:
	$(UV) run python scripts/manage_risk_control_artifacts.py validate

generate-clean-room-release:
	$(UV) run python scripts/manage_clean_room_release.py generate

validate-clean-room-release:
	$(UV) run python scripts/manage_clean_room_release.py validate

generate-release-artifacts:
	$(UV) run python scripts/manage_release_artifacts.py generate

validate-release-artifacts:
	$(UV) run python scripts/manage_release_artifacts.py validate

validate-scale-benchmark-smoke:
	$(VENV)/bin/python scripts/run_scale_benchmarks.py --scales 1000 --iterations 2 --mode ci_smoke --output /tmp/eei-scale-benchmark-smoke.json --fail-on-budget --quiet

validate-scale-browser-benchmark:
	node scripts/run_browser_scale_benchmarks.mjs --scales 10000,100000,1000000 --iterations 1 --output /tmp/eei-browser-scale-benchmark.json --fail-on-budget --quiet

validate-scale-benchmark-operator: validate-scale-browser-benchmark
	$(VENV)/bin/python scripts/run_scale_benchmarks.py --scales 10000,100000,1000000 --iterations 1 --mode operator_full --output /tmp/eei-scale-benchmark-operator.json --browser-runtime-artifact /tmp/eei-browser-scale-benchmark.json --fail-on-budget --require-full-targets --quiet

validate-soak-smoke:
	node scripts/run_soak_smoke.mjs --mode ci_smoke --duration-seconds 3 --output /tmp/eei-soak-smoke.json --fail-on-budget --quiet

secret-scan:
	$(UV) run python scripts/secret_scan.py

copy-lint:
	$(UV) run python scripts/validate_ui_copy.py

lint:
	$(UV) run ruff check apps tests scripts/db_tools.py scripts/env_doctor.py scripts/migrate.py scripts/load_seed_catalogs.py scripts/load_synthetic_fixtures.py scripts/load_curated_ingestion_anchors.py scripts/job_scheduler.py scripts/run_scale_benchmarks.py scripts/check_database_schema.py scripts/wait_for_database.py scripts/validate_contracts.py scripts/secret_scan.py scripts/validate_ui_copy.py scripts/validate_prototype_parity.py scripts/validate_github_governance.py scripts/validate_governance_consistency.py scripts/validate_v5_production_readiness_sync.py scripts/manage_development_status_artifacts.py scripts/manage_risk_control_artifacts.py scripts/manage_clean_room_release.py scripts/manage_release_artifacts.py

typecheck:
	$(PNPM) --filter @eei/web typecheck

test-unit:
	$(UV) run pytest tests/unit

test-integration:
	if [[ -f .env ]]; then set -a; source .env; set +a; fi; $(UV) run pytest tests/integration

test-e2e:
	$(PNPM) --filter @eei/web test:e2e

test-e2e-live:
	$(PNPM) --filter @eei/web exec playwright test --config=../../playwright.live.config.ts

test: test-unit

verify: validate-governance validate-contracts validate-prototype-parity validate-github-governance validate-governance-consistency validate-v5-production-readiness-sync validate-development-status-artifacts validate-risk-control-artifacts validate-clean-room-release validate-release-artifacts validate-scale-benchmark-smoke validate-scale-benchmark-operator validate-soak-smoke secret-scan copy-lint lint typecheck test

verify-g1: db-up health verify test-e2e

verify-g2-db: db-up health verify test-integration test-e2e test-e2e-live

dev-api:
	$(UV) run uvicorn apps.api.app.main:app --reload --port 8000

dev-web:
	$(PNPM) --filter @eei/web dev

clean-local:
	rm -rf $(VENV) node_modules apps/web/node_modules apps/web/.next .pytest_cache .ruff_cache test-results playwright-report
