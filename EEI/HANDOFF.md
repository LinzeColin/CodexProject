# HANDOFF

Updated: 2026-06-19 Australia/Sydney

## Current Goal

开发推进到满足 MVP 的交付标准 for 商域图谱 / Enterprise Ecosystem Intelligence.

## Current Status

- GitHub target: `LinzeColin/CodexProject/EEI`
- Current gate: Phase 1 / G1 - Repository foundation
- Gate status: IN PROGRESS
- Local EEI repo commits:
  - `1f4a813` baseline Task Pack import
  - `d53e72d` Phase 0 governance freeze
  - `8329592` G1 repository foundation batch 1
  - `3e04747` PostgreSQL readiness contract
  - `53ece4b` G1 environment doctor
- GitHub `CodexProject` commit pushed:
  - `c5838bc` added EEI root validation workflow

## Completed

- Imported Task Pack v4.2.0 into `work/EEI`.
- Added `PURSUING_GOAL.md`, `CURRENT_PHASE.md`, ADR-006 through ADR-015, and `docs/phase/MVP_DEVELOPMENT_RECORD.md`.
- Added `data/product_navigation_catalog.csv` for the frozen 16 user-facing navigation modules.
- Fixed release gate mapping drift and added validator coverage.
- Added pinned pnpm/uv workspace, FastAPI health shell, Next.js Watchlist-first workspace shell, worker/package/infra anchors, contract validation, secret scan, unit test, and Playwright smoke test.
- Pushed the current EEI subtree to GitHub at `LinzeColin/CodexProject/EEI`.

## Verification Evidence

Run from `work/EEI`:

- `make bootstrap`: PASS
- `make health`: PASS
- `make verify`: PASS
- `npx --yes pnpm@11.8.0 --filter @eei/web build`: PASS
- `npx --yes pnpm@11.8.0 --filter @eei/web test:e2e`: PASS
- 2026-06-19 update: `make health` now correctly fails closed without `DATABASE_URL`; `make verify-g1` correctly fails because `docker` is not installed.
- 2026-06-19 update: `make doctor` added; current host reports no `docker`, `psql`, `postgres`, or `initdb`, and `g1_ready=false`.
- 2026-06-19 update: root GitHub workflow `.github/workflows/eei-validation.yml` added in `LinzeColin/CodexProject` so EEI subdirectory changes can be validated by GitHub Actions.
- 2026-06-19 update: first root GitHub Actions run reached `Verify G1 PostgreSQL readiness and E2E` and failed there after prior verification steps passed.
- 2026-06-19 update: `scripts/wait_for_database.py` and `make wait-db` added to prevent immediate post-startup database readiness races.
- 2026-06-19 update: `make verify` passes after the wait-contract change; local `make verify-g1` still fails closed because Docker is not installed.

Remote verification:

- GitHub connector fetched `EEI/README.md` from `LinzeColin/CodexProject` on `main`.

## Not Completed

- Docker is not installed on the current host.
- `docker compose up -d postgres` and PostgreSQL container health checks have not been run.
- `/health/ready` now requires a real PostgreSQL readiness check; no database means `not_ready`.
- G1 is not PASS yet.
- Remote GitHub Actions needs to be re-run after the PostgreSQL wait contract is pushed.
- G2 domain schema/migration/data model work has not started.
- MVP is not complete.

## Recommended Next Step

Resolve G1 database service verification:

1. Install/start Docker Desktop or approve another local PostgreSQL service path.
2. Copy `.env.example` to `.env`.
3. Run `make verify-g1`; this now starts Docker PostgreSQL, waits for `select 1`, runs `make health`, then static/unit/E2E verification.
4. Inspect GitHub Actions for `.github/workflows/eei-validation.yml` after the wait-contract push.
5. Only consider G1 PASS after either local Docker/PostgreSQL or GitHub Actions proves `make verify-g1`.
