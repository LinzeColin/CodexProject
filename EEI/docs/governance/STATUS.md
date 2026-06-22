# Project Governance Status

## Snapshot Metadata

- source_base_commit: `738887de4034ad42d90347d0fa0db6c0f3ed966f`
- source_tree_hash: `6d67efb26a6ea61fd8b05706dbb3eb2f1d34ab9f`
- source_snapshot_hash: `sha256:d105c98bd5a360c0143f3a0a4456ee17f8ea9f961206202fb75760b6a089bdc6`
- snapshot_event_time: `2026-06-22T20:49:58Z`
- generator_version: `4.0.0`
- final_commit_binding: `CI_ATTESTED:d009516c57c4908a025c401a711dfb4d599f7b73 Project Governance run 27950933950 job 82707373153; EEI validation run 27950933933 job 82707372790`

## Current State

- Project: `EEI`
- Path: `EEI`
- Product version: `0.1.0`
- Phase/Gate: `C / TASK-T1301-T1302-T1303-CI-EVIDENCE-BINDING-IN-PROGRESS`
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
- Release gate: `TASK-T1301-T1302-T1303-CI-EVIDENCE-BINDING-IN-PROGRESS`
- Next executable task: `TASK-T1301`
- Pending/stale events: `36`
- Tree-bound events: `0`
- Commit-bound events: `7`
- Legacy unbound events: `17`
- Unresolved fact IDs: `7`
