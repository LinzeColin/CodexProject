# DEVELOPMENT_LEDGER

Project: `EEI`
Active product version: `0.1.0`
Governance spec version: `1.0.0`

This ledger is human-readable. The append-only machine record is `development_events.jsonl`.

## Current State

- Product version: `0.1.0`
- Product version status: `provisional`
- Current phase: `C`
- Current gate: `TASK-T1301-T1302-T1303-CI-EVIDENCE-BINDING-IN-PROGRESS`
- Confirmed iteration count: 25
- Reconstructed development event count: 3
- Current task: `TASK-T1301/TASK-T1302/TASK-T1303 governance evidence binding`
- Blockers: commit `d009516c57c4908a025c401a711dfb4d599f7b73` is remote-CI bound by Project Governance run `27950933950` and EEI validation run `27950933933`, but A202 still lacks real source-license review, passage-level relationship review, production owner approval, legal release clearance, brand clearance, release-manager activation and public relationship publication; A203 remains open until production-approved relationship edges and downstream release gates have current evidence; A204/A205 remain open until deployment wake, atomic refresh consistency and long-duration refresh evidence are current; A026 requires at least 50 production human-labeled entity-resolution gold cases with precision >=95%; A027 requires at least 100 production human-labeled relationship gold cases with precision >=90%; A209 remains a background long-running gate until 24h operator soak evidence is produced and CI-validated, but it must not block unrelated MVP feature delivery; A210 still needs formal brand legal/market clearance or signed risk waiver; 7 active motion parameters still have UNKNOWN runtime activation evidence, and FORM-012 remains HUMAN_REVIEW_REQUIRED.

## Phase Matrix

| Phase | Name | Status | Exit criteria | Evidence |
|---|---|---|---|---|
| A | Discovery and baseline | in_progress | EEI validator passes | this run |
| B | Model and data specification | planned | UNKNOWN model/parameter gaps closed or accepted | pending |
| C | Implementation | planned | product task evidence remains traceable | pending |
| D | Verification and hardening | planned | required mode can pass | pending |
| E | Delivery and operation | planned | append-only events and handoff updated | pending |

## Confirmed Iterations

Do not infer iteration count from Git commit count.

### `ITER-20260620-001`

- Date: 2026-06-20
- Fact level: EXTRACTED
- Version before: `v4.2.0` in legacy `VERSION`; product package version was `0.1.0`
- Version after: `0.1.0` with legacy label preserved in `VERSION_MATRIX.yaml`
- Base commit: `9516776`
- Result commit: `PENDING`
- Task IDs: `GOV-G2-EEI-REPAIR-001`
- Goal: create the first CodexProject-auditable EEI governance baseline without runtime behavior change.
- Assumptions: use existing CSV/config/test evidence; mark unsupported runtime/calibration facts UNKNOWN.
- Files read: root governance files, EEI legacy governance Markdown, EEI data/config registries, EEI validators/tests.
- Files changed: EEI governance docs and legacy governance indexes only.
- Model changes: canonical ID mapping plus MOD-012 operational threshold control.
- Parameter changes: 60 legacy parameters mapped to PARAM-001..PARAM-060 with separated default/prior/active values.
- Commands run: see validation section below.
- Test results: required root EEI governance validator passed; root all-project validator passed with advisory warnings only outside EEI; focused EEI governance and model-config validators passed.
- Successes: canonical EEI governance files validate; legacy count drift is removed from editable Markdown; VERSION now separates product version from legacy Task Pack label.
- Failures: `python scripts/validate_task_pack.py` was attempted as an additional focused check and stopped on missing local dependency `pypdf`; dependencies were not installed in this run.
- Decisions: legacy CSV/config remain evidence inputs; `docs/governance/*` is canonical for CodexProject governance.
- Remaining risks: motion active values and empirical model calibration remain UNKNOWN and task-linked.
- Rollback: remove `EEI/docs/governance` and restore edited EEI index files, VERSION, and CHANGELOG.
- Next step: GOV-G2-EEI-VERIFY-001 after validation passes.

### `ITER-20260621-001`

- Date: 2026-06-21
- Fact level: EXTRACTED
- Version before: `0.1.0`
- Version after: `0.1.0`
- Base commit: `b3370a4`
- Result commit: `954b534`
- Task IDs: `TASK-T1307`
- Goal: add a resumable operator soak runner for T1307/A209 without claiming 4h/24h soak completion.
- Assumptions: the 3-second runner readiness artifact proves command and checkpoint behavior only; long-duration soak remains a release blocker.
- Files read: EEI soak harness, worker deployment validator, legacy v5 sync/status files, and canonical governance files.
- Files changed: `EEI/scripts/run_operator_soak.mjs`, A209 readiness artifacts, legacy trace/status files, and canonical governance files.
- Model changes: no scoring model behavior change; MOD-012 operational controls now include `PARAM-061`.
- Parameter changes: added `soak.operator_window_seconds=300` / `PARAM-061`.
- Commands run: `node scripts/run_operator_soak.mjs ...`, `make validate-operator-soak-runner`, `UV_CACHE_DIR=/private/tmp/eei-uv-cache make verify`.
- Test results: local elevated runner readiness PASS; local elevated `make verify` PASS with unit tests 37/37; GitHub Actions run `27886864382` / job `82523564731` PASS, including G2 PostgreSQL integration, browser E2E and live FastAPI PostgreSQL E2E.
- Successes: checkpoint JSONL, `--resume`, operator 4h/24h command surface and CI-safe readiness target are now governed.
- Failures: governance PDF binary was not regenerated because Python `playwright.sync_api` is missing in the current environment.
- Decisions: A209 remains `IN_PROGRESS`; CI smoke and 3-second readiness are not long-duration soak substitutes.
- Remaining risks: 4h and 24h operator soak and live Docker Compose duration proof are still pending.
- Rollback: revert the runner commit, remove A209 readiness artifacts, regenerate clean-room/release artifacts, and rerun validation.
- Next step: execute and attach 4h operator soak, then 24h operator soak.

### `ITER-20260621-002`

- Date: 2026-06-21
- Fact level: EXTRACTED
- Version before: `0.1.0`
- Version after: `0.1.0`
- Base commit: `944d9e0`
- Result commit: `PENDING`
- Task IDs: `TASK-T1301`
- Goal: add second independent official-source closure for the two Golden Vertical relationship fact candidates without claiming A202 completion.
- Assumptions: the added TSMC/ASML/NVIDIA official historical sources are acceptable supporting official-source anchors for local fixture evidence; live retrieval, legal clearance and real owner approval remain separate blockers.
- Files read: curated ingestion loader, database schema checker, Golden Vertical fact candidates, integration tests, review fixtures, V5 synchronization notes and canonical governance files.
- Files changed: Golden Vertical source anchors/candidates, curated ingestion loader, schema/integration/E2E expectations, review fixtures, status ledgers and governance task records.
- Model changes: no scoring formula change; source-threshold policy remains `minimum_independent_sources=2`.
- Parameter changes: no parameter value change.
- Commands run: focused ruff, unit tests, task-pack validator, web typecheck, local integration skip check; full `make verify` and remote PostgreSQL CI are required before remote evidence can be recorded.
- Test results: focused local checks passed where runnable; local PostgreSQL integration skipped because this host has no `DATABASE_URL`.
- Successes: each Golden Vertical relationship candidate now has two official source anchors, `independent_source_count=2`, `source_threshold_met=true` and no source-threshold override in review fixtures.
- Failures: live official retrieval, real production owner sign-off, formal legal/market clearance, and 4h/24h soak evidence remain incomplete.
- Decisions: A202 remains `IN_PROGRESS`; second-source closure reduces one blocker but does not make any real fact production-approved.
- Remaining risks: historical/supporting official sources may still be insufficient for final market/legal clearance without owner review.
- Rollback: revert the second-source data/loader/test changes, regenerate clean-room/release artifacts, and rerun validation.
- Next step: run full local verification, push for remote PostgreSQL/browser/live FastAPI CI proof, then execute the real live-source and owner-signoff closure.

