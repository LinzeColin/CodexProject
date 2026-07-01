# KM_IDSystem Development Ledger

Product version: `1.0.0`
Governance spec version: `1.0.0`

## Current State

- Product version: `1.0.0`
- Product version status: `provisional`
- Current phase: `B`
- Current gate: `GOV-SEMANTIC-OPME-in-progress`
- Confirmed iterations: 3
- Reconstructed development events: 1
- Latest remediation task: `S3PCT01`
- Current product task: `TASK-OPME-B-001`
- Blockers: `TASK-OPME-B-001` for calibration, prompt/provider governance, and signoff evidence.

## Confirmed Iterations

### `ITER-20260620-OPME-001`

- Date: 2026-06-20
- Fact level: EXTRACTED
- Version before: `1.0.0`
- Version after: `1.0.0`
- Base commit: `9516776`
- Result commit: `PENDING`
- Task IDs: `TASK-OPME-A-001`, `TASK-OPME-A-002`
- Goal: establish KM_IDSystem governance baseline without changing backend/frontend behavior.
- Model changes: documentation only; 7 models/rules recorded.
- Parameter changes: documentation only; rule constants and router parameters recorded.
- Commands: `python scripts/validate_project_governance.py --project KM_IDSystem`; `python -m pytest tests/test_analysis.py -q`; `python -m pytest tests/test_api.py -q`; `python scripts/validate_project_governance.py --all`; `git diff --check`.
- Test results: OpMe project validator exit 0 with errors 0 warnings 0; `test_analysis.py` exit 0 with 2 passed; `test_api.py` exit 2 because `fastapi` is missing in current environment; all-project validator exit 0 with advisory warnings only outside required projects; diff check exit 0.
- Rollback: remove `docs/governance` and restore indexes/VERSION/CHANGELOG.
- Next step: continue with OpenAIDatabase P10.

### `ITER-20260621-OPME-001`

- Date: 2026-06-21
- Fact level: EXTRACTED
- Version before: `1.0.0`
- Version after: `1.0.0`
- Base commit: `1fa711b5f480c78b2421d63bd9183939022d9ca0`
- Result commit: `PENDING`
- Task IDs: `GOV-SEMANTIC-OPME-001`, `ACC-SEMANTIC-OPME-001`
- Goal: add machine semantic extractor coverage for KM_IDSystem rule constants and active formula implementation fingerprints without changing backend/frontend behavior.
- Model changes: no model behavior change; 7 active formulas now include implementation refs, fingerprints, verification commit, verification time, and evidence hash.
- Parameter changes: no parameter value change; 49 active parameters now include source selector, extracted value, verification commit, verification time, evidence hash, and machine semantic status.
- Commands: `python3 scripts/validate_semantic_extractors.py KM_IDSystem`; `python3 scripts/validate_project_governance.py --project KM_IDSystem --semantic`; `python3 scripts/validate_project_governance.py --all --semantic --drift-report`; `python3 scripts/validate_project_governance.py --changed-only --enforce-sync --semantic`; focused governance and OpMe tests.
- Test results: semantic extractor exit 0 with 49 parameters and 7 formulas checked; OpMe semantic validator exit 0; all-project semantic drift exit 0; changed-only enforce-sync semantic exit 0; governance tests exit 0 with 50 passed; generated dashboard/status output stable on repeat; OpMe backend tests blocked in current environment by missing `pydantic` and `fastapi`.
- Success criteria: semantic validator checks 49 parameters and 7 formulas; root validator passes for OpMe in semantic mode; changed-only sync gate passes.
- Remaining risks: engineering calibration source, prompt/provider policy, and owner signoff evidence remain blocked under `TASK-OPME-B-001`.
- Rollback: revert semantic registry fields, reset `governance/projects.yaml` OpMe semantic coverage to planned, and remove `governance/run_manifests/GOV-SEMANTIC-OPME-EXTRACT-001.json`.
- Next step: run local validation and bind CI evidence after merge.

