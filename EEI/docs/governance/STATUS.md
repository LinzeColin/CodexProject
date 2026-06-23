# Project Governance Status

## Snapshot Metadata

- source_base_commit: `738887de4034ad42d90347d0fa0db6c0f3ed966f`
- source_tree_hash: `6d67efb26a6ea61fd8b05706dbb3eb2f1d34ab9f`
- source_snapshot_hash: `sha256:075a0e30f6373607cd845134cdf957ae8af897ff4465d7813b9ab7a45d5b65a1`
- snapshot_event_time: `2026-06-23T04:05:00Z`
- generator_version: `4.0.0`
- final_commit_binding: `PRECOMMIT_TREE_BOUND_PENDING_CI_ATTESTATION`

## Current State

- Project: `EEI`
- Path: `EEI`
- Product version: `0.1.0`
- Phase/Gate: `C / TASK-T904-A026-A027-PRODUCTION-GOLD-INTAKE-IN-PROGRESS`
- Models/Formulas/Parameters total: `12 / 12 / 68`
- Active formulas/parameters: `11 / 68`
- Machine checked formulas/parameters: `11 / 68`

## Assurance

| Dimension | Status | Evidence |
|---|---|---|
| structural_completeness | `VERIFIED` | `scripts/validate_project_governance.py` |
| implementation_congruence | `VERIFIED` | `EEI/docs/governance/parameter_registry.csv, EEI/docs/governance/formula_registry.yaml` |
| parameter_source_quality | `VERIFIED` | `EEI/docs/governance/parameter_registry.csv` |
| methodological_rationale | `UNVERIFIED` | `EEI/docs/governance/MODEL_SPEC.md` |
| empirical_validation | `PARTIAL` | `EEI/docs/governance/delivery_tasks.yaml` |
| operational_validation | `PARTIAL` | `EEI/docs/governance/development_events.jsonl` |
| delivery_evidence | `FAILED` | `EEI/docs/governance/delivery_tasks.yaml` |
| evidence_freshness | `PARTIAL` | `EEI/docs/governance/development_events.jsonl` |

## Delivery

- Readiness: `FAILED`
- Release gate: `TASK-T904-A026-A027-PRODUCTION-GOLD-INTAKE-IN-PROGRESS`
- Next executable task: `TASK-T1301`
- Pending/stale events: `43`
- Tree-bound events: `0`
- Commit-bound events: `13`
- Legacy unbound events: `17`
- Unresolved fact IDs: `3`

## A209 Background Soak Update

- T1307/A209 24h operator soak is running as background production-stability evidence and remains non-blocking for other MVP development.
- Latest local checkpoint after current supervisor check: operator PID `12478`, `44/288` windows PASS, generated at `2026-06-23T14:19:36Z`; detached watchdog PID `62233` is running with `cycles=300` and `interval_seconds=300`.
- Monitor contract: `EEI/scripts/monitor_operator_soak.py` reports `release_gate_closed_by_monitor=false`; supervisor contract `EEI/scripts/supervise_operator_soak.py` reports `release_gate_closed_by_supervisor=false`, observes the live PID without double-starting, dry-runs recovery by default, and is included in clean-room release packaging. Watchdog contract `EEI/scripts/watch_operator_soak.py` reports `release_gate_closed_by_watchdog=false`, resumes only paused successful checkpoints when launched with `--execute --auto-resume`, and reports stale live PIDs without killing them. A209 remains `IN_PROGRESS` until full 24h summary and checkpoint evidence validate.

## T1303 Model Config Apply Update

- `scripts/apply_model_config.py` is now a fail-closed A204/A205 operator entrypoint: `--dry-run` emits hash-bound preview evidence without writes; `--execute` requires PostgreSQL and delegates draft creation, transactional activation and score recompute enqueue to `DomainRepository`.
- `artifacts/model_config_import_preview.json` records `release_gate_closed_by_apply_model_config=false`; A204/A205 remain `IN_PROGRESS` until final release-manager activation has real A202, A026/A027, A209 and A210 gate evidence.
