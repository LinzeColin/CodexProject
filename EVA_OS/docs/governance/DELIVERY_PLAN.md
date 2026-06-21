# EVA_OS Delivery Plan

- model_count: 16
- formula_count: 16
- parameter_count: 189
- task_count: 13

Machine task source of truth: `delivery_tasks.yaml`.

## Phase A Discovery And Baseline

- TASK-EVA-A-001: P10 read-only audit, completed with scoped code/test evidence.
- TASK-EVA-A-002: P11 governance migration, completed; project validator exit 0.
- TASK-EVA-A-003: P12 verification, completed; project validator exit 0 and focused executable subset 99 passed, with `tests/test_strategy_templates.py` blocked by missing local `docx` dependency.
- TASK-EVA-A-004: P13 promotion to required, completed; all-project validator exit 0 with only advisory warnings for unmigrated projects.

## Phase B Model And Data Specification

- TASK-EVA-B-001 through TASK-EVA-B-008: blocked calibration/source-rationale repairs for heuristic constants and thresholds.

## Acceptance

Completed tasks must have at least one Acceptance ID, actual test command, actual result and evidence reference in `delivery_tasks.yaml`. Planned or blocked tasks are not represented as completed evidence.
