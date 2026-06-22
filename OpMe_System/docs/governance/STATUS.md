# Project Governance Status

## Snapshot Metadata

- source_base_commit: `05c69c6522a74901f33350e03046f03a6f47b061`
- source_snapshot_hash: `sha256:95e46d7aa228bcfa136bff34c9174c00a3057fa576a0964e5ee6942f50f3de90`
- snapshot_event_time: `2026-06-22T00:24:25Z`
- generator_version: `2.0.0`
- final_commit_binding: `CI_ATTESTATION_REQUIRED`

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
| structural_validation | `pass` | `scripts/validate_project_governance.py` |
| implementation_congruence | `machine_verified` | `OpMe_System/docs/governance/parameter_registry.csv, OpMe_System/docs/governance/formula_registry.yaml` |
| empirical_validation | `unknown` | `OpMe_System/docs/governance/delivery_tasks.yaml` |
| operational_evidence | `blocked` | `OpMe_System/docs/governance/development_events.jsonl` |

## Delivery

- Readiness: `conditional`
- Release gate: `GOV-SEMANTIC-OPME-in-progress`
- Next executable task: `GOV-SEMANTIC-OPME-001`
- Pending/stale events: `6`
- Unresolved fact IDs: `3`
