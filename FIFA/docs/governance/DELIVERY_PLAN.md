# FIFA Delivery Plan

fact_level: EXTRACTED
task_count: 9

This delivery plan uses `docs/governance/delivery_tasks.yaml` as the machine source of truth. Markdown is an explanatory layer only.

## Acceptance IDs

| Acceptance ID | Requirement | Evidence Status |
| --- | --- | --- |
| ACC-FIFA-001 | Governance baseline files exist with stable IDs for models, formulas, parameters, tasks, and traceability. | completed |
| ACC-FIFA-002 | Governance validator exits 0 for FIFA. | completed with `python3`; `python` binary is unavailable in this shell |
| ACC-FIFA-003 | Focused FIFA checks pass without changing business behavior. | completed; real-HOME full suite separately exposed missing external Downloads entry |
| ACC-FIFA-004 | Business code has no diff in this governance run. | pending final diff check |
| ACC-FIFA-005 | FIFA is promoted to `required` only after governance baseline files are valid. | completed |
| ACC-FIFA-006 | Heuristic thresholds have calibration/backtest evidence or remain explicitly linked to an open task. | planned |
| ACC-FIFA-007 | Curation maps, marker lists, expected artifacts, and manual fields have source rationale. | planned |
| ACC-FIFA-008 | Authorized raw recovery path is available without prohibited browser bypasses. | blocked |
| ACC-FIFA-009 | TT-001 manual Team Total rows pass import quality and hash gate. | blocked |
| ACC-FIFA-010 | Read-only My Bets private snapshot gate passes. | blocked |
| ACC-FIFA-011 | Manual overlay publish preflight passes with matching signature. | blocked |
| ACC-FIFA-012 | Recurring report generation is explicitly authorized and remains report-only. | blocked |
| ACC-FIFA-013 | Legacy softmax model status is explicitly retained, migrated, or retired. | planned |

## Phase A: Discovery and Baseline

- `TASK-FIFA-A-001`: Create first auditable governance baseline. Status: `completed`.

Acceptance: `ACC-FIFA-001` through `ACC-FIFA-005`.

## Phase B: Model and Data Specification

- `TASK-FIFA-B-001`: Collect calibration evidence for thresholds and gates. Status: `planned`.
- `TASK-FIFA-B-002`: Audit curation and marker-list rationale. Status: `planned`.

## Phase C: Implementation

- `TASK-FIFA-C-001`: Recover authorized raw data path. Status: `blocked`.
- `TASK-FIFA-C-002`: Complete TT-001 Team Total manual verification. Status: `blocked`.

## Phase D: Verification and Hardening

- `TASK-FIFA-D-001`: Obtain read-only private My Bets snapshot. Status: `blocked`.
- `TASK-FIFA-D-002`: Pass manual signature and formal publish preflight. Status: `blocked`.

## Phase E: Delivery and Operation

- `TASK-FIFA-E-001`: Authorize recurring report generation only after gates are ready. Status: `blocked`.
- `TASK-FIFA-E-002`: Decide legacy softmax model lifecycle. Status: `planned`.