### `ITER-20260621-003`

- Date: 2026-06-21
- Fact level: EXTRACTED
- Version before: `0.1.0`
- Version after: `0.1.0`
- Base commit: `f52d4a1`
- Result commit: `PENDING`
- Task IDs: `TASK-T1309`
- Goal: add a fail-closed brand-clearance preflight contract for A210 without claiming legal or market clearance.
- Assumptions: current local v5 brand policy and conflict register are sufficient to validate repository controls, but they are not legal advice or trademark clearance.
- Files read: brand policy, brand conflict register, v5 synchronization validator, task/acceptance/status ledgers and release governance records.
- Files changed: A210 preflight script/artifact, Makefile validation wiring, T1309/A210 status rows, V5 synchronization notes, delivery tasks and this ledger.
- Model changes: no scoring model change; brand release gate remains a governance control.
- Parameter changes: no parameter value change; `brand.clearance_required=true` remains active.
- Commands run: `scripts/validate_brand_clearance.py generate` and `scripts/validate_brand_clearance.py validate`; broader validation is required before commit.
- Test results: local A210 preflight generation and validation passed.
- Successes: EEI name lock, forbidden-name coverage, BRAND-G1 fail-closed release status and required clearance checklist are now machine-validated.
- Failures: formal legal opinion, trademark knockout, market search evidence and signed risk waiver remain absent.
- Decisions: A210 moves to `IN_PROGRESS`, not `DONE`.
- Remaining risks: a repository preflight can be mistaken for legal clearance if status files are not read carefully.
- Rollback: revert the A210 preflight script/artifact/status changes, regenerate release artifacts, and rerun validation.
- Next step: attach dated legal/market clearance evidence or signed risk waiver before any public brand launch.

### `ITER-20260621-004`

- Date: 2026-06-21
- Fact level: EXTRACTED
- Version before: `0.1.0`
- Version after: `0.1.0`
- Base commit: `71a697e`
- Result commit: `PENDING`
- Task IDs: `TASK-T1301`
- Goal: repair the A202 curated-ingestion PostgreSQL integration failure without weakening the human review gate.
- Assumptions: candidate-level `ready_for_review` is a publication workflow status, while `ingestion_evidence_chain.review_status` must stay within the existing database enum-like check.
- Files read: CI job step summary, curated ingestion loader, PostgreSQL migration constraints, integration tests and schema checker.
- Files changed: `EEI/scripts/load_curated_ingestion_anchors.py`, MVP development record and this ledger.
- Model changes: no scoring model change.
- Parameter changes: no parameter value change.
- Commands run: remote run `27890945803` showed Step 10 failure; focused ruff, task-pack validation, V5 readiness sync and brand-clearance validation passed after patch.
- Test results: local static/governance validations PASS; remote PostgreSQL CI rerun pending.
- Successes: introduced an explicit status mapper so evidence-chain rows remain database-valid while candidates remain ready for review.
- Failures: remote PostgreSQL CI still needs a rerun.
- Decisions: keep A202 `IN_PROGRESS`; do not change relationship candidate publication semantics.
- Remaining risks: without direct CI logs, the repair is based on migration constraint analysis and integration-test expectations.
- Rollback: revert the status mapper and rerun PostgreSQL integration.
- Next step: run local validation, commit, push and verify CI Step 10-12.

### `ITER-20260621-005`

- Date: 2026-06-21
- Fact level: EXTRACTED
- Version before: `0.1.0`
- Version after: `0.1.0`
- Base commit: `501f296`
- Result commit: `PENDING`
- Task IDs: `TASK-T1301`
- Goal: repair the remaining A202 PostgreSQL integration failure by aligning relationship fact candidate review-state semantics with the production database constraint.
- Assumptions: `ready_for_review` is a publication workflow state; database `review_status` records evidence/review verification state and must remain in the enum-like set enforced by migrations.
- Files read: failed GitHub Actions step summary, A202 fixture data, curated ingestion loader, migration constraints, integration tests, schema checker and E2E state fixture.
- Files changed: `EEI/data/golden_vertical_fact_candidates.json`, `EEI/scripts/load_curated_ingestion_anchors.py`, `EEI/tests/integration/test_database_migrations.py`, `EEI/scripts/check_database_schema.py`, `EEI/tests/e2e/state-contract.spec.ts`, MVP development record and this ledger.
- Model changes: no scoring model change.
- Parameter changes: no parameter value change.
- Commands run: remote run `27891135295` showed Step 10 failure; focused ruff, Task Pack validation, V5 readiness sync, brand-clearance validation, JSON parse, unit tests, web typegen, TypeScript, clean-room/release artifact regeneration/validation and checksum validation passed after patch.
- Test results: local non-browser/non-PostgreSQL validation PASS; local `make verify` remains blocked by macOS Chromium MachPort sandbox at browser benchmark; remote PostgreSQL CI rerun required.
- Successes: removed the contradiction between `publication_status=ready_for_review` and database `review_status` check constraints without weakening the human publication gate.
- Failures: remote PostgreSQL CI logs remain unavailable through the unauthenticated logs endpoint.
- Decisions: keep A202 `IN_PROGRESS`; do not publish candidate relationships to graph edges from this fix.
- Remaining risks: exact remote traceback is unavailable; local Docker/PostgreSQL is unavailable; full proof depends on rerunning GitHub Actions Step 10-12.
- Rollback: revert the A202 review-status normalization patch and rerun PostgreSQL integration.
- Next step: run local validation, commit, push and verify CI Step 10-12.

### `ITER-20260621-006`

- Date: 2026-06-21
- Fact level: EXTRACTED
- Version before: `0.1.0`
- Version after: `0.1.0`
- Base commit: `9fbbb87`
- Result commit: `PENDING`
- Task IDs: `TASK-T1301`, `TASK-T1308`
- Goal: align live FastAPI/PostgreSQL E2E with the A202 second-source publication state.
- Assumptions: Step 12 failure is caused by live E2E expecting the pre-A202 candidate publication text, because the same run passed Step 10 PostgreSQL integration and Step 11 browser E2E.
- Files read: latest GitHub Actions step summary, live Playwright config, saved-view live E2E spec and production-data UI rendering.
- Files changed: `EEI/tests/e2e/saved-view-live.spec.ts`, MVP development record and this ledger.
- Model changes: no scoring model change.
- Parameter changes: no parameter value change.
- Commands run: remote run `27891379096` showed Step 10 and Step 11 pass, Step 12 fail; local validation pending after patch.
- Test results: remote PostgreSQL integration PASS; remote browser E2E PASS; remote live E2E rerun required.
- Successes: preserved A202 publication gate while updating the live route contract to expect `ready_for_review`.
- Failures: exact Step 12 traceback is unavailable because GitHub logs endpoint returned 403.
- Decisions: do not revert the A202 `ready_for_review` publication state to satisfy an outdated live assertion.
- Remaining risks: Step 12 may expose an additional live assertion after this contract drift is fixed.
- Rollback: revert the live E2E assertion and rerun Step 12.
- Next step: run local TypeScript/checksum validations, commit, push and verify CI Step 12.

### `ITER-20260621-007`