### `ITER-20260624-OPME-S3PCT01`

- Date: 2026-06-24
- Fact level: VERIFIED
- Version before: `1.0.0`
- Version after: `1.0.0`
- Base commit: `e1e00541933529e54909b92ecf07cc0f9e9d015b`
- Result commit: `PENDING`
- Task IDs: `S3PCT01`, `ACC-S3PCT01`
- Goal: verify OpMe startup/stop dependency fallback, launcher cleanup, and SQLite save/recovery behavior without production connections.
- Model changes: no diagnostic scoring formula or LLM routing behavior changed.
- Parameter changes: no active parameter value changed.
- Commands: lifecycle unittest, bash syntax checks for runtime scripts, py_compile for config/db/test, and existing OpMe analysis test.
- Test results: lifecycle contract exit 0 with 4 tests; shell syntax exit 0; py_compile exit 0; existing `test_analysis.py` remains blocked locally by missing `pydantic`.
- Success criteria: runtime entrypoints fail fast with explicit dependency bootstrap commands, stale/invalid launcher PID files are cleaned from a temp runtime, and SQLite persistence can recover from a temp database path.
- Remaining risks: full API/backend tests still require a dependency-prepared environment with `pydantic` and `fastapi`; production Docker/browser/provider runtime was not started.
- Rollback: revert S3PCT01 code, scripts, tests, stage-gate evidence, rendered governance files, and run manifest.
- Next step: continue to `S3PCT02` for PFI lifecycle/cache/SQLite/resume stability.

## Reconstructed Development Events

- `EVENT-RECON-OPME-20260619-001`: project import/continuity reconstructed from Git history and legacy notes; not counted as confirmed iteration.

## Validation History

| Command | Result | Evidence |
|---|---|---|
| `python scripts/validate_project_governance.py --project KM_IDSystem` | PASS | exit 0; errors 0 warnings 0 |
| `python -m pytest tests/test_analysis.py -q` | PASS | exit 0; 2 passed |
| `python -m pytest tests/test_api.py -q` | BLOCKED | exit 2; `fastapi` missing and dependency install is outside this run |
| `python scripts/validate_project_governance.py --all` | PASS | exit 0; advisory warnings only outside required projects |
| `git diff --check` | PASS | exit 0 |
| `python3 scripts/validate_semantic_extractors.py KM_IDSystem` | PASS | exit 0; semantic_parameters_checked=49 semantic_formulas_checked=7 |
| `python3 scripts/validate_project_governance.py --project KM_IDSystem --semantic` | PASS | exit 0; errors 0 warnings 0 |
| `python3 scripts/validate_project_governance.py --all --semantic --drift-report` | PASS | exit 0; errors 0 warnings 0 |
| `python3 scripts/validate_project_governance.py --changed-only --enforce-sync --semantic` | PASS | exit 0; errors 0 warnings 0 |
| `python3 -m pytest tests/governance/test_project_governance_validator.py -q` | PASS | exit 0; 50 passed |
| `PYTHONPATH=. python3 -m pytest tests/test_analysis.py -q` | BLOCKED | exit 2; `pydantic` missing in current environment |
| `PYTHONPATH=. python3 -m pytest tests/test_api.py -q` | BLOCKED | exit 2; `fastapi` missing in current environment |
| `python -B -m unittest KM_IDSystem.backend.tests.test_lifecycle_contract -q` | PASS | exit 0; 4 lifecycle contract tests |
| `bash -n KM_IDSystem/scripts/run_local_services.sh KM_IDSystem/scripts/stop_local_services.sh KM_IDSystem/scripts/smoke_test.sh KM_IDSystem/scripts/dev.sh` | PASS | exit 0 |
| `python -B -m py_compile KM_IDSystem/backend/app/core/config.py KM_IDSystem/backend/app/services/db.py KM_IDSystem/backend/tests/test_lifecycle_contract.py` | PASS | exit 0 |
