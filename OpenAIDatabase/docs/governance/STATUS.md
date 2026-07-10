# Project Governance Status

## Snapshot Metadata

- source_base_commit: `9a3b9ae977275f4774e08ae69f61b54f7270b419`
- source_tree_hash: `6d67efb26a6ea61fd8b05706dbb3eb2f1d34ab9f`
- source_snapshot_hash: `sha256:2ed89f6edbb130900a5f73e04521c73093bd63cb88ba5edf6d3890d9392dd3ac`
- snapshot_event_time: `2026-07-10T18:35:12+10:00`
- generator_version: `4.0.1`
- final_commit_binding: `COMMIT_BOUND:9a3b9ae977275f4774e08ae69f61b54f7270b419`

## Current State

- Project: `OpenAIDatabase`
- Path: `OpenAIDatabase`
- Product version: `0.2.0`
- Phase/Gate: `CF-L2 / ACC-CF-L2-20260710-BLOCKED-BY-WORKERS-AUTH`
- Models/Formulas/Parameters total: `12 / 12 / 99`
- Active formulas/parameters: `12 / 99`
- Machine checked formulas/parameters: `10 / 28`

## Assurance

| Dimension | Status | Evidence |
|---|---|---|
| structural_completeness | `VERIFIED` | `scripts/validate_project_governance.py` |
| implementation_congruence | `PARTIAL` | `OpenAIDatabase/docs/governance/parameter_registry.csv, OpenAIDatabase/docs/governance/formula_registry.yaml` |
| parameter_source_quality | `PARTIAL` | `OpenAIDatabase/docs/governance/parameter_registry.csv` |
| methodological_rationale | `UNVERIFIED` | `OpenAIDatabase/docs/governance/MODEL_SPEC.md` |
| empirical_validation | `UNVERIFIED` | `OpenAIDatabase/docs/governance/delivery_tasks.yaml` |
| operational_validation | `FAILED` | `OpenAIDatabase/docs/governance/development_events.jsonl` |
| delivery_evidence | `FAILED` | `OpenAIDatabase/docs/governance/delivery_tasks.yaml` |
| evidence_freshness | `PARTIAL` | `OpenAIDatabase/docs/governance/development_events.jsonl` |

## Delivery

- Readiness: `FAILED`
- Release gate: `ACC-CF-L2-20260710-BLOCKED-BY-WORKERS-AUTH`
- Next executable task: `CF-L2-20260710`
- Pending/stale events: `17`
- Tree-bound events: `0`
- Commit-bound events: `2`
- Legacy unbound events: `6`
- Unresolved fact IDs: `9`
