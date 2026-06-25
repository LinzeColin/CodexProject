# Project Governance Status

## Snapshot Metadata

- source_base_commit: `12df22b6347fd881d42545afe387ac9e41e56fb4`
- source_tree_hash: `00e27599461403192b998e8f9a3f7f0e769e5d8f`
- source_snapshot_hash: `sha256:56771ab1961e7273f879c00e918268b940990f9d010935ce6f2502f095fcd463`
- snapshot_event_time: `2026-06-25T14:03:21Z`
- generator_version: `4.0.0`
- final_commit_binding: `PRECOMMIT_TREE_BOUND_PENDING_CI_ATTESTATION`

## Current State

- Project: `EEI`
- Path: `EEI`
- Product version: `0.1.0`
- Phase/Gate: `C / TASK-T1307-A209-OPERATOR-SOAK-HEARTBEAT-135-PENDING-CI`
- Models/Formulas/Parameters total: `12 / 12 / 87`
- Active formulas/parameters: `11 / 87`
- Machine checked formulas/parameters: `11 / 87`

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
- Release gate: `TASK-T1307-A209-OPERATOR-SOAK-HEARTBEAT-135-PENDING-CI`
- Next executable task: `TASK-T1301`
- Pending/stale events: `90`
- Tree-bound events: `0`
- Commit-bound events: `14`
- Legacy unbound events: `19`
- Unresolved fact IDs: `5`
