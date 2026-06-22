# Project Governance Status

## Snapshot Metadata

- source_base_commit: `932446fd2154ac477ea0cb6862a60098b1e1ed55`
- source_tree_hash: `a661be1db22d99ff3afe6183ac1ae8f4c444be18`
- source_snapshot_hash: `sha256:b2b976ab6befc216f0344a19176a2a356642c131c48921f075bc0d0637e6daeb`
- snapshot_event_time: `2026-06-22T00:24:25Z`
- generator_version: `3.0.0`
- final_commit_binding: `PRECOMMIT_TREE_BOUND_PENDING_CI_ATTESTATION`

## Current State

- Project: `PFI_BIG_DATA_SIMULATOR`
- Path: `PFI/大数据模拟器`
- Product version: `0.1.0`
- Phase/Gate: `B / GOV-SEMANTIC-PFI-in-progress`
- Models/Formulas/Parameters total: `15 / 15 / 213`
- Active formulas/parameters: `15 / 213`
- Machine checked formulas/parameters: `15 / 211`

## Assurance

| Dimension | Status | Evidence |
|---|---|---|
| structural_completeness | `VERIFIED` | `scripts/validate_project_governance.py` |
| implementation_congruence | `PARTIAL` | `PFI/大数据模拟器/docs/governance/parameter_registry.csv, PFI/大数据模拟器/docs/governance/formula_registry.yaml` |
| parameter_source_quality | `PARTIAL` | `PFI/大数据模拟器/docs/governance/parameter_registry.csv` |
| empirical_validation | `UNVERIFIED` | `PFI/大数据模拟器/docs/governance/delivery_tasks.yaml` |
| operational_validation | `FAILED` | `PFI/大数据模拟器/docs/governance/development_events.jsonl` |
| delivery_evidence | `UNVERIFIED` | `PFI/大数据模拟器/docs/governance/delivery_tasks.yaml` |
| evidence_freshness | `PARTIAL` | `PFI/大数据模拟器/docs/governance/development_events.jsonl` |

## Delivery

- Readiness: `UNVERIFIED`
- Release gate: `GOV-SEMANTIC-PFI-in-progress`
- Next executable task: `GOV-SEMANTIC-PFI-001`
- Pending/stale events: `4`
- Tree-bound events: `0`
- Commit-bound events: `0`
- Legacy unbound events: `3`
- Unresolved fact IDs: `14`
