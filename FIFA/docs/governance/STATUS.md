# Project Governance Status

## Snapshot Metadata

- source_base_commit: `05c69c6522a74901f33350e03046f03a6f47b061`
- source_snapshot_hash: `sha256:0fb9f070d4237965b5408ff87ec805b1d58042247ef1ae8e5834ce19e4aa1f76`
- snapshot_event_time: `2026-06-22T00:24:25Z`
- generator_version: `2.0.0`
- final_commit_binding: `CI_ATTESTATION_REQUIRED`

## Current State

- Project: `FIFA`
- Path: `FIFA`
- Product version: `0.1.0`
- Phase/Gate: `B / GOV-SEMANTIC-FIFA-in-progress`
- Models/Formulas/Parameters total: `11 / 11 / 117`
- Active formulas/parameters: `10 / 108`
- Machine checked formulas/parameters: `10 / 91`

## Assurance

| Dimension | Status | Evidence |
|---|---|---|
| structural_validation | `pass` | `scripts/validate_project_governance.py` |
| implementation_congruence | `partial` | `FIFA/docs/governance/parameter_registry.csv, FIFA/docs/governance/formula_registry.yaml` |
| empirical_validation | `unknown` | `FIFA/docs/governance/delivery_tasks.yaml` |
| operational_evidence | `blocked` | `FIFA/docs/governance/development_events.jsonl` |

## Delivery

- Readiness: `conditional`
- Release gate: `GOV-SEMANTIC-FIFA-in-progress`
- Next executable task: `GOV-SEMANTIC-FIFA-001`
- Pending/stale events: `4`
- Unresolved fact IDs: `6`
