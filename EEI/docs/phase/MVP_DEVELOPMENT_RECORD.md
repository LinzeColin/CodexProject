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

- T404 still owns breadcrumb/browser-history synchronization for reroot flows; T408 still owns critical three-reroot E2E.

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

- T405 still owns full graph/table explorer node actions; T406 still owns bounded evidence-bearing path queries.

## 2026-06-19 - Phase 1 / G4 T404 Breadcrumb and browser history synchronization

Status: LOCAL E2E PASS; remote CI pending

Completed:

- Added stable workspace attributes for current focus key and serialized focus path so browser/history assertions can compare UI state and URL state.
- Strengthened the state-contract E2E to cover reroot browser back, browser forward, app back, full breadcrumb visibility, and clickable intermediate breadcrumb restoration.
- Marked T404, A049, and A050 as `DONE`; A051 was already done by T401 and remains covered by state-contract URL assertions.

Verification evidence:

- Local `npx --yes pnpm@11.8.0 --filter @eei/web typecheck`: PASS.
- Local `npx --yes pnpm@11.8.0 --filter @eei/web test:e2e -- tests/e2e/state-contract.spec.ts`: PASS, 21 tests.

Acceptance status:

- A049 is covered by full path breadcrumb assertions for `nvidia.foundry.equipment.materials` and clickable restoration to `nvidia.foundry`.
- A050 is covered by browser `goBack`, browser `goForward`, and in-app back assertions restoring identical focus/path state.
- A051 remains covered by URL/session path and state assertions in `tests/e2e/state-contract.spec.ts` plus the T401 API state contract.

Residual risks:

- Remote CI must still prove the browser-history E2E under the GitHub runner.
- T408 still owns the critical three-reroot E2E acceptance A048.
