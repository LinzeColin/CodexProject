# Project Governance Status

## Snapshot Metadata

- source_base_commit: `ed0fe3a3e8f2f0f46d0f4f442c23fed5ed093935`
- source_tree_hash: `5f05ad339e9519bd5981b54e788f0dbeefbcac9c`
- source_snapshot_hash: `sha256:03ed8687b7d9a5a0c3710a7c246751260049e16c671b1e2d5a8855326b9ca16e`
- snapshot_event_time: `2026-07-10T19:46:00+10:00`
- generator_version: `4.0.1`
- final_commit_binding: `COMMIT_BOUND:ed0fe3a3e8f2f0f46d0f4f442c23fed5ed093935`

## Current State

- Project: `PFI`
- Path: `PFI`
- Product version: `v0.2.2 数据库治理 Stage 4`
- Phase/Gate: `CF-L2 / ACC-CF-L2-20260710-PASSED`
- Models/Formulas/Parameters total: `1 / 1 / 23`
- Active formulas/parameters: `1 / 23`
- Machine checked formulas/parameters: `0 / 0`

## Assurance

| Dimension | Status | Evidence |
|---|---|---|
| structural_completeness | `VERIFIED` | `scripts/validate_project_governance.py` |
| implementation_congruence | `PARTIAL` | `PFI/docs/governance/parameter_registry.csv, PFI/docs/governance/formula_registry.yaml` |
| parameter_source_quality | `PARTIAL` | `PFI/docs/governance/parameter_registry.csv` |
| methodological_rationale | `VERIFIED` | `PFI/docs/governance/MODEL_SPEC.md` |
| empirical_validation | `UNVERIFIED` | `PFI/docs/governance/delivery_tasks.yaml` |
| operational_validation | `UNVERIFIED` | `PFI/docs/governance/development_events.jsonl` |
| delivery_evidence | `FAILED` | `PFI/docs/governance/delivery_tasks.yaml` |
| evidence_freshness | `PARTIAL` | `PFI/docs/governance/development_events.jsonl` |

## Delivery

- Readiness: `FAILED`
- Release gate: `ACC-CF-L2-20260710-PASSED`
- Next executable task: `NONE`
- Pending/stale events: `8`
- Tree-bound events: `0`
- Commit-bound events: `3`
- Legacy unbound events: `6`
- Unresolved fact IDs: `2`
