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
- Confirmed iteration count: 1
- Reconstructed development event count: 2
- Current task: `GOV-G2-EEI-REPAIR-001`
- Blockers: none for governance file generation; remaining UNKNOWN items are task-linked.

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

## Reconstructed Development Events

- `EVENT-RECON-20260619-001`: Task Pack v4.2.0 catalog baseline reconstructed from legacy files and validators.
- `EVENT-RECON-20260620-001`: recent T1207-T1209 evidence reconstructed from Git log and HANDOFF.

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
