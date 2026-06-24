# Project Governance Status

## Snapshot Metadata

- source_base_commit: `d80785a099d1ff7f16798381c3716e8793b2ffae`
- source_tree_hash: `6d67efb26a6ea61fd8b05706dbb3eb2f1d34ab9f`
- source_snapshot_hash: `sha256:385ba409ac5a4f450e78cdf2eca5df1d6fd0020e9912ba6bc26135e347499a7c`
- snapshot_event_time: `2026-06-24T11:45:50Z`
- generator_version: `4.0.0`
- final_commit_binding: `PRECOMMIT_TREE_BOUND_PENDING_CI_ATTESTATION`

## Current State

- Project: `EEI`
- Path: `EEI`
- Product version: `0.1.0`
- Phase/Gate: `C / TASK-T904-A026-A027-PRODUCTION-GOLD-INTAKE-IN-PROGRESS`
- Models/Formulas/Parameters total: `12 / 12 / 82`
- Active formulas/parameters: `11 / 82`
- Machine checked formulas/parameters: `11 / 82`

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
- Pending/stale events: `79`
- Tree-bound events: `0`
- Commit-bound events: `14`
- Legacy unbound events: `18`
- Unresolved fact IDs: `3`
