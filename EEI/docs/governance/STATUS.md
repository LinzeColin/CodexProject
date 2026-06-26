# Project Governance Status

## Snapshot Metadata

- source_base_commit: `047b4094d56fb7b3162b24265501e985690296f0`
- source_tree_hash: `8737d055c5c24cf2e160003744e375aba6f6145b`
- source_snapshot_hash: `sha256:c32fb1c4ff733015edc9ab464a4c7ae85741c63fda9819178da79ccef8319b8b`
- snapshot_event_time: `2026-06-26T18:49:21+10:00`
- generator_version: `4.0.0`
- final_commit_binding: `PRECOMMIT_TREE_BOUND_PENDING_CI_ATTESTATION`

## Current State

- Project: `EEI`
- Path: `EEI`
- Product version: `0.1.0`
- Phase/Gate: `C / TASK-T1308-A211-APP-ICON-BRAND-REFRESH`
- Models/Formulas/Parameters total: `12 / 12 / 90`
- Active formulas/parameters: `11 / 90`
- Machine checked formulas/parameters: `11 / 90`

## Assurance

| Dimension | Status | Evidence |
|---|---|---|
| structural_completeness | `VERIFIED` | `scripts/validate_project_governance.py` |
| implementation_congruence | `VERIFIED` | `EEI/docs/governance/parameter_registry.csv, EEI/docs/governance/formula_registry.yaml` |
| parameter_source_quality | `VERIFIED` | `EEI/docs/governance/parameter_registry.csv` |
| methodological_rationale | `UNVERIFIED` | `EEI/docs/governance/MODEL_SPEC.md` |
| empirical_validation | `PARTIAL` | `EEI/docs/governance/delivery_tasks.yaml` |
| operational_validation | `PARTIAL` | `EEI/docs/governance/development_events.jsonl` |
| delivery_evidence | `FAILED` | `EEI/docs/governance/delivery_tasks.yaml` |
| evidence_freshness | `PARTIAL` | `EEI/docs/governance/development_events.jsonl` |

## Delivery

- Readiness: `FAILED`
- Release gate: `TASK-T1308-A211-APP-ICON-BRAND-REFRESH`
- Next executable task: `TASK-T1301`
- Pending/stale events: `117`
- Tree-bound events: `0`
- Commit-bound events: `21`
- Legacy unbound events: `19`
- Unresolved fact IDs: `8`
