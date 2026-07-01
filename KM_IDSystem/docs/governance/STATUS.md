# Project Governance Status

## Snapshot Metadata

- source_base_commit: `738887de4034ad42d90347d0fa0db6c0f3ed966f`
- source_tree_hash: `6d67efb26a6ea61fd8b05706dbb3eb2f1d34ab9f`
- source_snapshot_hash: `sha256:7add22a5c7c8324482fc956ba199008ae5ce6d02e9e7d3d9f5b8e4f3578a7d6e`
- snapshot_event_time: `2026-06-24T20:15:00+10:00`
- generator_version: `4.0.0`
- final_commit_binding: `PRECOMMIT_TREE_BOUND_PENDING_CI_ATTESTATION`

## Current State

- Project: `KM_IDSystem`
- Path: `KM_IDSystem`
- Product version: `1.0.0`
- Phase/Gate: `B / GOV-SEMANTIC-OPME-in-progress`
- Models/Formulas/Parameters total: `7 / 7 / 49`
- Active formulas/parameters: `7 / 49`
- Machine checked formulas/parameters: `7 / 49`

## Assurance

| Dimension | Status | Evidence |
|---|---|---|
| structural_completeness | `VERIFIED` | `scripts/validate_project_governance.py` |
| implementation_congruence | `VERIFIED` | `KM_IDSystem/docs/governance/parameter_registry.csv, KM_IDSystem/docs/governance/formula_registry.yaml` |
| parameter_source_quality | `VERIFIED` | `KM_IDSystem/docs/governance/parameter_registry.csv` |
| methodological_rationale | `UNVERIFIED` | `KM_IDSystem/docs/governance/MODEL_SPEC.md` |
| empirical_validation | `UNVERIFIED` | `KM_IDSystem/docs/governance/delivery_tasks.yaml` |
| operational_validation | `FAILED` | `KM_IDSystem/docs/governance/development_events.jsonl` |
| delivery_evidence | `UNVERIFIED` | `KM_IDSystem/docs/governance/delivery_tasks.yaml` |
| evidence_freshness | `PARTIAL` | `KM_IDSystem/docs/governance/development_events.jsonl` |

## Delivery

- Readiness: `UNVERIFIED`
- Release gate: `GOV-SEMANTIC-OPME-in-progress`
- Next executable task: `TASK-OPME-B-001`
- Pending/stale events: `7`
- Tree-bound events: `0`
- Commit-bound events: `1`
- Legacy unbound events: `6`
- Unresolved fact IDs: `3`
