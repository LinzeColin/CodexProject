# Project Governance Status

## Snapshot Metadata

- source_base_commit: `fd66c8a0a6af645fc955f2e9695f32a7cca089bf`
- source_tree_hash: `00e27599461403192b998e8f9a3f7f0e769e5d8f`
- source_snapshot_hash: `sha256:7e0d8296ea40acfca3185cb63edf522b6f405da61aae12f3e1caf6ca6db523a0`
- snapshot_event_time: `2026-06-27T18:08:00+10:00`
- generator_version: `4.0.0`
- final_commit_binding: `PRECOMMIT_TREE_BOUND_PENDING_CI_ATTESTATION`

## Current State

- Project: `EEI`
- Path: `EEI`
- Product version: `0.1.0`
- Phase/Gate: `D / TASK-T1307-A209-BROWSER-SLICE-REUSE`
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
- Release gate: `TASK-T1307-A209-BROWSER-SLICE-REUSE`
- Next executable task: `TASK-T1301`
- Pending/stale events: `110`
- Tree-bound events: `0`
- Commit-bound events: `18`
- Legacy unbound events: `19`
- Unresolved fact IDs: `6`
