# Project Governance Status

## Snapshot Metadata

- source_base_commit: `932446fd2154ac477ea0cb6862a60098b1e1ed55`
- source_tree_hash: `a661be1db22d99ff3afe6183ac1ae8f4c444be18`
- source_snapshot_hash: `sha256:247e33700f97a30d3d15a674ccf1e487115b15bcd47db56abd8a68b3e1978ea0`
- snapshot_event_time: `2026-06-22T00:24:25Z`
- generator_version: `3.0.0`
- final_commit_binding: `PRECOMMIT_TREE_BOUND_PENDING_CI_ATTESTATION`

## Current State

- Project: `Serenity-Alipay`
- Path: `Serenity-Alipay`
- Product version: `0.1.0`
- Phase/Gate: `B / GOV-REVIEW6-B-SEMANTIC-EXTRACT`
- Models/Formulas/Parameters total: `5 / 12 / 49`
- Active formulas/parameters: `12 / 49`
- Machine checked formulas/parameters: `12 / 49`

## Assurance

| Dimension | Status | Evidence |
|---|---|---|
| structural_completeness | `VERIFIED` | `scripts/validate_project_governance.py` |
| implementation_congruence | `VERIFIED` | `Serenity-Alipay/docs/governance/parameter_registry.csv, Serenity-Alipay/docs/governance/formula_registry.yaml` |
| parameter_source_quality | `VERIFIED` | `Serenity-Alipay/docs/governance/parameter_registry.csv` |
| empirical_validation | `UNVERIFIED` | `Serenity-Alipay/docs/governance/delivery_tasks.yaml` |
| operational_validation | `PARTIAL` | `Serenity-Alipay/docs/governance/development_events.jsonl` |
| delivery_evidence | `UNVERIFIED` | `Serenity-Alipay/docs/governance/delivery_tasks.yaml` |
| evidence_freshness | `PARTIAL` | `Serenity-Alipay/docs/governance/development_events.jsonl` |

## Delivery

- Readiness: `UNVERIFIED`
- Release gate: `GOV-REVIEW6-B-SEMANTIC-EXTRACT`
- Next executable task: `TASK-A-001`
- Pending/stale events: `4`
- Tree-bound events: `0`
- Commit-bound events: `0`
- Legacy unbound events: `3`
- Unresolved fact IDs: `2`
