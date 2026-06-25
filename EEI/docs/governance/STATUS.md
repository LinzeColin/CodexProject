# Project Governance Status

## Snapshot Metadata

- source_base_commit: `12df22b6347fd881d42545afe387ac9e41e56fb4`
- source_tree_hash: `00e27599461403192b998e8f9a3f7f0e769e5d8f`
- source_snapshot_hash: `sha256:ac733702f16a4c1ca8ba97378c20b1b475c603335498817e3c96d3018ce2a825`
- snapshot_event_time: `2026-06-25T15:12:30Z`
- generator_version: `4.0.0`
- final_commit_binding: `CI_ATTESTED:a246df94bf73b6fba7111805f3c5a02b6edeb070 Project Governance run 28179389094 PASS; EEI validation run 28179389156 PASS`

## Current State

- Project: `EEI`
- Path: `EEI`
- Product version: `0.1.0`
- Phase/Gate: `C / TASK-T1301-A202-SIGNED-INTAKE-SOURCE-BOUNDARY-CI-BOUND-RELEASE-BLOCKED`
- Models/Formulas/Parameters total: `12 / 12 / 88`
- Active formulas/parameters: `11 / 88`
- Machine checked formulas/parameters: `11 / 88`

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
- Release gate: `TASK-T1301-A202-SIGNED-INTAKE-SOURCE-BOUNDARY-CI-BOUND-RELEASE-BLOCKED`
- Next executable task: `TASK-T1301`
- Pending/stale events: `94`
- Tree-bound events: `0`
- Commit-bound events: `15`
- Legacy unbound events: `19`
- Unresolved fact IDs: `5`
