# Project Governance Status

## Snapshot Metadata

- source_base_commit: `738887de4034ad42d90347d0fa0db6c0f3ed966f`
- source_tree_hash: `6d67efb26a6ea61fd8b05706dbb3eb2f1d34ab9f`
- source_snapshot_hash: `sha256:184e4e88248ec83e432778047b206bd4715ba5bba9256055e6d7453d5988b9b0`
- snapshot_event_time: `2026-06-22T22:30:00Z`
- generator_version: `4.0.0`
- final_commit_binding: `PRECOMMIT_TREE_BOUND_PENDING_CI_ATTESTATION`

## Current State

- Project: `EEI`
- Path: `EEI`
- Product version: `0.1.0`
- Phase/Gate: `C / TASK-T1301-A202-PUBLICATION-OPERATION-LOG-AUDIT-IN-PROGRESS`
- Models/Formulas/Parameters total: `12 / 12 / 68`
- Active formulas/parameters: `11 / 68`
- Machine checked formulas/parameters: `10 / 61`

## Assurance

| Dimension | Status | Evidence |
|---|---|---|
| structural_completeness | `VERIFIED` | `scripts/validate_project_governance.py` |
| implementation_congruence | `PARTIAL` | `EEI/docs/governance/parameter_registry.csv, EEI/docs/governance/formula_registry.yaml` |
| parameter_source_quality | `PARTIAL` | `EEI/docs/governance/parameter_registry.csv` |
| methodological_rationale | `UNVERIFIED` | `EEI/docs/governance/MODEL_SPEC.md` |
| empirical_validation | `PARTIAL` | `EEI/docs/governance/delivery_tasks.yaml` |
| operational_validation | `PARTIAL` | `EEI/docs/governance/development_events.jsonl` |
| delivery_evidence | `FAILED` | `EEI/docs/governance/delivery_tasks.yaml` |
| evidence_freshness | `PARTIAL` | `EEI/docs/governance/development_events.jsonl` |

## Delivery

- Readiness: `FAILED`
- Release gate: `TASK-T1301-A202-PUBLICATION-OPERATION-LOG-AUDIT-IN-PROGRESS`
- Next executable task: `TASK-T1301`
- Pending/stale events: `38`
- Tree-bound events: `0`
- Commit-bound events: `8`
- Legacy unbound events: `17`
- Unresolved fact IDs: `7`
