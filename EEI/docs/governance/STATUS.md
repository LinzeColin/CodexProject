# Project Governance Status

## Snapshot Metadata

- source_base_commit: `932446fd2154ac477ea0cb6862a60098b1e1ed55`
- source_tree_hash: `a661be1db22d99ff3afe6183ac1ae8f4c444be18`
- source_snapshot_hash: `sha256:a3ce95e782fae9c5191da47dd2ec35180f12fc6073656e9f9d3eacb42d27a5de`
- snapshot_event_time: `2026-06-22T14:35:00+10:00`
- generator_version: `3.0.0`
- final_commit_binding: `PRECOMMIT_TREE_BOUND_PENDING_CI_ATTESTATION`

## Current State

- Project: `EEI`
- Path: `EEI`
- Product version: `0.1.0`
- Phase/Gate: `B / GOV-EEI-BINDING-CLASSIFICATION`
- Models/Formulas/Parameters total: `12 / 12 / 61`
- Active formulas/parameters: `11 / 61`
- Machine checked formulas/parameters: `10 / 54`

## Assurance

| Dimension | Status | Evidence |
|---|---|---|
| structural_completeness | `VERIFIED` | `scripts/validate_project_governance.py` |
| implementation_congruence | `PARTIAL` | `EEI/docs/governance/parameter_registry.csv, EEI/docs/governance/formula_registry.yaml` |
| parameter_source_quality | `PARTIAL` | `EEI/docs/governance/parameter_registry.csv` |
| empirical_validation | `PARTIAL` | `EEI/docs/governance/delivery_tasks.yaml` |
| operational_validation | `PARTIAL` | `EEI/docs/governance/development_events.jsonl` |
| delivery_evidence | `FAILED` | `EEI/docs/governance/delivery_tasks.yaml` |
| evidence_freshness | `PARTIAL` | `EEI/docs/governance/development_events.jsonl` |

## Delivery

- Readiness: `FAILED`
- Release gate: `GOV-EEI-BINDING-CLASSIFICATION`
- Next executable task: `TASK-T1301`
- Pending/stale events: `23`
- Tree-bound events: `0`
- Commit-bound events: `6`
- Legacy unbound events: `24`
- Unresolved fact IDs: `7`
