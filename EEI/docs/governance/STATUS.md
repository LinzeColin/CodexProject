# Project Governance Status

## Snapshot Metadata

- source_base_commit: `047b4094d56fb7b3162b24265501e985690296f0`
- source_tree_hash: `8737d055c5c24cf2e160003744e375aba6f6145b`
- source_snapshot_hash: `sha256:53fa71e2df920dd3ab836bcab904164eb33248d2522e5ece7b0a96cfd5060c1b`
- snapshot_event_time: `2026-06-26T21:58:00+10:00`
- generator_version: `4.0.0`
- final_commit_binding: `PRECOMMIT_TREE_BOUND_PENDING_CI_ATTESTATION`

## Current State

- Project: `EEI`
- Path: `EEI`
- Product version: `0.1.0`
- Phase/Gate: `D / TASK-T1307-A209-RECOVERY-AUTHORIZATION-PACKET`
- Models/Formulas/Parameters total: `12 / 12 / 92`
- Active formulas/parameters: `11 / 92`
- Machine checked formulas/parameters: `11 / 92`

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
- Release gate: `TASK-T1307-A209-RECOVERY-AUTHORIZATION-PACKET`
- Next executable task: `TASK-T1301`
- Pending/stale events: `123`
- Tree-bound events: `0`
- Commit-bound events: `21`
- Legacy unbound events: `19`
- Unresolved fact IDs: `8`