- Date: 2026-06-21
- Fact level: EXTRACTED
- Version before: `0.1.0`
- Version after: `0.1.0`
- Base commit: `4450533`
- Result commit: `PENDING`
- Task IDs: `TASK-T1307`
- Goal: add fail-closed validation for future 4h/24h operator soak evidence without claiming A209 completion.
- Assumptions: current repository does not include committed 4h/24h operator soak JSON/checkpoint artifacts, so the correct validator status is `MISSING_OPERATOR_EVIDENCE`.
- Files read: T1307/A209 readiness artifacts, `scripts/run_operator_soak.mjs`, `scripts/run_soak_smoke.mjs`, Makefile, v5 readiness validator, A209 traceability and development status ledgers.
- Files changed: `EEI/scripts/validate_operator_soak_evidence.py`, `EEI/tests/unit/test_operator_soak_evidence.py`, `EEI/artifacts/tests/a209/t1307_operator_soak_evidence_validation.json`, Makefile, v5 readiness validator, A209 traceability, development status ledger, MVP development record and this ledger.
- Model changes: no scoring model change.
- Parameter changes: no parameter value change; `soak.short_duration_hours=4`, `soak.long_duration_hours=24` and `soak.operator_window_seconds=300` remain authoritative.
- Commands run: generated A209 evidence-validation artifact; focused ruff, unit test, ordinary A209 evidence validation, fail-closed release-gate validation and v5 readiness validation.
- Test results: focused ruff PASS; A209 validator unit tests PASS 3/3; ordinary A209 evidence validation PASS with `MISSING_OPERATOR_EVIDENCE`; release-gate mode expected-fail while long artifacts are absent; v5 readiness sync PASS.
- Successes: future 4h/24h evidence now has an explicit machine-checkable release gate that fails on insufficient duration, invalid checkpoints, budget breaches or missing Docker Compose worker binding.
- Failures: actual 4h and 24h operator soaks are still absent.
- Decisions: keep A209 `IN_PROGRESS`; `MISSING_OPERATOR_EVIDENCE` is an honest blocker state, not a release pass.
- Remaining risks: local macOS sandbox cannot prove long browser/worker soak; actual 4h/24h evidence still requires an operator-capable runtime.
- Rollback: revert the validator script, unit test, artifact, Makefile wiring and A209 traceability/docs changes.
- Next step: run focused lint/unit/v5/release validations, commit, push and verify CI.

### `ITER-20260621-008`

- Date: 2026-06-21
- Fact level: EXTRACTED
- Version before: `0.1.0`
- Version after: `0.1.0`
- Base commit: `5594da2`
- Result commit: `PENDING`
- Task IDs: `TASK-T1301`, `TASK-T1304`
- Goal: add a bounded live official-source retrieval adapter and no-network evidence contract without claiming A202 completion.
- Assumptions: the correct committed state is `NETWORK_EVIDENCE_MISSING` because real official-source network capture, operator review, PostgreSQL live-capture ingestion and legal/release clearance are not present.
- Files read: A202 official-source dry-run script and fixtures, source anchor registry, v5 readiness validator, A202/A206 traceability, development status ledger, v5 sync doc and MVP development record.
- Files changed: `EEI/scripts/fetch_official_source_full_text.py`, `EEI/tests/unit/test_official_source_live_capture.py`, `EEI/artifacts/tests/a202/t1301_live_official_retrieval_contract.json`, v5 readiness validator, A202/A206 traceability, acceptance matrix, development status ledger, development status artifacts, `DEVELOPMENT_STATUS.md`, MVP development record, v5 sync doc, this ledger and governance events.
- Model changes: no scoring formula change.
- Parameter changes: no canonical parameter value change; live capture contract records `min_text_chars=240`, `min_token_coverage_ratio=1.0`, `timeout_seconds=20.0`, `max_bytes=8388608` and the existing three-attempt retry policy.
- Commands run: generated A202 live official retrieval contract artifact; focused ruff; A202 live adapter unit tests; JSON validation; v5 readiness validation; development status artifact generation.
- Test results: focused ruff PASS; A202 live adapter unit tests PASS 4/4; JSON artifact validation PASS; v5 readiness sync PASS; development status artifact generation/validation PASS.
- Successes: live capture code path can parse HTML/PDF, hash source text, record retry/source-health metadata and prove no full official text or relationship publication is committed.
- Failures: no real operator live payload, live PostgreSQL ingestion, owner approval, legal clearance or 4h/24h source-health soak evidence exists.
- Decisions: keep A202 and A206 `IN_PROGRESS`; do not treat a no-network contract as live evidence or release clearance.
- Remaining risks: real official-source sites may require per-source fetch tuning, licensing review or PDF extraction adjustments during operator capture.
- Rollback: revert the live adapter script changes, unit test, generated artifact and A202/A206 traceability/status/docs changes, then regenerate development/release artifacts and rerun validation.
- Next step: run full unit/task-pack/release/checksum validations, commit, push and verify GitHub Actions.

### `ITER-20260621-009`

- Date: 2026-06-21
- Fact level: EXTRACTED
- Version before: `0.1.0`
- Version after: `0.1.0`
- Base commit: `f5fa298`
- Result commit: `PENDING`
- Task IDs: `TASK-T1301`, `TASK-T1304`
- Goal: record remote CI evidence for the A202 live official retrieval adapter contract without closing A202/A206.
- Commands run: GitHub Actions EEI validation run `27892494323` / job `82538366876`; GitHub Actions Project Governance run `27892494331`.
- Test results: EEI validation PASS; Step 7 static/contract/lint/typecheck/unit PASS, Step 8 G2 PostgreSQL preparation PASS, Step 9 G2 static/contract/lint/typecheck/unit PASS, Step 10 G2 PostgreSQL integration PASS, Step 11 browser E2E PASS and Step 12 live FastAPI PostgreSQL E2E PASS. Project Governance PASS.
- Decisions: keep A202/A206 `IN_PROGRESS`; remote CI proves the adapter and no-network contract, not real operator capture, live DB ingestion, legal clearance or long soak.
- Remaining risks: production capture still depends on operator-approved network run, source licensing review and PostgreSQL live-capture ingestion.
- Rollback: revert the remote evidence update and regenerate release artifacts with `remote_status=PENDING`.
- Next step: commit and push the remote evidence update, then verify the evidence-only CI run.

### `ITER-20260621-010`

- Date: 2026-06-21
- Fact level: EXTRACTED
- Version before: `0.1.0`
- Version after: `0.1.0`
- Base commit: `e37c2aa`
- Result commit: `PENDING`
- Task IDs: `TASK-T1301`, `TASK-T1304`
- Goal: add the T1301/A202 PostgreSQL ingestion path for live official-source capture artifacts without claiming live operator evidence or legal clearance.
- Assumptions: committed fixtures may validate loader behavior only when explicitly marked as `fixture_artifact`; real A202 evidence still requires an operator-approved live network payload and owner/legal review.
- Files read: A202 live adapter, operator-source capture loader, PostgreSQL ingestion tests, v5 readiness validator, A202/A206 traceability and development status ledgers.
- Files changed: `EEI/scripts/load_live_official_captures.py`, `EEI/tests/fixtures/live_official_captures/nvidia_live_official_capture_fixture.json`, `EEI/tests/unit/test_official_source_live_capture.py`, `EEI/tests/integration/test_database_migrations.py`, `EEI/artifacts/tests/a202/t1301_live_capture_postgres_ingestion_contract.json`, Makefile, v5 readiness validator, A202/A206 traceability, acceptance matrix, development status ledger, `DEVELOPMENT_STATUS.md`, MVP development record, v5 sync doc, this ledger and governance events.
- Model changes: no scoring formula change.
- Parameter changes: no canonical parameter change; ingestion uses existing `min_text_chars=240`, `min_token_coverage_ratio=1.0`, `record_mode=live` and `review_status=machine_verified` before operator review.
- Commands run: generated A202 live capture PostgreSQL ingestion contract artifact; focused ruff; A202 focused unit tests; JSON validation for live fixture and contract artifact; v5 readiness validation.
- Test results: focused ruff PASS; A202 live unit tests PASS 7/7; fixture JSON validation PASS; contract JSON validation PASS; v5 readiness sync PASS.
- Successes: live capture artifacts can now be loaded into PostgreSQL as hash/excerpt/source-health evidence without storing official full text or publishing relationship facts.
- Failures: no real operator live payload, source-license review, production owner approval, legal clearance or 4h/24h retry/dead-letter soak evidence exists.
- Decisions: keep A202 and A206 `IN_PROGRESS`; fixture ingestion is a CI contract and not production evidence.
- Remaining risks: real live payload ingestion may reveal per-source PDF/HTML parser differences and source licensing restrictions.
- Rollback: remove the live ingestion loader, fixture, tests, contract artifact and status/traceability updates; remove any deployed live parser rows by `parser_version='nvidia-official-fulltext-live-v1'` or restore a data snapshot.
- Next step: run full local verification, regenerate release artifacts, commit, push and verify GitHub Actions.

