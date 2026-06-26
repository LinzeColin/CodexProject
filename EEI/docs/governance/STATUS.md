# Project Governance Status

## Snapshot Metadata

- source_base_commit: `047b4094d56fb7b3162b24265501e985690296f0`
- source_tree_hash: `8737d055c5c24cf2e160003744e375aba6f6145b`
- source_snapshot_hash: `sha256:dc2a4a1c2bacbef78381d8487eb70aa4f04eefe3766dc6e4f3e407f1d61bbe15`
- snapshot_event_time: `2026-06-27T01:17:20+10:00`
- generator_version: `4.0.0`
- final_commit_binding: `PRECOMMIT_TREE_BOUND_PENDING_CI_ATTESTATION`

## Current State

- Project: `EEI`
- Path: `EEI`
- Product version: `0.1.0`
- Phase/Gate: `D / TASK-T1303-OPERATOR-INPUT-SUBMISSION-PREFLIGHT`
- Models/Formulas/Parameters total: `12 / 12 / 95`
- Active formulas/parameters: `11 / 95`
- Machine checked formulas/parameters: `11 / 95`

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
- Release gate: `TASK-T1303-OPERATOR-INPUT-SUBMISSION-PREFLIGHT`
- Next executable task: `TASK-T1303`
- Latest non-closure product binding: `EVENT-20260627-018` adds a dry-run operator-input submission preflight/validator dispatch plan while release readiness remains blocked.
- Pending/stale events: `126`
- Tree-bound events: `0`
- Commit-bound events: `21`
- Legacy unbound events: `19`
- Unresolved fact IDs: `8`
