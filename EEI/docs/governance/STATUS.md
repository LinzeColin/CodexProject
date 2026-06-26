# Project Governance Status

## Snapshot Metadata

- source_base_commit: `058c792f8376312842784533016d8716f9177dae`
- source_tree_hash: `00e27599461403192b998e8f9a3f7f0e769e5d8f`
- source_snapshot_hash: `sha256:7c54a3c5bccbba28955e4bbf5c06815c44996965b66c98fe91c7f1069d328342`
- snapshot_event_time: `2026-06-26T10:05:00+10:00`
- generator_version: `4.0.0`
- final_commit_binding: `CI_ATTESTED:f1b89fc30e6b87fc21f8d75527e8cbc5f2b74298; Project Governance run 28210071092/job 83569239854 PASS; EEI validation run 28210071130/job 83569239684 PASS; A209 remains open until 288/288 zero-failure evidence is promoted and release-ready validation passes.`

## Current State

- Project: `EEI`
- Path: `EEI`
- Product version: `0.1.0`
- Phase/Gate: `D / TASK-T1309-A210-SIGNED-BUNDLE-SOURCE-BOUNDARY`
- Models/Formulas/Parameters total: `12 / 12 / 89`
- Active formulas/parameters: `11 / 89`
- Machine checked formulas/parameters: `11 / 89`

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
- Release gate: `TASK-T1309-A210-SIGNED-BUNDLE-SOURCE-BOUNDARY`
- Next executable task: `TASK-T1309`
- Pending/stale events: `101`
- Tree-bound events: `0`
- Commit-bound events: `18`
- Legacy unbound events: `19`
- Unresolved fact IDs: `5`
