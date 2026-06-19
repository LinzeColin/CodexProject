# HANDOFF

Updated: 2026-06-19 Australia/Sydney

## Current Goal

开发推进到满足 MVP 的交付标准 for 商域图谱 / Enterprise Ecosystem Intelligence.

## Current Status

- GitHub target: `LinzeColin/CodexProject/EEI`
- Current gate: Phase 1 / G4 - Recursive exploration and live context
- Gate status: IN PROGRESS
- Previous gate: Phase 1 / G3 - Entry and management
- G3 status: PASS by GitHub Actions run `27835479352`
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
- Latest GitHub implementation commit proven by CI:
  - `79f8185` test: prove EEI breadcrumb history sync

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
- Added T303 Watchlist persistence breadth: `/v1/watchlists/{watchlistId}` detail, item remove/restore, entity/industry/theme/facility item validation, saved state persistence, and operation-log checks.
- Completed T303 with A035/A036 by GitHub Actions run `27832504683`; A037 remains open for T306 UI/E2E unread-change and saved-view evidence.
- Added T304 user-oriented home entry controls on the existing Watchlist-first graph workspace: global search, industries, Watchlist, recent explorations, important changes, freshness, active model status, calibration status, and keyboard entry coverage.
- Completed T304 with A029/A030/A039/A040 by GitHub Actions run `27833468626`; job `82375686964` passed static/contract/lint/typecheck/unit plus PostgreSQL migrations and E2E.
- Added T305 `/industries` landscape page with chain stages, subindustries, entities, bottlenecks, capital, policy, changes, and visible cross-industry navigation path.
- Completed T305 with A032/A034 by GitHub Actions run `27834152257`; job `82377987783` passed static/contract/lint/typecheck/unit plus PostgreSQL migrations and E2E.
- Added T306 Watchlist unread-change and saved-view/profile E2E restore behavior on the home workspace.
- Completed T306 with A037 by GitHub Actions run `27834549643`; job `82379303157` passed static/contract/lint/typecheck/unit plus PostgreSQL migrations and E2E.
- Added URL/session/localStorage workspace state, browser/app back, clickable breadcrumb restore, versioned local saved views, as-of timeline overlays, and shared active model/profile/data/score snapshot reporting.
- Added model config validation to Task Pack validation and closed T1110, T1111, T1112, T1113, T1201, and T1206 locally.
- Marked A154, A155, A156, A157, A158, A159, A160, A171, and A178 as `DONE` with local E2E/model-validation evidence.
- Completed the remaining G3 state/history/saved-view/timeline/model-context batch by GitHub Actions run `27835479352`; job `82382357217` passed.
- Closed G3 as `PASS` and started G4 as `IN PROGRESS`.
- Added T1205 `/development-status` navigation screen with six delivery status lanes, tasks/risks/controls/acceptance evidence links, function status, task evidence, acceptance evidence, and risk-control panels.
- Completed T1205 with A173/A174 by GitHub Actions run `27836121209`; job `82384436376` passed static/contract/lint/typecheck/unit plus PostgreSQL migrations and E2E.
- Added T400 bounded `/v1/explore` query defaults, hard limits, truncation metadata, continuation metadata, OpenAPI contract updates, and integration assertions for A041-A044.
- Completed T400 with A041-A044 by GitHub Actions run `27836910412`; job `82386959577` passed static/contract/lint/typecheck/unit plus PostgreSQL migrations and E2E.
- Fixed a saved-view restore hydration race exposed by GitHub Actions run `27836653255`: `restoreSavedView()` now reads the latest persisted saved-view payload from `localStorage` before applying workspace state.
- Added T401 exploration session and URL state contract with migration `0002_exploration_state`, persisted direction/hops/budget, response `state.url_state`, restore payload, and A051 integration assertions.
- Completed T401 with A051 by GitHub Actions run `27837609322`; job `82389170752` passed static/contract/lint/typecheck/unit plus PostgreSQL migrations and E2E.
- Added T402 reroot inherited/reset state contract: default reroot preserves layers/time/profile/filters/direction/hops/budget, while `inherit_state=false` resets to canonical defaults.
- Completed T402 with A045-A047 by GitHub Actions run `27838436423`; job `82391789245` passed static/contract/lint/typecheck/unit plus PostgreSQL migrations and E2E.
- Added T403 incremental directional expand contract locally: `/v1/explore/expand` expands from a selected anchor without changing session root, filters by selected direction/layers, and bounds returned graph size by `expand_nodes`.
- Completed T403 with A052 by GitHub Actions run `27839023906`; job `82393647163` passed static/contract/lint/typecheck/unit plus PostgreSQL migrations and E2E.
- Added T404 breadcrumb/browser-history synchronization contract locally: full path breadcrumb is visible and clickable, browser back/forward and app back restore identical focus/path state.
- Completed T404 with A049-A050 by GitHub Actions run `27839493483`; job `82395103164` passed static/contract/lint/typecheck/unit plus PostgreSQL migrations and E2E.

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
- 2026-06-19 update: GitHub Actions run `27830557839` passed; job `82365960123` proved the final T300 evidence commit.
- 2026-06-19 update: local `make verify` passed after T301 `/v1/home` aggregation, freshness, global-search metadata, and calibration status contract.
- 2026-06-19 update: local `env -u DATABASE_URL .venv/bin/uv run pytest tests/integration -q` passed with 1 expected skip after T301.
- 2026-06-19 update: GitHub Actions run `27830933960` failed because the integration test asserted non-empty home changes before any change records existed.
- 2026-06-19 update: GitHub Actions run `27831147683` passed; job `82367964670` proved T301 home aggregation under PostgreSQL after aligning the changes-feed test lifecycle.
- 2026-06-19 update: GitHub Actions run `27831351290` passed; job `82368640839` proved the final T301 evidence commit.
- 2026-06-19 update: local `make verify` passed after T302 `/v1/industries` and `/v1/industries/{industryId}/landscape`.
- 2026-06-19 update: GitHub Actions run `27831861052` passed; job `82370353436` proved T302 industry landscape API, fixture memberships, and A031/A033 checks under PostgreSQL.
- 2026-06-19 update: local `make verify` passed after T303 Watchlist persistence breadth and explicit DELETE 204 response fix.
- 2026-06-19 update: local `env -u DATABASE_URL .venv/bin/uv run pytest tests/integration -q` passed with 1 expected skip after T303.
- 2026-06-19 update: GitHub Actions run `27832285368` failed because `DELETE /v1/watchlists/{watchlistId}/items` returned a response object with no status code.
- 2026-06-19 update: GitHub Actions run `27832504683` passed; job `82372497975` proved T303 Watchlist CRUD/restore/item-type persistence under PostgreSQL after returning an explicit 204 response.
- 2026-06-19 update: local `npx --yes pnpm@11.8.0 --filter @eei/web test:e2e` passed 12 tests after T304 home page entry controls.
- 2026-06-19 update: local `make verify` passed after T304; governance trace count is now 215 after adding missing A039/A040 traceability rows.
- 2026-06-19 update: GitHub Actions run `27833468626` passed; job `82375686964` proved T304 user-oriented home entry and updated governance count on remote CI.
- 2026-06-19 update: local `npx --yes pnpm@11.8.0 --filter @eei/web test:e2e -- tests/e2e/industry.spec.ts` passed 14 tests after T305.
- 2026-06-19 update: local `npx --yes pnpm@11.8.0 --filter @eei/web build` passed with static `/industries`.
- 2026-06-19 update: local `make verify` passed after T305.
- 2026-06-19 update: GitHub Actions run `27834152257` passed; job `82377987783` proved T305 industry landscape page remotely.
- 2026-06-19 update: local `npx --yes pnpm@11.8.0 --filter @eei/web test:e2e` passed 15 tests after T306 Watchlist saved-view restore.
- 2026-06-19 update: local `npx --yes pnpm@11.8.0 --filter @eei/web build` passed after T306 with static `/`, `/industries`, and `/objects-scope`.
- 2026-06-19 update: local `make verify` passed after T306.
- 2026-06-19 update: GitHub Actions run `27834549643` passed; job `82379303157` proved T306 remotely.
- 2026-06-19 update: local `npx --yes pnpm@11.8.0 --filter @eei/web typecheck` passed after T1110/T1111/T1112/T1113/T1201/T1206.
- 2026-06-19 update: local `npx --yes pnpm@11.8.0 --filter @eei/web test:e2e` passed 19 tests after state/history/saved-view/timeline/active-context implementation.
- 2026-06-19 update: local `.venv/bin/uv run python scripts/validate_task_pack.py` passed and now includes model config validation.
- 2026-06-19 update: local `npx --yes pnpm@11.8.0 --filter @eei/web build` passed after the state/context batch.
- 2026-06-19 update: local `make verify` passed after the state/context batch.
- 2026-06-19 update: local `git diff --check` passed after the state/context batch.
- 2026-06-19 update: GitHub Actions run `27835479352` passed; job `82382357217` proved the G3 state/history/saved-view/timeline/model-context batch remotely.
- 2026-06-19 update: GitHub Actions step 7 `Verify static, contract, lint, typecheck and unit tests` passed.
- 2026-06-19 update: GitHub Actions step 8 `Verify G2 PostgreSQL migrations and E2E` passed.
- 2026-06-19 update: local `npx --yes pnpm@11.8.0 --filter @eei/web test:e2e` passed 21 tests after T1205.
- 2026-06-19 update: local `npx --yes pnpm@11.8.0 --filter @eei/web build` passed with static `/development-status`.
- 2026-06-19 update: local `make verify` passed after T1205.
- 2026-06-19 update: GitHub Actions run `27836121209` passed; job `82384436376` proved T1205 remotely.
- 2026-06-19 update: local `.venv/bin/uv run python scripts/validate_task_pack.py` passed after T400 bounded graph query service.
- 2026-06-19 update: local `env -u DATABASE_URL .venv/bin/uv run pytest tests/integration -q` passed with 1 expected skip after T400 because this host has no configured PostgreSQL.
- 2026-06-19 update: local `make verify` passed after T400.
- 2026-06-19 update: local `git diff --check` passed after T400.
- 2026-06-19 update: GitHub Actions run `27836653255` failed after T400 because Step 8 E2E hit a saved-view restore hydration race; PostgreSQL integration itself passed in that run.
- 2026-06-19 update: local `npx --yes pnpm@11.8.0 --filter @eei/web test:e2e -- tests/e2e/state-contract.spec.ts` passed 21 tests after the saved-view restore hardening.
- 2026-06-19 update: local `make verify` passed after the saved-view restore hardening.
- 2026-06-19 update: local `git diff --check` passed after the saved-view restore hardening.
- 2026-06-19 update: GitHub Actions run `27836910412` passed; job `82386959577` proved T400 and the saved-view restore hardening remotely.
- 2026-06-19 update: GitHub Actions step 7 `Verify static, contract, lint, typecheck and unit tests` passed.
- 2026-06-19 update: GitHub Actions step 8 `Verify G2 PostgreSQL migrations and E2E` passed.
- 2026-06-19 update: local `make verify` passed after T401 session/url state.
- 2026-06-19 update: local `env -u DATABASE_URL .venv/bin/uv run pytest tests/integration -q` passed with 1 expected skip after T401 because this host has no configured PostgreSQL.
- 2026-06-19 update: local `git diff --check` passed after T401.
- 2026-06-19 update: GitHub Actions run `27837609322` passed; job `82389170752` proved T401 remotely.
- 2026-06-19 update: GitHub Actions step 7 `Verify static, contract, lint, typecheck and unit tests` passed.
- 2026-06-19 update: GitHub Actions step 8 `Verify G2 PostgreSQL migrations and E2E` passed.
- 2026-06-19 update: local `make verify` passed after T402 reroot inherited/reset state.
- 2026-06-19 update: local `env -u DATABASE_URL .venv/bin/uv run pytest tests/integration -q` passed with 1 expected skip after T402 because this host has no configured PostgreSQL.
- 2026-06-19 update: local `git diff --check` passed after T402.
- 2026-06-19 update: GitHub Actions run `27838042448` failed on T402 because inherited PostgreSQL `datetime` state serialized as `+00:00` instead of canonical `Z`; fixed by canonical UTC API serialization.
- 2026-06-19 update: GitHub Actions run `27838285776` failed on T402 because the reset-reroot test expected a stale theme display name; fixed by aligning the assertion with `data/mock_entities.json`.
- 2026-06-19 update: GitHub Actions run `27838436423` passed; job `82391789245` proved T402 remotely.
- 2026-06-19 update: GitHub Actions step 7 `Verify static, contract, lint, typecheck and unit tests` passed.
- 2026-06-19 update: GitHub Actions step 8 `Verify G2 PostgreSQL migrations and E2E` passed.
- 2026-06-19 update: local `make verify` passed after T403 incremental directional expand.
- 2026-06-19 update: local `env -u DATABASE_URL .venv/bin/uv run pytest tests/integration -q` passed with 1 expected skip after T403 because this host has no configured PostgreSQL.
- 2026-06-19 update: local `git diff --check` passed after T403.
- 2026-06-19 update: GitHub Actions run `27839023906` passed; job `82393647163` proved T403 remotely.
- 2026-06-19 update: GitHub Actions step 7 `Verify static, contract, lint, typecheck and unit tests` passed.
- 2026-06-19 update: GitHub Actions step 8 `Verify G2 PostgreSQL migrations and E2E` passed.
- 2026-06-19 update: local `npx --yes pnpm@11.8.0 --filter @eei/web typecheck` passed after T404.
- 2026-06-19 update: local `npx --yes pnpm@11.8.0 --filter @eei/web test:e2e -- tests/e2e/state-contract.spec.ts` passed 21 tests after T404.
- 2026-06-19 update: local `make verify` passed after T404.
- 2026-06-19 update: local `git diff --check` passed after T404.
- 2026-06-19 update: GitHub Actions run `27839493483` passed; job `82395103164` proved T404 remotely.
- 2026-06-19 update: GitHub Actions step 7 `Verify static, contract, lint, typecheck and unit tests` passed.
- 2026-06-19 update: GitHub Actions step 8 `Verify G2 PostgreSQL migrations and E2E` passed.

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
- GitHub Actions run `27830557839`: PASS.
- GitHub Actions job `82365960123`: PASS.
- GitHub Actions run `27830933960`: FAIL, fixed by moving non-empty home changes assertion after generated change records.
- GitHub Actions job `82367238904`: FAIL.
- GitHub Actions run `27831147683`: PASS.
- GitHub Actions job `82367964670`: PASS.
- GitHub Actions run `27831351290`: PASS.
- GitHub Actions job `82368640839`: PASS.
- GitHub Actions run `27831861052`: PASS.
- GitHub Actions job `82370353436`: PASS.
- GitHub Actions run `27832285368`: FAIL, fixed by returning an explicit `Response(status_code=204)` from the Watchlist item delete route.
- GitHub Actions job `82371769481`: FAIL.
- GitHub Actions run `27832504683`: PASS.
- GitHub Actions job `82372497975`: PASS.
- GitHub Actions run `27833468626`: PASS.
- GitHub Actions job `82375686964`: PASS.
- GitHub Actions run `27834152257`: PASS.
- GitHub Actions job `82377987783`: PASS.
- GitHub Actions run `27834549643`: PASS.
- GitHub Actions job `82379303157`: PASS.
- GitHub Actions run `27835479352`: PASS.
- GitHub Actions job `82382357217`: PASS.
- GitHub Actions run `27835657493`: PASS.
- GitHub Actions job `82382936095`: PASS.
- GitHub Actions run `27836121209`: PASS.
- GitHub Actions job `82384436376`: PASS.
- GitHub Actions run `27836653255`: FAIL, fixed by reading persisted saved-view state during restore instead of relying only on hydration-populated React state.
- GitHub Actions job `82386126081`: FAIL.
- GitHub Actions run `27836910412`: PASS.
- GitHub Actions job `82386959577`: PASS.
- GitHub Actions run `27837609322`: PASS.
- GitHub Actions job `82389170752`: PASS.
- GitHub Actions run `27838042448`: FAIL, fixed by canonical UTC API serialization for PostgreSQL-inherited exploration state.
- GitHub Actions job `82390539693`: FAIL.
- GitHub Actions run `27838285776`: FAIL, fixed by aligning reset-reroot fixture display name with `data/mock_entities.json`.
- GitHub Actions job `82391319828`: FAIL.
- GitHub Actions run `27838436423`: PASS.
- GitHub Actions job `82391789245`: PASS.
- GitHub Actions run `27838623184`: PASS.
- GitHub Actions job `82392383667`: PASS.
- GitHub Actions run `27839023906`: PASS.
- GitHub Actions job `82393647163`: PASS.
- GitHub Actions run `27839173843`: PASS.
- GitHub Actions job `82394120613`: PASS.
- GitHub Actions run `27839493483`: PASS.
- GitHub Actions job `82395103164`: PASS.
- GitHub Actions run `27840198892`: PASS.
- GitHub Actions job `82397301394`: PASS.
- GitHub Actions run `27840744734`: PASS.
- GitHub Actions job `82399027153`: PASS.
- GitHub Actions run `27841131928`: PASS.
- GitHub Actions job `82400216009`: PASS.

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
- T301 home aggregation API is DONE and remote CI passed.
- T302 industry list and landscape API is DONE and remote CI passed; A031/A033 are DONE.
- T303 Watchlist CRUD and persistence API is DONE and remote CI passed; A035/A036 are DONE.
- T304 user-oriented home page is DONE and remote CI passed; A029/A030/A039/A040 are DONE.
- T305 industry landscape page is DONE and remote CI passed; A032/A034 are DONE.
- T306 home/industry/watchlist E2E is DONE and remote CI passed; A037 is DONE.
- T1110/T1111/T1112/T1113/T1201/T1206 are DONE and remote CI passed.
- G3 is `PASS`.
- T1205 / A173 / A174 are DONE and remote CI passed.
- T400 / A041-A044 are DONE and remote CI passed.
- T401 / A051 are DONE and remote CI passed.
- T402 / A045-A047 are DONE and remote CI passed.
- T403 / A052 is DONE and remote CI passed.
- T404 / A049-A050 is DONE and remote CI passed.
- T405 / A053-A055/A058 is DONE and remote CI passed; `tests/e2e/home.spec.ts` passed with 22 tests after adding graph table alternative, node actions, pin/compare/Watchlist state, and explicit non-color visual semantics.
- T406 / A056 is DONE and remote CI passed; `/v1/paths` now supports bounded evidence-bearing shortest/upstream/downstream/control/capital/policy/bottleneck path queries.
- T407 / A057 is DONE and remote CI passed; the graph inspector now explains inclusion sorting, truncation reasons and `/v1/explore/expand` continuation metadata.
- T408 / A048 is DONE locally; `tests/e2e/state-contract.spec.ts` now has a dedicated critical three-reroot E2E ending at `nvidia.foundry.equipment.materials`, and local E2E plus `make verify` passed.
- G4 remains open because recursive exploration, live context, accessible list/table equivalents, model preview propagation, and remaining governance tasks are not complete.
- MVP is not complete.

## Recommended Next Step

Continue G4 with a bounded recursive-exploration/live-context batch:

1. Push T408 and wait for GitHub Actions PostgreSQL/E2E evidence.
2. Start T409 cross-industry reroot E2E after T408 CI is recorded.
3. Keep A026/A027 open until T904/G9 real gold precision evaluation.
4. Preserve the existing G3/G4 state/history/path contracts while adding recursive exploration and governance views.
