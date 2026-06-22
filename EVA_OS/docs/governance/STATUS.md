# Project Governance Status

## Snapshot Metadata

- source_base_commit: `932446fd2154ac477ea0cb6862a60098b1e1ed55`
- source_tree_hash: `a661be1db22d99ff3afe6183ac1ae8f4c444be18`
- source_snapshot_hash: `sha256:5a35994864b903f11c70f98698d4ba2a5ad7d789ab6fa83d7e34f6aec668668b`
- snapshot_event_time: `2026-06-22T00:24:25Z`
- generator_version: `3.0.0`
- final_commit_binding: `PRECOMMIT_TREE_BOUND_PENDING_CI_ATTESTATION`

## Current State

- Project: `EVA_OS`
- Path: `EVA_OS`
- Product version: `0.1.0`
- Phase/Gate: `B / GOV-SEMANTIC-EVA-001-in-progress`
- Models/Formulas/Parameters total: `16 / 16 / 189`
- Active formulas/parameters: `16 / 189`
- Machine checked formulas/parameters: `16 / 52`

## Assurance

| Dimension | Status | Evidence |
|---|---|---|
| structural_completeness | `VERIFIED` | `scripts/validate_project_governance.py` |
| implementation_congruence | `PARTIAL` | `EVA_OS/docs/governance/parameter_registry.csv, EVA_OS/docs/governance/formula_registry.yaml` |
| parameter_source_quality | `PARTIAL` | `EVA_OS/docs/governance/parameter_registry.csv` |
| empirical_validation | `UNVERIFIED` | `EVA_OS/docs/governance/delivery_tasks.yaml` |
| operational_validation | `FAILED` | `EVA_OS/docs/governance/development_events.jsonl` |
| delivery_evidence | `FAILED` | `EVA_OS/docs/governance/delivery_tasks.yaml` |
| evidence_freshness | `PARTIAL` | `EVA_OS/docs/governance/development_events.jsonl` |

## Delivery

- Readiness: `FAILED`
- Release gate: `GOV-SEMANTIC-EVA-001-in-progress`
- Next executable task: `GOV-SEMANTIC-EVA-001`
- Pending/stale events: `4`
- Tree-bound events: `0`
- Commit-bound events: `0`
- Legacy unbound events: `3`
- Unresolved fact IDs: `12`
