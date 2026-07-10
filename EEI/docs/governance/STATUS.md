# Project Governance Status

## Snapshot Metadata

- source_base_commit: `ed0fe3a3e8f2f0f46d0f4f442c23fed5ed093935`
- source_tree_hash: `356fcd0bb5d3b892b331d28351fe9e99a64c8457`
- source_snapshot_hash: `sha256:56124c632cd26ffba6d80a5fe301291a6d4ea499157244616f8ef00bb65346d8`
- snapshot_event_time: `2026-07-10T19:46:00+10:00`
- generator_version: `4.0.1`
- final_commit_binding: `COMMIT_BOUND:ed0fe3a3e8f2f0f46d0f4f442c23fed5ed093935`

## Current State

- Project: `EEI`
- Path: `EEI`
- Product version: `0.1.0`
- Phase/Gate: `CF-L2 / ACC-CF-L2-20260710-PASSED`
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
- Release gate: `ACC-CF-L2-20260710-PASSED`
- Next executable task: `TASK-T1301`
- Pending/stale events: `115`
- Tree-bound events: `0`
- Commit-bound events: `21`
- Legacy unbound events: `19`
- Unresolved fact IDs: `6`