### `ITER-20260621-011`

- Date: 2026-06-21
- Fact level: EXTRACTED
- Version before: `0.1.0`
- Version after: `0.1.0`
- Base commit: `4c9c63a`
- Result commit: `PENDING`
- Task IDs: `TASK-T1301`, `TASK-T1304`
- Goal: record remote CI evidence for the A202 live capture PostgreSQL ingestion contract without closing A202/A206.
- Commands run: GitHub Actions EEI validation run `27893172875` / job `82540125436`; GitHub Actions Project Governance run `27893172917`.
- Test results: EEI validation PASS; Step 7 static/contract/lint/typecheck/unit PASS, Step 8 G2 PostgreSQL preparation PASS, Step 9 G2 static/contract/lint/typecheck/unit PASS, Step 10 G2 PostgreSQL integration PASS, Step 11 browser E2E PASS and Step 12 live FastAPI PostgreSQL E2E PASS. Project Governance PASS.
- Decisions: keep A202/A206 `IN_PROGRESS`; remote CI proves the loader contract and fixture-gated PostgreSQL path, not real operator payload, owner decision, legal clearance or long soak.
- Remaining risks: production capture still depends on operator-approved network run, source licensing review, non-fixture PostgreSQL ingestion, owner sign-off and A206/A209 long-duration evidence.
- Rollback: revert the remote evidence update and regenerate release artifacts with `remote_status=PENDING`.
- Next step: commit and push the remote evidence update, then verify the evidence-only CI run.

### `ITER-20260621-012`

- Date: 2026-06-21
- Fact level: EXTRACTED
- Version before: `0.1.0`
- Version after: `0.1.0`
- Base commit: `19cf61e`
- Result commit: `PENDING`
- Task IDs: `TASK-T1301`, `TASK-T1304`
- Goal: add selected-anchor real live official-source capture evidence and remote PostgreSQL assertions without closing A202/A206.
- Assumptions: a selected-anchor artifact can move A202 forward only if it stays no-full-text, no-publication and no-clearance; unsupported anchors must remain explicit review items.
- Files read: A202 live adapter, live capture loader, NVIDIA source anchor registry, PostgreSQL integration tests, v5 readiness validator, A202/A206 traceability and development status ledgers.
- Files changed: `EEI/scripts/fetch_official_source_full_text.py`, `EEI/tests/unit/test_official_source_live_capture.py`, `EEI/tests/integration/test_database_migrations.py`, `EEI/artifacts/tests/a202/t1301_live_official_retrieval_contract.json`, `EEI/artifacts/tests/a202/t1301_live_official_selected_capture_evidence.json`, `EEI/scripts/validate_v5_production_readiness_sync.py`, A202/A206 traceability and status docs, this ledger and governance events.
- Model changes: no scoring formula change.
- Parameter changes: no canonical parameter change; selected capture records `timeout_seconds=30.0`, `min_text_chars=240`, `min_token_coverage_ratio=1.0`, and `token_alias_policy_version=official-source-token-alias-v1`.
- Commands run: selected live network capture for `NVDA-ANCHOR-002/003/004`; focused ruff; A202 focused unit tests; JSON/no-full-text artifact validation; v5 readiness validation.
- Test results: focused ruff PASS; A202 live unit tests PASS 9/9; selected live artifact validation PASS; v5 readiness sync PASS.
- Successes: committed a real selected-anchor live evidence artifact with 3 healthy NVIDIA official-source captures, 100% token coverage, no committed full text, no relationship publication and no release clearance; added remote PostgreSQL assertions for non-fixture ingestion.
- Failures: local PostgreSQL integration could not run because the shell has no `docker`, `.env`, `DATABASE_URL`, `psql` or `pg_ctl`; `NVDA-ANCHOR-001` did not support the current `packaging/test` expected-token contract and remains a semantic review item.
- Decisions: keep A202 and A206 `IN_PROGRESS`; selected live capture is ready for operator review but is not owner/legal approval, production relationship publication or long-duration retry/dead-letter evidence.
- Remaining risks: remote G2 PostgreSQL must prove non-fixture ingestion; source licensing, owner decision, legal clearance, failed-anchor review and A206/A209 long-duration evidence remain open.
- Rollback: revert the live adapter alias and `--anchor-id` changes, remove the selected live artifact, restore fixture-only integration assertions, regenerate release artifacts and rerun validation.
- Next step: run full local validation where possible, regenerate release artifacts, commit, push and verify GitHub Actions G2 PostgreSQL integration.

### `ITER-20260621-013`

- Date: 2026-06-21
- Fact level: EXTRACTED
- Version before: `0.1.0`
- Version after: `0.1.0`
- Base commit: `d2c7442`
- Result commit: `PENDING`
- Task IDs: `TASK-T1301`, `TASK-T1304`
- Goal: record remote CI evidence for selected-anchor live official-source capture ingestion without closing A202/A206.
- Commands run: GitHub Actions EEI validation run `27893872934` / job `82541974047`; GitHub Actions Project Governance run `27893872928`.
- Test results: EEI validation PASS; Step 7 static/contract/lint/typecheck/unit PASS, Step 8 G2 PostgreSQL preparation PASS, Step 9 G2 static/contract/lint/typecheck/unit PASS, Step 10 G2 PostgreSQL integration PASS, Step 11 browser E2E PASS and Step 12 live FastAPI PostgreSQL E2E PASS. Project Governance PASS.
- Successes: remote CI proved the selected live artifact loads into PostgreSQL without fixture mode and preserves no-full-text, zero relationship fact candidates and source-health evidence boundaries through browser and live API paths.
- Decisions: keep A202/A206 `IN_PROGRESS`; remote CI proves ingestion mechanics, not production owner approval, source-license/legal clearance, relationship publication, `NVDA-ANCHOR-001` semantic resolution or long-duration retry/dead-letter soak.
- Remaining risks: formal operator/legal approval, failed-anchor review and A206/A209 4h/24h soak evidence remain open.
- Rollback: revert the remote evidence update and regenerate release artifacts with `remote_status=PENDING`.
- Next step: commit and push the remote evidence update, then verify the evidence-only CI run.

### `ITER-20260621-014`

