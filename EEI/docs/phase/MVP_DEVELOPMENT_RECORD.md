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
- G4 remains open because T1205 and T1208 are not complete.

Residual risks:

- The remaining G2-linked open IDs after A170 closure are A012, A013, A014, A026, and A027.
- G4 remains open because T1205 and T1208 are not complete.

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
