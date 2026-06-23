# Project Governance Status

## Snapshot Metadata

- source_base_commit: `738887de4034ad42d90347d0fa0db6c0f3ed966f`
- source_tree_hash: `6d67efb26a6ea61fd8b05706dbb3eb2f1d34ab9f`
- source_snapshot_hash: `sha256:0ac16c5fc4a654f43cb048cd5403b0fc0b589cf9bdd04a48c62768719fd86b7d`
- snapshot_event_time: `2026-06-22T00:24:25Z`
- generator_version: `4.0.0`
- final_commit_binding: `CI_ATTESTED:governance/run_manifests/GOV-REVIEW6-FINAL-PORTFOLIO-001.json`

## Current State

- Project: `EVA_OS`
- Path: `EVA_OS`
- Product version: `0.1.0`
- Phase/Gate: `B / GOV-SEMANTIC-EVA-001-in-progress`
- Models/Formulas/Parameters total: `16 / 16 / 189`
- Active formulas/parameters: `16 / 189`
- Machine checked formulas/parameters: `16 / 52`

## Assurance

| Dimension | Status | Evidence |
|---|---|---|
| structural_completeness | `VERIFIED` | `scripts/validate_project_governance.py` |
| implementation_congruence | `PARTIAL` | `EVA_OS/docs/governance/parameter_registry.csv, EVA_OS/docs/governance/formula_registry.yaml` |
| parameter_source_quality | `PARTIAL` | `EVA_OS/docs/governance/parameter_registry.csv` |
| methodological_rationale | `UNVERIFIED` | `EVA_OS/docs/governance/MODEL_SPEC.md` |
| empirical_validation | `UNVERIFIED` | `EVA_OS/docs/governance/delivery_tasks.yaml` |
| operational_validation | `FAILED` | `EVA_OS/docs/governance/development_events.jsonl` |
| delivery_evidence | `FAILED` | `EVA_OS/docs/governance/delivery_tasks.yaml` |
| evidence_freshness | `PARTIAL` | `EVA_OS/docs/governance/development_events.jsonl` |

## Delivery

- Readiness: `FAILED`
- Release gate: `GOV-SEMANTIC-EVA-001-in-progress`
- Next executable task: `TASK-EVA-B-001`
- Pending/stale events: `4`
- Tree-bound events: `0`
- Commit-bound events: `1`
- Legacy unbound events: `3`
- Unresolved fact IDs: `12`
