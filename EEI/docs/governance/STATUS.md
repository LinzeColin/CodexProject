# Project Governance Status

## Snapshot Metadata

- source_base_commit: `0175e2b9616fa77d50ae06bcf0cd68ce9d015f7d`
- source_tree_hash: `356fcd0bb5d3b892b331d28351fe9e99a64c8457`
- source_snapshot_hash: `sha256:0aca7308792067310a98a33c5200f7a551e034e4565dcfa250be586487fa1866`
- snapshot_event_time: `2026-06-27T19:13:36+10:00`
- generator_version: `4.0.0`
- final_commit_binding: `PRECOMMIT_TREE_BOUND_PENDING_CI_ATTESTATION`

## Current State

- Project: `EEI`
- Path: `EEI`
- Product version: `0.1.0`
- Phase/Gate: `D / TASK-T1301-A202-LIVE-OFFICIAL-CAPTURE-FRESHNESS`
- Models/Formulas/Parameters total: `12 / 12 / 90`
- Active formulas/parameters: `11 / 90`
- Machine checked formulas/parameters: `11 / 90`

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
- Release gate: `TASK-T1301-A202-LIVE-OFFICIAL-CAPTURE-FRESHNESS`
- Next executable task: `TASK-T1301`
- Pending/stale events: `112`
- Tree-bound events: `0`
- Commit-bound events: `18`
- Legacy unbound events: `19`
- Unresolved fact IDs: `6`
