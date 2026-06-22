# Project Governance Status

## Snapshot Metadata

- source_base_commit: `738887de4034ad42d90347d0fa0db6c0f3ed966f`
- source_tree_hash: `6d67efb26a6ea61fd8b05706dbb3eb2f1d34ab9f`
- source_snapshot_hash: `sha256:840279a08b2e199a20877ede3590d2cb85798de78e5392f0386388a80e4abb44`
- snapshot_event_time: `2026-06-22T05:40:07Z`
- generator_version: `4.0.0`
- final_commit_binding: `PRECOMMIT_TREE_BOUND_PENDING_CI_ATTESTATION`

## Current State

- Project: `EEI`
- Path: `EEI`
- Product version: `0.1.0`
- Phase/Gate: `C / TASK-T1307-A209-4H-OPERATOR-SOAK-PARTIAL`
- Models/Formulas/Parameters total: `12 / 12 / 62`
- Active formulas/parameters: `11 / 62`
- Machine checked formulas/parameters: `10 / 55`

## Assurance

| Dimension | Status | Evidence |
|---|---|---|
| structural_completeness | `VERIFIED` | `scripts/validate_project_governance.py` |
| implementation_congruence | `PARTIAL` | `EEI/docs/governance/parameter_registry.csv, EEI/docs/governance/formula_registry.yaml` |
| parameter_source_quality | `PARTIAL` | `EEI/docs/governance/parameter_registry.csv` |
| methodological_rationale | `UNVERIFIED` | `EEI/docs/governance/MODEL_SPEC.md` |
| empirical_validation | `PARTIAL` | `EEI/docs/governance/delivery_tasks.yaml` |
| operational_validation | `PARTIAL` | `EEI/docs/governance/development_events.jsonl` |
| delivery_evidence | `FAILED` | `EEI/docs/governance/delivery_tasks.yaml` |
| evidence_freshness | `PARTIAL` | `EEI/docs/governance/development_events.jsonl` |

## Delivery

- Readiness: `FAILED`
- Release gate: `TASK-T1307-A209-4H-OPERATOR-SOAK-PARTIAL`
- Next executable task: `TASK-T1301`
- Pending/stale events: `28`
- Tree-bound events: `0`
- Commit-bound events: `6`
- Legacy unbound events: `17`
- Unresolved fact IDs: `7`
