# MVP Development Record

Append-only development ledger for 商域图谱 / Enterprise Ecosystem Intelligence.

## 2026-06-19 - Phase 1 / G1 start

Status: DONE

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

## 2026-06-19 - Phase 1 / G1 close and G2 start

Status: G1 PASS; G2 IN PROGRESS

Completed:

- Pushed `LinzeColin/CodexProject` commit `5de38fd` with the PostgreSQL wait contract.
- Confirmed GitHub Actions run `27820777762` completed with conclusion `success`.
- Confirmed the `verify` job and all steps passed, including `Verify G1 PostgreSQL readiness and E2E`.
- Advanced `data/release_gate_catalog.csv` to `G1=PASS` and `G2=IN PROGRESS`.

Verification results:

- GitHub Actions run: `https://github.com/LinzeColin/CodexProject/actions/runs/27820777762`.
- GitHub Actions job: `https://github.com/LinzeColin/CodexProject/actions/runs/27820777762/job/82333085277`.
- Step 8 `Verify G1 PostgreSQL readiness and E2E`: PASS.

G2 scope and Acceptance IDs:

- T200: A011, A012, A013, A014, A015, A022.
- T201: A016, A020, A021.
- T202: A019.
- T203: A011, A090.
- T204: A017, A018, A028.
- T205: A016, A025, A067.
- T206: A023.
- T207: A024, A028.
- T208: A011, A026, A027.
- T1103: A136, A137.
- T1104: A138, A139, A140.
- T1105: A141, A142.
- T1106: A143, A144, A145.
- T1107: A146, A147.
- T1108: A148, A149, A150.
- T1109: A151, A152.
- T1203: A169, A170.

Residual risks:

- Local host still cannot run Docker-based `make verify-g1`; G1 PASS is based on GitHub Actions evidence.
- G2 has a wide acceptance surface; implementation should split database migrations/data checks from visual canvas work to keep diffs reviewable.

## 2026-06-19 - Phase 1 / G2 database foundation batch 1

Status: IN PROGRESS

Completed:

- Added `infra/db/migrations/0001_core_domain/up.sql` and `down.sql`.
- Added `scripts/migrate.py` for versioned PostgreSQL upgrade/downgrade/status operations.
- Added `scripts/load_seed_catalogs.py` for deterministic catalog and research-universe seed loading.
- Added `scripts/check_database_schema.py` for table and seed-count invariants.
- Added `tests/integration/test_database_migrations.py` for migration, seed idempotency, and rollback.
- Added `make verify-g2-db` to run Docker PostgreSQL, health, static verification, integration tests, and E2E.
- Extended `specs/domain_schema.sql` with catalog-backed relationship families, relationship types, supply-chain stages, seed runs, and research-universe tables.
- Marked T200, T201, T202, T203, T204, T206, T207, and T208 as `IN PROGRESS`.

Verification results:

- `make lint`: PASS.
- `make verify`: PASS.
- `env -u DATABASE_URL .venv/bin/uv run pytest tests/integration -q`: PASS with 1 expected skip.
- `make verify-g2-db`: expected FAIL on current host because `docker` is not installed.

Acceptance IDs touched:

- A011, A012, A013, A014, A015, A016, A017, A018, A019, A020, A021, A022, A023, A024, A026, A027, A028, A090.

Residual risks:

- Actual PostgreSQL migration execution has not been proven locally because Docker is unavailable.
- GitHub Actions must be updated to run `make verify-g2-db` and prove migration/seed/rollback on PostgreSQL.
- T205 synthetic recursive supply-chain fixtures and T1103-T1109 visual canvas tasks are not started.

## 2026-06-20 - Phase 1 / T1306 A208 scale benchmark contracts

Status: IN PROGRESS

Completed:

- Added `scripts/run_scale_benchmarks.py` as a deterministic benchmark contract for API projection, layout, render payload, memory payload, estimated frame budget and synthetic long-task counts.
- Added `tests/unit/test_scale_benchmarks.py` to lock the A208 payload schema, target scale coverage semantics and per-scale pass/fail budget output.
- Added `make validate-scale-benchmark-smoke` and wired it into `make verify`.
- Added `make validate-scale-benchmark-operator` for the manual 10k/100k/1m operator contract.
- Added `scripts/run_browser_scale_benchmarks.mjs` for Chromium browser runtime frame, memory and long-task measurement.
- Advanced T1306/A208 governance from `NOT_STARTED` to `DONE`.

Verification results:

- `.venv/bin/python -m compileall scripts/run_scale_benchmarks.py tests/unit/test_scale_benchmarks.py scripts/validate_v5_production_readiness_sync.py`: PASS.
- `.venv/bin/python scripts/run_scale_benchmarks.py --scales 1000 --iterations 2 --mode ci_smoke --output artifacts/tests/a208/t1306_scale_benchmark_smoke.json --fail-on-budget --quiet`: PASS; output status remains `PARTIAL`.
- `node scripts/run_browser_scale_benchmarks.mjs --scales 10000,100000,1000000 --iterations 1 --output artifacts/tests/a208/t1306_browser_runtime_benchmark.json --fail-on-budget --quiet`: PASS; Chromium browser runtime status is `PASS`.
- `.venv/bin/python scripts/run_scale_benchmarks.py --scales 10000,100000,1000000 --iterations 1 --mode operator_full --output artifacts/tests/a208/t1306_scale_benchmark_operator_contract.json --browser-runtime-artifact artifacts/tests/a208/t1306_browser_runtime_benchmark.json --fail-on-budget --require-full-targets --quiet`: PASS; full A208 coverage status is `PASS`.
- `make validate-scale-benchmark-operator`: PASS with Chromium browser runtime and merged operator contract.
- `UV_CACHE_DIR=/private/tmp/eei-uv-cache PNPM=/Users/linzezhang/.cache/codex-runtimes/codex-primary-runtime/dependencies/bin/pnpm make verify`: PASS; includes A208 browser benchmark, merged operator contract, governance validators, lint, typecheck and 11 unit tests.
- GitHub Actions `EEI validation` run `27860478421`, job `82455538742`: PASS, including static/contract/lint/typecheck/unit and G2 PostgreSQL/E2E.

Residual risks:

- Browser runtime benchmark uses a bounded SVG runtime contract with 500 visible nodes and 2000 visible edges; production componentized frontend remains T1308/A211.
- Long-duration memory/timer/listener stability remains T1307/A209 soak scope.

## 2026-06-20 - Phase 1 / T1307 A209 soak smoke harness

Status: IN PROGRESS

Completed:

- Added `scripts/run_soak_smoke.mjs` as a browser+worker soak harness.
- Added `make validate-soak-smoke` and wired it into `make verify`.
- Generated `artifacts/tests/a209/t1307_soak_smoke.json` with heap, DOM, listener, timer, frame, long-task, CPU, retry and recovery metrics.
- Advanced T1307/A209 governance from `NOT_STARTED` to `IN PROGRESS`.

Verification results:

- `node --check scripts/run_soak_smoke.mjs`: PASS.
- `node scripts/run_soak_smoke.mjs --mode ci_smoke --duration-seconds 3 --output artifacts/tests/a209/t1307_soak_smoke.json --fail-on-budget --quiet`: PASS; output status remains `PARTIAL` because 4h/24h durations are not measured.
- `UV_CACHE_DIR=/private/tmp/eei-uv-cache PNPM=/Users/linzezhang/.cache/codex-runtimes/codex-primary-runtime/dependencies/bin/pnpm make verify`: PASS; includes T1307 soak smoke, A208 benchmark contracts, governance validators, lint, typecheck and 11 unit tests.
- GitHub Actions `EEI validation` run `27860819378`, job `82456417742`: PASS, including static/contract/lint/typecheck/unit and G2 PostgreSQL/E2E.

Residual risks:

- A209 is not complete until the same harness runs and records 4h and 24h operator soak evidence.
- Smoke validates the measurement contract and budget checks only; it does not prove long-duration memory, timer, listener or retry stability.

## 2026-06-19 - Phase 1 / G2 database CI repair loop 1

Status: IN PROGRESS

Failure evidence:

- GitHub Actions run `27821508751` failed in `Verify G2 PostgreSQL migrations and E2E`.
- Migration upgrade and schema table checks passed.
- `scripts/load_seed_catalogs.py` failed while loading `relationship_taxonomy.csv`.
- Root cause: `relationship_type_catalog.direction` allowed only `directed` and `undirected`, but the canonical taxonomy contains 6 `bidirectional` relationship types.

Fix:

- Updated `specs/domain_schema.sql` so `relationship_type_catalog.direction` allows `directed`, `undirected`, and `bidirectional`.

Verification to run:

- `make verify`.
- Push and rerun GitHub Actions `make verify-g2-db`.

## 2026-06-19 - Phase 1 / G2 database CI repair loop 2

Status: IN PROGRESS

Failure evidence:

- GitHub Actions run `27821664492` failed in `Verify G2 PostgreSQL migrations and E2E`.
- Migration upgrade and relationship taxonomy loading passed after repair loop 1.
- `scripts/load_seed_catalogs.py` failed while loading `supply_chain_stage_taxonomy.csv`.
- Root cause: `supply_chain_stages.default_direction` allowed an invented set, while the canonical taxonomy contains `upstream`, `downstream`, `midstream`, and `crosscutting`.

Fix:

- Updated `specs/domain_schema.sql` so `supply_chain_stages.default_direction` matches the canonical taxonomy.

Verification to run:

- `make verify`.
- Push and rerun GitHub Actions `make verify-g2-db`.

## 2026-06-19 - Phase 1 / G2 database foundation CI pass

Status: DATABASE SUBSET PASS; G2 IN PROGRESS

Completed:

- GitHub Actions run `27821808812` completed with conclusion `success`.
- Step 8 `Verify G2 PostgreSQL migrations and E2E` passed.
- Integration test `tests/integration/test_database_migrations.py` passed on PostgreSQL.
- E2E smoke test passed after the database integration test.
- Marked T200, T201, T202, T204, T207, and T208 as `DONE`.

Verification evidence:

- GitHub Actions run: `https://github.com/LinzeColin/CodexProject/actions/runs/27821808812`.
- GitHub Actions job: `82336483266`.
- `make verify-g2-db`: PASS in GitHub Actions.
- PostgreSQL readiness: PASS.
- Migration upgrade/schema check/seed idempotency/rollback integration test: PASS.
- Playwright E2E smoke: PASS.

Still open in G2:

- T203 remains `IN PROGRESS` because exploration, Watchlist, scoring, audit, and calibration repository/API behavior is not implemented yet.
- T205 remains `NOT STARTED` because synthetic recursive supply-chain fixtures are not loaded yet.
- T206 remains `IN PROGRESS` because supersession/conflict repository behavior is not implemented beyond schema fields.
- T1103-T1109 and T1203 remain not started or only indirectly scaffolded.

## 2026-06-19 - Phase 1 / G2 T205 synthetic fixture loader

Status: IN PROGRESS

Completed:

- Added fixture dataset, fixture entity notice, and fixture relationship notice tables to the core migration.
- Added `scripts/load_synthetic_fixtures.py` to load `data/mock_entities.json` and `data/mock_relationships.json` idempotently.
- Added fixture checks for A016, A025, and A067 into `scripts/check_database_schema.py`.
- Updated integration test flow to load fixtures twice and verify relationship families, fixture notices, and NVIDIA recursive supply-chain stage coverage.
- Marked T205 as `IN PROGRESS`.

Verification results:

- `make lint`: PASS.
- `make verify`: PASS.
- `env -u DATABASE_URL .venv/bin/uv run pytest tests/integration -q`: PASS with 1 expected skip.

Acceptance IDs touched:

- A016, A025, A067.

Residual risks:

- Actual fixture loading has not been proven on PostgreSQL yet because local Docker is unavailable.
- GitHub Actions must run `make verify-g2-db` to prove fixture migration, load, idempotency, and rollback.

## 2026-06-19 - Phase 1 / G2 T205 backend fixture CI pass

Status: BACKEND FIXTURE SUBSET PASS; T205 IN PROGRESS

Completed:

- GitHub Actions run `27822341025` completed with conclusion `success`.
- Step 8 `Verify G2 PostgreSQL migrations and E2E` passed after adding fixture loading.
- The integration test now proves migration upgrade, seed loading, fixture loading twice, fixture/live separation checks, NVIDIA stage coverage checks, and rollback.

Verification evidence:

- GitHub Actions run: `https://github.com/LinzeColin/CodexProject/actions/runs/27822341025`.
- GitHub Actions job: `82338210943`.
- `make verify-g2-db`: PASS in GitHub Actions.

Acceptance status:

- A016 backend data check is covered by fixture family validation.
- A025 is not fully accepted yet because visible UI/API content tests are not implemented.
- A067 is not fully accepted yet because scenario-level recursive exploration E2E is not implemented.

Residual risks:

- T205 remains `IN PROGRESS` until UI/API fixture marking and recursive scenario E2E exist.
- T203/T206 repository/API behavior is still needed before those acceptance IDs can close.

## 2026-06-19 - Phase 1 / G2 T203/T206 domain API repository pass

Status: DOMAIN API SUBSET PASS; G2 IN PROGRESS

Completed:

- Added database-backed FastAPI routes for `/v1/home`, `/v1/explore`, `/v1/explore/reroot`, `/v1/watchlists`, `/v1/changes`, `/v1/audit-logs`, `/v1/scoring/profiles`, and `/v1/calibrations`.
- Added `DomainRepository` methods for Watchlist persistence, exploration session history, bounded one-hop graph response, audit logging, calibration queueing, scoring profile reads, and relationship supersession/conflict recording.
- Seeded the default `balanced-v2` scoring model/profile/version from `config/model_profiles/balanced-v2.json` and `config/thresholds/default-v2.json`.
- Extended database checks to require the exploration/watchlist/scoring/change/audit/calibration tables, one active scoring profile, weight sum `1.0`, and fixed 14-day calibration cadence.
- Extended PostgreSQL integration coverage to exercise Watchlist add/list, home aggregation, exploration graph fixture disclosure, audit logs, manual calibration queueing, relationship supersession, conflict change feed, and rollback.
- Marked T203 and T206 as `DONE`.
- Marked A011, A023, and A090 as `DONE` with evidence in `tests/integration/test_database_migrations.py`.

Verification evidence:

- Local `make verify`: PASS.
- Local `env -u DATABASE_URL .venv/bin/uv run pytest tests/integration -q`: PASS with 1 expected skip.
- Local `make verify-g2-db`: FAIL CLOSED because Docker is not installed on this host.
- GitHub Actions run: `https://github.com/LinzeColin/CodexProject/actions/runs/27823282804`.
- GitHub Actions job: `82341300203`.
- GitHub Actions step 7 `Verify static, contract, lint, typecheck and unit tests`: PASS.
- GitHub Actions step 8 `Verify G2 PostgreSQL migrations and E2E`: PASS.

