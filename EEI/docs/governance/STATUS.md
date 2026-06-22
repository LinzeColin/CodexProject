# Project Governance Status

## Snapshot Metadata

- source_base_commit: `05c69c6522a74901f33350e03046f03a6f47b061`
- source_snapshot_hash: `sha256:a1a6ded910036fbb09d39ee671540009baa8dbd850065cd3d470d8e85c0c59d1`
- snapshot_event_time: `2026-06-22T00:42:00Z`
- generator_version: `2.0.0`
- final_commit_binding: `CI_ATTESTATION_REQUIRED`

## Current State

- Project: `EEI`
- Path: `EEI`
- Product version: `0.1.0`
- Phase/Gate: `C / TASK-T1307-A209-4H-OPERATOR-SOAK-PARTIAL`
- Models/Formulas/Parameters total: `12 / 12 / 61`
- Active formulas/parameters: `11 / 61`
- Machine checked formulas/parameters: `10 / 54`

## Assurance

| Dimension | Status | Evidence |
|---|---|---|
| structural_validation | `pass` | `scripts/validate_project_governance.py` |
| implementation_congruence | `partial` | `EEI/docs/governance/parameter_registry.csv, EEI/docs/governance/formula_registry.yaml` |
| empirical_validation | `partial` | `EEI/docs/governance/delivery_tasks.yaml` |
| operational_evidence | `partial` | `EEI/docs/governance/development_events.jsonl` |

## Delivery

- Readiness: `blocked`
- Release gate: `TASK-T1307-A209-4H-OPERATOR-SOAK-PARTIAL`
- Next executable task: `TASK-T1301`
- Pending/stale events: `18`
- Unresolved fact IDs: `7`
