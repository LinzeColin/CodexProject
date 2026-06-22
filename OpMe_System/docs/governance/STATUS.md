# Project Governance Status

## Snapshot Metadata

- source_base_commit: `932446fd2154ac477ea0cb6862a60098b1e1ed55`
- source_tree_hash: `a661be1db22d99ff3afe6183ac1ae8f4c444be18`
- source_snapshot_hash: `sha256:5668b5998e2fc8db196938d3fd981a2a2b91bd7579dba5b6f4d19da6991aac2d`
- snapshot_event_time: `2026-06-22T00:24:25Z`
- generator_version: `3.0.0`
- final_commit_binding: `PRECOMMIT_TREE_BOUND_PENDING_CI_ATTESTATION`

## Current State

- Project: `OpMe_System`
- Path: `OpMe_System`
- Product version: `1.0.0`
- Phase/Gate: `B / GOV-SEMANTIC-OPME-in-progress`
- Models/Formulas/Parameters total: `7 / 7 / 49`
- Active formulas/parameters: `7 / 49`
- Machine checked formulas/parameters: `7 / 49`

## Assurance

| Dimension | Status | Evidence |
|---|---|---|
| structural_completeness | `VERIFIED` | `scripts/validate_project_governance.py` |
| implementation_congruence | `VERIFIED` | `OpMe_System/docs/governance/parameter_registry.csv, OpMe_System/docs/governance/formula_registry.yaml` |
| parameter_source_quality | `VERIFIED` | `OpMe_System/docs/governance/parameter_registry.csv` |
| empirical_validation | `UNVERIFIED` | `OpMe_System/docs/governance/delivery_tasks.yaml` |
| operational_validation | `FAILED` | `OpMe_System/docs/governance/development_events.jsonl` |
| delivery_evidence | `UNVERIFIED` | `OpMe_System/docs/governance/delivery_tasks.yaml` |
| evidence_freshness | `PARTIAL` | `OpMe_System/docs/governance/development_events.jsonl` |

## Delivery

- Readiness: `UNVERIFIED`
- Release gate: `GOV-SEMANTIC-OPME-in-progress`
- Next executable task: `GOV-SEMANTIC-OPME-001`
- Pending/stale events: `6`
- Tree-bound events: `0`
- Commit-bound events: `0`
- Legacy unbound events: `6`
- Unresolved fact IDs: `3`
