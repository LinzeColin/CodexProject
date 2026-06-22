# Project Governance Status

## Snapshot Metadata

- source_base_commit: `3ce9066664bab17253a25da11529d8146d8b314f`
- source_snapshot_hash: `sha256:19f488ad4b0d0052cb3cd995bb79bb2394e2b222942ac96c6efef83d24f697d8`
- snapshot_event_time: `2026-06-22T00:24:25Z`
- generator_version: `2.0.0`
- final_commit_binding: `CI_ATTESTATION_REQUIRED`

## Current State

- Project: `OpenAIDatabase`
- Path: `OpenAIDatabase`
- Product version: `0.2.0`
- Phase/Gate: `B / GOV-SEMANTIC-OAIDB-in-progress`
- Models/Formulas/Parameters total: `11 / 11 / 92`
- Active formulas/parameters: `11 / 92`
- Machine checked formulas/parameters: `10 / 28`

## Assurance

| Dimension | Status | Evidence |
|---|---|---|
| structural_validation | `pass` | `scripts/validate_project_governance.py` |
| implementation_congruence | `partial` | `OpenAIDatabase/docs/governance/parameter_registry.csv, OpenAIDatabase/docs/governance/formula_registry.yaml` |
| empirical_validation | `unknown` | `OpenAIDatabase/docs/governance/delivery_tasks.yaml` |
| operational_evidence | `blocked` | `OpenAIDatabase/docs/governance/development_events.jsonl` |

## Delivery

- Readiness: `blocked`
- Release gate: `GOV-SEMANTIC-OAIDB-in-progress`
- Next executable task: `GOV-SEMANTIC-OAIDB-001`
- Pending/stale events: `7`
- Unresolved fact IDs: `6`
