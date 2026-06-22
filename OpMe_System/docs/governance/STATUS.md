# Project Governance Status

## Snapshot Metadata

- source_base_commit: `738887de4034ad42d90347d0fa0db6c0f3ed966f`
- source_tree_hash: `6d67efb26a6ea61fd8b05706dbb3eb2f1d34ab9f`
- source_snapshot_hash: `sha256:a3a6fb81408535bf4a238ce5e5a4e884417ff2e35eac416f1f03e6dddfbea41f`
- snapshot_event_time: `2026-06-22T00:24:25Z`
- generator_version: `4.0.0`
- final_commit_binding: `PRECOMMIT_TREE_BOUND_PENDING_CI_ATTESTATION`

## Current State

- Project: `OpMe_System`
- Path: `OpMe_System`
- Product version: `1.0.0`
- Phase/Gate: `B / GOV-SEMANTIC-OPME-in-progress`
- Models/Formulas/Parameters total: `7 / 7 / 49`
- Active formulas/parameters: `7 / 49`
- Machine checked formulas/parameters: `7 / 49`

## Assurance

| Dimension | Status | Evidence |
|---|---|---|
| structural_completeness | `VERIFIED` | `scripts/validate_project_governance.py` |
| implementation_congruence | `VERIFIED` | `OpMe_System/docs/governance/parameter_registry.csv, OpMe_System/docs/governance/formula_registry.yaml` |
| parameter_source_quality | `VERIFIED` | `OpMe_System/docs/governance/parameter_registry.csv` |
| methodological_rationale | `UNVERIFIED` | `OpMe_System/docs/governance/MODEL_SPEC.md` |
| empirical_validation | `UNVERIFIED` | `OpMe_System/docs/governance/delivery_tasks.yaml` |
| operational_validation | `FAILED` | `OpMe_System/docs/governance/development_events.jsonl` |
| delivery_evidence | `UNVERIFIED` | `OpMe_System/docs/governance/delivery_tasks.yaml` |
| evidence_freshness | `PARTIAL` | `OpMe_System/docs/governance/development_events.jsonl` |

## Delivery

- Readiness: `UNVERIFIED`
- Release gate: `GOV-SEMANTIC-OPME-in-progress`
- Next executable task: `TASK-OPME-B-001`
- Pending/stale events: `6`
- Tree-bound events: `0`
- Commit-bound events: `0`
- Legacy unbound events: `6`
- Unresolved fact IDs: `3`
