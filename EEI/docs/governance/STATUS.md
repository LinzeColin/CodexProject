# Project Governance Status

## Snapshot Metadata

- source_base_commit: `12df22b6347fd881d42545afe387ac9e41e56fb4`
- source_tree_hash: `00e27599461403192b998e8f9a3f7f0e769e5d8f`
- source_snapshot_hash: `sha256:a68e5590179b962bdfef5a8b90bbf2e68f6fea1c090f722e6bef50d9438f33fb`
- snapshot_event_time: `2026-06-25T18:43:05Z`
- generator_version: `4.0.0`
- final_commit_binding: `PRECOMMIT_TREE_BOUND_PENDING_CI_ATTESTATION`

## Current State

- Project: `EEI`
- Path: `EEI`
- Product version: `0.1.0`
- Phase/Gate: `C / TASK-T1301-A202-OPERATOR-REVIEW-PACKET-FRESHNESS-REPAIRED-RELEASE-BLOCKED`
- Models/Formulas/Parameters total: `12 / 12 / 88`
- Active formulas/parameters: `11 / 88`
- Machine checked formulas/parameters: `11 / 88`

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
- Release gate: `TASK-T1301-A202-OPERATOR-REVIEW-PACKET-FRESHNESS-REPAIRED-RELEASE-BLOCKED`
- Next executable task: `TASK-T1301`
- Pending/stale events: `100`
- Tree-bound events: `0`
- Commit-bound events: `17`
- Legacy unbound events: `19`
- Unresolved fact IDs: `5`
