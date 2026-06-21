# PFI Big Data Simulator Delivery Plan

- model_count: 15
- formula_count: 15
- parameter_count: 213
- task_count: 15

Machine task source of truth: `delivery_tasks.yaml`.

## Phase A Discovery And Baseline

- TASK-PFI-A-001: P10 read-only audit, completed with scoped code/test evidence.
- TASK-PFI-A-002: P11 governance migration, completed; project validator exit 0.
- TASK-PFI-A-003: P12 verification, completed; focused tests `32 passed`.
- TASK-PFI-A-004: P13 promotion to required, completed; all-project validator exit 0 with only advisory warnings for unmigrated projects.

## Phase B Model And Data Specification

- TASK-PFI-B-001 through TASK-PFI-B-010: blocked calibration/source-rationale repairs for heuristic constants, thresholds, provider gates and score weights.

## Acceptance

Completed tasks must have at least one Acceptance ID, actual test command, actual result and evidence reference in `delivery_tasks.yaml`. Planned or blocked tasks are not represented as completed evidence.
