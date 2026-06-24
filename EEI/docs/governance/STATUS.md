# Project Governance Status

## Snapshot Metadata

- source_base_commit: `c34ca0785d612e0f8d1730de75f82772af468f85`
- source_tree_hash: `6d67efb26a6ea61fd8b05706dbb3eb2f1d34ab9f`
- source_snapshot_hash: `sha256:d322066ededba3eb1bd029bf31d97bda694ba0a27c46706f2cd400516f97367b`
- snapshot_event_time: `2026-06-24T21:21:40Z`
- generator_version: `4.0.0`
- final_commit_binding: `PRECOMMIT_TREE_BOUND_PENDING_CI_ATTESTATION`

## Current State

- Project: `EEI`
- Path: `EEI`
- Product version: `0.1.0`
- Phase/Gate: `C / TASK-T1302-T1308-A211-FRONTEND-HYDRATION-CI-REPAIR-PENDING-CI`
- Models/Formulas/Parameters total: `12 / 12 / 84`
- Active formulas/parameters: `11 / 84`
- Machine checked formulas/parameters: `11 / 84`

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
- Release gate: `TASK-T1302-T1308-A211-FRONTEND-HYDRATION-CI-REPAIR-PENDING-CI`
- Next executable task: `TASK-T1301`
- Pending/stale events: `80`
- Tree-bound events: `0`
- Commit-bound events: `14`
- Legacy unbound events: `19`
- Unresolved fact IDs: `3`
