# Project Governance Status

## Snapshot Metadata

- source_base_commit: `00f4187f43960a3b25fc696ae2a15951f4431763`
- source_tree_hash: `6d67efb26a6ea61fd8b05706dbb3eb2f1d34ab9f`
- source_snapshot_hash: `sha256:95810479060b9ee632413b4c1fc501a0a5350cc64736cc81a880cd28a09b952e`
- snapshot_event_time: `2026-07-10T18:53:05+10:00`
- generator_version: `4.0.1`
- final_commit_binding: `COMMIT_BOUND:00f4187f43960a3b25fc696ae2a15951f4431763`

## Current State

- Project: `OpenAIDatabase`
- Path: `OpenAIDatabase`
- Product version: `0.2.0`
- Phase/Gate: `CF-L2 / ACC-CF-L2-20260710-PASSED-ACCESS-PROTECTED`
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
- Release gate: `ACC-CF-L2-20260710-PASSED-ACCESS-PROTECTED`
- Next executable task: `TASK-OAI-B-001`
- Pending/stale events: `17`
- Tree-bound events: `0`
- Commit-bound events: `3`
- Legacy unbound events: `6`
- Unresolved fact IDs: `9`