- Date: 2026-06-21
- Fact level: EXTRACTED
- Version before: `0.1.0`
- Version after: `0.1.0`
- Base commit: `51ba6ef`
- Result commit: `PENDING`
- Task IDs: `TASK-T1307`, `TASK-T1304`
- Goal: repair the A209 operator soak window semantics before running 4h/24h evidence.
- Commands run: attempted 4h operator soak and interrupted after no first checkpoint was written; JS syntax checks; A209 unit tests; focused ruff; A209 evidence validator generation; 5-second parallel operator soak probe.
- Test results: `node --check` PASS for `run_soak_smoke.mjs` and `run_operator_soak.mjs`; A209 validator unit tests PASS 4/4; focused ruff PASS; 5-second parallel probe PASS with completed duration 5 seconds, elapsed wall 6.5612 seconds and worker jobs 12/12.
- Successes: `scripts/run_soak_smoke.mjs` now measures browser and worker soak concurrently inside each operator window, and `scripts/validate_operator_soak_evidence.py` rejects serialized double-wall-clock soak evidence.
- Failures: the first 4h attempt exposed the old serial child-harness behavior; no 4h or 24h release evidence was produced.
- Decisions: keep A209 and A206 `IN_PROGRESS`; the repair is prerequisite hardening, not long-duration evidence.
- Remaining risks: actual 4h and 24h operator artifacts still must be run, committed, validated and referenced in release evidence.
- Rollback: revert the parallel measurement and elapsed-wall validator changes, regenerate A209 evidence-validation artifact and rerun validation.
- Next step: commit/push the runner repair, verify CI, then run the 4h operator soak on the CI-validated code.

### `ITER-20260621-015`

- Date: 2026-06-21
- Fact level: EXTRACTED
- Version before: `0.1.0`
- Version after: `0.1.0`
- Base commit: `5b9fe87`
- Result commit: `PENDING`
- Task IDs: `TASK-T1307`, `TASK-T1304`
- Goal: record remote CI evidence for the A209 operator soak parallel-window repair without closing A209/A206.
- Commands run: GitHub Actions EEI validation run `27894602887` / job `82543882466`; GitHub Actions Project Governance run `27894602898`.
- Test results: EEI validation PASS; Step 7 static/contract/lint/typecheck/unit PASS, Step 8 G2 PostgreSQL preparation PASS, Step 9 G2 static/contract/lint/typecheck/unit PASS, Step 10 G2 PostgreSQL integration PASS, Step 11 browser E2E PASS, Step 12 live FastAPI PostgreSQL E2E PASS and Step 13 PostgreSQL stop PASS. Project Governance PASS.
- Successes: remote CI proved the soak runner/validator repair is compatible with the full EEI validation chain, including G2 PostgreSQL and browser/live API paths.
- Decisions: keep A209 and A206 `IN_PROGRESS`; remote CI proves only the runner repair, not committed 4h/24h operator soak evidence.
- Remaining risks: actual 4h and 24h operator artifacts must still be generated, validated, committed and referenced before A209 can close.
- Rollback: revert the remote evidence update and regenerate release artifacts with `remote_status=PENDING`.
- Next step: commit/push the remote evidence update, verify the evidence-only CI run, then run the 4h operator soak.

### `ITER-20260621-016`

- Date: 2026-06-21
- Fact level: EXTRACTED
- Version before: `0.1.0`
- Version after: `0.1.0`
- Base commit: `810ea9f`
- Result commit: `PENDING`
- Task IDs: `GOV-SEMANTIC-EEI-001`
- Goal: add partial machine semantic extraction for EEI active parameter and formula governance facts without changing runtime behavior.
- Assumptions: values equal to `EEI/data/parameter_catalog.csv` default values are machine-checkable in this slice; motion runtime activation values and FORM-012 threshold-control semantics remain unresolved until extractor or human-review evidence is added.
- Files read: root governance validator, EEI parameter registry, EEI formula registry, EEI parameter/formula CSV evidence sources, EEI delivery task registry.
- Files changed: EEI semantic governance registries, EEI delivery task registry, EEI version matrix, this ledger, and clean-room/release checksum evidence regenerated because the EEI CI release package must include the updated governance ledger.
- Model changes: no model behavior change; 10 active formula entries now have machine implementation fingerprints from `EEI/data/formula_registry.csv`, and FORM-012 is marked `HUMAN_REVIEW_REQUIRED`.
- Parameter changes: no active parameter value change; 54 active parameters now have machine source selectors and evidence hashes; 7 UNKNOWN motion parameters remain task-bound to `GOV-SEMANTIC-EEI-001`.
- Commands run: `python3 scripts/validate_semantic_extractors.py EEI`, root governance validators, governance pytest suite, `python scripts/manage_clean_room_release.py generate`, and `python scripts/manage_release_artifacts.py generate --remote-status PENDING`.
- Test results: local semantic extractor direct run PASS with `semantic_parameters_checked=54` and `semantic_formulas_checked=10`; root governance tests passed; clean-room release package regenerated with 390 package paths; release artifacts regenerated with `remote_status=PENDING`.
- Successes: EEI is no longer structure-only for its verifiable parameter/catalog facts and canonical formula CSV rows.
- Failures: EEI is not `machine_verified` because motion runtime activation sources and FORM-012 implementation fingerprint are still unresolved.
- Decisions: keep `semantic_coverage.status=in_progress`, not `machine_verified`.
- Remaining risks: catalog-level extraction does not prove every runtime loader path yet; FORM-012 still needs a dedicated extractor or explicit human-review acceptance.
- Rollback: remove the semantic selector/fingerprint fields, reset EEI semantic coverage to `planned`, regenerate clean-room/release artifacts from the reverted tree, and rerun governance validators.
- Next step: verify the partial EEI semantic extraction through root validator, all-project semantic drift report and GitHub CI.

### `ITER-20260621-017`

- Date: 2026-06-21
- Fact level: EXTRACTED
- Version before: `0.1.0`
- Version after: `0.1.0`
- Base commit: `4d31fff`
- Result commit: `PENDING`
- Task IDs: `TASK-T1307`, `TASK-T1304`
- Goal: produce committed 4h A209 operator soak evidence while keeping A209 open until 24h evidence exists.
- Commands run: fixed-path Playwright install; 5-second fixed-browser-path probe; `PLAYWRIGHT_BROWSERS_PATH=/private/tmp/eei-ms-playwright node scripts/run_operator_soak.mjs --mode operator_4h --duration-hours 4 --window-seconds 300 --output artifacts/tests/a209/t1307_operator_soak_4h.json --checkpoint artifacts/tests/a209/t1307_operator_soak_4h.checkpoints.jsonl --fail-on-budget --quiet`; A209 evidence validator generate/validate.
- Test results: 4h operator soak PASS; 48/48 checkpoint windows PASS; completed duration 14400 seconds; windows_failed 0; validator status `PARTIAL_OPERATOR_EVIDENCE` because 24h output/checkpoint are missing.
- Successes: generated real 4h browser+worker soak evidence with windowed checkpoint audit and fail-closed A209 validator coverage.
- Failures: an earlier 4h attempt failed at window 33 because the default macOS Playwright cache lost `chromium_headless_shell-1228`; the accepted run was restarted from zero with an explicit `PLAYWRIGHT_BROWSERS_PATH`.
- Decisions: keep A209 and A206 `IN_PROGRESS`; 4h evidence alone is not 24h evidence and cannot close the release gate.
- Remaining risks: 24h operator soak, CI validation of the committed 4h artifact, and final A209 release-manager review are still required.
- Rollback: remove the 4h JSON/checkpoint, regenerate the A209 evidence-validation artifact back to missing 4h/24h evidence, and rerun validation.
- Next step: commit/push the 4h local evidence, verify GitHub Actions, then run 24h operator soak.

### `ITER-20260622-001`

