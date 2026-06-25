# Project Governance Status

## Snapshot Metadata

- source_base_commit: `12df22b6347fd881d42545afe387ac9e41e56fb4`
- source_tree_hash: `00e27599461403192b998e8f9a3f7f0e769e5d8f`
- source_snapshot_hash: `sha256:7c54a3c5bccbba28955e4bbf5c06815c44996965b66c98fe91c7f1069d328342`
- snapshot_event_time: `2026-06-25T19:26:47Z`
- generator_version: `4.0.0`
- final_commit_binding: `CI_ATTESTED:236d25354db7d8f9774d1f91981ae30d69b0234e https://github.com/LinzeColin/CodexProject/actions/runs/28194420774`

## Current State

- Project: `EEI`
- Path: `EEI`
- Product version: `0.1.0`
- Phase/Gate: `C / TASK-T1301-A202-OPERATOR-REVIEW-PACKET-FRESHNESS-CI-ATTESTED-RELEASE-BLOCKED`
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
- Release gate: `TASK-T1301-A202-OPERATOR-REVIEW-PACKET-FRESHNESS-CI-ATTESTED-RELEASE-BLOCKED`
- Next executable task: `TASK-T1301`
- Pending/stale events: `100`
- Tree-bound events: `0`
- Commit-bound events: `18`
- Legacy unbound events: `19`
- Unresolved fact IDs: `5`
