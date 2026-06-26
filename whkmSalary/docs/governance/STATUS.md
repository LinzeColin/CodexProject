# Project Governance Status

## Snapshot Metadata

- source_base_commit: `738887de4034ad42d90347d0fa0db6c0f3ed966f`
- source_tree_hash: `6d67efb26a6ea61fd8b05706dbb3eb2f1d34ab9f`
- source_snapshot_hash: `sha256:e50caa7ad2aec3d44f5b788fd0d357ace57d7fff8fd4aee20f85cc583c08b094`
- snapshot_event_time: `2026-06-25T00:00:00+10:00`
- generator_version: `4.0.0`
- final_commit_binding: `PRECOMMIT_TREE_BOUND_PENDING_CI_ATTESTATION`

## Current State

- Project: `whkmSalary`
- Path: `whkmSalary`
- Product version: `0.0.0`
- Phase/Gate: `S4PC / S4PC-GATE-in-progress`
- Models/Formulas/Parameters total: `2 / 10 / 80`
- Active formulas/parameters: `10 / 80`
- Machine checked formulas/parameters: `9 / 78`

## Assurance

| Dimension | Status | Evidence |
|---|---|---|
| structural_completeness | `VERIFIED` | `scripts/validate_project_governance.py` |
| implementation_congruence | `PARTIAL` | `whkmSalary/docs/governance/parameter_registry.csv, whkmSalary/docs/governance/formula_registry.yaml` |
| parameter_source_quality | `PARTIAL` | `whkmSalary/docs/governance/parameter_registry.csv` |
| methodological_rationale | `UNVERIFIED` | `whkmSalary/docs/governance/MODEL_SPEC.md` |
| empirical_validation | `UNVERIFIED` | `whkmSalary/docs/governance/delivery_tasks.yaml` |
| operational_validation | `FAILED` | `whkmSalary/docs/governance/development_events.jsonl` |
| delivery_evidence | `FAILED` | `whkmSalary/docs/governance/delivery_tasks.yaml` |
| evidence_freshness | `PARTIAL` | `whkmSalary/docs/governance/development_events.jsonl` |

## Delivery

- Readiness: `FAILED`
- Release gate: `S4PC-GATE-in-progress`
- Next executable task: `TASK-WHKM-B-001`
- Pending/stale events: `8`
- Tree-bound events: `4`
- Commit-bound events: `1`
- Legacy unbound events: `4`
- Unresolved fact IDs: `7`
