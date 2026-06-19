# MVP Development Record

Append-only development ledger for 商域图谱 / Enterprise Ecosystem Intelligence.

## 2026-06-19 - Phase 1 / G1 start

Status: IN PROGRESS

Completed:

- Imported the v4.2.0 Task Pack into an implementation repository.
- Created a baseline Git commit before implementation changes.
- Confirmed Task Pack validation passes after import.

Current scope:

- G1 repository foundation and governance synchronization.

Current Acceptance IDs:

- A004, A005, A006, A007, A008, A009, A010, A131, A132, A133, A134, A135, A153, A169, A177.

Evidence commands:

- `PYTHONPATH=/Users/linzezhang/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/lib/python3.12/site-packages python scripts/validate_task_pack.py`

Residual risks:

- `pnpm`, `uv`, and `docker` are not globally installed on the current host.
- Raw `python3 scripts/validate_task_pack.py` fails until Python dependencies are pinned through project tooling.

## 2026-06-19 - Phase 1 / G1 repository foundation batch 1

Status: IN PROGRESS

Completed:

- Added pinned root workspace files: `Makefile`, `package.json`, `pnpm-workspace.yaml`, `pyproject.toml`, `uv.lock`, and `pnpm-lock.yaml`.
- Added FastAPI health shell under `apps/api`.
- Added Watchlist-first Next.js app shell under `apps/web`.
- Added worker/package/infra/test directory anchors.
- Added contract validation and secret scan scripts.
- Added Playwright homepage smoke test.

Verification results:

- `make bootstrap`: PASS.
- `make health`: PASS.
- `make verify`: PASS.
- `npx --yes pnpm@11.8.0 --filter @eei/web build`: PASS.
- `npx --yes pnpm@11.8.0 --filter @eei/web test:e2e`: PASS after installing Playwright Chromium.

Residual risks:

- Docker is not installed on the current host, so `docker compose up -d postgres` and PostgreSQL container health checks were not executed.
- G1 remains IN PROGRESS until the Docker/PostgreSQL health path is verified or an approved non-Docker fallback is added.
- Unit tests pass with a FastAPI/Starlette deprecation warning about `httpx`; monitor when upgrading test dependencies.

## 2026-06-19 - Phase 1 / G1 database readiness contract

Status: IN PROGRESS

Completed:

- Added a PostgreSQL readiness check using pinned `psycopg[binary]==3.3.4`.
- Changed `/health/ready` and `make health` so they fail closed when `DATABASE_URL` is missing or PostgreSQL is unreachable.
- Added unit coverage for missing database configuration and successful `select 1` readiness.
- Added `make db-up`, `make db-down`, `make db-logs`, and `make verify-g1`.

Verification results:

- `make bootstrap-python`: PASS.
- `make test-unit`: PASS, 3 tests.
- `make lint`: PASS.
- `make verify`: PASS.
- `npx --yes pnpm@11.8.0 --filter @eei/web build`: PASS.
- `npx --yes pnpm@11.8.0 --filter @eei/web test:e2e`: PASS.
- `make health`: expected FAIL on current host with `status=not_ready` and `database=not_configured`.
- `make verify-g1`: expected FAIL on current host because `docker` is not installed.

Residual risks:

- G1 cannot pass until Docker/PostgreSQL readiness is verified on a host with Docker or an approved PostgreSQL service path.
- The current host has no `docker` and no `psql` executable.

## 2026-06-19 - Phase 1 / G1 environment doctor and GitHub validation entry

Status: IN PROGRESS

Completed:

- Added `scripts/env_doctor.py` and `make doctor` for structured local environment diagnostics.
- Confirmed the current host reports `docker=null`, `psql=null`, `postgres=null`, `initdb=null`, `database.status=not_configured`, and `g1_ready=false`.
- Added a root GitHub Actions workflow in `LinzeColin/CodexProject` at `.github/workflows/eei-validation.yml` because nested `EEI/.github/workflows/*` files do not run when EEI is stored as a subdirectory.

Verification results:

- `make doctor`: PASS as diagnostic output; reports G1 not ready.
- `.github/workflows/eei-validation.yml` YAML parse: PASS.
- `make lint`: PASS.
- `make verify`: PASS.
- `make verify-g1`: expected FAIL on current host because `docker` is not installed.

Residual risks:

- The root GitHub workflow has been added for future remote verification, but remote Actions status still needs to be inspected after push.
- G1 remains blocked on an actual Docker/PostgreSQL-capable runtime.

## 2026-06-19 - Phase 1 / G1 PostgreSQL startup wait contract

Status: IN PROGRESS

Completed:

- Confirmed the first root GitHub Actions run reached the G1 PostgreSQL/E2E step and failed there after static, contract, lint, typecheck, and unit tests passed.
- Added `scripts/wait_for_database.py` to poll the same `select 1` database readiness contract used by `/health/ready`.
- Added `make wait-db` and changed `make db-up` so Docker startup waits for PostgreSQL before `make health`.
- Added the wait script to `make lint`.

Verification results:

- `make lint`: PASS.
- `make verify`: PASS.
- `env -u DATABASE_URL .venv/bin/uv run python scripts/wait_for_database.py --timeout 1`: expected FAIL with `ERROR: DATABASE_URL is required before waiting for PostgreSQL`.
- `make verify-g1`: expected FAIL on current host because `docker` is not installed.

Residual risks:

- The current host still has no Docker runtime, so local `make verify-g1` remains an expected fail-closed check until Docker/PostgreSQL is available.
- Remote GitHub Actions must be re-run after this change to determine whether the failure was solely a PostgreSQL startup race.