- Date: 2026-06-22
- Fact level: EXTRACTED
- Version before: `0.1.0`
- Version after: `0.1.0`
- Base commit: `0da8463`
- Result commit: `PENDING`
- Task IDs: `TASK-T1301`
- Goal: resolve the `NVDA-ANCHOR-001` source-registry semantic mismatch without publishing relationship facts or claiming legal clearance.
- Assumptions: the prior selected live evidence already proved `NVDA-ANCHOR-002/003/004`; `NVDA-ANCHOR-001` should remain a discovery/context anchor unless a separate passage-level relationship review is attached.
- Files changed: `EEI/data/nvidia_public_source_anchors.csv`, `EEI/scripts/load_curated_ingestion_anchors.py`, `EEI/scripts/fetch_official_source_full_text.py`, `EEI/scripts/load_operator_source_captures.py`, `EEI/scripts/load_live_official_captures.py`, `EEI/tests/unit/test_official_source_live_capture.py`, `EEI/tests/integration/test_database_migrations.py`, A202 fixtures/artifacts, traceability/status docs, this ledger and governance events.
- Model changes: no scoring formula change.
- Parameter changes: no canonical runtime parameter change; `NVDA-ANCHOR-001` expected-token scope is revised from precise stage terms to discovery context terms and `publication_scope=discovery_context_only`.
- Commands run: focused ruff; A202 focused unit tests; JSON validation for A202 fixtures/artifacts; v5 readiness validation.
- Test results: focused ruff PASS; `tests/unit/test_official_source_live_capture.py` PASS 10/10; A202 JSON validation PASS; v5 readiness sync PASS.
- Successes: added `artifacts/tests/a202/t1301_context_anchor_semantic_revision_contract.json`; persisted `anchor_scope` metadata through curated, dry-run, operator and live evidence paths; kept relationship publication and release clearance false.
- Decisions: keep A202 `IN_PROGRESS`; this revision closes only the failed-anchor semantic-review sub-gap, not owner sign-off, source-license review, legal clearance or A206/A209 soak.
- Remaining risks: local PostgreSQL integration was not run in this shell; remote G2 PostgreSQL must prove the updated counts and `anchor_scope` persistence.
- Rollback: restore the previous `NVDA-ANCHOR-001` expected-token list, remove `anchor_scope` persistence fields and the new contract artifact, restore candidate-count assertions, then rerun validation.
- Next step: run focused validation, then commit/push and verify GitHub Actions.

- CI artifact-sync note: follow-up governance repair synchronized the generated traceability artifact, release artifacts, status views, delivery task view and event binding metadata after GitHub Actions run `27929407037` flagged the pushed-diff contract.
- Additional validation: EEI single-project information-quality gate PASS, development-status artifact validation PASS, clean-room release validation PASS, release artifact validation PASS and checksum validation PASS.
- CI fixture-hash repair: GitHub Actions run `27929407052` flagged `NVDA-ANCHOR-001 source_text_sha256 does not match text` in the operator-source capture fixture; the fixture attestation hash was corrected, clean-room/release evidence was regenerated, and A209 24h soak remains a background evidence task.
- CI dry-run count repair: GitHub Actions run `27930880852` flagged the A202 dry-run ingestion count assertion as stale: `ingestion_runs.counts.entity_resolution_candidates` and the SQL table count are `50`, while the test expected `52`. The assertion was aligned to `50` without changing loader behavior, scoring formulas, publication status, owner sign-off, source-license review, legal clearance or A209 soak status.
- A202 operator/legal review packet note: `scripts/validate_a202_operator_review_packet.py` and `artifacts/tests/a202/t1301_operator_review_packet_contract.json` bind selected live official-source evidence to seven required closure gates while preserving `release_clearance=false`, zero relationship publication and A202 `IN_PROGRESS`. A209 24h soak remains a separate background gate and is not replaced by this packet.

### `ITER-20260622-011`

- Date: 2026-06-22
- Fact level: EXTRACTED
- Version before: `0.1.0`
- Version after: `0.1.0`
- Base commit: `f3fdd649`
- Result commit: `PENDING`
- Task IDs: `TASK-T1304`, `TASK-T1307`, `TASK-T1301`
- Goal: close the T1304/A206 scheduler, retry and dead-letter functionality gate independently from the A209 24h operator soak.
- Assumptions: GitHub Actions run `27934137278` / job `82651968987` proves the scheduler, worker, PostgreSQL, browser and live FastAPI/PostgreSQL paths on the current baseline; A209 24h soak remains a separate release stability gate.
- Files changed: A206 status ledgers, A202 operator-review packet gate map, A206 contract artifact, v5 sync validator, development status artifacts, delivery task traceability, release artifacts and governance status views.
- Model changes: no scoring, graph traversal or extraction formula behavior change.
- Parameter changes: no active threshold value changed; PARAM-062 remains a count of seven A202 review-packet gates, with the A206 gate now present instead of missing.
- Commands run: A202 review packet generation, v5 readiness sync, A202 packet validation, targeted unit tests, ruff, development-status generation, clean-room release generation, release artifact generation and checksum validation.
- Test results: local A202 packet generation/validation PASS, v5 readiness PASS, targeted unit tests PASS, ruff PASS; final full verification and remote CI binding remain pending for this commit.
- Successes: T1304/A206 is no longer blocked by waiting for all 288 five-minute A209 24h soak windows; scheduler auto wake, idempotency, heartbeat, retry cap, dead-letter, graceful shutdown, outbox dispatch, worker supervisor and Docker Compose worker binding remain traced to A206 evidence.
- Failures: A209 24h operator soak is still incomplete in the separate long-running evidence worktree.
- Decisions: mark A206 `DONE`; keep A209 `IN_PROGRESS`; keep A202 and A210 blocked until their owner/legal/source clearance contracts are satisfied.
- Remaining risks: remote GitHub Actions validation for this status-closure commit is pending; stale downstream docs could overstate production readiness if they ignore the still-open A209/A202/A210 gates.
- Rollback: revert the A206 status rows, validator status move, A206 contract status, A202 gate map and regenerated release artifacts; rerun `make verify`.
- Next step: commit/push this closure and verify EEI validation plus Project Governance CI before proceeding to the next MVP gap.

### `ITER-20260622-012`

- Date: 2026-06-22
- Fact level: EXTRACTED
- Version before: `0.1.0`
- Version after: `0.1.0`
- Base commit: `19206c19`
- Result commit: `PENDING`
- Task IDs: `TASK-T1301`, `TASK-T1309`
- Goal: add a fail-closed A202/A210 signed release decision bundle contract without claiming legal clearance, relationship publication, public brand launch or A209 closure.
- Assumptions: A209 24h soak continues as a background long-running evidence gate; waiting for all 288 five-minute windows must not block bounded A202/A210 feature delivery.
- Files changed: `scripts/validate_release_decision_bundle.py`, `tests/fixtures/release_decision_bundle/a202_a210_release_decision_bundle_template.json`, `tests/unit/test_release_decision_bundle.py`, `artifacts/tests/a202/t1301_a202_a210_release_decision_bundle_contract.json`, Makefile, A202/A210 acceptance/traceability rows, v5 readiness validator, delivery tasks, phase records and governance traceability.
- Model changes: no scoring formula, graph traversal, extraction model or model-weight behavior change.
- Parameter changes: no runtime threshold change; new schema constants define the release decision bundle contract and validation behavior.
- Commands run: release decision bundle generation/validation, template-only bundle validation, focused unit tests, focused ruff, py_compile, A202 official-source unit slice, v5 readiness sync and task-pack validation.
- Test results: release decision bundle generate PASS; contract validate PASS; template-only bundle validate PASS with `release_ready=false`; targeted bundle unit tests PASS 4/4; combined A202 bundle/official-source tests PASS 16/16; ruff PASS; py_compile PASS; v5 readiness sync PASS; task-pack validation PASS.
- Successes: A202/A210 now have one machine-readable bundle listing the exact signed source-license, passage-level, owner, legal and brand decisions still required before closure; signed bundle completion remains separate from A209 and release-manager activation.
- Failures: no real signed source-license review, production owner approval, legal opinion, brand clearance, risk waiver or 24h soak evidence was added.
- Decisions: keep A202 and A210 `IN_PROGRESS`; keep A209 as an independent background production-stability gate; do not change EEI system name.
- Remaining risks: remote GitHub Actions validation is pending; a future operator could still misread a repository template as clearance if downstream release checks ignore `release_ready=false`.
- Rollback: revert the release-decision bundle script, template, test, artifact, Makefile and governance/data record updates; regenerate release artifacts and rerun the documented validation subset.
- Next step: regenerate development/release artifacts, run final local verification, commit/push and bind this event to CI.
- CI merge-context repair: renamed the current release gate to `TASK-T1301-T1309-SIGNED-DECISION-BUNDLE-AWAITING-CI`, updated the root governance test so A209 24h soak remains open but non-blocking, and regenerated status/release evidence for the PR merge tree.

