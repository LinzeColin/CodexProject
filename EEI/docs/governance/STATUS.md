# Project Governance Status

## Snapshot Metadata

- source_base_commit: `2a9afde825a2819da337e27b16f31201d2150f3e`
- source_tree_hash: `9657d04d30d592c81ed3a9d6ffbd0deda0478c3c`
- source_snapshot_hash: `sha256:a723f6ef86547ac0f48486cbe0b962b05fb48815654a6bef8e6cb65a1011c216`
- snapshot_event_time: `2026-06-26T12:52:00+10:00`
- generator_version: `4.0.0`
- final_commit_binding: `CI_ATTESTED:2a9afde825a2819da337e27b16f31201d2150f3e Project Governance run 28213678625 job 83580117668; EEI validation run 28213678638 job 83580117632`

## Current State

- Project: `EEI`
- Path: `EEI`
- Product version: `0.1.0`
- Phase/Gate: `D / TASK-T904-A026-A027-GOLD-LABEL-SOURCE-BOUNDARY`
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
- Release gate: `TASK-T904-A026-A027-GOLD-LABEL-SOURCE-BOUNDARY`
- Next executable task: `TASK-T1301`
- Pending/stale events: `107`
- Tree-bound events: `0`
- Commit-bound events: `21`
- Legacy unbound events: `19`
- Unresolved fact IDs: `7`