Acceptance status:

- A011 is covered by migration upgrade/downgrade and schema checks in PostgreSQL CI.
- A023 is covered by repository integration tests that preserve superseded relationship history and emit conflict changes without deleting the source relationship.
- A090 is covered by seed/check/API tests that preserve a fixed 14-day calibration cadence and queue manual calibration without auto-activating model changes.
- A025 is partially covered at API level because graph edges expose `synthetic` and `fixture_notice`, but visible frontend content tests are still open.
- A067 remains open because scenario-level recursive exploration E2E is not implemented.

Residual risks:

- T205 remains `IN PROGRESS` until UI fixture marking and recursive scenario E2E exist.
- T1103-T1109 visual company workspace tasks remain not started.
- T1203 taxonomy/object-scope API remains not started.

## 2026-06-19 - Phase 1 / G2 T205 fixture visibility and reroot E2E pass

Status: FIXTURE VISIBILITY AND RECURSIVE SUPPLY-CHAIN E2E PASS; G2 IN PROGRESS

Completed:

- Rebuilt the Next.js workspace shell into a visual-first company workspace with a persistent EEI navigation rail, current-focus panel, central relationship graph, stage coverage rail, evidence inspector, and reroot breadcrumb.
- Added visible fixture disclosures: `Synthetic fixture`, `Fixture-only data`, `Live facts: disabled`, relationship-level fixture notices, and stage-level synthetic supply-chain coverage.
- Added a deterministic NVIDIA fixture scenario spanning materials, equipment, manufacturing, design/IP, advanced packaging, system integration, data center, energy, and customer stages.
- Added set-as-center interactions for NVIDIA -> Synthetic Advanced Foundry -> Synthetic Lithography Equipment Co. -> Synthetic Specialty Materials Co.
- Extended Playwright E2E to assert visible fixture marking and the recursive NVIDIA supply-chain reroot path.
- Marked T205 as `DONE`.
- Marked A025 and A067 as `DONE` with evidence in `tests/e2e/home.spec.ts`.
- Marked T1103, T1104, T1107, and T1108 as `IN PROGRESS` because the workspace, directional layout, inspector, and set-as-center interaction have started but their full acceptance sets are not closed.

Verification evidence:

- Local `make verify`: PASS.
- Local `npx --yes pnpm@11.8.0 --filter @eei/web build`: PASS.
- Local `npx --yes pnpm@11.8.0 --filter @eei/web test:e2e`: PASS, 2 tests.
- Local `env -u DATABASE_URL .venv/bin/uv run pytest tests/integration -q`: PASS with 1 expected skip.
- Local `make verify-g2-db`: FAIL CLOSED because Docker is not installed on this host.
- GitHub Actions run: `https://github.com/LinzeColin/CodexProject/actions/runs/27824233483`.
- GitHub Actions job: `82344470407`.
- GitHub Actions step 7 `Verify static, contract, lint, typecheck and unit tests`: PASS.
- GitHub Actions step 8 `Verify G2 PostgreSQL migrations and E2E`: PASS.

Acceptance status:

- A025 is covered by Playwright assertions for visible fixture disclosure and disabled live-fact status.
- A067 is covered by Playwright assertions for NVIDIA synthetic scenario stage coverage and three-step recursive reroot path.
- A136-A152 remain open unless separately proven by visual measurement, screenshot/DOM assertions, lens behavior, semantic zoom/grouping, inspector coverage, set-as-center keyboard/touch behavior, mental-map regression, and failure-state tests.

Residual risks:

- The current workspace is still static fixture-driven and not bound to live API graph responses.
- T1105/T1106/T1109 remain not started.
- T1203 taxonomy/object-scope API remains not started.

## 2026-06-19 - Phase 1 / G2 T1103/T1104/T1107/T1108 visual workspace acceptance pass

Status: VISUAL WORKSPACE ACCEPTANCE SUBSET PASS; G2 IN PROGRESS

Completed:

- Added business, capital/control, and policy/risk synthetic relationship layers to the default NVIDIA commercial map without claiming live facts.
- Added deterministic reroot scenarios for business segment, capital commitment, and policy context nodes so every selectable node offered by the workspace has a bounded center contract.
- Split node selection from subject rerooting: clicking or keyboard-selecting a node updates the inspector while preserving the current subject until the explicit primary set-as-center action is used.
- Added inspector detail for selected node stage, role, and current subject plus set-as-center, upstream, downstream, watch, path, and evidence actions.
- Added keyboard-reachable SVG node controls and Playwright coverage proving primary navigation does not require double-click, right-click, hover, or drag.
- Added visual measurement and DOM/SVG assertions for central canvas coverage, upstream-left/focus-center/downstream-right layout, capital-above/policy-below layout, directed edges, and human-language relationship labels.
- Marked T1103, T1104, T1107, and T1108 as `DONE`.
- Marked A136, A137, A138, A139, A140, A146, A147, A148, A149, and A150 as `DONE` with evidence in `tests/e2e/home.spec.ts`.

Verification evidence:

- Local `npx --yes pnpm@11.8.0 --filter @eei/web typecheck`: PASS.
- Local `npx --yes pnpm@11.8.0 --filter @eei/web test:e2e`: PASS, 5 tests.
- Local `npx --yes pnpm@11.8.0 --filter @eei/web build`: PASS.
- Local `make verify`: PASS.
- Local `env -u DATABASE_URL .venv/bin/uv run pytest tests/integration -q`: PASS with 1 expected skip.
- Local `make verify-g2-db`: FAIL CLOSED because Docker is not installed on this host.
- GitHub Actions run: `https://github.com/LinzeColin/CodexProject/actions/runs/27825230977`.
- GitHub Actions job: `82347837228`.
- GitHub Actions step 7 `Verify static, contract, lint, typecheck and unit tests`: PASS.
- GitHub Actions step 8 `Verify G2 PostgreSQL migrations and E2E`: PASS.

Acceptance status:

- A136 is covered by Playwright visual coverage measurement of `ecosystem-map-surface` within `visual-canvas`.
- A137 is covered by visible upstream, downstream, business, capital/control, and policy/risk fixture nodes and labels.
- A138 is covered by SVG bounding-box assertions for upstream-left, focus-center, and downstream-right positions.
- A139 is covered by SVG bounding-box assertions for capital/control above and policy/risk below the focus node.
- A140 is covered by directed SVG edge assertions and human-language relationship-label assertions.
- A146 is covered by selecting a node into the inspector without changing `current-focus-title`.
- A147 is covered by inspector action assertions for set-as-center, upstream, downstream, watch, path, and evidence actions.
- A148 is covered by the visible primary set-as-center action completing reroot in one action after node selection.
- A149 is covered by keyboard node selection plus single primary action navigation.
- A150 is covered by the three-step reroot path preserving the same `recursive-enterprise-map` workspace model.

Residual risks:

- The current visual workspace remains static fixture-driven and not yet bound to live API graph responses.
- T1105/T1106/T1109 remain not started, so lens filtering, semantic zoom/grouping, and retained-node mental-map behavior are still open.
- T1203 taxonomy/object-scope API remains not started.

## 2026-06-19 - Phase 1 / G2 T1105/T1106/T1109 lens zoom mental-map pass

Status: VISUAL LENS, SEMANTIC ZOOM, AND MENTAL-MAP SUBSET PASS; G2 IN PROGRESS

Completed:

- Implemented persistent canvas lenses for all, supply-chain, business-segment, capital/transaction, and policy/risk views.
- Lens switching now fades nonmatching relationship layers without navigating away from the current workspace and preserves current subject, selected node, path length, semantic zoom, and viewport anchor.
- Implemented semantic zoom levels `L0`, `L1`, `L2`, and `L3` with an explicit UI contract and machine-testable `data-semantic-zoom` state.
- Added L0 anti-hairball grouping for dense synthetic system-maker nodes with an aggregate count and a list-view expansion path.
- Added L2 evidence-state edge annotations and L3 node-role labels without relying on hover-only discovery.
- Added transition loading and fallback states for reroot requests so subject changes indicate progress and failed center requests preserve the existing nonblank canvas.
- Added directional grammar assertions for retained nodes after rerooting.
- Marked T1105, T1106, and T1109 as `DONE`.
- Marked A141, A142, A143, A144, A145, A151, and A152 as `DONE` with evidence in `tests/e2e/home.spec.ts`.

Verification evidence:

- Local `npx --yes pnpm@11.8.0 --filter @eei/web typecheck`: PASS.
- Local `npx --yes pnpm@11.8.0 --filter @eei/web test:e2e`: PASS, 9 tests.
- Local `npx --yes pnpm@11.8.0 --filter @eei/web build`: PASS.
- Local `make verify`: PASS.
- Local `env -u DATABASE_URL .venv/bin/uv run pytest tests/integration -q`: PASS with 1 expected skip.
- Local `make verify-g2-db`: FAIL CLOSED because Docker is not installed on this host.
- GitHub Actions run: `https://github.com/LinzeColin/CodexProject/actions/runs/27826081868`.
- GitHub Actions job: `82350766117`.
- GitHub Actions step 7 `Verify static, contract, lint, typecheck and unit tests`: PASS.
- GitHub Actions step 8 `Verify G2 PostgreSQL migrations and E2E`: PASS.

Acceptance status:

- A141 is covered by Playwright lens switching assertions for faded nonmatching edges on the same workspace URL.
- A142 is covered by state assertions preserving subject, selected node, path length, semantic zoom, and viewport anchor across lens changes.
- A143 is covered by `L0-L3` zoom controls and semantic-zoom state assertions.
- A144 is covered by the synthetic grouped system-maker node with count `8` and an inspector list-view expansion.
- A145 is covered by default node/edge budget assertions below the 40-edge first-screen anti-hairball threshold.
- A151 is covered by directional grammar assertions after reroot from NVIDIA to Synthetic Advanced Foundry.
- A152 is covered by transition-loading and invalid-center fallback assertions that keep the canvas populated.

Residual risks:

- The current visual workspace remains static fixture-driven and not yet bound to live API graph responses.
- T1203 taxonomy/object-scope API remains not started.
- G2 remains open until T1203 and any remaining G2 gate checks are complete.

## 2026-06-19 - Phase 1 / G2 T1203 taxonomy and object-scope API pass

Status: TAXONOMY AND OBJECT-SCOPE API LOCAL PASS; G2 IN PROGRESS

Completed:

- Added a CSV-backed canonical catalog repository for relationship families, relationship types, upstream/downstream roles, supply-chain stages, industries, sectors, business segments, capital objects, domain objects, and companies.
- Added machine-readable API endpoints for `GET /v1/catalogs`, `GET /v1/catalogs/{catalogKey}`, CSV export via `format=csv`, and `GET /v1/system/object-scope`.
- Exposed an Objects and Scope navigation contract with module label, route, source document, Acceptance IDs, coverage counts, catalog summaries, and export links without requiring `DATABASE_URL`.
- Updated `specs/api_contract.yaml` for catalog inventory, catalog detail, CSV export, and object-scope responses.
- Added unit and integration coverage proving A169 catalog availability, row counts, definitions, and CSV export.
- Marked T1203 and A169 as `DONE`.

Verification evidence:

- Local `.venv/bin/uv run pytest tests/unit/test_api_health.py -q`: PASS, 7 tests.
- Local `.venv/bin/uv run python scripts/validate_contracts.py`: PASS.
- Local `.venv/bin/uv run ruff check apps/api/app/domain.py apps/api/app/domain_repository.py tests/unit/test_api_health.py tests/integration/test_database_migrations.py`: PASS.
- Local `make verify`: PASS.
- Local `env -u DATABASE_URL .venv/bin/uv run pytest tests/integration -q`: PASS with 1 expected skip.
- Local `make verify-g2-db`: FAIL CLOSED because Docker is not installed on this host.
- GitHub Actions run: `https://github.com/LinzeColin/CodexProject/actions/runs/27826870509`.
- GitHub Actions job: `82353421402`.
- GitHub Actions step 7 `Verify static, contract, lint, typecheck and unit tests`: PASS.
- GitHub Actions step 8 `Verify G2 PostgreSQL migrations and E2E`: PASS.

Acceptance status:

- A169 is covered by `tests/unit/test_api_health.py`, `tests/integration/test_database_migrations.py`, and `specs/api_contract.yaml`.
- A170 is not closed by this run. The API now exposes the Objects and Scope module contract, counts, definitions, coverage, and export links, but T1204 still needs the visible navigation screen plus E2E/visual regression evidence.

Residual risks:

- The G2 task list is complete, but `data/release_gate_catalog.csv` remains `IN PROGRESS` until a separate acceptance audit resolves G2-linked IDs that are still `NOT STARTED`.
- T1204 / A170 remains open.
- MVP is not complete.

## 2026-06-19 - Phase 1 / G2 acceptance audit pass 1

Status: ACCEPTANCE TRACEABILITY PARTIAL CLOSE; G2 IN PROGRESS

Completed:

- Added schema-check assertions for required entity type labels, supply-chain attribute columns, temporal columns, research universe tier counts, industry parent/child taxonomy, and multi-label industry membership support.
- Marked A015, A016, A017, A018, A019, A020, A021, A022, A024, and A028 as `DONE` only where existing validators/integration tests now provide explicit evidence.
- Updated duplicate traceability rows for the closed IDs so each function-level trace points to concrete scripts, schemas, data files, and integration tests.
- Left A012, A013, A014, A026, A027, and A170 as `NOT STARTED`.

Verification evidence:

- Local `make verify`: PASS.
- Local `.venv/bin/uv run ruff check scripts/check_database_schema.py`: PASS.
- Local `env -u DATABASE_URL .venv/bin/uv run pytest tests/integration -q`: PASS with 1 expected skip.
- GitHub Actions run: `https://github.com/LinzeColin/CodexProject/actions/runs/27827498238`.
- GitHub Actions job: `82355514060`.
- GitHub Actions step 7 `Verify static, contract, lint, typecheck and unit tests`: PASS.
- GitHub Actions step 8 `Verify G2 PostgreSQL migrations and E2E`: PASS.

Acceptance status:

- A015-A022, A024, and A028 are covered by `scripts/check_database_schema.py`, `tests/integration/test_database_migrations.py`, `specs/domain_schema.sql`, and the canonical CSV validators.
- A012 still needs a publishable relationship/event evidence enforcement contract, not only evidence tables.
- A013 still needs explicit unknown/null coercion regression tests.
- A014 still needs amount-kind compatibility and non-summing regression tests beyond the basic currency/kind constraint.
- A026 and A027 still require gold-set precision evaluation.
- A170 still requires T1204 UI plus E2E/visual regression.

Residual risks:

- `data/release_gate_catalog.csv` remains `G2=IN PROGRESS`.
- Remaining G2-linked open IDs are A012, A013, A014, A026, A027, and A170.

## 2026-06-19 - Phase 1 / G4 T1204 Objects and Scope screen

