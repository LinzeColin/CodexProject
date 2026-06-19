# HANDOFF

Updated: 2026-06-19 Australia/Sydney

## Current Goal

开发推进到满足 MVP 的交付标准 for 商域图谱 / Enterprise Ecosystem Intelligence.

## Current Status

- GitHub target: `LinzeColin/CodexProject/EEI`
- Current gate: Phase 1 / G3 - Entry and management
- Gate status: IN PROGRESS
- Previous gate: Phase 1 / G2 - Domain and data model
- G2 status: PASS by GitHub Actions run `27828738097` plus `DEFER-003` for A026/A027 gold evaluation
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
  - `8ff658f` feat: add EEI fixture reroot workspace

## Completed

- Imported Task Pack v4.2.0 into `work/EEI`.
- Added `PURSUING_GOAL.md`, `CURRENT_PHASE.md`, ADR-006 through ADR-015, and `docs/phase/MVP_DEVELOPMENT_RECORD.md`.
- Added `data/product_navigation_catalog.csv` for the frozen 16 user-facing navigation modules.
- Fixed release gate mapping drift and added validator coverage.
- Added pinned pnpm/uv workspace, FastAPI health shell, Next.js Watchlist-first workspace shell, worker/package/infra anchors, contract validation, secret scan, unit test, and Playwright smoke test.
- Pushed the current EEI subtree to GitHub at `LinzeColin/CodexProject/EEI`.
- Started G2 database foundation with reversible SQL migration scaffolding, seed loader, schema checks, and integration test.
- Added G2 domain API repository anchors for home, exploration, Watchlist, scoring profiles, audit logs, calibration queueing, change feed, and relationship supersession/conflict preservation.
- Completed T203 and T206 by GitHub Actions run `27823282804`.
- Added a visual-first NVIDIA synthetic recursive supply-chain workspace with visible fixture notices, stage coverage, relationship labels, and three-step reroot path.
- Completed T205, A025, and A067 by GitHub Actions run `27824233483`.
- Added business, capital/control, and policy/risk layers to the visual workspace; split node selection from rerooting; added inspector actions and keyboard-reachable node selection.
- Completed T1103, T1104, T1107, and T1108 with A136-A140 and A146-A150 by GitHub Actions run `27825230977`.
- Added persistent analysis lenses, semantic zoom L0-L3, grouped synthetic system-maker list expansion, bounded first-screen graph budget checks, directional grammar assertions, and nonblank reroot fallback behavior.
- Completed T1105, T1106, and T1109 with A141-A145 and A151-A152 by GitHub Actions run `27826081868`.
- Added the T1203 CSV-backed taxonomy and object-scope API with catalog inventory, catalog detail, CSV export, object-scope coverage counts, and A169 local verification.
- Completed T1203 and A169 by GitHub Actions run `27826870509`; G2 task list is complete, but G2 remains `IN PROGRESS` pending acceptance audit for unresolved G2-linked IDs.
- Completed G2 acceptance audit pass 1 locally: A015-A022, A024, and A028 now have explicit validator/integration evidence; A012-A014, A026-A027, and A170 remain open.
- Completed G2 acceptance audit pass 1 remote CI by GitHub Actions run `27827498238`; job `82355514060` passed static/contract/lint/typecheck/unit plus G2 PostgreSQL migrations and E2E.
- Added T1204 `/objects-scope` visible navigation screen and marked A170 done locally.
- Completed T1204 and A170 by GitHub Actions run `27828194718`; job `82357916025` passed static/contract/lint/typecheck/unit plus G2 PostgreSQL migrations and E2E.
- Added A012-A014 data quality and amount/unknown regression checks locally; A026/A027 remain open because real gold precision evaluation is not implemented.
- Completed A012-A014 data contract checks by GitHub Actions run `27828738097`; job `82359769929` passed static/contract/lint/typecheck/unit plus G2 PostgreSQL migrations and E2E.
- Closed G2 as `PASS` with `DEFER-003`; A026/A027 remain open for T904/G9 gold precision evaluation rather than synthetic self-grading.
- Proved G2 gate-close commit by GitHub Actions run `27829131193`; job `82361095081` passed.

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
- 2026-06-19 update: GitHub Actions run `27821808812` passed; `make verify-g2-db` proved PostgreSQL migration, seed idempotency, rollback, and E2E.
- 2026-06-19 update: T205 synthetic fixture loader added locally; remote PostgreSQL CI still needs to prove it.
- 2026-06-19 update: GitHub Actions run `27822341025` passed; backend fixture load/idempotency/live-separation/stage checks are proven.
- 2026-06-19 update: GitHub Actions run `27823282804` passed; T203/T206 domain API repository and A023/A090 integration checks are proven.
- 2026-06-19 update: GitHub Actions run `27824233483` passed; A025 visible fixture marking and A067 NVIDIA recursive supply-chain E2E are proven.
- 2026-06-19 update: local `npx --yes pnpm@11.8.0 --filter @eei/web test:e2e` passed 5 tests for A136-A140 and A146-A150.
- 2026-06-19 update: GitHub Actions run `27825230977` passed; A136-A140 and A146-A150 visual workspace acceptance checks are proven.
- 2026-06-19 update: local `npx --yes pnpm@11.8.0 --filter @eei/web test:e2e` passed 9 tests for A141-A145 and A151-A152.
- 2026-06-19 update: GitHub Actions run `27826081868` passed; A141-A145 and A151-A152 lens, semantic-zoom, budget, and mental-map checks are proven.
- 2026-06-19 update: local `.venv/bin/uv run pytest tests/unit/test_api_health.py -q` passed 7 tests for catalog/object-scope API coverage.
- 2026-06-19 update: local `make verify` passed after the T1203 catalog API change.
- 2026-06-19 update: local `env -u DATABASE_URL .venv/bin/uv run pytest tests/integration -q` passed with 1 expected skip.
- 2026-06-19 update: local `make verify-g2-db` still fails closed because Docker is not installed.
- 2026-06-19 update: GitHub Actions run `27826870509` passed; job `82353421402` proved T1203 through static/contract/lint/typecheck/unit plus G2 PostgreSQL migrations and E2E.
- 2026-06-19 update: local `make verify` passed after strengthening G2 schema checks and acceptance traceability.
- 2026-06-19 update: GitHub Actions run `27827498238` passed; job `82355514060` proved strengthened G2 schema checks under PostgreSQL.
- 2026-06-19 update: local `npx --yes pnpm@11.8.0 --filter @eei/web test:e2e` passed 10 tests for the Objects and Scope screen.
- 2026-06-19 update: local `npx --yes pnpm@11.8.0 --filter @eei/web build` passed with static route `/objects-scope`.
- 2026-06-19 update: local `make verify` passed after T1204.
- 2026-06-19 update: GitHub Actions run `27828194718` passed; job `82357916025` proved T1204 remotely.
- 2026-06-19 update: local `make verify` passed after A012-A014 data contract checks.
- 2026-06-19 update: GitHub Actions run `27828738097` passed; job `82359769929` proved A012-A014 data contract checks under PostgreSQL.
- 2026-06-19 update: local `make verify` passed after T300/A038 typed entity search, alias seeding, `pg_trgm` schema support, and governance trace count repair.
- 2026-06-19 update: local `env -u DATABASE_URL .venv/bin/uv run pytest tests/integration -q` passed with 1 expected skip.
- 2026-06-19 update: local `make verify-g2-db` still fails closed because Docker is not installed.
- 2026-06-19 update: GitHub Actions run `27830167274` failed on A038 because SQL `ILIKE` treated `_` as a wildcard; fixed by escaping LIKE patterns.
- 2026-06-19 update: GitHub Actions run `27830403844` passed; job `82365417548` proved T300/A038 typed entity search under PostgreSQL.

