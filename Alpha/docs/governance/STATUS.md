# Project Governance Status

## Snapshot Metadata

- source_base_commit: `738887de4034ad42d90347d0fa0db6c0f3ed966f`
- source_tree_hash: `6d67efb26a6ea61fd8b05706dbb3eb2f1d34ab9f`
- source_snapshot_hash: `sha256:29f122fad6497014bb26f65ef7488255d0735cb560e92fa1359a98a0db415737`
- snapshot_event_time: `2026-06-24T00:00:00+10:00`
- generator_version: `4.0.0`
- final_commit_binding: `PRECOMMIT_TREE_BOUND_PENDING_CI_ATTESTATION`

## Current State

- Project: `Alpha`
- Path: `Alpha`
- Product version: `0.1.0`
- Phase/Gate: `S3PB / S3PB-GATE-complete-technical`
- Models/Formulas/Parameters total: `9 / 9 / 55`
- Active formulas/parameters: `9 / 55`
- Machine checked formulas/parameters: `9 / 42`

## Assurance

| Dimension | Status | Evidence |
|---|---|---|
| structural_completeness | `VERIFIED` | `scripts/validate_project_governance.py` |
| implementation_congruence | `PARTIAL` | `Alpha/docs/governance/parameter_registry.csv, Alpha/docs/governance/formula_registry.yaml` |
| parameter_source_quality | `PARTIAL` | `Alpha/docs/governance/parameter_registry.csv` |
| methodological_rationale | `UNVERIFIED` | `Alpha/docs/governance/MODEL_SPEC.md` |
| empirical_validation | `UNVERIFIED` | `Alpha/docs/governance/delivery_tasks.yaml` |
| operational_validation | `FAILED` | `Alpha/docs/governance/development_events.jsonl` |
| delivery_evidence | `FAILED` | `Alpha/docs/governance/delivery_tasks.yaml` |
| evidence_freshness | `PARTIAL` | `Alpha/docs/governance/development_events.jsonl` |

## Delivery

- Readiness: `FAILED`
- Release gate: `S3PB-GATE-complete-technical`
- Next executable task: `TASK-ALPHA-B-001`
- Pending/stale events: `8`
- Tree-bound events: `3`
- Commit-bound events: `1`
- Legacy unbound events: `5`
- Unresolved fact IDs: `5`
