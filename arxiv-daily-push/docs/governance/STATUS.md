# Project Governance Status

## Snapshot Metadata

- source_base_commit: `05c69c6522a74901f33350e03046f03a6f47b061`
- source_snapshot_hash: `sha256:4ef9728988981807592d5f81629877123cb59a275b11f263c3ac5244e120fe25`
- snapshot_event_time: `2026-06-22T13:05:00+10:00`
- generator_version: `2.0.0`
- final_commit_binding: `CI_ATTESTATION_REQUIRED`

## Current State

- Project: `arxiv-daily-push`
- Path: `arxiv-daily-push`
- Product version: `0.12.3`
- Phase/Gate: `E / ADP-PHASE12-MANUAL-DELIVERY-RELEASE-DEDUPE-PREPARED`
- Models/Formulas/Parameters total: `34 / 36 / 184`
- Active formulas/parameters: `36 / 183`
- Machine checked formulas/parameters: `36 / 183`

## Assurance

| Dimension | Status | Evidence |
|---|---|---|
| structural_validation | `pass` | `scripts/validate_project_governance.py` |
| implementation_congruence | `machine_verified` | `arxiv-daily-push/docs/governance/parameter_registry.csv, arxiv-daily-push/docs/governance/formula_registry.yaml` |
| empirical_validation | `partial` | `arxiv-daily-push/docs/governance/delivery_tasks.yaml` |
| operational_evidence | `partial` | `arxiv-daily-push/docs/governance/development_events.jsonl` |

## Delivery

- Readiness: `blocked`
- Release gate: `ADP-PHASE12-MANUAL-DELIVERY-RELEASE-DEDUPE-PREPARED`
- Next executable task: `ADP-PHASE12-MANUAL-DELIVERY-RELEASE-DEDUPE-034`
- Pending/stale events: `58`
- Unresolved fact IDs: `3`
