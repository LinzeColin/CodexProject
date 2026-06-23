# Roadmap

## 摘要

- project_id: `<PROJECT_ID>`
- product_version: `<VERSION>`
- current_stage: `<STAGE_ID> - <STAGE_NAME>`
- current_phase: `<PHASE_ID> - <PHASE_NAME>`
- current_task: `<TASK_ID> - <TASK_NAME>`
- total_active_task_hours: `<TOTAL_ACTIVE_TASK_HOURS>`
- completed_task_hours: `<COMPLETED_TASK_HOURS>`
- progress: `<PERCENT>%`
- blockers: `<BLOCKERS_OR_NONE>`
- next_gate: `<GATE_ID> - <GATE_NAME>`
- next_unique_task: `<TASK_ID> - <TASK_NAME>`
- evidence_status: `<VERIFIED|PARTIAL|UNKNOWN>`

## 计算规则

- structure: `Stage -> Phase -> Task`
- task_pct: `task_hours / total_active_task_hours * 100`
- phase_hours: `sum(child task hours)`
- stage_hours: `sum(descendant task hours)`
- progress: `completed task hours / total_active_task_hours * 100`
- display_percent_precision: `2 decimal places`
- validation_tolerance: `0.1 percentage-point`

## Stages

### `<STAGE_ID> <STAGE_NAME>`

| 字段 | 值 |
|---|---|
| objective | `<OBJECTIVE>` |
| stop_conditions | `<STOP_CONDITIONS>` |
| stop_gate | `<STOP_GATE>` |
| pass_criteria | `<PASS_CRITERIA>` |
| failure_action | `<FAILURE_ACTION>` |
| approver | `<APPROVER>` |
| child_count | `<CHILD_COUNT>` |
| derived_hours | `<DERIVED_HOURS>` |
| derived_percent | `<DERIVED_PERCENT>%` |
| evidence_refs | `<EVIDENCE_REFS>` |

## Phases

### `<PHASE_ID> <PHASE_NAME>`

| 字段 | 值 |
|---|---|
| parent_stage | `<STAGE_ID>` |
| person_goal | `<PERSON_GOAL>` |
| stop_conditions | `<STOP_CONDITIONS>` |
| stop_gate | `<STOP_GATE>` |
| pass_criteria | `<PASS_CRITERIA>` |
| failure_action | `<FAILURE_ACTION>` |
| child_count | `<CHILD_COUNT>` |
| derived_hours | `<DERIVED_HOURS>` |
| derived_percent | `<DERIVED_PERCENT>%` |
| evidence_refs | `<EVIDENCE_REFS>` |

## Tasks

### `<TASK_ID> <TASK_NAME>`

| 字段 | 值 |
|---|---|
| parent_phase | `<PHASE_ID>` |
| objective | `<OBJECTIVE>` |
| status | `<proposed|planned|ready|in_progress|blocked|completed|rejected|deprecated>` |
| estimate_hours | `<HOURS>` |
| dependencies | `<TASK_IDS_OR_NONE>` |
| acceptance_ids | `<ACCEPTANCE_IDS>` |
| test_commands | `<ACTUAL_OR_PLANNED_COMMANDS>` |
| test_results | `<RESULTS_OR_PENDING_REASON>` |
| evidence_refs | `<EVIDENCE_REFS>` |
| risks | `<RISKS_OR_NONE>` |
| rollback | `<ROLLBACK>` |
| current_result | `<CURRENT_RESULT>` |
| completion_version_or_commit | `<VERSION_OR_COMMIT_OR_NOT_COMPLETED>` |

## Stop Gates

| Gate | Scope | Pass Criteria | Evidence | Failure Action | Approver |
|---|---|---|---|---|---|
| `<GATE_ID>` | `<STAGE_OR_PHASE>` | `<PASS_CRITERIA>` | `<EVIDENCE_REFS>` | `<FAILURE_ACTION>` | `<APPROVER>` |

## Acceptance And Evidence

| Acceptance ID | Task | Required Evidence | Actual Evidence | Status |
|---|---|---|---|---|
| `<ACC-ID>` | `<TASK_ID>` | `<REQUIRED_EVIDENCE>` | `<ACTUAL_EVIDENCE>` | `<STATUS>` |