### `ITER-20260622-014`

- Date: 2026-06-22
- Fact level: EXTRACTED
- Version before: `0.1.0`
- Version after: `0.1.0`
- Base commit: `0e0967c`
- Result commit: `PENDING`
- Task IDs: `TASK-T904`, `TASK-T1301`
- Goal: add a fail-closed A026/A027 gold-quality evaluation contract for the Golden Vertical without claiming production gold-set coverage or relationship publication.
- Assumptions: the repository fixture is intentionally small and not production gold-set evidence; A209 24h soak continues as a background long-running stability gate and does not block this bounded quality-contract slice.
- Files changed: `scripts/validate_gold_quality_evaluation.py`, `tests/fixtures/gold_quality/golden_vertical_gold_labels_sample.json`, `tests/unit/test_gold_quality_evaluation.py`, A026/A027 gold-quality artifacts, Makefile, acceptance/traceability rows, parameter/model/phase records and V5 readiness sync.
- Model changes: no scoring formula, graph traversal, extraction model or model-weight behavior changed; MOD-012/FORM-012 now list gold-quality gate constants.
- Parameter changes: added `PARAM-064` through `PARAM-068` for entity minimum cases 50, entity precision 0.95, relationship minimum cases 100, relationship precision 0.90 and required source coverage 1.0.
- Commands run: gold-quality contract generation/validation, focused py_compile, focused unit tests and focused ruff.
- Test results: gold-quality generation PASS with `release_gate_closure_allowed=false`; contract validation PASS with A026/A027 `IN_PROGRESS`; unit tests PASS 4/4; focused ruff PASS; final broader validation and remote CI binding remain pending for this commit.
- Successes: A026/A027 now have explicit precision, recall and source-coverage reporting requirements plus sample-size thresholds, and repository fixtures cannot be mistaken for production acceptance evidence.
- Failures: no production human-labeled gold set, owner approval, legal/source clearance or A209 24h soak evidence was added.
- Decisions: keep A026 and A027 `IN_PROGRESS`; keep A202 `IN_PROGRESS`; keep A209 as a non-blocking background production-stability gate; do not change EEI system name.
- Remaining risks: broader generated artifacts and remote CI still need to bind this pre-commit event; future operators must attach real labeled data before closing A026/A027.
- Rollback: revert the gold-quality script, fixture, test, artifacts, Makefile, parameter rows and governance/data records; regenerate release artifacts and rerun validation.
- Next step: run V5 sync, semantic governance sync, release artifact validation, commit/push and verify CI.

### `ITER-20260622-016`

- Date: 2026-06-22
- Fact level: EXTRACTED
- Version before: `0.1.0`
- Version after: `0.1.0`
- Base commit: `5e6207f5`
- Result commit: `PENDING`
- Task IDs: `TASK-T1302`
- Goal: extend A203 production scoring explanations and score-result recompute coverage to first-class `theme` and `facility` objects without claiming A203 completion.
- Assumptions: `theme` and `facility` are stored in `entities` with type-specific `entity_type` values; the entity coverage formula remains valid when the request is type-guarded and the response object type is explicit.
- Files changed: `apps/api/app/domain_repository.py`, `scripts/job_scheduler.py`, `specs/api_contract.yaml`, `tests/integration/test_database_migrations.py`, A203 contract artifact, V5 readiness sync map, acceptance/status records, phase records and this ledger.
- Model changes: no scoring formula, graph traversal, extraction model or model-weight behavior changed; `theme` and `facility` reuse entity coverage scoring with a strict entity-type guard.
- Parameter changes: no active threshold value changed.
- Commands run: focused py_compile, focused ruff, OpenAPI contract validation, scoring unit tests and local integration collection.
- Test results: py_compile PASS; ruff PASS; contract validation PASS; `tests/unit/test_scoring.py` PASS 14/14; `tests/integration/test_database_migrations.py` SKIPPED locally because this host has no `.env` or `DATABASE_URL`; remote PostgreSQL CI remains pending.
- Successes: `/v1/scoring/explain/theme/{id}` and `/v1/scoring/explain/facility/{id}` now return typed scoring explanations, mismatched IDs fail closed with 404, and `score_recompute` records eight MVP object families in `score_results`.
- Failures: no production-approved relationship edge, legal/source clearance, production gold set or A209 24h soak evidence was added.
- Decisions: keep A203 `IN_PROGRESS`; keep A209 as a non-blocking background stability gate; do not change scoring weights or EEI system name.
- Remaining risks: remote GitHub Actions validation still needs to prove the new PostgreSQL assertions, browser E2E and live FastAPI/PostgreSQL E2E.
- Rollback: revert the T1302 API/repository/worker/test/contract/status changes, regenerate release artifacts and rerun `make verify`.
- Next step: run V5 sync, task-pack validation, release artifact regeneration, full local verification, commit/push and verify CI.

### `ITER-20260622-018`

- Date: 2026-06-22
- Fact level: EXTRACTED
- Version before: `0.1.0`
- Version after: `0.1.0`
- Base commit: `9055f2b2`
- Result commit: `PENDING`
- Task IDs: `TASK-T1301`
- Goal: require the A202/A210 signed release decision bundle before the production owner sign-off publication path can write reviewed relationship facts, without claiming A202/A210/A209 completion.
- Assumptions: repository signed-decision fixtures may validate schema and persistence only; real source-license review, passage-level review, production owner/legal/brand clearance and A209 24h soak remain external evidence.
- Files changed: `scripts/publish_reviewed_relationship_facts.py`, `scripts/validate_release_decision_bundle.py`, signed release-decision fixture, release-decision unit tests, PostgreSQL integration assertions, `Makefile`, A202 contract artifact, V5 readiness sync map, acceptance/status records, phase records and this ledger.
- Model changes: no scoring formula, graph traversal, extraction model or model-weight behavior changed; this is a fail-closed publication-control and evidence-chain binding change.
- Parameter changes: no active threshold value changed; existing release-decision bundle schema contract remains the controlling governance parameter.
- Commands run: signed-bundle JSON validation, py_compile, focused ruff, release-decision unit tests, signed bundle validation and release-decision contract generation/validation.
- Test results: signed fixture JSON PASS; py_compile PASS; focused ruff PASS after import-format repair; `tests/unit/test_release_decision_bundle.py` PASS 5/5; signed bundle validate PASS with `signed_decision_complete=true` and `release_ready=false`; release-decision contract validate PASS.
- Successes: production owner sign-off publication now fails closed without `--release-decision-bundle`; template bundles fail closed; successful contract-test publication persists release bundle hash and signed decision summaries into `data_snapshots`, relationship qualifiers, relationship evidence and fact-version payloads.
- Failures: no real signed release bundle, legal clearance, source-license approval, public relationship publication, release-manager activation, production gold set or A209 24h soak evidence was added.
- Decisions: keep A202, A210 and A209 `IN_PROGRESS`; keep A209 as a non-blocking background stability gate; do not change EEI system name.
- Remaining risks: remote PostgreSQL CI still needs to prove the new publication-binding assertions; future operators must not treat the contract-test signed fixture as legal, brand or source-license clearance.
- Rollback: revert the A202 publication script, signed fixture, unit/integration tests, release-decision artifact/status updates and regenerated release artifacts; rerun `make verify`.
- Next step: run V5 sync, task-pack validation, release artifact regeneration, full local verification, commit/push and verify CI.

