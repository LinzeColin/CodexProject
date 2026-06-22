# Project Governance Status

## Snapshot Metadata

- source_base_commit: `05c69c6522a74901f33350e03046f03a6f47b061`
- source_snapshot_hash: `sha256:4532d4d6fabbbd25e47fdd5b4ff12e91e60fcd40eec79e2b6227285b0d10434e`
- snapshot_event_time: `2026-06-22T00:24:25Z`
- generator_version: `2.0.0`
- final_commit_binding: `CI_ATTESTATION_REQUIRED`

## Current State

- Project: `Alpha`
- Path: `Alpha`
- Product version: `0.1.0`
- Phase/Gate: `B / GOV-SEMANTIC-ALPHA-in-progress`
- Models/Formulas/Parameters total: `9 / 9 / 55`
- Active formulas/parameters: `9 / 55`
- Machine checked formulas/parameters: `9 / 42`

## Assurance

| Dimension | Status | Evidence |
|---|---|---|
| structural_validation | `pass` | `scripts/validate_project_governance.py` |
| implementation_congruence | `partial` | `Alpha/docs/governance/parameter_registry.csv, Alpha/docs/governance/formula_registry.yaml` |
| empirical_validation | `unknown` | `Alpha/docs/governance/delivery_tasks.yaml` |
| operational_evidence | `blocked` | `Alpha/docs/governance/development_events.jsonl` |

## Delivery

- Readiness: `blocked`
- Release gate: `GOV-SEMANTIC-ALPHA-in-progress`
- Next executable task: `GOV-SEMANTIC-ALPHA-001`
- Pending/stale events: `5`
- Unresolved fact IDs: `5`
