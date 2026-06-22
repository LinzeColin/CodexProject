# Project Governance Status

## Snapshot Metadata

- source_base_commit: `05c69c6522a74901f33350e03046f03a6f47b061`
- source_snapshot_hash: `sha256:5a65a85815a5e5f5b703ceed5c51a17fe746eab7f09bd8434baaac79009b504b`
- snapshot_event_time: `2026-06-22T00:24:25Z`
- generator_version: `2.0.0`
- final_commit_binding: `CI_ATTESTATION_REQUIRED`

## Current State

- Project: `Serenity-Alipay`
- Path: `Serenity-Alipay`
- Product version: `0.1.0`
- Phase/Gate: `B / GOV-REVIEW6-B-SEMANTIC-EXTRACT`
- Models/Formulas/Parameters total: `5 / 12 / 49`
- Active formulas/parameters: `12 / 49`
- Machine checked formulas/parameters: `12 / 49`

## Assurance

| Dimension | Status | Evidence |
|---|---|---|
| structural_validation | `pass` | `scripts/validate_project_governance.py` |
| implementation_congruence | `machine_verified` | `Serenity-Alipay/docs/governance/parameter_registry.csv, Serenity-Alipay/docs/governance/formula_registry.yaml` |
| empirical_validation | `unknown` | `Serenity-Alipay/docs/governance/delivery_tasks.yaml` |
| operational_evidence | `partial` | `Serenity-Alipay/docs/governance/development_events.jsonl` |

## Delivery

- Readiness: `conditional`
- Release gate: `GOV-REVIEW6-B-SEMANTIC-EXTRACT`
- Next executable task: `TASK-A-001`
- Pending/stale events: `4`
- Unresolved fact IDs: `2`
