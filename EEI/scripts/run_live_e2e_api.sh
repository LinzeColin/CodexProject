#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

if [[ -f .env ]]; then
  set -a
  source .env
  set +a
fi

if [[ "${EEI_ALLOW_DB_RESET_FOR_E2E:-}" != "1" ]]; then
  echo "ERROR: EEI_ALLOW_DB_RESET_FOR_E2E=1 is required for live E2E database reset" >&2
  exit 1
fi

if [[ -z "${DATABASE_URL:-}" ]]; then
  echo "ERROR: DATABASE_URL is required for live E2E API" >&2
  exit 1
fi

.venv/bin/python scripts/migrate.py downgrade --all
.venv/bin/python scripts/migrate.py upgrade
.venv/bin/python scripts/load_seed_catalogs.py
.venv/bin/python scripts/load_synthetic_fixtures.py

exec .venv/bin/python -m uvicorn apps.api.app.main:app --host 127.0.0.1 --port 8000
