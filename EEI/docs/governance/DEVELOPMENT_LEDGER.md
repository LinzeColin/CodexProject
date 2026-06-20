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

## Reconstructed Development Events

- `EVENT-RECON-20260619-001`: Task Pack v4.2.0 catalog baseline reconstructed from legacy files and validators.
- `EVENT-RECON-20260620-001`: recent T1207-T1209 evidence reconstructed from Git log and HANDOFF.
- `EVENT-20260621-002`: remote CI validation for TASK-T1307 operator soak runner readiness.
- `EVENT-20260621-003`: local implementation evidence for TASK-T1301/A202 second independent official-source closure.

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
