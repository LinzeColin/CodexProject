# Project Governance Status

## Snapshot Metadata

- source_base_commit: `0c666014e86d5694f83508007335f92296cf0bff`
- source_tree_hash: `356fcd0bb5d3b892b331d28351fe9e99a64c8457`
- source_snapshot_hash: `sha256:2fe23aacfa978490c71ea1aabb4bb06839c0fd21db37248108e8f0c85923a382`
- snapshot_event_time: `2026-07-15T12:59:11+10:00`
- generator_version: `4.0.1`
- final_commit_binding: `COMMIT_BOUND:0c666014e86d5694f83508007335f92296cf0bff`

## Current State

- Project: `EEI`
- Path: `EEI`
- Product version: `0.1.0`
- Phase/Gate: `D / A205_CI_REPRODUCIBILITY_VERIFIED_A209_GATE_OPEN`
- Models/Formulas/Parameters total: `12 / 12 / 93`
- Active formulas/parameters: `11 / 93`
- Machine checked formulas/parameters: `11 / 93`

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
- Release gate: `A205_CI_REPRODUCIBILITY_VERIFIED_A209_GATE_OPEN`
- Next executable task: `TASK-T1301`
- Pending/stale events: `115`
- Tree-bound events: `0`
- Commit-bound events: `25`
- Legacy unbound events: `19`
- Unresolved fact IDs: `6`
