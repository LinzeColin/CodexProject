# Project Governance Status

## Snapshot Metadata

- source_base_commit: `932446fd2154ac477ea0cb6862a60098b1e1ed55`
- source_tree_hash: `a661be1db22d99ff3afe6183ac1ae8f4c444be18`
- source_snapshot_hash: `sha256:267e808b46dce0d5d7d705e13fd3f01341ae2a8d35fcbc5453eae4ff1b2d763a`
- snapshot_event_time: `2026-06-22T00:24:25Z`
- generator_version: `3.0.0`
- final_commit_binding: `PRECOMMIT_TREE_BOUND_PENDING_CI_ATTESTATION`

## Current State

- Project: `FIFA`
- Path: `FIFA`
- Product version: `0.1.0`
- Phase/Gate: `B / GOV-SEMANTIC-FIFA-in-progress`
- Models/Formulas/Parameters total: `11 / 11 / 117`
- Active formulas/parameters: `10 / 108`
- Machine checked formulas/parameters: `10 / 91`

## Assurance

| Dimension | Status | Evidence |
|---|---|---|
| structural_completeness | `VERIFIED` | `scripts/validate_project_governance.py` |
| implementation_congruence | `PARTIAL` | `FIFA/docs/governance/parameter_registry.csv, FIFA/docs/governance/formula_registry.yaml` |
| parameter_source_quality | `PARTIAL` | `FIFA/docs/governance/parameter_registry.csv` |
| empirical_validation | `UNVERIFIED` | `FIFA/docs/governance/delivery_tasks.yaml` |
| operational_validation | `FAILED` | `FIFA/docs/governance/development_events.jsonl` |
| delivery_evidence | `UNVERIFIED` | `FIFA/docs/governance/delivery_tasks.yaml` |
| evidence_freshness | `PARTIAL` | `FIFA/docs/governance/development_events.jsonl` |

## Delivery

- Readiness: `UNVERIFIED`
- Release gate: `GOV-SEMANTIC-FIFA-in-progress`
- Next executable task: `GOV-SEMANTIC-FIFA-001`
- Pending/stale events: `4`
- Tree-bound events: `0`
- Commit-bound events: `4`
- Legacy unbound events: `3`
- Unresolved fact IDs: `6`
