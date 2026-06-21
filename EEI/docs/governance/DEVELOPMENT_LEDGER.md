# DEVELOPMENT_LEDGER

Project: `EEI`
Active product version: `0.1.0`
Governance spec version: `1.0.0`

This ledger is human-readable. The append-only machine record is `development_events.jsonl`.

## Current State

- Product version: `0.1.0`
- Product version status: `provisional`
- Current phase: `A`
- Current gate: `GOV-G2-EEI-BASELINE`
- Confirmed iteration count: 2
- Reconstructed development event count: 2
- Current task: `TASK-T1307`
- Blockers: A209 remains open until committed 4h and 24h operator soak evidence exists.

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
