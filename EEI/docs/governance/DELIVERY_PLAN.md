# DELIVERY_PLAN

Project: `EEI`
Governance spec version: `1.0.0`

## Canonical Sources

- Task registry: `delivery_tasks.yaml`
- Traceability: `TRACEABILITY_MATRIX.csv`
- Legacy evidence inputs: `data/task_backlog.csv`, `data/acceptance_matrix.csv`, `data/acceptance_traceability.csv`, `data/risk_register.csv`, `data/release_gate_catalog.csv`

## Task Summary

machine_summary:

- task_count: 128
- acceptance_count: 192
- completed_task_count: 52
- planned_task_count: 69
- in_progress_task_count: 6
- blocked_task_count: 1

Counts are generated from canonical machine registries. Historical Markdown files are compatibility indexes only.

## Phase Map

| Phase | Purpose | Exit Gate |
|---|---|---|
| A | Governance baseline and evidence repair | Validator passes for EEI |
| B | Model and data specification hardening | Unknown model/parameter tasks closed or explicitly deferred |
| C | Runtime implementation tracking | Product task evidence remains traceable |
| D | Verification and release hardening | Required CI can be enabled without advisory drift |
| E | Operation and maintenance | Governance events remain append-only |

## Delivery Tasks

Machine source: `delivery_tasks.yaml`. Completed tasks are only marked `completed` when legacy DONE status has DONE acceptance traceability evidence.

| Status | Count | Evidence |
|---|---:|---|
| completed | 52 | DONE task plus DONE acceptance trace rows |
| in_progress | 6 | T1301/A202 source/legal/owner clearance pending; T1302/A203 production-approved edges pending; T1303/A204-A205 refresh/wake/soak evidence pending; T1307/A209 24h operator soak running as background gate with heartbeat `58/288` PASS and watchdog PID `62233`; T1309/A210 formal brand clearance pending |
| planned | 69 | Legacy NOT STARTED tasks |

## Release Gates

- Gate count from legacy catalog: 10 (machine evidence: `data/release_gate_catalog.csv`).
- Current governance gate: `TASK-T904-A026-A027-PRODUCTION-GOLD-INTAKE-IN-PROGRESS`.
