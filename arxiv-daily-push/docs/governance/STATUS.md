# Project Governance Status

## Snapshot Metadata

- source_base_commit: `05c69c6522a74901f33350e03046f03a6f47b061`
- source_snapshot_hash: `sha256:20b9a5a9ea6748d678de1f6ece25d59959ee165cd91e0c9c17b3cf77d54759bc`
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
