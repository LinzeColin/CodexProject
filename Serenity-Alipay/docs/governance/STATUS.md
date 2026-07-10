# Project Governance Status

## Snapshot Metadata

- source_base_commit: `9a3b9ae977275f4774e08ae69f61b54f7270b419`
- source_tree_hash: `6d67efb26a6ea61fd8b05706dbb3eb2f1d34ab9f`
- source_snapshot_hash: `sha256:208a1ad9a8021a6076953d2976895a92c2d17ec028cc4aec5916186de3e4d61e`
- snapshot_event_time: `2026-07-10T18:35:12+10:00`
- generator_version: `4.0.1`
- final_commit_binding: `COMMIT_BOUND:9a3b9ae977275f4774e08ae69f61b54f7270b419`

## Current State

- Project: `Serenity-Alipay`
- Path: `Serenity-Alipay`
- Product version: `0.1.0`
- Phase/Gate: `CF-L2 / ACC-CF-L2-20260710-BLOCKED-BY-WORKERS-AUTH`
- Models/Formulas/Parameters total: `5 / 12 / 50`
- Active formulas/parameters: `12 / 50`
- Machine checked formulas/parameters: `12 / 50`

## Assurance

| Dimension | Status | Evidence |
|---|---|---|
| structural_completeness | `VERIFIED` | `scripts/validate_project_governance.py` |
| implementation_congruence | `VERIFIED` | `Serenity-Alipay/docs/governance/parameter_registry.csv, Serenity-Alipay/docs/governance/formula_registry.yaml` |
| parameter_source_quality | `VERIFIED` | `Serenity-Alipay/docs/governance/parameter_registry.csv` |
| methodological_rationale | `UNVERIFIED` | `Serenity-Alipay/docs/governance/MODEL_SPEC.md` |
| empirical_validation | `UNVERIFIED` | `Serenity-Alipay/docs/governance/delivery_tasks.yaml` |
| operational_validation | `PARTIAL` | `Serenity-Alipay/docs/governance/development_events.jsonl` |
| delivery_evidence | `UNVERIFIED` | `Serenity-Alipay/docs/governance/delivery_tasks.yaml` |
| evidence_freshness | `PARTIAL` | `Serenity-Alipay/docs/governance/development_events.jsonl` |

## Delivery

- Readiness: `UNVERIFIED`
- Release gate: `ACC-CF-L2-20260710-BLOCKED-BY-WORKERS-AUTH`
- Next executable task: `CF-L2-20260710`
- Pending/stale events: `6`
- Tree-bound events: `0`
- Commit-bound events: `2`
- Legacy unbound events: `3`
- Unresolved fact IDs: `2`
