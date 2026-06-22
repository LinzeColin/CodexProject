# Project Governance Status

## Snapshot Metadata

- source_base_commit: `738887de4034ad42d90347d0fa0db6c0f3ed966f`
- source_tree_hash: `6d67efb26a6ea61fd8b05706dbb3eb2f1d34ab9f`
- source_snapshot_hash: `sha256:5b5740ee2f00eb590e9bb155a3935522251dae2f84ead585266f9c20ea429d4b`
- snapshot_event_time: `2026-06-22T21:55:00Z`
- generator_version: `4.0.0`
- final_commit_binding: `CI_ATTESTED:df1925aa6c8d2e2c5cd6e4f0c760ebc21b168ed4`

## Current State

- Project: `EEI`
- Path: `EEI`
- Product version: `0.1.0`
- Phase/Gate: `C / TASK-T1303-A204-A205-WORKER-WAKE-CI-EVIDENCE-BINDING-IN-PROGRESS`
- Models/Formulas/Parameters total: `12 / 12 / 68`
- Active formulas/parameters: `11 / 68`
- Machine checked formulas/parameters: `10 / 61`

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
- Release gate: `TASK-T1303-A204-A205-WORKER-WAKE-CI-EVIDENCE-BINDING-IN-PROGRESS`
- Next executable task: `TASK-T1301`
- Pending/stale events: `37`
- Tree-bound events: `0`
- Commit-bound events: `8`
- Legacy unbound events: `17`
- Unresolved fact IDs: `7`
