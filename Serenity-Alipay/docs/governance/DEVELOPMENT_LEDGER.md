# DEVELOPMENT_LEDGER

Project: `Serenity-Alipay`
Product version: `0.1.0`
Governance spec version: `1.0.0`

This ledger is human-readable. The append-only machine event stream is
`development_events.jsonl`.

## Current State

- Product version: `0.1.0`
- Product version status: `provisional`
- Current phase: `A`
- Current gate: `GOV-G3-SERENITY-BASELINE`
- Confirmed iteration count: 1
- Reconstructed development event count: 2
- Current task: `GOV-G3-SERENITY-MIGRATE-001`
- Blockers: validation not yet recorded in this file; see final run report for actual command results.

machine_summary:

- model_count: 5
- formula_count: 12
- parameter_count: 49
- task_count: 7

## Phase Matrix

| Phase | Name | Status | Exit criteria | Evidence |
|---|---|---|---|---|
| A | Discovery and baseline | in_progress | Governance files exist and validator passes for Serenity-Alipay | current run |
| B | Model and data specification | planned | Calibration and sensitivity UNKNOWNs are closed or explicitly deferred | `TASK-B-001`, `TASK-B-002` |
| C | Implementation | planned | Future behavior changes update governance in the same run | `TASK-C-001` |
| D | Verification and hardening | ready | Focused model tests and governance validator pass | `TASK-D-001` |
| E | Delivery and operation | planned | CI required mode can be enabled without advisory drift | `TASK-E-001` |

## Confirmed Iterations

Do not infer iteration count from Git commit count.

### `ITER-20260621-001`

- Date: 2026-06-21
- Fact level: EXTRACTED
- Version before: no `VERSION` file; `pyproject.toml` declared `0.1.0`
- Version after: `0.1.0`
- Base commit: `9516776`
- Result commit: `PENDING`
- Task IDs: `GOV-G3-SERENITY-MIGRATE-001`, `TASK-A-001`
- Goal: create the first CodexProject-auditable Serenity-Alipay governance baseline without changing scoring, ranking, gate, parameter, data, or business behavior.
- Assumptions: use only current code, tests, README, HANDOFF, old governance entry files, small manual CSV headers/samples, and limited Git history.
- Files read: root governance standard, root project registry, Serenity README, HANDOFF, old governance files, `app/core/scoring.py`, `app/core/pipeline.py`, `app/core/metrics.py`, `app/core/comparison.py`, `app/core/discipline.py`, `app/scheduler.py`, focused tests.
- Files changed: Serenity governance docs, `VERSION`, `CHANGELOG.md`, README governance entry, and old governance entry indexes.
- Model changes: no runtime model change; governance IDs assigned to current behavior.
- Parameter changes: no active parameter value change; current constants were registered as PARAM-001 through PARAM-049.
- Commands run: validation is recorded in the final run report.
- Test results: pending at the time this ledger entry was created.
- Successes: scoring, ranking, MDD, recovery, Top5, comparison, discipline, and schedule rules are traceable to code and tests.
- Failures: none recorded before validation.
- Decisions: old `模型参数文件`, `开发记录`, and `功能清单` become indexes into `docs/governance/`.
- Remaining risks: empirical calibration and sensitivity evidence are not proven; see `TASK-B-001` and `TASK-B-002`.
- Rollback: remove `docs/governance/` and restore edited Serenity root files from pre-run state.
- Next step: `GOV-G3-SERENITY-VERIFY-001`.

## Reconstructed Development Events

- `EVENT-RECON-20260612-001`: MVP scoring, dry-run automation, OpenD/MooMoo lifecycle, and local-first safety behavior reconstructed from `HANDOFF.md` and current tests. Fact level: RECONSTRUCTED.
- `EVENT-RECON-20260614-001`: delivery package, app entry, history-integrity, and production-readiness evidence reconstructed from `HANDOFF.md`. Fact level: RECONSTRUCTED.

## Unknown Historical Periods

- Exact iteration boundaries before `ITER-20260621-001` are UNKNOWN and are not inferred from Git commit count.
- Exact stdout for every historical test command in `HANDOFF.md` is not fully re-executed by this governance migration.
- Remote `LinzeColin/Serenity-Alipay` main HEAD mentioned in `HANDOFF.md` is not verified in this run.

## Validation History

| Command | Result | Evidence |
|---|---|---|
| `python scripts/validate_project_governance.py --project Serenity-Alipay` | BLOCKED | exit 127; current shell has no `python` executable |
| `python3 scripts/validate_project_governance.py --project Serenity-Alipay` | PASS | exit 0; errors 0, warnings 0 |
| `python scripts/validate_project_governance.py --all` | BLOCKED | exit 127; current shell has no `python` executable |
| `python3 scripts/validate_project_governance.py --all` | PASS_WITH_EXTERNAL_WARNINGS | exit 0; warnings 5 from EEI only |
| `python -m pytest` focused Serenity tests | BLOCKED | exit 127; current shell has no `python` executable |
| `python3 -m pytest` focused Serenity tests | PASS | exit 0; 20 passed |
| `git diff --check` | PASS | exit 0 |
