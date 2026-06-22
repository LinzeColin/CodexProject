# Project Governance Status

## Snapshot Metadata

- source_base_commit: `932446fd2154ac477ea0cb6862a60098b1e1ed55`
- source_tree_hash: `a661be1db22d99ff3afe6183ac1ae8f4c444be18`
- source_snapshot_hash: `sha256:87076d8e8f26202e52e3993847be5502d29af192ab38b127e4b149d1d1af5c79`
- snapshot_event_time: `2026-06-22T00:24:25Z`
- generator_version: `3.0.0`
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
| empirical_validation | `UNVERIFIED` | `whkmSalary/docs/governance/delivery_tasks.yaml` |
| operational_validation | `FAILED` | `whkmSalary/docs/governance/development_events.jsonl` |
| delivery_evidence | `FAILED` | `whkmSalary/docs/governance/delivery_tasks.yaml` |
| evidence_freshness | `PARTIAL` | `whkmSalary/docs/governance/development_events.jsonl` |

## Delivery

- Readiness: `FAILED`
- Release gate: `GOV-SEMANTIC-WHKM-in-progress`
- Next executable task: `GOV-SEMANTIC-WHKM-001`
- Pending/stale events: `4`
- Tree-bound events: `0`
- Commit-bound events: `0`
- Legacy unbound events: `4`
- Unresolved fact IDs: `7`