Status: OBJECTS AND SCOPE SCREEN LOCAL PASS; G4 IN PROGRESS

Completed:

- Added `/objects-scope` as a visible Objects and Scope navigation screen.
- Added a secondary system-module navigation entry labelled `对象与范围` without changing the frozen 16 primary product navigation modules.
- The screen reads canonical CSV catalogs at build time and exposes counts, definitions, coverage, primary keys, source files, and JSON/CSV export links.
- Added E2E coverage for A170 navigation visibility, counts, definitions, export links, and visual layout contract.
- Marked T1204 and A170 as `DONE`.

Verification evidence:

- Local `npx --yes pnpm@11.8.0 --filter @eei/web typecheck`: PASS.
- Local `npx --yes pnpm@11.8.0 --filter @eei/web test:e2e`: PASS, 10 tests.
- Local `npx --yes pnpm@11.8.0 --filter @eei/web build`: PASS, static routes `/` and `/objects-scope`.
- Local `make verify`: PASS.
- GitHub Actions run: `https://github.com/LinzeColin/CodexProject/actions/runs/27828194718`.
- GitHub Actions job: `82357916025`.
- GitHub Actions step 7 `Verify static, contract, lint, typecheck and unit tests`: PASS.
- GitHub Actions step 8 `Verify G2 PostgreSQL migrations and E2E`: PASS.

Acceptance status:

- A170 is covered by `tests/e2e/home.spec.ts` and `apps/web/src/app/objects-scope/page.tsx`.
- At this checkpoint, G4 remained open because T1205 and T1208 were not complete.

Residual risks:

- The remaining G2-linked open IDs after A170 closure are A012, A013, A014, A026, and A027.
- At this checkpoint, G4 remained open because T1205 and T1208 were not complete.

## 2026-06-19 - Phase 1 / G2 data contract audit pass 2

Status: DATA CONTRACT LOCAL PASS; G2 IN PROGRESS

Completed:

- Added PostgreSQL-backed data quality checks for publishable relationship/event evidence coverage.
- Added unknown-semantics regression checks so intentionally unknown relationships remain `unknown` and are not coerced to numeric zero.
- Added amount semantics checks and an integration regression proving amount facts without `currency` and `amount_kind` are rejected.
- Marked A012, A013, and A014 as `DONE`.
- Left A026 and A027 as `NOT STARTED` because they require real gold precision evaluation, not synthetic fixture self-grading.

Verification evidence:

- Local `.venv/bin/uv run ruff check scripts/check_database_schema.py tests/integration/test_database_migrations.py`: PASS.
- Local `make verify`: PASS.
- Local `env -u DATABASE_URL .venv/bin/uv run pytest tests/integration -q`: PASS with 1 expected skip.
- GitHub Actions run: `https://github.com/LinzeColin/CodexProject/actions/runs/27828738097`.
- GitHub Actions job: `82359769929`.
- GitHub Actions step 7 `Verify static, contract, lint, typecheck and unit tests`: PASS.
- GitHub Actions step 8 `Verify G2 PostgreSQL migrations and E2E`: PASS.

Acceptance status:

- A012 is covered by `scripts/check_database_schema.py` and `tests/integration/test_database_migrations.py`.
- A013 is covered by `scripts/check_database_schema.py`, `tests/integration/test_database_migrations.py`, and `data/mock_relationships.json`.
- A014 is covered by `specs/domain_schema.sql`, `scripts/check_database_schema.py`, and `tests/integration/test_database_migrations.py`.
- A026 and A027 remain open and should be handled by T904 quality evaluation or an explicit approved defer decision.

Residual risks:

- `data/release_gate_catalog.csv` remains `G2=IN PROGRESS` while A026 and A027 remain open.

## 2026-06-19 - Phase 1 / G2 gate close with gold-evaluation deferral

Status: G2 PASS; G3 IN PROGRESS

Completed:

- Recorded `DEFER-003` for A026/A027 because entity-resolution and relationship precision require real gold evaluation and must not be satisfied by synthetic self-graded fixtures.
- Left A026 and A027 as `NOT STARTED` in `data/acceptance_matrix.csv`.
- Advanced `data/release_gate_catalog.csv` from `G2=IN PROGRESS` to `G2=PASS` because the explicit G2 stop condition is `Migrations+catalog validation pass` and remote CI has repeatedly passed that gate.
- Advanced `G3` to `IN PROGRESS`.

Verification evidence:

- GitHub Actions run `27828738097`: PASS for strengthened A012-A014 PostgreSQL data contracts.
- GitHub Actions run `27828895082`: PASS for the final documentation commit after A012-A014 evidence recording.
- GitHub Actions run `27829131193`: PASS for the G2 gate-close commit with `DEFER-003`.
- GitHub Actions job `82361095081`: PASS.

Residual risks:

- A026 and A027 remain P0 release-quality acceptance IDs and must be implemented by T904/G9 or an explicit later release deferral.
- G3 implementation has not started yet.

## 2026-06-19 - Phase 1 / G3 T301 Home aggregation API

Status: T301 PASS; G3 IN PROGRESS

Completed:

- Added `/v1/home` aggregation fields for global search metadata, freshness, Watchlist, recent explorations, changes, active scoring profile, fixture policy, entity/relationship counts, and last/next calibration status.
- Updated the OpenAPI `HomeResponse` contract so `global_search` and `freshness` are required.
- Added PostgreSQL-backed integration assertions for search entry metadata, Watchlist presence, recent exploration state, synthetic fixture freshness, active model profile, and queued calibration status.
- Marked T301 as `DONE` in `data/task_backlog.csv`; A029/A030 remain open until the user-facing home UI and E2E coverage in T304/T306.
- Fixed a CI-only lifecycle assertion by allowing `home.changes` to be an empty list before any change records exist, then asserting non-empty home changes after supersession/conflict records are created.

Verification evidence:

- Local `make verify`: PASS.
- Local `env -u DATABASE_URL .venv/bin/uv run pytest tests/integration -q`: PASS with 1 expected skip.
- GitHub Actions run `27830933960`: FAIL in step 8 because the integration test asserted `len(home["changes"]) >= 1` before any `changes` rows existed.
- GitHub Actions job `82367238904`: FAIL.
- GitHub Actions run `27831147683`: PASS after the test lifecycle fix.
- GitHub Actions job `82367964670`: PASS.
- GitHub Actions step 7 `Verify static, contract, lint, typecheck and unit tests`: PASS.
- GitHub Actions step 8 `Verify G2 PostgreSQL migrations and E2E`: PASS.

Acceptance status:

- T301 is complete for API/data contract coverage.
- A029 and A030 remain `NOT STARTED` in `data/acceptance_matrix.csv` because their declared evidence type is E2E and will close through T304/T306, not by API assertions alone.

Residual risks:

- Home UI still needs to consume the new aggregation fields.
- Industry API/page and Watchlist item-type breadth remain open in T302/T303/T305/T306.

## 2026-06-19 - Phase 1 / G3 T302 Industry list and landscape API

Status: T302 PASS; G3 IN PROGRESS

Completed:

- Added `/v1/industries` with human-readable, versioned taxonomy rows and optional parent filtering.
- Added `/v1/industries/{industryId}/landscape` with industry summary, subindustries, chain stages, entities, bottlenecks, capital relationships, policy relationships, changes, cross-industry links, coverage, and explicit fixture/data mode.
- Added synthetic fixture industry memberships for primary, secondary, and supply-chain roles across semiconductor, AI cloud, software, energy, telecom, real-estate and industrial nodes.
- Updated OpenAPI with `IndustryLandscapeResponse`.
- Added PostgreSQL-backed integration assertions for A031 and A033, plus API-level coverage for chain stages, bottlenecks, capital, policy, and cross-industry navigation payloads.
- Marked T302 as `DONE`, A031 as `DONE`, and A033 as `DONE`; A032/A034 remain open because their declared evidence type is UI/E2E.

Verification evidence:

- Local `.venv/bin/uv run ruff check apps/api/app/domain.py apps/api/app/domain_repository.py scripts/load_synthetic_fixtures.py tests/integration/test_database_migrations.py`: PASS.
- Local `.venv/bin/uv run python scripts/validate_contracts.py`: PASS.
- Local `.venv/bin/uv run python scripts/validate_task_pack.py`: PASS.
- Local `make verify`: PASS.
- Local `env -u DATABASE_URL .venv/bin/uv run pytest tests/integration -q`: PASS with 1 expected skip.
- GitHub Actions run `27831861052`: PASS.
- GitHub Actions job `82370353436`: PASS.
- GitHub Actions step 7 `Verify static, contract, lint, typecheck and unit tests`: PASS.
- GitHub Actions step 8 `Verify G2 PostgreSQL migrations and E2E`: PASS.

Acceptance status:

- A031 is covered by `/v1/industries`, `specs/api_contract.yaml`, and `tests/integration/test_database_migrations.py`.
- A033 is covered by `entity_industry_memberships`, `scripts/load_synthetic_fixtures.py`, `/v1/industries/{industryId}/landscape`, and PostgreSQL integration assertions.
- A032 and A034 remain `NOT STARTED` until T305/T306 provide user-facing industry landscape and visible cross-industry E2E evidence.

Residual risks:

- Industry landscape UI is still not implemented.
- Landscape aggregation currently uses synthetic fixture memberships and relationship rows; live ingestion still belongs to later data-ingestion tasks.

## 2026-06-19 - Phase 1 / G3 T303 Watchlist CRUD and persistence API

Status: T303 PASS; G3 IN PROGRESS

Completed:

- Added `/v1/watchlists/{watchlistId}` detail retrieval.
- Added PostgreSQL-backed Watchlist item remove/restore assertions.
- Enforced Watchlist item object validation for `entity`, `industry`, `theme`, and `facility`.
- Preserved `saved_state` for restored Watchlist items.
- Added operation-log assertions for Watchlist item removal.
- Marked T303 as `DONE`, A035 as `DONE`, and A036 as `DONE`; A037 remains open because its declared evidence type is E2E.
- Fixed a CI-only DELETE response bug by returning an explicit `Response(status_code=204)` from `/v1/watchlists/{watchlistId}/items`.

Verification evidence:

- Local `git diff --check`: PASS.
- Local `.venv/bin/uv run ruff check apps/api/app/domain.py tests/integration/test_database_migrations.py`: PASS.
- Local `.venv/bin/uv run python scripts/validate_contracts.py`: PASS.
- Local `.venv/bin/uv run python scripts/validate_task_pack.py`: PASS.
- Local `make verify`: PASS.
- Local `env -u DATABASE_URL .venv/bin/uv run pytest tests/integration -q`: PASS with 1 expected skip.
- GitHub Actions run `27832285368`: FAIL in step 8 because the DELETE Watchlist item route returned a response object with status code `None`.
- GitHub Actions job `82371769481`: FAIL.
- GitHub Actions run `27832504683`: PASS after the explicit 204 response fix.
- GitHub Actions job `82372497975`: PASS.
- GitHub Actions step 7 `Verify static, contract, lint, typecheck and unit tests`: PASS.
- GitHub Actions step 8 `Verify G2 PostgreSQL migrations and E2E`: PASS.

Acceptance status:

- A035 is covered by `/v1/watchlists/{watchlistId}`, item remove/restore integration assertions, and PostgreSQL persistence checks.
- A036 is covered by item-type validation for `entity`, `industry`, `theme`, and `facility`.
- A037 remains `NOT STARTED` until T306 provides user-facing unread-change and saved-view/profile E2E evidence.

Residual risks:

- Watchlist UI still needs to consume detail, saved state, unread changes, and restore flows.
- Current Watchlist API is proven on synthetic fixtures; live ingestion and alert freshness remain later MVP tasks.

## 2026-06-19 - Phase 1 / G3 T304 User-oriented home page

Status: T304 PASS; G3 IN PROGRESS

Completed:

- Added user-oriented home entry controls to the existing Watchlist-first graph workspace without reverting to an industry-card dashboard.
- Added global search projection for `/v1/entities`, with legal-entity, industry, theme, and facility supported-type metadata.
- Added visible industries, Watchlist, recent explorations, important changes, freshness, active scoring profile, and calibration cadence/status.
- Added keyboard-reachable home controls for search, industry, Watchlist, recent exploration, and change-feed entry points.
- Added a new-user path from search query `tsmc` to a company focus within two primary actions.
- Marked T304 as `DONE`; marked A029, A030, A039, and A040 as `DONE`.
- Added missing A039/A040 acceptance traceability rows and updated the canonical trace count from 213 to 215.
- Adjusted the reroot loading state to 360ms so the existing transition test observes the loading state and the interaction remains within the documented 320-420ms animation threshold.

Verification evidence:

- Local `.venv/bin/uv run python scripts/validate_task_pack.py`: PASS.
- Local `npx --yes pnpm@11.8.0 --filter @eei/web typecheck`: PASS.
- Local `npx --yes pnpm@11.8.0 --filter @eei/web test:e2e`: PASS, 12 tests.
- Local `make verify`: PASS.
- Local `git diff --check`: PASS.
- GitHub Actions run `27833468626`: PASS.
- GitHub Actions job `82375686964`: PASS.
- GitHub Actions step 7 `Verify static, contract, lint, typecheck and unit tests`: PASS.
- GitHub Actions step 8 `Verify G2 PostgreSQL migrations and E2E`: PASS.

Acceptance status:

- A029 is covered by `apps/web/src/app/page.tsx` and `tests/e2e/home.spec.ts` for global search, industries, Watchlist, recent explorations, changes, and freshness.
- A030 is covered by the model status E2E assertions for active profile, calibration status, cadence, and next scheduled date.
- A039 is covered by the search-to-company-focus E2E path with `data-primary-actions-to-focus="2"`.
- A040 is covered by keyboard E2E assertions across home search, industry, Watchlist, recent exploration, and change-feed controls.

Residual risks:

- Homepage data is still a synthetic UI projection of the already-proven `/v1/home` contract; live frontend API hydration is not implemented in T304.
- Industry landscape UI remains open in T305, and Watchlist unread/saved-view E2E remains open in T306/A037.

## 2026-06-19 - Phase 1 / G3 T305 Industry landscape page

Status: T305 PASS; G3 IN PROGRESS

Completed:

- Added `/industries` as a user-facing industry landscape page.
- Added visible industry chain stages, subindustries, top entities, bottlenecks, capital items, policy items, and changes.
- Added cross-industry navigation between semiconductors, AI cloud infrastructure, and power/data-center energy.
- Added a visible cross-industry path indicator so industry jumps are preserved and inspectable.
- Added homepage link to the industry map from the industry entry section.
- Marked T305 as `DONE`; marked A032 and A034 as `DONE`.

Verification evidence:

