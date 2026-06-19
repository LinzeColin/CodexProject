# HANDOFF

Updated: 2026-06-19 Australia/Sydney

## Current Goal

开发推进到满足 MVP 的交付标准 for 商域图谱 / Enterprise Ecosystem Intelligence.

## Current Status

- GitHub target: `LinzeColin/CodexProject/EEI`
- Current gate: Phase 1 / G2 - Domain and data model
- Gate status: IN PROGRESS
- Previous gate: Phase 1 / G1 - Repository foundation
- G1 status: PASS by GitHub Actions run `27820777762`
- Local EEI repo commits:
  - `1f4a813` baseline Task Pack import
  - `d53e72d` Phase 0 governance freeze
  - `8329592` G1 repository foundation batch 1
  - `3e04747` PostgreSQL readiness contract
  - `53ece4b` G1 environment doctor
  - `baa5dbd` PostgreSQL startup wait contract
- GitHub `CodexProject` commit pushed:
  - `5de38fd` wait for EEI PostgreSQL readiness

## Completed

- Imported Task Pack v4.2.0 into `work/EEI`.
- Added `PURSUING_GOAL.md`, `CURRENT_PHASE.md`, ADR-006 through ADR-015, and `docs/phase/MVP_DEVELOPMENT_RECORD.md`.
- Added `data/product_navigation_catalog.csv` for the frozen 16 user-facing navigation modules.
- Fixed release gate mapping drift and added validator coverage.
- Added pinned pnpm/uv workspace, FastAPI health shell, Next.js Watchlist-first workspace shell, worker/package/infra anchors, contract validation, secret scan, unit test, and Playwright smoke test.
- Pushed the current EEI subtree to GitHub at `LinzeColin/CodexProject/EEI`.
- Started G2 database foundation with reversible SQL migration scaffolding, seed loader, schema checks, and integration test.

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
- 2026-06-19 update: GitHub Actions run `27820777762` passed; step 8 `Verify G1 PostgreSQL readiness and E2E` passed.
- 2026-06-19 update: `make verify-g2-db` added; local run fails closed because Docker is not installed.

Remote verification:

- GitHub connector fetched `EEI/README.md` from `LinzeColin/CodexProject` on `main`.
- GitHub Actions run `27820777762`: PASS.
- GitHub Actions job `82333085277`: PASS.

## Not Completed

- Docker is not installed on the current host, so local `make verify-g1` still fails closed.
- G2 migration/seed implementation has not yet passed remote PostgreSQL CI.
- T205 synthetic recursive supply-chain fixtures are not started.
- T1103-T1109 visual company workspace tasks are not started.
- MVP is not complete.

## Recommended Next Step

Start G2 with a bounded database-first run:

1. Update the root GitHub Actions workflow to run `make verify-g2-db`.
2. Push the G2 database foundation batch and inspect Actions.
3. If CI passes, mark the database subset of G2 as proven and proceed to T205 fixtures.
4. If CI fails, fix migration/seed/rollback without weakening the integration test.
