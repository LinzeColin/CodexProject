# Project Governance Status

## Snapshot Metadata

- source_base_commit: `05c69c6522a74901f33350e03046f03a6f47b061`
- source_snapshot_hash: `sha256:87611d049cd444155001a30c448635e552e553cd3d2d7367f42f521bf5c45ac7`
- snapshot_event_time: `2026-06-22T00:24:25Z`
- generator_version: `2.0.0`
- final_commit_binding: `CI_ATTESTATION_REQUIRED`

## Current State

- Project: `EVA_OS`
- Path: `EVA_OS`
- Product version: `0.1.0`
- Phase/Gate: `B / GOV-SEMANTIC-EVA-001-in-progress`
- Models/Formulas/Parameters total: `16 / 16 / 189`
- Active formulas/parameters: `16 / 189`
- Machine checked formulas/parameters: `16 / 52`

## Assurance

| Dimension | Status | Evidence |
|---|---|---|
| structural_validation | `pass` | `scripts/validate_project_governance.py` |
| implementation_congruence | `partial` | `EVA_OS/docs/governance/parameter_registry.csv, EVA_OS/docs/governance/formula_registry.yaml` |
| empirical_validation | `unknown` | `EVA_OS/docs/governance/delivery_tasks.yaml` |
| operational_evidence | `blocked` | `EVA_OS/docs/governance/development_events.jsonl` |

## Delivery

- Readiness: `blocked`
- Release gate: `GOV-SEMANTIC-EVA-001-in-progress`
- Next executable task: `GOV-SEMANTIC-EVA-001`
- Pending/stale events: `4`
- Unresolved fact IDs: `12`
