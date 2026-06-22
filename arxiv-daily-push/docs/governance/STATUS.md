# Project Governance Status

## Snapshot Metadata

- source_base_commit: `05c69c6522a74901f33350e03046f03a6f47b061`
- source_snapshot_hash: `sha256:c6c9985afd8b0de3b93172999a1eb1421f171cebf876a6f4da92bb929772a4da`
- snapshot_event_time: `2026-06-22T12:04:20+10:00`
- generator_version: `2.0.0`
- final_commit_binding: `CI_ATTESTATION_REQUIRED`

## Current State

- Project: `arxiv-daily-push`
- Path: `arxiv-daily-push`
- Product version: `0.12.1`
- Phase/Gate: `E / ADP-PHASE12-PRODUCTION-ENABLEMENT-CLOUD-GATED`
- Models/Formulas/Parameters total: `33 / 35 / 180`
- Active formulas/parameters: `35 / 179`
- Machine checked formulas/parameters: `35 / 179`

## Assurance

| Dimension | Status | Evidence |
|---|---|---|
| structural_validation | `pass` | `scripts/validate_project_governance.py` |
| implementation_congruence | `machine_verified` | `arxiv-daily-push/docs/governance/parameter_registry.csv, arxiv-daily-push/docs/governance/formula_registry.yaml` |
| empirical_validation | `partial` | `arxiv-daily-push/docs/governance/delivery_tasks.yaml` |
| operational_evidence | `partial` | `arxiv-daily-push/docs/governance/development_events.jsonl` |

## Delivery

- Readiness: `blocked`
- Release gate: `ADP-PHASE12-PRODUCTION-ENABLEMENT-CLOUD-GATED`
- Next executable task: `NONE`
- Pending/stale events: `56`
- Unresolved fact IDs: `3`