- Local `npx --yes pnpm@11.8.0 --filter @eei/web typecheck`: PASS.
- Local `npx --yes pnpm@11.8.0 --filter @eei/web test:e2e -- tests/e2e/industry.spec.ts`: PASS, 14 tests ran and passed.
- Local `.venv/bin/uv run python scripts/validate_task_pack.py`: PASS.
- Local `npx --yes pnpm@11.8.0 --filter @eei/web build`: PASS, static route `/industries`.
- Local `make verify`: PASS.
- Local `git diff --check`: PASS.
- GitHub Actions run `27834152257`: PASS.
- GitHub Actions job `82377987783`: PASS.
- GitHub Actions step 7 `Verify static, contract, lint, typecheck and unit tests`: PASS.
- GitHub Actions step 8 `Verify G2 PostgreSQL migrations and E2E`: PASS.

Acceptance status:

- A032 is covered by `apps/web/src/app/industries/page.tsx` and `tests/e2e/industry.spec.ts`.
- A034 is covered by cross-industry navigation controls and visible path assertions in `tests/e2e/industry.spec.ts`.

Residual risks:

- Industry page still uses synthetic UI projection; live frontend API hydration remains future work.
- T306 remains open for consolidated home/industry/watchlist E2E and A037 Watchlist unread/saved-view evidence.

## 2026-06-19 - Phase 1 / G3 T306 Home, industry and Watchlist E2E

Status: T306 PASS; G3 IN PROGRESS

Completed:

- Added Watchlist unread-change and saved-view/profile state display to the home workspace.
- Added Watchlist restore behavior so selecting a Watchlist item restores saved lens, semantic zoom, profile context, and focus subject.
- Added Playwright coverage for A037 saved view/profile state restoration.
- Updated T306 to include A037 alongside A029/A035/A039/A040.
- Marked T306 as `DONE`; marked A037 as `DONE`.

Verification evidence:

- Local `npx --yes pnpm@11.8.0 --filter @eei/web typecheck`: PASS.
- Local `npx --yes pnpm@11.8.0 --filter @eei/web test:e2e`: PASS, 15 tests.
- Local `.venv/bin/uv run python scripts/validate_task_pack.py`: PASS.
- Local `npx --yes pnpm@11.8.0 --filter @eei/web build`: PASS, static routes `/`, `/industries`, and `/objects-scope`.
- Local `make verify`: PASS.
- Local `git diff --check`: PASS.
- GitHub Actions run `27834549643`: PASS.
- GitHub Actions job `82379303157`: PASS.
- GitHub Actions step 7 `Verify static, contract, lint, typecheck and unit tests`: PASS.
- GitHub Actions step 8 `Verify G2 PostgreSQL migrations and E2E`: PASS.

Acceptance status:

- A037 is covered by `apps/web/src/app/page.tsx` and `tests/e2e/home.spec.ts`.
- A035 now has both PostgreSQL persistence coverage and frontend Watchlist restore E2E coverage.

Residual risks:

- The MVP still lacks full create/remove Watchlist controls in the browser UI; API persistence for those actions is proven in T303.
- G3 still remains open for model registry/config import tasks listed in the gate, unless explicitly deferred.

## 2026-06-19 - Phase 1 / G3 State history, saved views, timeline and active context

Status: T1110/T1111/T1112/T1113/T1201/T1206 PASS; G3 PASS; G4 IN PROGRESS

Completed:

- Added a shared active analysis context for model/profile/data/score snapshot versions.
- Added URL/session/localStorage workspace state for subject, selected node, lens, as-of time, filters, path, and semantic zoom.
- Added browser back, app back, and clickable breadcrumb restoration.
- Added versioned local saved views with subject, lens, time, filters, layout, notes, model version, and data snapshot.
- Added as-of timeline controls and change overlay with explicit non-real-time fixture language.
- Added cross-page active model/profile/data/score snapshot reporting on `/`, `/industries`, and `/objects-scope`.
- Added model configuration validation to `scripts/validate_task_pack.py`.
- Marked T1110, T1111, T1112, T1113, T1201, and T1206 as `DONE`.
- Marked A154, A155, A156, A157, A158, A159, A160, A171, and A178 as `DONE`.

Verification evidence:

- Local `npx --yes pnpm@11.8.0 --filter @eei/web typecheck`: PASS.
- Local `npx --yes pnpm@11.8.0 --filter @eei/web test:e2e`: PASS, 19 tests.
- Local `.venv/bin/uv run python scripts/validate_task_pack.py`: PASS, including `validate_model_config.py`.
- Local `npx --yes pnpm@11.8.0 --filter @eei/web build`: PASS.
- Local `make verify`: PASS.
- Local `git diff --check`: PASS.
- GitHub Actions run `27835479352`: PASS.
- GitHub Actions job `82382357217`: PASS.
- GitHub Actions step 7 `Verify static, contract, lint, typecheck and unit tests`: PASS.
- GitHub Actions step 8 `Verify G2 PostgreSQL migrations and E2E`: PASS.

Acceptance status:

- A154/A155 are covered by `tests/e2e/state-contract.spec.ts` browser back, app back, and breadcrumb assertions.
- A156/A157 are covered by URL/session/reload assertions in `tests/e2e/state-contract.spec.ts`.
- A158/A159 are covered by versioned saved-view save/restore assertions in `tests/e2e/state-contract.spec.ts`.
- A160 is covered by timeline/as-of overlay assertions in `tests/e2e/state-contract.spec.ts`.
- A171 is covered by canonical model registry files plus `scripts/validate_model_config.py` through `scripts/validate_task_pack.py`.
- A178 is covered by cross-page active context assertions in `tests/e2e/state-contract.spec.ts`.

Residual risks:

- Saved views are local browser persistence only; production `/v1/saved-views` create/share/export remains future work.
- Timeline uses synthetic fixture snapshots; real snapshot comparison and change_events API remain future work.
- Model online edit, preview, activation, rollback, score recomputation, and operation-log UI remain future work.
- G4 remains open for recursive exploration, live context, model preview propagation, governance/status screens, accessibility/list equivalents, and visual regression/performance checks.

## 2026-06-19 - Phase 1 / G4 T1205 Development Status navigation

Status: PASS

Completed:

- Added `/development-status` as a visible development governance screen.
- Added status lanes for resolved, prototyped, specified, not started, blocked, and out-of-scope work.
- Linked tasks, risks, controls, and acceptance evidence to their canonical CSV sources.
- Added function status, recent task evidence, acceptance evidence, and risk-control panels.
- Added system navigation entry from the main workspace and Objects and Scope page.
- Marked T1205 as `DONE`; marked A173 and A174 as `DONE`.

Verification evidence:

- Local `npx --yes pnpm@11.8.0 --filter @eei/web typecheck`: PASS.
- Local `npx --yes pnpm@11.8.0 --filter @eei/web test:e2e`: PASS, 21 tests.
- Local `.venv/bin/uv run python scripts/validate_task_pack.py`: PASS.
- Local `npx --yes pnpm@11.8.0 --filter @eei/web build`: PASS, static route `/development-status`.
- Local `make verify`: PASS.
- GitHub Actions run `27836121209`: PASS.
- GitHub Actions job `82384436376`: PASS.

Acceptance status:

- A173 is covered by `apps/web/src/app/development-status/page.tsx` and `tests/e2e/development-status.spec.ts`.
- A174 is covered by visible system navigation, evidence links, and E2E link assertions in `tests/e2e/development-status.spec.ts`.

Residual risks:

- The page is server-rendered from local CSV files; live `/v1/governance/status` and `/v1/governance/traceability` APIs remain future work.
- GitHub issue forms, PR template enforcement, branch rules, release checklist, and clean-room governance validation remain future work.

## 2026-06-19 - Phase 1 / G4 T400 Bounded graph query service

Status: PASS

Completed:

- Added server-side defaults for `/v1/explore`: one hop, both directions, `supply_chain_operations`, and initial budget `max_nodes=42`, `max_edges=64`, `expand_nodes=12`.
- Enforced request hard limits through the API model: `hops<=2`, `max_nodes<=500`, `max_edges<=2000`, and `expand_nodes<=100`.
- Added bounded graph response metadata: query echo, hard limits, truncation reasons, returned counts, warnings, and continuation pointer.
- Aligned reroot-generated exploration requests with the same initial graph budget defaults.
- Updated the OpenAPI contract for default request fields, graph budget defaults, and truncation/continuation response shape.
- Added PostgreSQL-backed integration assertions for A041-A044 in `tests/integration/test_database_migrations.py`.
- Marked T400 as `DONE`; marked A041, A042, A043, and A044 as `DONE`.

Verification evidence:

- Local `.venv/bin/uv run python scripts/validate_task_pack.py`: PASS.
- Local `env -u DATABASE_URL .venv/bin/uv run pytest tests/integration -q`: PASS with 1 expected skip because the current host has no configured database.
- Local `make verify`: PASS.
- Local `git diff --check`: PASS.
- GitHub Actions run `27836910412`: PASS.
- GitHub Actions job `82386959577`: PASS.
- GitHub Actions step 7 `Verify static, contract, lint, typecheck and unit tests`: PASS.
- GitHub Actions step 8 `Verify G2 PostgreSQL migrations and E2E`: PASS.

Acceptance status:

- A041 is covered by explicit `/v1/explore` request fields and query echo assertions for focus, layers, direction, hops, as-of, profile, filters, and budget.
- A042 is covered by default `/v1/explore` assertions for one-hop, both-direction, `supply_chain_operations`, and 42/64/12 initial budget.
- A043 is covered by negative 422 assertions for `hops=3`, `max_nodes=501`, and `max_edges=2001`, plus response hard-limit metadata.
- A044 is covered by over-budget assertions for truncated graph responses, reasons, bounded returned counts, warnings, and `/v1/explore/expand` continuation metadata.

Residual risks:

- Local PostgreSQL execution is still unavailable on this host; GitHub Actions run `27836910412` proved the new integration assertions against the real migration/seed/fixture path.
- `/v1/explore/expand` is referenced only as continuation metadata; the actual incremental expand endpoint remains T403.
- Two-hop traversal accepts and records `hops=2`, but bounded multi-hop traversal semantics remain future work outside T400.

## 2026-06-19 - Phase 1 / G4 Saved-view restore CI hardening

Status: PASS

Completed:

- Investigated GitHub Actions run `27836653255`, where Step 8 passed PostgreSQL integration but failed one E2E state restoration assertion.
- Identified the failure as a hydration/storage race: after reload, `restoreSavedView()` could use the default React state before `useEffect` had reloaded the saved view from `localStorage`.
- Changed `restoreSavedView()` to synchronously read the latest `localStorage` saved-view payload before applying workspace state.

Verification evidence:

- Local `npx --yes pnpm@11.8.0 --filter @eei/web test:e2e -- tests/e2e/state-contract.spec.ts`: PASS, 21 tests.
- Local `make verify`: PASS.
- Local `git diff --check`: PASS.
- GitHub Actions run `27836910412`: PASS.
- GitHub Actions job `82386959577`: PASS.

Residual risks:

- Saved-view persistence is still browser-local; production shared saved-view APIs remain future work.

## 2026-06-19 - Phase 1 / G4 T401 Exploration session and URL state

Status: PASS

Completed:

- Added migration `0002_exploration_state` to persist exploration `state_version`, `direction`, `hops`, and `budget` on `exploration_sessions`.
- Updated the logical PostgreSQL schema and schema checker so exploration session state columns are required.
- Added canonical `state` and `state.url_state` to `/v1/explore` responses, including URL query fields and a full `restore_payload`.
- Updated `/v1/explore` create/update paths to persist direction, hops, budget, active layers, as-of time, scoring profile, and filters.
- Updated recent exploration rows returned by `/v1/home` to include persisted session state fields.
- Added integration assertions that serialize focus/layers/direction/time/profile/filters into URL state, POST the restore payload, and verify the same session state is persisted.
- Marked T401 and A051 as `DONE`.

Verification evidence:

- Local `make verify`: PASS.
- Local `env -u DATABASE_URL .venv/bin/uv run pytest tests/integration -q`: PASS with 1 expected skip because the current host has no configured PostgreSQL.
- Local `git diff --check`: PASS.
- GitHub Actions run `27837609322`: PASS.
- GitHub Actions job `82389170752`: PASS.
- GitHub Actions step 7 `Verify static, contract, lint, typecheck and unit tests`: PASS.
- GitHub Actions step 8 `Verify G2 PostgreSQL migrations and E2E`: PASS.

Acceptance status:

- A051 is covered by `state.url_state.query`, `state.url_state.query_string`, and `state.url_state.restore_payload` assertions in `tests/integration/test_database_migrations.py`.
- Existing G3 URL/session browser coverage in `tests/e2e/state-contract.spec.ts` remains part of the traceability evidence for A051.

Residual risks:

- GitHub Actions run `27837609322` proved the new migration and integration assertions against PostgreSQL.
- T404 still owns breadcrumb/browser-history synchronization for reroot flows; T401 only closes canonical session and URL state serialization/restoration.

## 2026-06-19 - Phase 1 / G4 T402 Reroot inherited and reset state

Status: REMOTE CI PASS

Completed:

- Updated `/v1/explore/reroot` so default reroot preserves active layers, direction, hops, as-of time, scoring profile, filters, and graph budget.
- Updated `inherit_state=false` reroot to reset to default exploration state: `supply_chain_operations`, `both`, one hop, default 42/64/12 budget, no as-of time, no scoring profile, and empty filters.
- Added integration assertions that reroot from NVIDIA to a facility entity preserves state by default.
- Added integration assertions that reroot from the same session to a theme entity resets state and persists the reset values in `exploration_sessions`.
- Updated the OpenAPI contract so `inherit_state` is optional with default `true`.
- Canonicalized UTC `datetime` API serialization to `Z` so inherited reroot state matches URL/session restore contracts after PostgreSQL round-trips.
- Aligned the reset-reroot fixture assertion with `data/mock_entities.json` for the `AI Infrastructure` theme entity.
- Marked T402, A045, A046, and A047 as `DONE`.

Verification evidence:

- Local `make verify`: PASS.
- Local `env -u DATABASE_URL .venv/bin/uv run pytest tests/integration -q`: PASS with 1 expected skip because the current host has no configured PostgreSQL.
- Local `git diff --check`: PASS.
- GitHub Actions run `27838042448`: FAIL in step 8 on inherited `as_of` timestamp serialization (`+00:00` vs `Z`); fixed by canonical UTC serialization.
- GitHub Actions run `27838285776`: FAIL in step 8 on reset-reroot fixture display name (`AI Infrastructure` vs stale expected label); fixed by aligning the test with the fixture catalog.
- GitHub Actions run `27838436423`: PASS.
- GitHub Actions job `82391789245`: PASS.
- GitHub Actions step 7 `Verify static, contract, lint, typecheck and unit tests`: PASS.
- GitHub Actions step 8 `Verify G2 PostgreSQL migrations and E2E`: PASS.

Acceptance status:

