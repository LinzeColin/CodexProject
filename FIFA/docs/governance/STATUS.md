# Project Governance Status

## Snapshot Metadata

- source_base_commit: `738887de4034ad42d90347d0fa0db6c0f3ed966f`
- source_tree_hash: `6d67efb26a6ea61fd8b05706dbb3eb2f1d34ab9f`
- source_snapshot_hash: `sha256:0d38f9c46f563aea165f54162ab9b4b7dd72d00051446ba2924efea10771f778`
- snapshot_event_time: `2026-06-24T22:05:00+10:00`
- generator_version: `4.0.0`
- final_commit_binding: `PRECOMMIT_TREE_BOUND_PENDING_CI_ATTESTATION`

## Current State

- Project: `FIFA`
- Path: `FIFA`
- Product version: `0.1.0`
- Phase/Gate: `S3PD / S3PD-GATE-IN-PROGRESS; S5PB-GATE-IN-PROGRESS`
- Models/Formulas/Parameters total: `11 / 11 / 118`
- Active formulas/parameters: `10 / 109`
- Machine checked formulas/parameters: `10 / 92`

## Assurance

| Dimension | Status | Evidence |
|---|---|---|
| structural_completeness | `VERIFIED` | `scripts/validate_project_governance.py` |
| implementation_congruence | `PARTIAL` | `FIFA/docs/governance/parameter_registry.csv, FIFA/docs/governance/formula_registry.yaml` |
| parameter_source_quality | `PARTIAL` | `FIFA/docs/governance/parameter_registry.csv` |
| methodological_rationale | `UNVERIFIED` | `FIFA/docs/governance/MODEL_SPEC.md` |
| empirical_validation | `UNVERIFIED` | `FIFA/docs/governance/delivery_tasks.yaml` |
| operational_validation | `FAILED` | `FIFA/docs/governance/development_events.jsonl` |
| delivery_evidence | `UNVERIFIED` | `FIFA/docs/governance/delivery_tasks.yaml` |
| evidence_freshness | `PARTIAL` | `FIFA/docs/governance/development_events.jsonl` |

## Delivery

- Readiness: `UNVERIFIED`
- Release gate: `S3PD-GATE-IN-PROGRESS; S5PB-GATE-IN-PROGRESS`
- Next executable task: `TASK-FIFA-C-001`
- Pending/stale events: `5`
- Tree-bound events: `0`
- Commit-bound events: `5`
- Legacy unbound events: `3`
- Unresolved fact IDs: `6`
