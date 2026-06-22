# Project Governance Status

## Snapshot Metadata

- source_base_commit: `3ce9066664bab17253a25da11529d8146d8b314f`
- source_snapshot_hash: `sha256:b3ef4cb3148bd3da194634ca4a097e460ef1475ec9097b55f105bf2191ca7588`
- snapshot_event_time: `2026-06-22T00:24:25Z`
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
- Pending/stale events: `17`
- Unresolved fact IDs: `7`