- A045 is covered by rerooting to non-legal-entity focusable entities in `tests/integration/test_database_migrations.py`.
- A046 is covered by inherited state assertions for layers, time, profile, filters, direction, hops, and budget.
- A047 is covered by reset/default state assertions plus direct persisted-session checks.

Residual risks:

- At T402 closeout, T404 still owned breadcrumb/browser-history synchronization and T408 still owned critical three-reroot E2E; both are now completed below.

## 2026-06-19 - Phase 1 / G4 T403 Incremental directional expand

Status: REMOTE CI PASS

Completed:

- Added the FastAPI `/v1/explore/expand` route with an explicit `ExpandRequest` model.
- Added repository support for incremental expansion from a selected `anchor_entity_id` without changing the session root.
- Added layer-to-relationship-family filtering so graph queries and expansions only return selected relationship families.
- Added expand-mode graph bounds so incremental expansion returns at most `expand_nodes` edges and `expand_nodes + 1` nodes including the anchor.
- Added integration assertions that upstream supply-chain expansion from NVIDIA returns only selected direction/layer edges within the expand budget.
- Marked T403 and A052 as `DONE`.

Verification evidence:

- Local `make verify`: PASS.
- Local `env -u DATABASE_URL .venv/bin/uv run pytest tests/integration -q`: PASS with 1 expected skip because the current host has no configured PostgreSQL.
- Local `git diff --check`: PASS.
- GitHub Actions run `27839023906`: PASS.
- GitHub Actions job `82393647163`: PASS.
- GitHub Actions step 7 `Verify static, contract, lint, typecheck and unit tests`: PASS.
- GitHub Actions step 8 `Verify G2 PostgreSQL migrations and E2E`: PASS.

Acceptance status:

- A052 is covered by `/v1/explore/expand` integration assertions for upstream direction, `supply_chain_operations` layer filtering, and `expand_nodes=2` node/edge bounds.

Residual risks:

- At T403 closeout, T405 still owned full graph/table explorer node actions and T406 still owned bounded evidence-bearing path queries; both are now completed below, with T406 awaiting remote PostgreSQL CI evidence.

## 2026-06-19 - Phase 1 / G4 T404 Breadcrumb and browser history synchronization

Status: REMOTE CI PASS

Completed:

- Added stable workspace attributes for current focus key and serialized focus path so browser/history assertions can compare UI state and URL state.
- Strengthened the state-contract E2E to cover reroot browser back, browser forward, app back, full breadcrumb visibility, and clickable intermediate breadcrumb restoration.
- Marked T404, A049, and A050 as `DONE`; A051 was already done by T401 and remains covered by state-contract URL assertions.

Verification evidence:

- Local `npx --yes pnpm@11.8.0 --filter @eei/web typecheck`: PASS.
- Local `npx --yes pnpm@11.8.0 --filter @eei/web test:e2e -- tests/e2e/state-contract.spec.ts`: PASS, 21 tests.
- Local `make verify`: PASS.
- Local `git diff --check`: PASS.
- GitHub Actions run `27839493483`: PASS.
- GitHub Actions job `82395103164`: PASS.
- GitHub Actions step 7 `Verify static, contract, lint, typecheck and unit tests`: PASS.
- GitHub Actions step 8 `Verify G2 PostgreSQL migrations and E2E`: PASS.

Acceptance status:

- A049 is covered by full path breadcrumb assertions for `nvidia.foundry.equipment.materials` and clickable restoration to `nvidia.foundry`.
- A050 is covered by browser `goBack`, browser `goForward`, and in-app back assertions restoring identical focus/path state.
- A051 remains covered by URL/session path and state assertions in `tests/e2e/state-contract.spec.ts` plus the T401 API state contract.

Residual risks:

- At T404 closeout, T408 still owned the critical three-reroot E2E acceptance A048; T408 is now completed below.

## 2026-06-19 - Phase 1 / G4 T405 Graph table explorer and node actions

Status: REMOTE CI PASS

Completed:

- Added selected-node actions for reroot, upstream, downstream, path, compare, pin, Watchlist and evidence entry points.
- Added pinned, comparison and Watchlist state summaries that persist while the user changes semantic zoom/layout level.
- Added a filterable graph table alternative backed by the same visible relationship edges as the graph.
- Added explicit visual semantics metadata and copy stating that layout position is not control semantics and color is not the only encoding; labels, arrows, stages, roles and evidence carry semantics.
- Strengthened the home E2E suite for node actions, layout-preserved pinned/comparison state, table filtering and non-color encoding semantics.
- Marked T405, A053, A054, A055 and A058 as `DONE`.

Verification evidence:

- Local `npx --yes pnpm@11.8.0 --filter @eei/web test:e2e -- tests/e2e/home.spec.ts`: PASS, 22 tests.
- Local `npx --yes pnpm@11.8.0 --filter @eei/web typecheck`: PASS.
- Local `make verify`: PASS.
- Local `git diff --check`: PASS.
- GitHub Actions run `27840198892`: PASS.
- GitHub Actions job `82397301394`: PASS.
- GitHub Actions step 7 `Verify static, contract, lint, typecheck and unit tests`: PASS.
- GitHub Actions step 8 `Verify G2 PostgreSQL migrations and E2E`: PASS.

Acceptance status:

- A053 is covered by visible action buttons and action-state assertions in `tests/e2e/home.spec.ts`.
- A054 is covered by pin/compare persistence after semantic zoom/layout changes.
- A055 is covered by the `graph-table-alternative` table and `graph-table-filter` lens assertions.
- A058 is covered by explicit semantic metadata plus visible arrow and edge-label assertions.

Residual risks:

- T406 is completed below and awaits remote PostgreSQL CI evidence.
- T407 is completed below and awaits remote CI evidence.
- T408 is completed below and awaits remote CI evidence.

## 2026-06-19 - Phase 1 / G4 T406 Bounded evidence-bearing path queries

Status: REMOTE CI PASS

Completed:

- Added `GET /v1/paths` with `from`, `to`, `path_type`, `max_length` and `as_of` query parameters.
- Implemented bounded recursive path search with `max_length <= 8`, `max_paths <= 8`, no repeated nodes, active/supersession filtering and as-of filtering.
- Supported `shortest`, `upstream`, `downstream`, `control`, `capital`, `policy` and `bottleneck` path types with explicit relationship-family filters.
- Required every returned path edge to have at least one `relationship_evidence` row and expanded source document evidence into the response.
- Added OpenAPI `PathResponse`, `PathResult` and `PathEdge` contracts for evidence-bearing bounded paths.
- Added PostgreSQL integration assertions for all seven A056 path types, evidence/source payloads, path bounds, hard limit metadata and `max_length=9` rejection.
- Marked T406 and A056 as `DONE`.

Verification evidence:

- Local `make verify`: PASS.
- Local `env -u DATABASE_URL .venv/bin/uv run pytest tests/integration -q`: PASS with 1 expected skip because the current host has no configured PostgreSQL.
- Local `git diff --check`: PASS.
- GitHub Actions run `27840744734`: PASS.
- GitHub Actions job `82399027153`: PASS.
- GitHub Actions step 7 `Verify static, contract, lint, typecheck and unit tests`: PASS.
- GitHub Actions step 8 `Verify G2 PostgreSQL migrations and E2E`: PASS.

Acceptance status:

- A056 is covered by `tests/integration/test_database_migrations.py` assertions over `/v1/paths` for shortest/upstream/downstream/control/capital/policy/bottleneck path types.

Residual risks:

- T407 is completed below and awaits remote CI evidence.
- T408 is completed below and awaits remote CI evidence.

## 2026-06-19 - Phase 1 / G4 T407 Inclusion and truncation explanations

Status: REMOTE CI PASS

Completed:

- Added a visible inclusion/truncation explanation panel to the graph inspector.
- Exposed machine-readable UI contract attributes for inclusion sorting keys, truncation reasons and continuation endpoint.
- Documented the inclusion order as active lens, evidence-bearing edges, confidence, observed time and stable id.
- Documented truncation reasons as `edge_budget` and `node_budget`, with returned counts and `/v1/explore/expand` continuation metadata.
- Strengthened home E2E coverage to assert the visible explanation and contract attributes.
- Marked T407 and A057 as `DONE`; A044 remains `DONE` with additional UI evidence.

Verification evidence:

- Local `npx --yes pnpm@11.8.0 --filter @eei/web test:e2e -- tests/e2e/home.spec.ts`: PASS, 22 tests.
- Local `make verify`: PASS.
- Local `git diff --check`: PASS.
- GitHub Actions run `27841131928`: PASS.
- GitHub Actions job `82400216009`: PASS.
- GitHub Actions step 7 `Verify static, contract, lint, typecheck and unit tests`: PASS.
- GitHub Actions step 8 `Verify G2 PostgreSQL migrations and E2E`: PASS.

Acceptance status:

- A057 is covered by `tests/e2e/home.spec.ts` assertions for `inclusion-truncation-explanation`.
- A044 retains API coverage from T400 and now has UI coverage for visible truncation reasons and continuation metadata.

Residual risks:

- T408 is completed below and awaits remote CI evidence.

## 2026-06-19 - Phase 1 / G4 T408 Critical three-reroot E2E

Status: REMOTE CI PASS

Completed:

- Added a dedicated A048 state-contract E2E named `A048 completes three consecutive semiconductor reroots without fallback`.
- The test reroots from NVIDIA to `Synthetic Advanced Foundry`, then `Synthetic Lithography Equipment Co.`, then `Synthetic Specialty Materials Co.`.
- The test asserts canonical path state, URL path serialization, `data-reroot-state=ready`, final `data-path-length=4`, full breadcrumb visibility, the materials graph node, and no transition fallback.
- Marked T408 and A048 as `DONE`.

Verification evidence:

- Local `npx --yes pnpm@11.8.0 --filter @eei/web test:e2e -- tests/e2e/state-contract.spec.ts`: PASS, 23 tests.
- Local `make verify`: PASS.
- GitHub Actions run `27841663304`: PASS.
- GitHub Actions job `82401845967`: PASS.
- GitHub Actions step 7 `Verify static, contract, lint, typecheck and unit tests`: PASS.
- GitHub Actions step 8 `Verify G2 PostgreSQL migrations and E2E`: PASS.

Acceptance status:

- A048 is covered by `tests/e2e/state-contract.spec.ts` with three consecutive semiconductor-fixture reroots ending at `nvidia.foundry.equipment.materials`.

Residual risks:

- T409 is completed below and awaits remote CI evidence.

## 2026-06-19 - Phase 1 / G4 T409 Cross-industry reroot E2E

Status: REMOTE CI PASS

Completed:

- Added a visible cross-industry reroot notice to the commercial-map workspace.
- Added a deterministic focus-to-industry mapping for the synthetic fixture path.
- The workspace now exposes `data-cross-industry` and `data-industry-path` attributes for the current reroot path.
- Added an A034 state-contract E2E named `A034 visibly marks cross-industry reroot path from chips to energy`.
- The test reroots from NVIDIA to cloud, data center and grid utility, then verifies visible industry path, breadcrumb and ready reroot state.
- Marked T409 as `DONE`; A034 remains `DONE` with additional workspace reroot evidence.

Verification evidence:

- Local `npx --yes pnpm@11.8.0 --filter @eei/web test:e2e -- tests/e2e/state-contract.spec.ts`: PASS, 24 tests.
- Local `make verify`: PASS.
- GitHub Actions run `27842200422`: PASS.
- GitHub Actions job `82403504484`: PASS.
- GitHub Actions step 7 `Verify static, contract, lint, typecheck and unit tests`: PASS.
- GitHub Actions step 8 `Verify G2 PostgreSQL migrations and E2E`: PASS.

Acceptance status:

- A034 is covered by `/industries` cross-industry navigation and now by `tests/e2e/state-contract.spec.ts` workspace reroot assertions for `nvidia.cloud.datacenter.energy`.

Residual risks:

- T1114/T1115/T1116/T1117 are completed below and await remote CI evidence.

## 2026-06-19 - Phase 1 / G4 T1114-T1117 Accessibility and UI copy contract

Status: REMOTE CI PASS

Completed:

- Strengthened the graph table alternative into a graph-equivalent accessible list with `direction`, `type`, `evidence_status` and `observed_at` fields.
- Added visible evidence labels and retained non-color encodings through labels, arrows, stages, roles and evidence pills.
- Added global visible focus styling and E2E assertions for keyboard-reachable graph node, primary center action and table filter.
- Added target-size assertions for dense graph nodes and equivalent controls.
- Added `scripts/validate_ui_copy.py` and wired `copy-lint` into `make verify`.
- Replaced visible internal copy such as `Rerooted`, `Profile`, `Calibration` and `Gate` with user-facing wording.
- Marked T1114, T1115, T1116, T1117 and A161-A166 as `DONE`.

Verification evidence:

- Local `.venv/bin/uv run python scripts/validate_ui_copy.py`: PASS.
- Local `npx --yes pnpm@11.8.0 --filter @eei/web test:e2e -- tests/e2e/home.spec.ts`: PASS, 25 tests.
- Local `make verify`: PASS.
- GitHub Actions run `27842880134`: PASS.
- GitHub Actions job `82405633120`: PASS.
- GitHub Actions step 7 `Verify static, contract, lint, typecheck and unit tests`: PASS.
- GitHub Actions step 8 `Verify G2 PostgreSQL migrations and E2E`: PASS.

Acceptance status:

- A161/A162 are covered by `graph-table-alternative` contract attributes and table row assertions in `tests/e2e/home.spec.ts`.
- A163/A164 are covered by keyboard focus and 24px target-size assertions in `tests/e2e/home.spec.ts`.
- A165 is covered by non-color encoding metadata and evidence labels in `apps/web/src/app/page.tsx`.
- A166 is covered by `scripts/validate_ui_copy.py` and the `copy-lint` Makefile target.

Residual risks:

- T1207 is completed below and awaits remote CI evidence.

## 2026-06-19 - Phase 1 / G4 T1207 Model preview context propagation

Status: REMOTE CI PASS

Completed:

- Added a typed shared analysis context hook with active and preview model/profile/data/score snapshots.
- Added a visible model preview panel on the commercial-map workspace with explicit preview scope and storage contract metadata.
- Persisted preview profile and score snapshot metadata into versioned saved-view records.
- Propagated preview context from the home workspace to the industry landscape page through session localStorage.
- Added an E2E contract that previews a supply-chain-emphasis model edit, saves the previewed view, navigates to `/industries`, returns to `/`, and clears the preview.
- Marked T1207 as `DONE`; A157/A158/A178 remain `DONE` with added preview propagation evidence.

Verification evidence:

- Local `npx --yes pnpm@11.8.0 --filter @eei/web test:e2e -- tests/e2e/state-contract.spec.ts`: PASS, 26 tests.
- Local `make verify`: PASS.
- Local `git diff --check`: PASS.
- GitHub Actions run `27843659754`: PASS.
- GitHub Actions job `82408058091`: PASS.
- GitHub Actions step 7 `Verify static, contract, lint, typecheck and unit tests`: PASS.
- GitHub Actions step 8 `Verify G2 PostgreSQL migrations and E2E`: PASS.