### `ITER-20260623-001`

- Date: 2026-06-23
- Fact level: EXTRACTED
- Version before: `0.1.0`
- Version after: `0.1.0`
- Base commit: `d009516c57c4908a025c401a711dfb4d599f7b73`
- Result commit: `d009516c57c4908a025c401a711dfb4d599f7b73` remote-CI attested; current governance repair commit still needs its own CI after push.
- Task IDs: `TASK-T1301`, `TASK-T1302`, `TASK-T1303`, `TASK-T1307`, `TASK-T1309`
- Goal: bind the `d009516c` Project Governance and EEI validation CI evidence into EEI governance status and add explicit T1302/T1303 delivery task contracts without waiting on A209 24h soak windows.
- Assumptions: CI evidence proves the committed contracts and current branch regressions only; it does not approve production relationship publication, legal/source/brand clearance, model release-manager activation or A209 closure.
- Files changed: governance generator, VERSION_MATRIX, delivery_tasks, development_events, acceptance/status ledgers, V5 sync record, generated EEI governance status files, run manifest and root governance tests.
- Model changes: no scoring formula, graph traversal, extraction model or model-weight behavior changed.
- Parameter changes: no active threshold value changed.
- Commands run: local regeneration and validation are required for the current repair commit; remote evidence already exists for `d009516c` through Project Governance run `27950933950` and EEI validation run `27950933933`.
- Test results: Project Governance run `27950933950` job `82707373153` PASS; EEI validation run `27950933933` job `82707372790` PASS, including Step 10 G2 PostgreSQL integration, Step 11 browser E2E and Step 12 live FastAPI/PostgreSQL E2E.
- Successes: A202 signed-bundle publication binding and T1302 theme/facility scoring evidence are no longer marked as remote-CI pending; T1302 and T1303 now have bounded delivery contracts with Acceptance IDs, commands, risks and rollback.
- Failures: A209 24h operator soak is still missing and must continue as a background independent evidence task; A202/A203/A204/A205/A210 remain in progress.
- Decisions: do not block MVP feature development on the 288 five-minute A209 windows; keep 24h soak as a production-stability release gate; continue bounded MVP implementation in parallel.
- Remaining risks: the current governance repair commit still needs local validation, push and GitHub CI; future operators must not read `CI_ATTESTED:d009516c` as full MVP completion.
- Rollback: revert the generator, `ITER-20260623-001` event, T1302/T1303 delivery task sections, ledger/status updates, run manifest and root test changes; regenerate governance/release artifacts and rerun validation.
- Next step: regenerate artifacts, run `make verify`, run governance sync and root governance tests, then commit/push and verify CI.

## Reconstructed Development Events

- `EVENT-RECON-20260619-001`: Task Pack v4.2.0 catalog baseline reconstructed from legacy files and validators.
- `EVENT-RECON-20260620-001`: recent T1207-T1209 evidence reconstructed from Git log and HANDOFF.
- `EVENT-20260621-002`: remote CI validation for TASK-T1307 operator soak runner readiness.
- `EVENT-20260621-003`: local implementation evidence for TASK-T1301/A202 second independent official-source closure.
- `EVENT-20260621-004`: local implementation evidence for TASK-T1309/A210 brand-clearance fail-closed preflight.
- `EVENT-20260621-005`: local repair for TASK-T1301/A202 evidence-chain review-status persistence.
- `EVENT-20260621-009`: fail-closed validator for TASK-T1307/A209 long-duration operator soak evidence.
- `EVENT-20260621-010`: local implementation evidence for TASK-T1301/A202 live official retrieval adapter contract.
- `EVENT-20260621-011`: remote CI validation evidence for TASK-T1301/A202 live official retrieval adapter contract.
- `EVENT-20260621-012`: local implementation evidence for TASK-T1301/A202 live capture PostgreSQL ingestion contract.
- `EVENT-20260621-013`: remote CI validation evidence for TASK-T1301/A202 live capture PostgreSQL ingestion contract.
- `EVENT-20260621-014`: local selected-anchor live official capture evidence for TASK-T1301/A202 and TASK-T1304/A206.
- `EVENT-20260621-015`: remote CI validation evidence for TASK-T1301/A202 selected-anchor live official capture ingestion.
- `EVENT-20260621-016`: local A209 operator soak parallel-window contract repair.
- `EVENT-20260621-017`: remote CI validation evidence for TASK-T1307/A209 operator soak parallel-window repair.
- `EVENT-20260621-019`: local 4h operator soak evidence for TASK-T1307/A209.
- `EVENT-20260622-001`: local context-anchor semantic revision for TASK-T1301/A202.
- `EVENT-20260622-002`: local validation for TASK-T1301/A202 context-anchor semantic revision.
- `EVENT-20260622-003`: clean-room and release evidence resync after TASK-T1301/A202 context-anchor semantic revision.
- `EVENT-20260622-004`: final clean-room and release evidence resync after tracking the A202 context-anchor artifact.
- `EVENT-20260622-005`: governance pushed-diff artifact sync for TASK-T1301/A202 context-anchor semantic revision.
- `EVENT-20260622-004`: final clean-room and release evidence resync after tracking the new A202 semantic-revision artifact.
- `EVENT-20260622-008`: local A202 dry-run ingestion count assertion repair after EEI validation run `27930880852` failed G2 PostgreSQL integration.
- `EVENT-20260622-010`: local A202 operator/legal review packet contract for selected live official-source evidence while A209 24h soak continues as a background release gate.
- `EVENT-20260622-011`: local T1304/A206 scheduler closure decoupled from A209 24h operator soak.
- `EVENT-20260622-012`: local A202/A210 signed release decision bundle contract; signed decisions are separate from A209 24h soak and release-manager activation.
- `EVENT-20260622-014`: local A026/A027 gold-quality evaluation contract; production gold-set labels remain required and A209 stays a background gate.
- `EVENT-20260622-015`: governance sync coverage repair for the current EEI branch diff after adding the A026/A027 gold-quality contract.
- `EVENT-20260622-016`: local T1302/A203 theme/facility scoring explain and eight-family score-result recompute extension.
- `EVENT-20260622-018`: local T1301/A202 signed release decision bundle binding for production owner sign-off publication.
- `EVENT-20260623-001`: remote CI evidence binding for `d009516c` and T1302/T1303 delivery task contract repair; A209 24h soak remains a background gate.

## Unknown Historical Periods

- Exact iteration boundaries before this governance baseline are UNKNOWN; Git commit count is not used as iteration count.
- Exact per-task stdout for every legacy DONE task is not fully preserved in the canonical governance files; tasks rely on acceptance traceability and HANDOFF/CI evidence.

## Validation History

| Command | Result | Evidence |
|---|---|---|
| `python scripts/validate_project_governance.py --project EEI` | PASS | exit 0; errors 0, warnings 0 |
| `python scripts/validate_project_governance.py --all` | PASS | exit 0; errors 0, warnings 96 from other advisory projects only |
| `python scripts/validate_governance.py` | PASS | exit 0; tasks/acceptance/risks/trace/gates 120/200/53/221/10 |
| `python scripts/validate_model_config.py config/model_profiles/balanced-v2.json config/thresholds/default-v2.json` | PASS | exit 0; weight_sum 1.0 and calibration_days 14 |
| `python scripts/validate_task_pack.py` | BLOCKED | exit 1; local dependency `pypdf` missing and dependency installation is outside this run |
