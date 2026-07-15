# Project Governance Status

## Snapshot Metadata

- source_base_commit: `0c789bdb49ed11c6924222d2229bd5ca9e7ef158`
- source_tree_hash: `356fcd0bb5d3b892b331d28351fe9e99a64c8457`
- source_snapshot_hash: `sha256:e20879d7f6547ffaf092cf475f947dfe516e50317c4b320803c116f5a93dd52f`
- snapshot_event_time: `2026-07-15T12:48:26+10:00`
- generator_version: `4.0.1`
- final_commit_binding: `PRECOMMIT_TREE_BOUND_PENDING_CI_ATTESTATION`

## Current State

- Project: `EEI`
- Path: `EEI`
- Product version: `0.1.0`
- Phase/Gate: `D / A209_EVIDENCE_READY_FOR_RELEASE_MANAGER_REVIEW`
- Models/Formulas/Parameters total: `12 / 12 / 93`
- Active formulas/parameters: `11 / 93`
- Machine checked formulas/parameters: `11 / 93`

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
- Release gate: `A209_EVIDENCE_READY_FOR_RELEASE_MANAGER_REVIEW`
- Next executable task: `TASK-T1301`
- Pending/stale events: `116`
- Tree-bound events: `0`
- Commit-bound events: `23`
- Legacy unbound events: `19`
- Unresolved fact IDs: `6`