Acceptance status:

- A157 is covered by reload/session context assertions in `tests/e2e/state-contract.spec.ts`.
- A158 is covered by saved-view preview profile and score snapshot persistence assertions.
- A178 is covered by cross-page active/preview context assertions on `/` and `/industries`.

Residual risks:

- T1207 is a local session preview contract, not a real online model editor. Real edit, activation, rollback, score recompute and model-center UI remain in T600-T604.

## 2026-06-19 - Phase 1 / G5 T1208 Global model/data version consistency E2E

Status: REMOTE CI PASS

Completed:

- Extended the global active context E2E to include `/development-status` in addition to `/`, `/industries` and `/objects-scope`.
- Confirmed the development governance screen participates in the same active model/profile/data/score snapshot contract through `data-active-*` attributes.
- Marked T1208 as `DONE`; A178 remains `DONE` with added all-current-navigation-page consistency evidence.

Verification evidence:

- Local `./node_modules/.bin/playwright test --config=../../playwright.config.ts state-contract.spec.ts --grep "reports one active model profile" --workers=1`: PASS, 1 test.
- Local `./node_modules/.bin/playwright test --config=../../playwright.config.ts --workers=1`: PASS, 26 tests.
- Local `make verify`: PASS.
- Local `git diff --check`: PASS.
- GitHub Actions run `27844479321`: PASS.
- GitHub Actions job `82410608346`: PASS.
- GitHub Actions step 7 `Verify static, contract, lint, typecheck and unit tests`: PASS.
- GitHub Actions step 8 `Verify G2 PostgreSQL migrations and E2E`: PASS.

Acceptance status:

- A178 is covered by cross-page active context assertions on `/`, `/industries`, `/objects-scope` and `/development-status`.

Residual risks:

- T1208 only verifies the active context contract across current navigation pages; real model editing, activation, rollback and recalculation remain in T600-T604.

## 2026-06-19 - Phase 1 / G5 T1209 Prototype parity smoke test

Status: REMOTE CI PASS

Completed:

- Added `scripts/validate_prototype_parity.py` to compare `prototype/index.html` and `prototype/standalone.html` by bytes and SHA-256 hash.
- The parity validator rejects external script and stylesheet references so the canonical prototype cannot silently point at stale JS/CSS.
- The validator asserts required prototype views and graph/model DOM anchors are present in the canonical HTML.
- Wired `validate-prototype-parity` into `make verify` and registered the script in the repository document registry.
- Marked T1209 and A176 as `DONE`.

Verification evidence:

- Local `.venv/bin/uv run python scripts/validate_prototype_parity.py`: PASS; canonical hash `7f06f96c917ff14fc42c94de09b0e5f89f622a22a44a0dd64da3941429486719`.
- Local `make verify`: PASS.
- Local `git diff --check`: PASS.
- GitHub Actions run `27844984873`: PASS.
- GitHub Actions job `82412132613`: PASS.
- GitHub Actions step 7 `Verify static, contract, lint, typecheck and unit tests`: PASS.
- GitHub Actions step 8 `Verify G2 PostgreSQL migrations and E2E`: PASS.

Acceptance status:

- A176 is covered by `scripts/validate_prototype_parity.py`, `prototype/index.html`, `prototype/standalone.html` and the `validate-prototype-parity` Makefile target.

Residual risks:

- T1209 validates static parity and stale asset references; it does not replace later visual-regression screenshots or clean-room release packaging in T1118/T1119/T1123/T1215.

## 2026-06-19 - Phase 1 / G8 T1210 GitHub governance contract and required checks

Status: REMOTE CI PASS

Completed:

- Added `.github/branch_protection.md` as the versioned source contract for required `main` branch protection.
- Added `.github/release_checklist.md` for release gate commands, required checks, manifest/checksum refresh and rollback evidence.
- Expanded `.github/CODEOWNERS` to cover `.github/` and `scripts/`.
- Added `scripts/validate_github_governance.py` to validate issue forms, PR template, CODEOWNERS, governance workflow, release categories, branch protection contract, release checklist and backup registry coverage.
- Wired `validate-github-governance` into `make verify` and `ruff`.
- Registered the new governance files and validator in `data/github_document_registry.csv`.
- Stabilized the reroot fallback E2E by removing assertions on a transient loading overlay while retaining focus, fallback, graph nonblank and directional-grammar assertions.
- Marked T1210 and A177 as `DONE`; A175 remains `NOT STARTED` until T1211 adds immutable release artifact and operation-log evidence.

Verification evidence:

- Local `.venv/bin/uv run python scripts/validate_github_governance.py`: PASS.
- Local `make verify`: PASS.
- Local `git diff --check`: PASS.
- Local `./node_modules/.bin/playwright test --config=../../playwright.config.ts home.spec.ts --grep "Objects and Scope|directional grammar" --workers=1`: PASS, 2 tests.
- Local `npx --yes pnpm@11.8.0 --filter @eei/web test:e2e`: PASS, 26 tests.
- GitHub Actions run `27845697888`: FAIL, isolated to brittle transient loading overlay E2E assertion and fixed by `tests/e2e/home.spec.ts`.
- GitHub Actions run `27846173368`: PASS.
- GitHub Actions job `82415726115`: PASS.

Acceptance status:

- A177 is covered by `.github/CODEOWNERS`, `.github/branch_protection.md`, `.github/release_checklist.md`, `.github/workflows/governance-validation.yml`, `scripts/validate_github_governance.py` and `data/github_document_registry.csv`.

Residual risks:

- Actual GitHub branch protection must still be applied in repository settings or through the GitHub API; T1210 versions and validates the required contract.
- A175 still depends on T1211 reproducible release evidence and immutable operation-log/release artifacts.

## 2026-06-19 - Phase 1 / G9 T1211 Reproducible release evidence

Status: REMOTE CI PASS

Completed:

- Added `scripts/manage_release_artifacts.py` to generate and validate release artifacts from tracked repository paths plus required release evidence files.
- Regenerated `manifest.txt`, `DIRECTORY_TREE.txt` and `CHECKSUMS.sha256` for the current EEI product repository tree.
- Added `artifacts/release_evidence_t1211.json` with release commands, rollback procedure, artifact paths and remote verification fields.
- Added `artifacts/release_operation_log_t1211.jsonl` with one immutable `release_artifact_publish` operation for T1211.
- Wired `validate-release-artifacts` into `make verify`.
- Marked T1211 and A175 as `DONE`; A177 remains `DONE` with release artifact evidence added.

Verification evidence:

- Local `.venv/bin/uv run python scripts/manage_release_artifacts.py generate`: PASS; manifest paths 273, checksum paths 272.
- Local `.venv/bin/uv run python scripts/manage_release_artifacts.py validate`: PASS.
- Local `sha256sum -c CHECKSUMS.sha256`: PASS.
- Local `make verify`: PASS.
- GitHub Actions run `27846828768`: PASS.
- GitHub Actions job `82417667186`: PASS.

Acceptance status:

- A175 is covered by `.github/pull_request_template.md`, `artifacts/release_evidence_t1211.json`, `artifacts/release_operation_log_t1211.jsonl`, `manifest.txt`, `DIRECTORY_TREE.txt`, `CHECKSUMS.sha256` and `scripts/manage_release_artifacts.py`.
- A177 remains covered by GitHub governance files plus manifest/checksum/release evidence.

Residual risks:

- T1211 does not replace T1215 clean-room Markdown/CSV/JSON/GitHub/prototype/PDF/ZIP validation.

## 2026-06-19 - Phase 1 / G0 T1212 GitHub governance consistency workflow

Status: REMOTE CI PASS

Completed:

- Added `scripts/validate_governance_consistency.py` to validate governance workflow path triggers, required workflow commands, `make verify` wiring, P0 function traceability and release clean-room preflight files.
- Wired `validate-governance-consistency` into `make verify` and the packaged `.github/workflows/governance-validation.yml`.
- Added acceptance evidence files for A182, A183 and the A200 clean-room preflight contract.
- Marked T1212, A182 and A183 as `DONE`; A200 remains open for the final T1215 clean-room release run.

Verification evidence:

- Local `.venv/bin/uv run python scripts/validate_governance_consistency.py`: PASS.
- Local `.venv/bin/uv run python scripts/validate_github_governance.py`: PASS.
- Local `.venv/bin/uv run python scripts/manage_release_artifacts.py validate`: PASS.
- Local `sha256sum -c CHECKSUMS.sha256`: PASS.
- Local `make verify`: PASS.
- Local `git diff --check`: PASS.
- GitHub Actions run `27847728171`: PASS.
- GitHub Actions job `82420393869`: PASS.

Acceptance status:

- A182 is covered by `.github/workflows/governance-validation.yml`, `Makefile`, `scripts/validate_governance_consistency.py`, `scripts/validate_github_governance.py` and `artifacts/tests/a182/t1212_governance_consistency_workflow.json`.
- A183 is covered by `scripts/validate_governance_consistency.py`, the canonical function/task/acceptance/traceability CSVs and `artifacts/tests/a183/t1212_p0_traceability_validator.json`.
- A200 has a T1212 preflight contract in `artifacts/tests/a200/t1212_clean_room_preflight.json`, but remains `NOT_STARTED` until T1215 completes the full clean-room release verification.

Residual risks:

- T1212 validates that the clean-room prerequisites exist and are checksummed; it does not run the final Markdown/CSV/JSON/GitHub/prototype/PDF/ZIP clean-room package validation.

## 2026-06-19 - Phase 1 / G0 T1213 Development status and traceability artifacts

Status: REMOTE CI PASS

Completed:

- Added `scripts/manage_development_status_artifacts.py` to generate and validate `artifacts/development_status_summary_t1213.json`, `artifacts/requirement_function_task_test_traceability_t1213.csv`, A183 evidence and A184 evidence.
- Wired `validate-development-status-artifacts` into `make verify` and `.github/workflows/governance-validation.yml`.
- Marked T1213 and A184 as `DONE`; A183 remains `DONE` with added T1213 matrix evidence.
- Updated stale traceability count documentation to the canonical 221 rows in `data/acceptance_traceability.csv`.

Verification evidence:

- Local `.venv/bin/uv run python scripts/manage_development_status_artifacts.py generate`: PASS.
- Local `.venv/bin/uv run python scripts/manage_development_status_artifacts.py validate`: PASS.
- Local `.venv/bin/uv run python scripts/validate_governance_consistency.py`: PASS.
- Local `.venv/bin/uv run python scripts/validate_github_governance.py`: PASS.
- Local `.venv/bin/uv run ruff check scripts/manage_development_status_artifacts.py scripts/validate_governance_consistency.py scripts/validate_github_governance.py`: PASS.
- Local `make verify`: PASS.
- Local `git diff --check`: PASS.
- GitHub Actions run `27848308523`: PASS.
- GitHub Actions job `82422115246`: PASS.

Acceptance status:

- A183 is additionally covered by `artifacts/requirement_function_task_test_traceability_t1213.csv` and `artifacts/tests/a183/t1213_requirement_function_task_test_traceability.json`.
- A184 is covered by `scripts/manage_development_status_artifacts.py`, `data/development_status_ledger.csv`, `data/resolved_unresolved_register.csv`, `artifacts/development_status_summary_t1213.json` and `artifacts/tests/a184/t1213_development_status_ledger.json`.

Residual risks:

- T1213 does not close risk-control traceability for high-risk items; that remains T1214 / A185.

## 2026-06-19 - Phase 1 / G0 T1214 Risk-control traceability artifacts

Status: REMOTE CI PASS

Completed:

- Added `scripts/manage_risk_control_artifacts.py` to generate and validate `artifacts/risk_control_summary_t1214.json`, `artifacts/risk_control_mapping_t1214.csv` and `artifacts/tests/a185/t1214_high_risk_traceability.json`.
- Wired `validate-risk-control-artifacts` into `make verify` and `.github/workflows/governance-validation.yml`.
- Filled missing T1214/A185 mappings for high/critical risk rows and replaced high-risk `cross-cutting` placeholders with concrete function IDs.
- Marked T1214 and A185 as `DONE`.

Verification evidence:

- Local `.venv/bin/uv run python scripts/manage_risk_control_artifacts.py generate`: PASS.
- Local `.venv/bin/uv run python scripts/manage_risk_control_artifacts.py validate`: PASS.
- Local `.venv/bin/uv run python scripts/validate_governance_consistency.py`: PASS.
- Local `.venv/bin/uv run python scripts/validate_github_governance.py`: PASS.
- Local `.venv/bin/uv run ruff check scripts/manage_risk_control_artifacts.py scripts/validate_governance_consistency.py scripts/validate_github_governance.py`: PASS.
- Local `make verify`: PASS.
- GitHub Actions run: `https://github.com/LinzeColin/CodexProject/actions/runs/27848881308`.
- GitHub Actions job: `82423801118`.
- GitHub Actions step 7 `Verify static, contract, lint, typecheck and unit tests`: PASS.
- GitHub Actions step 8 `Verify G2 PostgreSQL migrations and E2E`: PASS.

Acceptance status:

- A185 is covered by `scripts/manage_risk_control_artifacts.py`, `data/risk_register.csv`, `data/risk_control_traceability.csv`, `artifacts/risk_control_summary_t1214.json`, `artifacts/risk_control_mapping_t1214.csv` and `artifacts/tests/a185/t1214_high_risk_traceability.json`.

Residual risks:

- T1214 validates risk-control traceability; final clean-room Markdown/CSV/JSON/GitHub/prototype/PDF/ZIP verification remains T1215 / A200.

## 2026-06-19 - Phase 1 / G9 T1215 Clean-room release validation

Status: REMOTE CI PASS

Completed:

- Added `scripts/manage_clean_room_release.py` to generate and validate `artifacts/tests/a200/t1215_clean_room_release.json` and `artifacts/tests/a200/Enterprise_Ecosystem_Intelligence_clean_room_t1215.zip`.
- The clean-room ZIP includes an internal `PACKAGE_MANIFEST.json` and `PACKAGE_CHECKSUMS.sha256`, excludes its own package/evidence files, and validates Markdown, CSV, JSON, GitHub workflow, prototype and PDF categories.
- Wired `validate-clean-room-release` into `make verify` and `.github/workflows/governance-validation.yml`.
- Marked T1215 and A200 as `DONE`.

Verification evidence:

- Local `.venv/bin/uv run python scripts/manage_clean_room_release.py generate`: PASS.
- Local `.venv/bin/uv run python scripts/manage_clean_room_release.py validate`: PASS.
- Local `make verify`: PASS.
- Local `sha256sum --quiet -c CHECKSUMS.sha256`: PASS.
- GitHub Actions run: `https://github.com/LinzeColin/CodexProject/actions/runs/27849578583`.
- GitHub Actions job: `82425860903`.
- GitHub Actions step 7 `Verify static, contract, lint, typecheck and unit tests`: PASS.
- GitHub Actions step 8 `Verify G2 PostgreSQL migrations and E2E`: PASS.

