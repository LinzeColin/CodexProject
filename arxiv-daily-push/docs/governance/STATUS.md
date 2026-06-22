# Project Governance Status

## Snapshot Metadata

- source_base_commit: `05c69c6522a74901f33350e03046f03a6f47b061`
- source_snapshot_hash: `sha256:d5fd84399540bbd6c729893ed31cf6c665e38173d8a81d01f0f90cba5e80867e`
- snapshot_event_time: `2026-06-22T10:10:00+10:00`
- generator_version: `2.0.0`
- final_commit_binding: `CI_ATTESTATION_REQUIRED`

## Current State

- Project: `arxiv-daily-push`
- Path: `arxiv-daily-push`
- Product version: `0.12.0`
- Phase/Gate: `E / ADP-PHASE12-ALL-ARXIV-QUEUE-DELIVERY-PASS`
- Models/Formulas/Parameters total: `32 / 34 / 176`
- Active formulas/parameters: `34 / 175`
- Machine checked formulas/parameters: `34 / 175`

## Assurance

| Dimension | Status | Evidence |
|---|---|---|
| structural_validation | `pass` | `scripts/validate_project_governance.py` |
| implementation_congruence | `machine_verified` | `arxiv-daily-push/docs/governance/parameter_registry.csv, arxiv-daily-push/docs/governance/formula_registry.yaml` |
| empirical_validation | `partial` | `arxiv-daily-push/docs/governance/delivery_tasks.yaml` |
| operational_evidence | `partial` | `arxiv-daily-push/docs/governance/development_events.jsonl` |

## Delivery

- Readiness: `blocked`
- Release gate: `ADP-PHASE12-ALL-ARXIV-QUEUE-DELIVERY-PASS`
- Next executable task: `NONE`
- Pending/stale events: `55`
- Unresolved fact IDs: `3`
