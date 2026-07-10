# Project Governance Status

## Snapshot Metadata

- source_base_commit: `42abfd60a49d0505984364c2e41efbbdcc73e9ac`
- source_tree_hash: `356fcd0bb5d3b892b331d28351fe9e99a64c8457`
- source_snapshot_hash: `sha256:6f4c7043b199dcd781737a24c221d8460ba78785de94e4b37cdaee1ee0d46a39`
- snapshot_event_time: `2026-07-10T18:53:59+10:00`
- generator_version: `4.0.1`
- final_commit_binding: `COMMIT_BOUND:42abfd60a49d0505984364c2e41efbbdcc73e9ac`

## Current State

- Project: `EEI`
- Path: `EEI`
- Product version: `0.1.0`
- Phase/Gate: `CF-L2 / ACC-CF-L2-20260710-BLOCKED-BY-WORKERS-AUTH`
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
- Release gate: `ACC-CF-L2-20260710-BLOCKED-BY-WORKERS-AUTH`
- Next executable task: `CF-L2-20260710`
- Pending/stale events: `114`
- Tree-bound events: `0`
- Commit-bound events: `20`
- Legacy unbound events: `19`
- Unresolved fact IDs: `6`