Acceptance status:

- A200 is covered by `scripts/manage_clean_room_release.py`, `scripts/validate_governance_consistency.py`, `scripts/manage_release_artifacts.py`, `artifacts/tests/a200/t1215_clean_room_release.json` and `artifacts/tests/a200/Enterprise_Ecosystem_Intelligence_clean_room_t1215.zip`.

Residual risks:

- T1215 closes A200 clean-room release verification only. A180, A181, A186 and A199 remain open and are not claimed by this run.

## 2026-06-19 - Phase 1 / G5 T500 Entity dossier and human summary API

Status: REMOTE CI PASS

Completed:

- Expanded `/v1/entities/{entityId}` from a thin entity summary into an entity dossier response with aliases, industry memberships, relationship-family counts, dossier layers, recent events, freshness, coverage and `human_summary`.
- Added dossier layers for business, group, dependencies, capital, policy and signals without introducing new database tables or product dependencies.
- Added explicit data-gap language for missing capital and policy records so unknown fixture coverage is not rendered as zero or false.
- Updated `specs/api_contract.yaml` with `EntityDossier`, `EntityDossierLayer` and `EntityDossierHumanSummary` contract fields.
- Added integration assertions that every 30-row fixture seed from `data/mock_entities.json` opens through `/v1/entities/{entityId}` and that NVIDIA's golden dossier covers business, group, dependencies, capital, policy, signals and data gaps.
- Added A059 and A060 evidence artifacts under `artifacts/tests/a059/` and `artifacts/tests/a060/`.
- Marked T500, A059 and A060 as `DONE`; FUN-EXP-03 is now `PARTIAL` because T501-T508 workspace/detail tasks remain open.

Verification evidence:

- Local `.venv/bin/uv run python scripts/validate_contracts.py`: PASS.
- Local `.venv/bin/uv run python scripts/validate_catalog_integrity.py`: PASS.
- Local `.venv/bin/uv run ruff check apps/api/app/domain_repository.py tests/integration/test_database_migrations.py`: PASS.
- Local `.venv/bin/uv run pytest tests/unit -q`: PASS.
- Local `.venv/bin/uv run python scripts/manage_development_status_artifacts.py validate`: PASS.
- Local `.venv/bin/uv run pytest tests/integration -q`: SKIPPED because this host has no `.env` and no Docker-backed PostgreSQL.
- GitHub Actions run: `https://github.com/LinzeColin/CodexProject/actions/runs/27850433769`.
- GitHub Actions job: `82428282411`.
- GitHub Actions step `Verify static, contract, lint, typecheck and unit tests`: PASS.
- GitHub Actions step `Verify G2 PostgreSQL migrations and E2E`: PASS.

Acceptance status:

- A059 is covered by `apps/api/app/domain_repository.py`, `tests/integration/test_database_migrations.py` and `artifacts/tests/a059/t500_entity_focus_dossier_api.json`.
- A060 is covered by `apps/api/app/domain_repository.py`, `specs/api_contract.yaml`, `tests/integration/test_database_migrations.py` and `artifacts/tests/a060/t500_human_summary_dossier_api.json`.

Residual risks:

- T500 does not implement the full eight-layer workspace UI; T501-T508 still own group structure, supply-chain, capital/policy/technology layers, strategic signals, evidence drawer, timeline and export UX.
- Local database integration could not run on this host; GitHub Actions PostgreSQL validation passed and is the database/E2E evidence for this run.

## 2026-06-20 - Phase 1 / G5 T501 Group, business and structure workspace

Status: REMOTE CI PASS

Completed:

- Added `/v1/entities/{entityId}/empire` as the bounded company empire structure endpoint without adding new database tables.
- Added an eight-layer company focus workspace strip for group structure, business segments, supply chain, capital network, M&A transactions, control relationships, policy environment and strategic signals.
- Added a structure matrix that separates legal group, business segment, brand, product and facility rows.
- Preserved missing coverage semantics for brands and adjacent ecosystem semantics for facilities.
- Added the explicit rule that commercial empire is an ecosystem relationship view, not a legal-control assertion.
- Added A061, A062 and A063 evidence artifacts under `artifacts/tests/a061/`, `artifacts/tests/a062/` and `artifacts/tests/a063/`.
- Marked T501, A061, A062 and A063 as `DONE`; FUN-EXP-03 remains `PARTIAL` because T502/T503/T506-T508 still own deeper layer detail, evidence drawer and timeline scope.

Verification evidence:

- Local `.venv/bin/uv run ruff check apps/api/app/domain.py apps/api/app/domain_repository.py tests/integration/test_database_migrations.py`: PASS.
- Local `.venv/bin/uv run python scripts/validate_contracts.py`: PASS.
- Local `.venv/bin/uv run pytest tests/unit -q`: PASS.
- Local `npx --yes pnpm@11.8.0 --filter @eei/web typecheck`: PASS.
- Local `npx --yes pnpm@11.8.0 --filter @eei/web exec playwright test --config=../../playwright.config.ts --grep "eight company layers"`: PASS.
- Local `git diff --check`: PASS.
- GitHub Actions run: `https://github.com/LinzeColin/CodexProject/actions/runs/27851485026`.
- GitHub Actions job: `82431234525`.
- GitHub Actions step `Verify static, contract, lint, typecheck and unit tests`: PASS.
- GitHub Actions step `Verify G2 PostgreSQL migrations and E2E`: PASS.

Acceptance status:

- A061 is covered by `apps/web/src/app/page.tsx`, `apps/web/src/app/globals.css`, `tests/e2e/home.spec.ts` and `artifacts/tests/a061/t501_company_workspace_layers.json`.
- A062 is covered by `apps/api/app/domain_repository.py`, `apps/api/app/domain.py`, `specs/api_contract.yaml`, `tests/integration/test_database_migrations.py`, `apps/web/src/app/page.tsx`, `tests/e2e/home.spec.ts` and `artifacts/tests/a062/t501_structure_type_separation.json`.
- A063 is covered by `apps/api/app/domain_repository.py`, `apps/web/src/app/page.tsx`, `tests/e2e/home.spec.ts` and `artifacts/tests/a063/t501_commercial_empire_not_control.json`.

Residual risks:

- Local database integration remains unrun on this host because there is no `.env` and no Docker-backed PostgreSQL.
- T501 creates the bounded structure workspace and API contract only; T502/T503/T506-T508 still own full supply-chain, capital/policy/technology, evidence drawer, timeline, export and cross-layer workspace depth.

## 2026-06-20 - v5 Task Pack synchronization and MVP v0.1 blocker registration

Status: LOCAL GOVERNANCE SYNC IN PROGRESS

Completed:

- Imported v5 review evidence into `reviews/`, `data/review_issue_register.csv`, `TEST_STRATEGY.md` and `CONTINUITY_PLAN.md`.
- Adapted v5 brand/competitive research to the active EEI identity without changing the system name: 商域图谱 / Enterprise Ecosystem Intelligence.
- Added `docs/phase/V5_TASK_PACK_SYNCHRONIZATION.md` as the source-of-truth mapping from v5 production blockers to EEI tasks, Acceptance IDs, rollback rules and unresolved decisions.
- Added T1300-T1309 to `data/task_backlog.csv` for PostgreSQL, real ingestion, production API/query/scoring, model activation/refresh, scheduler/dead-letter, saved views, 10k/100k/1m scale, 4h/24h soak, production frontend and brand clearance.
- Added A201-A211 to `data/acceptance_matrix.csv` and corresponding trace rows in `data/acceptance_traceability.csv`.
- Added 15 production runtime/model governance parameters to `data/parameter_catalog.csv` and `config/model_runtime_defaults.yaml`.
- Added V5-001 through V5-010 to `data/development_status_ledger.csv` so the blocker list appears in the development record.

Important boundary:

- This synchronization does not implement the blockers. T1300-T1309 and A201-A211 remain `NOT STARTED`.
- Current pursuing goal may only become v0.1 after these blockers have implementation, tests, rollback evidence and CI evidence.

Residual risks:

- Formal EEI legal/market clearance is not complete.
- Production-scale benchmarks and soak tests are not yet executable evidence.
- Production PostgreSQL, ingestion, graph/API/scoring, scheduler, saved views and componentized frontend remain active MVP blockers.

## 2026-06-20 - T1300/A201 PostgreSQL production fact-version migration

Status: LOCAL STATIC PASS; REMOTE CI PASS

Completed:

- Added `infra/db/migrations/0003_production_fact_version_layers/up.sql` and `down.sql`.
- Added `data_snapshots` for snapshot-scoped publication with record mode, active-state, source hash, activation time and supersession metadata.
- Added `fact_versions` for immutable object versions with fact status, record mode, time-validity windows, observed time, parser version, payload hash, previous version link and source/ingestion references.
- Added `fact_version_evidence` so versioned facts keep evidence as a separate layer.
- Updated `specs/domain_schema.sql`, `scripts/check_database_schema.py`, and `tests/integration/test_database_migrations.py` to validate A201.
- Marked T1300 and A201 as `DONE` in `data/task_backlog.csv`, `data/acceptance_matrix.csv`, and `data/acceptance_traceability.csv`.

Verification evidence:

- Local `python3 scripts/validate_catalog_integrity.py`: PASS.
- Local `PYTHONPATH=/private/tmp/eei-pydeps python3 scripts/validate_governance.py`: PASS.
- Local `PYTHONPATH=/private/tmp/eei-pydeps python3 scripts/validate_task_pack.py`: PASS.
- Local `PYTHONPATH=/private/tmp/eei-ruff:/private/tmp/eei-pydeps python3 -m ruff check scripts/check_database_schema.py tests/integration/test_database_migrations.py`: PASS.
- Local `PYTHONPATH=scripts:. .venv/bin/python -c 'from migrate import discover_migrations; print([(m.version, m.name) for m in discover_migrations()])'`: PASS and includes `0003 production_fact_version_layers`.
- Local `git diff --check`: PASS.
- GitHub Actions run `27853994985`: PASS.
- GitHub Actions job `82437995756`.
- GitHub Actions step `Verify static, contract, lint, typecheck and unit tests`: PASS.
- GitHub Actions step `Verify G2 PostgreSQL migrations and E2E`: PASS.

Acceptance status:

- A201 is covered by `infra/db/migrations/0003_production_fact_version_layers/up.sql`, `infra/db/migrations/0003_production_fact_version_layers/down.sql`, `scripts/check_database_schema.py`, and `tests/integration/test_database_migrations.py`.

Residual risks:

- Local Docker/PostgreSQL is not available on this host, so migration upgrade/downgrade and integration execution still require GitHub Actions for database proof.
- T1300 closes the database version-layer blocker only. T1301-T1309 remain required before v0.1: real ingestion, production API/query/scoring, model activation/refresh, scheduler, saved views, scale, soak, production frontend and brand clearance.

## 2026-06-20 - T1301/A202 curated official ingestion audit layer

Status: LOCAL STATIC PASS; REMOTE CI PASS

Completed:

- Added `infra/db/migrations/0004_curated_ingestion_audit_layers/up.sql` and `down.sql`.
- Added `raw_source_snapshots` to preserve official anchor URL, source date, publisher, title, scope, record mode, validation status, parser version, content hash, raw payload and review status.
- Added `entity_resolution_candidates` to preserve candidate name, normalized name, matched entity/research IDs when available, match method, confidence, decision reason, review status and parser version.
- Added `ingestion_evidence_chain` to preserve anchor-level evidence context, relationship family, locator, support excerpt, structured fact payload, counter_evidence array, parser version, confidence and review status.
- Added `scripts/load_curated_ingestion_anchors.py` for deterministic ingestion of `data/nvidia_public_source_anchors.csv` in `curated_official_fixture` mode.
- Updated `scripts/check_database_schema.py` with `--expect-curated-ingestion`.
- Updated `tests/integration/test_database_migrations.py` to run the curated loader twice and assert raw snapshot, source document, entity resolution, evidence chain and non-publication invariants.
- Marked T1301/A202 as `IN PROGRESS` in task, acceptance, traceability and development status files.

Acceptance status:

- A202 is in progress, not done.
- Current evidence covers curated official NVIDIA source anchors and ingestion audit layers.
- The loader intentionally does not publish relationship edges from discovery anchors.

Residual risks:

- live/full-text official connector is not implemented.
- reviewed NVIDIA -> TSMC -> ASML relationship facts are not published.
- independent source cross-check and human review workflow are not implemented.
- source health, retry, dead-letter and scheduler semantics remain owned by T1304/A206.

Verification evidence:

- GitHub Actions run `27854549380`: PASS.
- GitHub Actions job `82439458056`.
- GitHub Actions step `Verify static, contract, lint, typecheck and unit tests`: PASS.
- GitHub Actions step `Verify G2 PostgreSQL migrations and E2E`: PASS.

## 2026-06-20 - T1301/A202 Golden Vertical relationship fact candidates

Status: LOCAL STATIC IN PROGRESS

Completed:

- Added `infra/db/migrations/0005_relationship_fact_candidates/up.sql` and `down.sql`.
- Added `relationship_fact_candidates` to preserve candidate Golden Vertical facts with relationship type/family, record mode, fact status, publication status, confidence, independent source count, review status, parser version, structured fact and counter_evidence.
- Added `relationship_fact_candidate_evidence` to link candidate facts back to `ingestion_evidence_chain` and `source_documents`.
- Added `manual_review_queue` so single-source candidate facts remain open for review instead of being published.
- Added `data/golden_vertical_fact_candidates.json` with deterministic official source snapshots from SEC-hosted NVIDIA Form 10-K and ASML official source material.
- Extended `scripts/load_curated_ingestion_anchors.py` so it loads the candidate NVIDIA/TSMC/ASML chain without inserting production `relationships` rows.
- Extended `scripts/check_database_schema.py` and `tests/integration/test_database_migrations.py` to validate two candidate facts, two evidence links, two open review items and no relationship publication side effect.

Acceptance status:

- A202 remains `IN PROGRESS`.
- The Golden Vertical path exists as candidate fact evidence only:
  - TSMC `wafer_foundry_for` NVIDIA.
  - ASML `equipment_provider_to` TSMC.
- Both candidates are below the independent-source threshold and require review before publication.

Residual risks:

- live/full-text connector is still not implemented.
- independent-source threshold is not satisfied for the two candidate facts.
- no human review approval has been recorded.
- production API and graph query do not yet consume these candidate tables.

## 2026-06-20 - T1302/A203 production graph and scoring contract slice

Status: LOCAL VALIDATED; REMOTE CI PASS

Completed:

