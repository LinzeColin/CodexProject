# Project Governance Status

## Snapshot Metadata

- source_base_commit: `05c69c6522a74901f33350e03046f03a6f47b061`
- source_snapshot_hash: `sha256:3d241c50d8420cb40bea95fbe91ba18ce0c27ab33002d87fdeec351003227545`
- snapshot_event_time: `2026-06-22T00:24:25Z`
- generator_version: `2.0.0`
- final_commit_binding: `CI_ATTESTATION_REQUIRED`

## Current State

- Project: `whkmSalary`
- Path: `whkmSalary`
- Product version: `0.0.0`
- Phase/Gate: `B / GOV-SEMANTIC-WHKM-in-progress`
- Models/Formulas/Parameters total: `2 / 10 / 80`
- Active formulas/parameters: `10 / 80`
- Machine checked formulas/parameters: `9 / 78`

## Assurance

| Dimension | Status | Evidence |
|---|---|---|
| structural_validation | `pass` | `scripts/validate_project_governance.py` |
| implementation_congruence | `partial` | `whkmSalary/docs/governance/parameter_registry.csv, whkmSalary/docs/governance/formula_registry.yaml` |
| empirical_validation | `unknown` | `whkmSalary/docs/governance/delivery_tasks.yaml` |
| operational_evidence | `blocked` | `whkmSalary/docs/governance/development_events.jsonl` |

## Delivery

- Readiness: `blocked`
- Release gate: `GOV-SEMANTIC-WHKM-in-progress`
- Next executable task: `GOV-SEMANTIC-WHKM-001`
- Pending/stale events: `4`
- Unresolved fact IDs: `7`
