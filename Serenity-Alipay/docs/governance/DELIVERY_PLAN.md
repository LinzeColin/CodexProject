# DELIVERY_PLAN

Project: `Serenity-Alipay`
Governance spec version: `1.0.0`

## Canonical Sources

- Task registry: `delivery_tasks.yaml`
- Traceability: `TRACEABILITY_MATRIX.csv`
- Model and parameter registries: `model_registry.yaml`, `formula_registry.yaml`, `parameter_registry.csv`
- Development ledger: `DEVELOPMENT_LEDGER.md`, `development_events.jsonl`

Old root files are compatibility indexes only:

- `模型参数文件`
- `开发记录`
- `功能清单`

## Task Summary

machine_summary:

- task_count: 10

No historical task is marked `completed` unless direct acceptance and evidence
are present in the canonical registry. Current historical implementation facts
are recorded as model evidence and reconstructed events, not completed delivery
tasks.

## Phase Plan

| Phase | Purpose | Current task | Status | Exit Gate |
|---|---|---|---|---|
| A | Discovery and baseline | `TASK-A-001` | in_progress | Serenity governance validator passes |
| B | Model and data specification | `TASK-B-003` | completed | Semantic extractor pilot passes for documented Serenity parameters and formulas |
| C | Implementation | `TASK-C-001` | planned | Future behavior changes update governance in same run |
| D | Verification and hardening | `TASK-D-001` | ready | Focused tests and governance validation pass |
| E | Delivery and operation | `TASK-E-001` | planned | Project can be promoted from advisory to required |

## Acceptance IDs

- `ACC-A-001`: Active scoring, metric, and hard-gate formulas are exact and traceable to code and tests.
- `ACC-A-002`: Ranking, Top5 selection, target weight, and deviation action rules are exact and traceable.
- `ACC-A-003`: Time-window, comparison, discipline, scheduler, and safety gates are traceable.
- `ACC-A-004`: Independent read-only verification confirms no business-code diff and no duplicate fact source.
- `ACC-B-001`: Calibration and sensitivity evidence is added or explicitly accepted as deferred.
- `ACC-B-002`: Parameter test coverage gaps are closed or task-linked.
- `ACC-B-003`: Active parameter values and formula implementation fingerprints are machine-checked against Serenity code without changing business behavior.
- `ACC-C-001`: Future model behavior changes update governance registries in the same run.
- `ACC-D-001`: Validator and focused tests pass in the local environment.
- `ACC-E-001`: Required CI mode blocks Serenity failures while advisory projects remain non-blocking.
- `ACC-S3PCT03`: Serenity OpenD auto-wake ownership, package atomicity, launchd tick wrapper, and close-cleanup contracts are verified with mocked or temporary local evidence and no real external side effects.

## Release Gates

- Current governance gate: `GOV-REVIEW6-B-SEMANTIC-EXTRACT`.
- Required promotion gate: `TASK-E-001` after `GOV-G3-SERENITY-VERIFY-001` passes.

## Rollback

Rollback is documentation-only for this migration:

1. Remove `Serenity-Alipay/docs/governance/`.
2. Restore `Serenity-Alipay/README.md`, `VERSION`, `CHANGELOG.md`, `模型参数文件`, `开发记录`, and `功能清单` from pre-run state.
3. Confirm `git diff --name-only -- Serenity-Alipay` contains no `app/`, `tests/`, or data changes.