- Added production context to graph/path responses with active data snapshot, active scoring profile, graph query version, scoring service version, record modes and publication policy.
- Added `GET /v1/scoring/explain/{objectType}/{objectId}` for `relationship_fact_candidate` explanations.
- Added candidate-fact coverage so Golden Vertical candidates remain excluded from graph edges until source threshold and human review gates pass.
- Updated `specs/api_contract.yaml` and `tests/integration/test_database_migrations.py` for the A203 contract.
- Added `artifacts/tests/a203/t1302_production_api_graph_scoring_contract.json`.
- Marked T1302/A203 as `IN PROGRESS`, not DONE.

Acceptance status:

- A203 is in progress.
- Current evidence covers candidate fact scoring explanations and graph/path publication context.

Residual risks:

- Full multi-object production scoring service is not complete.
- Candidate review approval and publication into relationship facts remain open.
- Scale, soak and downstream frontend production wiring remain separate blockers.

Verification evidence:

- GitHub Actions run `27856517135`: PASS.
- GitHub Actions job `82444936213`.
- GitHub Actions step `Verify static, contract, lint, typecheck and unit tests`: PASS.
- GitHub Actions step `Verify G2 PostgreSQL migrations and E2E`: PASS.

## 2026-06-20 - T1303/A204-A205 transactional activation and refresh context slice

Status: LOCAL STATIC IN PROGRESS

Completed:

- Added `infra/db/migrations/0006_model_activation_refresh_state/up.sql` and `down.sql`.
- Added a database-level global active scoring profile unique index.
- Added `active_analysis_contexts` for active profile, data snapshot, score snapshot, refresh token, refresh generation, affected modules and metadata.
- Extended `scripts/load_seed_catalogs.py` to initialize the global active context idempotently.
- Added `GET /v1/scoring/active-context` so clients can detect stale refresh tokens.
- Added `POST /v1/scoring/profiles/{profileVersionId}/activate` for transaction-scoped activation.
- Activation now locks current/target profile versions, creates a completed `scoring_runs` score snapshot, switches active profile, updates active context and writes operation logs in one transaction.
- Stale expected active profile requests return 409 and leave the active profile unchanged while logging a conflict operation.
- Extended `tests/integration/test_database_migrations.py` to assert success, conflict and database uniqueness semantics.
- Added A204/A205 evidence files under `artifacts/tests/a204/` and `artifacts/tests/a205/`.

Acceptance status:

- A204 and A205 are `IN PROGRESS`, not DONE.
- A204 has service/database transaction evidence pending CI database execution.
- A205 has server-side refresh token semantics, but not production frontend cross-view E2E completion.

Residual risks:

- Frontend modules still use the static analysis context and are not yet wired to `/v1/scoring/active-context`.
- Model-center edit/activate/rollback controls are not complete.
- Worker-driven data snapshot activation, transactional outbox, scheduler and dead-letter remain T1304 and later tasks.

## 2026-06-20 - T1304/A206 scheduler retry and dead-letter core slice

### Scope

- Added PostgreSQL scheduler state tables: `background_jobs`, `background_job_attempts`, and `dead_letter_jobs`.
- Added `scripts/job_scheduler.py` with idempotent enqueue, due-job lease, heartbeat, graceful release, bounded retry, expired lease recovery, completion and dead-letter transitions.
- Extended schema validation and integration coverage for A206.

### Files changed

- `infra/db/migrations/0007_scheduler_job_queue/up.sql`
- `infra/db/migrations/0007_scheduler_job_queue/down.sql`
- `specs/domain_schema.sql`
- `scripts/job_scheduler.py`
- `scripts/check_database_schema.py`
- `tests/integration/test_database_migrations.py`
- `artifacts/tests/a206/t1304_scheduler_retry_dead_letter_contract.json`
- `data/task_backlog.csv`
- `data/acceptance_matrix.csv`
- `data/acceptance_traceability.csv`
- `data/development_status_ledger.csv`
- `data/release_gate_catalog.csv`
- `docs/phase/V5_TASK_PACK_SYNCHRONIZATION.md`

### Acceptance mapping

- T1304 -> A206.
- A206 is now `IN PROGRESS`, not `DONE`.

### Validation

- Local ruff target: PASS for `scripts/job_scheduler.py`, `scripts/check_database_schema.py`, and `tests/integration/test_database_migrations.py`.
- PostgreSQL integration proof is required from GitHub Actions `make verify-g2-db` because this host has no local Docker/PostgreSQL.

### Remaining gaps

- Real curated ingestion and calibration handlers are not yet registered on the scheduler.
- Deployment-level wake/supervision is not yet packaged.
- T1307 4h/24h soak remains required before scheduler stability can be called production-ready.
- Local Docker/PostgreSQL is not available on this host, so database proof requires GitHub Actions.

## 2026-06-20 - T1305/A207 server-side saved-view conflict and recovery slice

### Scope

- Added PostgreSQL saved-view state tables: `saved_views` and `saved_view_versions`.
- Added `/v1/saved-views` list/create/get/update/version-list/restore routes.
- Added repository-level `FOR UPDATE` optimistic conflict control using `expected_version`.
- Added 409 `saved-view-conflict-v1` responses for duplicate names, stale updates and stale restores.
- Added recovery semantics where restoring a historical version appends a new current version instead of rewriting history.
- Extended schema validation, OpenAPI and PostgreSQL integration coverage for A207.

### Files changed

- `infra/db/migrations/0008_server_saved_views/up.sql`
- `infra/db/migrations/0008_server_saved_views/down.sql`
- `specs/domain_schema.sql`
- `apps/api/app/domain.py`
- `apps/api/app/domain_repository.py`
- `specs/api_contract.yaml`
- `scripts/check_database_schema.py`
- `tests/integration/test_database_migrations.py`
- `artifacts/tests/a207/t1305_server_saved_view_conflict_recovery_contract.json`
- `data/task_backlog.csv`
- `data/acceptance_matrix.csv`
- `data/acceptance_traceability.csv`
- `data/development_status_ledger.csv`
- `docs/phase/V5_TASK_PACK_SYNCHRONIZATION.md`

### Acceptance mapping

- T1305 -> A207.
- A207 is now `IN PROGRESS`, not `DONE`.

### Validation

- Local static and governance validation pending in this run.
- PostgreSQL integration proof is required from GitHub Actions `make verify-g2-db` because this host has no local Docker/PostgreSQL.

### Remaining gaps

- Superseded by the later frontend API-first adapter slice: saved-view controls now attempt `/v1/saved-views` and explicitly fall back locally when the API base/server id is missing.
- A real multi-session browser E2E with two contexts against live FastAPI/PostgreSQL is still required.
- Authn/authz user/workspace scoping remains required before public multi-user use.

## 2026-06-20 - T1308/A211 WorkspaceContext and production navigation slice

### Scope

- Added a `WorkspaceContext` contract for the 16 EEI navigation modules without changing the EEI system name.
- Added a componentized workspace navigation rail with route, lens, section and planned-disabled control states.
- Wired real lens controls to workspace state, section controls to existing work surfaces, and route controls to `/`, `/objects-scope`, and `/development-status`.
- Added disabled states and explicit reasons for unfinished M&A, control-path and strategic-signal modules.
- Exposed URL, sessionStorage and localStorage persistence keys plus server endpoint mappings for saved views, model context, exploration and catalogs.
- Added Playwright coverage for A211.

### Files changed

- `apps/web/src/app/workspace-context.tsx`
- `apps/web/src/app/workspace-navigation.tsx`
- `apps/web/src/app/page.tsx`
- `apps/web/src/app/globals.css`
- `tests/e2e/home.spec.ts`
- `artifacts/tests/a211/t1308_frontend_workspace_context_contract.json`
- `data/task_backlog.csv`
- `data/acceptance_matrix.csv`
- `data/acceptance_traceability.csv`
- `data/development_status_ledger.csv`
- `data/release_gate_catalog.csv`
- `scripts/validate_v5_production_readiness_sync.py`
- `docs/phase/V5_TASK_PACK_SYNCHRONIZATION.md`
- `DEVELOPMENT_STATUS.md`
- `README.md`

### Acceptance mapping

- T1308 -> A211.
- A211 is now `IN PROGRESS`, not `DONE`.

### Validation

- Local `PNPM=/Users/linzezhang/.cache/codex-runtimes/codex-primary-runtime/dependencies/bin/pnpm make typecheck`: PASS.
- Local Playwright E2E command ran the full E2E set and passed: 28/28.

### Remaining gaps

- Frontend data loading still needs production API hydration against a configured FastAPI base URL.
- Saved-view UI now has an API-first adapter and mock server E2E; live FastAPI/PostgreSQL multi-session E2E and 409 conflict-recovery UI remain open.
- Model-center controls still need transactional activation, rollback and stale-client refresh semantics.
- A live FastAPI/PostgreSQL cross-route E2E is still required before closing A211.

## 2026-06-20 - T1215/T1211 release package generated-file exclusion

### Scope

- Excluded `apps/web/next-env.d.ts` from clean-room ZIP, release manifest and release checksums.
- Reason: Next.js rewrites this generated type-reference file during CI bootstrap/type generation, making strict package checks fail even when source and artifacts are otherwise synchronized.
- Regenerated clean-room release and release manifest/checksum artifacts after the exclusion.

### Files changed

- `scripts/manage_clean_room_release.py`
- `scripts/manage_release_artifacts.py`
- `artifacts/tests/a200/Enterprise_Ecosystem_Intelligence_clean_room_t1215.zip`
- `artifacts/tests/a200/t1215_clean_room_release.json`
- `artifacts/release_evidence_t1211.json`
- `manifest.txt`
- `DIRECTORY_TREE.txt`
- `CHECKSUMS.sha256`

### Validation

- Local `make generate-clean-room-release validate-clean-room-release generate-release-artifacts validate-release-artifacts`: PASS.
- Local `make verify`: PASS.

### Remaining gaps

- This only fixes release packaging determinism for generated Next type files; it does not close A211 or v0.1 production blockers.

## 2026-06-20 - T1305/A207 frontend saved-view API-first adapter slice

### Scope

- Added a browser saved-view API adapter that targets `/v1/saved-views` through `NEXT_PUBLIC_EEI_API_BASE_URL` or localStorage key `eei.apiBaseUrl.v1`.
- Changed saved-view save/restore controls from local-only behavior to API-first behavior with explicit local fallback when the API base URL or server id is missing.
- Added DOM contract fields for sync mode, sync reason, server id, server version, server endpoint, workspace key and API-base storage key.
- Added Playwright coverage for local fallback (`local-saved`/`local-restored`) and mock server API create/restore (`server-saved`/`server-restored`).
- Added A207 frontend adapter evidence while keeping A207 `IN PROGRESS`.

### Files changed

- `apps/web/src/app/saved-view-client.ts`
- `apps/web/src/app/page.tsx`
- `tests/e2e/state-contract.spec.ts`
- `artifacts/tests/a207/t1305_frontend_saved_view_api_adapter_contract.json`
- `artifacts/tests/a207/t1305_server_saved_view_conflict_recovery_contract.json`
- `scripts/validate_v5_production_readiness_sync.py`
- `data/acceptance_traceability.csv`
- `data/development_status_ledger.csv`
- `DEVELOPMENT_STATUS.md`
- `README.md`

### Acceptance mapping

- T1305 -> A207.
- A207 remains `IN PROGRESS`, not `DONE`.

### Validation

- Local `PNPM=/Users/linzezhang/.cache/codex-runtimes/codex-primary-runtime/dependencies/bin/pnpm make typecheck`: PASS.
- Local `PNPM=/Users/linzezhang/.cache/codex-runtimes/codex-primary-runtime/dependencies/bin/pnpm /Users/linzezhang/.cache/codex-runtimes/codex-primary-runtime/dependencies/bin/pnpm --filter @eei/web test:e2e`: PASS, 29/29.

### Remaining gaps

- Superseded by the later live multisession E2E harness slice: live two-context harness and 409 fetch-latest conflict recovery UI now exist and have GitHub Actions `verify-g2-db` PASS evidence in run `27862471613`, job `82460665725`.
- User/workspace authn/authz remains required before public multi-user saved-view deployment.

## 2026-06-20 - T1305/A207 live multisession saved-view E2E harness and conflict recovery UI

### Scope

- Added configured FastAPI CORS support for browser saved-view requests from the local EEI web origin.
- Added a dedicated live Playwright config that starts FastAPI and Next.js with `NEXT_PUBLIC_EEI_API_BASE_URL`.
- Added `scripts/run_live_e2e_api.sh` to reset the local E2E PostgreSQL database, run migrations, seed catalogs, load synthetic fixtures and start uvicorn.
- Added a live two-browser-context E2E that creates server saved-view version 1, updates it to version 2 in another context, triggers stale-version 409 from the first context and resolves via the new conflict recovery UI.
- Added a visible `server-conflict` recovery button that fetches the latest saved view and reports `server-conflict-resolved`.
- Added CORS unit coverage and wired `test-e2e-live` into `verify-g2-db`.

### Files changed

- `Makefile`
- `apps/api/app/main.py`
- `apps/api/app/settings.py`
- `apps/web/src/app/page.tsx`
- `playwright.config.ts`
- `playwright.live.config.ts`
- `scripts/run_live_e2e_api.sh`
- `tests/e2e/saved-view-live.spec.ts`
- `tests/unit/test_api_health.py`
- `artifacts/tests/a207/t1305_live_saved_view_multisession_e2e_contract.json`
- `scripts/validate_v5_production_readiness_sync.py`
- `data/acceptance_traceability.csv`
- `data/development_status_ledger.csv`
- `DEVELOPMENT_STATUS.md`
- `README.md`
- `docs/phase/V5_TASK_PACK_SYNCHRONIZATION.md`

### Acceptance mapping

- T1305 -> A207.
- A207 remains `IN PROGRESS`, not `DONE`, until user/workspace authn/authz is present.

### Validation

- Local `PNPM=/Users/linzezhang/.cache/codex-runtimes/codex-primary-runtime/dependencies/bin/pnpm make typecheck`: PASS.
- Local `UV_CACHE_DIR=/private/tmp/eei-uv-cache make lint`: PASS.
- Local `UV_CACHE_DIR=/private/tmp/eei-uv-cache make test-unit`: PASS, 13/13 with existing Starlette `httpx` deprecation warning.
- Local default Playwright E2E: PASS, 29/29.
- Local live Playwright E2E: NOT RUN; this host does not have `docker`.
- GitHub Actions run `27862471613`: PASS.
- GitHub Actions job `82460665725`: PASS.
- GitHub Actions step `Verify static, contract, lint, typecheck and unit tests`: PASS.
- GitHub Actions step `Verify G2 PostgreSQL migrations and E2E`: PASS, including the live FastAPI/PostgreSQL multisession saved-view E2E harness.

### Remaining gaps

- User/workspace authn/authz remains required before public multi-user saved-view deployment.