Remote verification:

- GitHub connector fetched `EEI/README.md` from `LinzeColin/CodexProject` on `main`.
- GitHub Actions run `27820777762`: PASS.
- GitHub Actions job `82333085277`: PASS.
- GitHub Actions run `27821808812`: PASS.
- GitHub Actions job `82336483266`: PASS.
- GitHub Actions run `27822341025`: PASS.
- GitHub Actions job `82338210943`: PASS.
- GitHub Actions run `27823282804`: PASS.
- GitHub Actions job `82341300203`: PASS.
- GitHub Actions run `27824233483`: PASS.
- GitHub Actions job `82344470407`: PASS.
- GitHub Actions run `27825230977`: PASS.
- GitHub Actions job `82347837228`: PASS.
- GitHub Actions run `27826081868`: PASS.
- GitHub Actions job `82350766117`: PASS.
- GitHub Actions run `27826870509`: PASS.
- GitHub Actions job `82353421402`: PASS.
- GitHub Actions run `27827498238`: PASS.
- GitHub Actions job `82355514060`: PASS.
- GitHub Actions run `27828194718`: PASS.
- GitHub Actions job `82357916025`: PASS.
- GitHub Actions run `27828738097`: PASS.
- GitHub Actions job `82359769929`: PASS.
- GitHub Actions run `27829131193`: PASS.
- GitHub Actions job `82361095081`: PASS.
- GitHub Actions run `27830167274`: FAIL, fixed by escaping SQL LIKE patterns for `_`, `%`, and `\`.
- GitHub Actions job `82364621109`: FAIL.
- GitHub Actions run `27830403844`: PASS.
- GitHub Actions job `82365417548`: PASS.

## Not Completed

- Docker is not installed on the current host, so local `make verify-g1` still fails closed.
- G2 database foundation subset passed remote PostgreSQL CI.
- T205 is DONE, including backend fixture load, visible fixture marking, and recursive NVIDIA scenario E2E.
- T1103/T1104/T1107/T1108 visual company workspace tasks are DONE and remote CI passed.
- T1105/T1106/T1109 visual company workspace tasks are DONE and remote CI passed.
- T1203 taxonomy/object-scope API is DONE and remote CI passed.
- G2 is `PASS`; A026 and A027 remain open for T904/G9 gold precision evaluation under `DEFER-003`.
- T1204 / A170 Objects and Scope navigation screen is DONE and remote CI passed.
- T300 / A038 typed entity search is DONE and remote CI passed.
- G4 remains open because T1205 and T1208 are not complete.
- MVP is not complete.

## Recommended Next Step

Continue G3 with bounded entry/management implementation:

1. Start T301/T302/T303 home, industry and Watchlist entry-management implementation.
2. Keep A026/A027 open until T904/G9 real gold precision evaluation.
3. Continue G4/T1205 only after the next G3 slice is bounded.
