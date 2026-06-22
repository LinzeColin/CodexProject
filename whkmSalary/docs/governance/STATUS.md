# Project Governance Status

## Snapshot Metadata

- source_base_commit: `738887de4034ad42d90347d0fa0db6c0f3ed966f`
- source_tree_hash: `6d67efb26a6ea61fd8b05706dbb3eb2f1d34ab9f`
- source_snapshot_hash: `sha256:5ec80ab3b83ec9c6796f63f15f2fd519fc3f25e29790035bef6a2c688211f738`
- snapshot_event_time: `2026-06-22T00:24:25Z`
- generator_version: `4.0.0`
- final_commit_binding: `PRECOMMIT_TREE_BOUND_PENDING_CI_ATTESTATION`

## Current State

- Project: `whkmSalary`
- Path: `whkmSalary`
- Product version: `0.0.0`
- Phase/Gate: `B / GOV-SEMANTIC-WHKM-in-progress`
- Models/Formulas/Parameters total: `2 / 10 / 80`
- Active formulas/parameters: `10 / 80`
- Machine checked formulas/parameters: `9 / 78`

## Assurance

| Dimension | Status | Evidence |
|---|---|---|
| structural_completeness | `VERIFIED` | `scripts/validate_project_governance.py` |
| implementation_congruence | `PARTIAL` | `whkmSalary/docs/governance/parameter_registry.csv, whkmSalary/docs/governance/formula_registry.yaml` |
| parameter_source_quality | `PARTIAL` | `whkmSalary/docs/governance/parameter_registry.csv` |
| methodological_rationale | `UNVERIFIED` | `whkmSalary/docs/governance/MODEL_SPEC.md` |
| empirical_validation | `UNVERIFIED` | `whkmSalary/docs/governance/delivery_tasks.yaml` |
| operational_validation | `FAILED` | `whkmSalary/docs/governance/development_events.jsonl` |
| delivery_evidence | `FAILED` | `whkmSalary/docs/governance/delivery_tasks.yaml` |
| evidence_freshness | `PARTIAL` | `whkmSalary/docs/governance/development_events.jsonl` |

## Delivery

- Readiness: `FAILED`
- Release gate: `GOV-SEMANTIC-WHKM-in-progress`
- Next executable task: `TASK-WHKM-B-001`
- Pending/stale events: `4`
- Tree-bound events: `0`
- Commit-bound events: `0`
- Legacy unbound events: `4`
- Unresolved fact IDs: `7`
