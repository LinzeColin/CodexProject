# Project Governance Status

## Snapshot Metadata

- source_base_commit: `932446fd2154ac477ea0cb6862a60098b1e1ed55`
- source_tree_hash: `a661be1db22d99ff3afe6183ac1ae8f4c444be18`
- source_snapshot_hash: `sha256:ebd67bb1420c9586dbe3d7d6ccc8cdf09de8d3f4574b6d49ae499ed9bd058d25`
- snapshot_event_time: `2026-06-22T00:24:25Z`
- generator_version: `3.0.0`
- final_commit_binding: `PRECOMMIT_TREE_BOUND_PENDING_CI_ATTESTATION`

## Current State

- Project: `Alpha`
- Path: `Alpha`
- Product version: `0.1.0`
- Phase/Gate: `B / GOV-SEMANTIC-ALPHA-in-progress`
- Models/Formulas/Parameters total: `9 / 9 / 55`
- Active formulas/parameters: `9 / 55`
- Machine checked formulas/parameters: `9 / 42`

## Assurance

| Dimension | Status | Evidence |
|---|---|---|
| structural_completeness | `VERIFIED` | `scripts/validate_project_governance.py` |
| implementation_congruence | `PARTIAL` | `Alpha/docs/governance/parameter_registry.csv, Alpha/docs/governance/formula_registry.yaml` |
| parameter_source_quality | `PARTIAL` | `Alpha/docs/governance/parameter_registry.csv` |
| empirical_validation | `UNVERIFIED` | `Alpha/docs/governance/delivery_tasks.yaml` |
| operational_validation | `FAILED` | `Alpha/docs/governance/development_events.jsonl` |
| delivery_evidence | `FAILED` | `Alpha/docs/governance/delivery_tasks.yaml` |
| evidence_freshness | `PARTIAL` | `Alpha/docs/governance/development_events.jsonl` |

## Delivery

- Readiness: `FAILED`
- Release gate: `GOV-SEMANTIC-ALPHA-in-progress`
- Next executable task: `GOV-SEMANTIC-ALPHA-001`
- Pending/stale events: `5`
- Tree-bound events: `0`
- Commit-bound events: `0`
- Legacy unbound events: `5`
- Unresolved fact IDs: `5`
