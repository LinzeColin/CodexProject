SHELL := /usr/bin/env bash

PYTHON ?= python
VENV := .venv
UV_VERSION := 0.11.22
UV := $(VENV)/bin/uv
PNPM_VERSION := 11.8.0
PNPM := npx --yes pnpm@$(PNPM_VERSION)

.PHONY: bootstrap bootstrap-python bootstrap-node health validate-governance validate-catalogs validate-contracts secret-scan lint typecheck test test-unit test-integration test-e2e verify dev-api dev-web clean-local

$(UV):
	$(PYTHON) -m venv $(VENV)
	$(VENV)/bin/python -m pip install --upgrade pip
	$(VENV)/bin/python -m pip install uv==$(UV_VERSION)

bootstrap-python: $(UV)
	$(UV) sync --extra dev

bootstrap-node:
	if [[ -f pnpm-lock.yaml ]]; then $(PNPM) install --frozen-lockfile; else $(PNPM) install; fi

bootstrap: bootstrap-python bootstrap-node

health:
	$(UV) run python -m apps.api.app.healthcheck

validate-governance:
	$(UV) run python scripts/validate_task_pack.py

validate-catalogs:
	$(UV) run python scripts/validate_catalog_integrity.py

validate-contracts:
	$(UV) run python scripts/validate_contracts.py

secret-scan:
	$(UV) run python scripts/secret_scan.py

lint:
	$(UV) run ruff check apps tests scripts/validate_contracts.py scripts/secret_scan.py

typecheck:
	$(PNPM) --filter @eei/web typecheck

test-unit:
	$(UV) run pytest tests/unit

test-integration:
	$(UV) run pytest tests/integration

test-e2e:
	$(PNPM) --filter @eei/web test:e2e

test: test-unit

verify: validate-governance validate-contracts secret-scan lint typecheck test

dev-api:
	$(UV) run uvicorn apps.api.app.main:app --reload --port 8000

dev-web:
	$(PNPM) --filter @eei/web dev

clean-local:
	rm -rf $(VENV) node_modules apps/web/node_modules apps/web/.next .pytest_cache .ruff_cache test-results playwright-report
