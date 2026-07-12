# Project Governance Status

## Snapshot Metadata

- source_base_commit: `ed0fe3a3e8f2f0f46d0f4f442c23fed5ed093935`
- source_tree_hash: `6d67efb26a6ea61fd8b05706dbb3eb2f1d34ab9f`
- source_snapshot_hash: `sha256:bf98509632bca5f764251c736c8d8e6368ef9ab5f53e523768cbff0f4b28c6dc`
- snapshot_event_time: `2026-07-10T19:46:00+10:00`
- generator_version: `4.0.1`
- final_commit_binding: `COMMIT_BOUND:ed0fe3a3e8f2f0f46d0f4f442c23fed5ed093935`

## Current State

- Project: `Serenity-Alipay`
- Path: `Serenity-Alipay`
- Product version: `0.1.0`
- Phase/Gate: `CF-L2 / ACC-CF-L2-20260710-PASSED`
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
- Release gate: `ACC-CF-L2-20260710-PASSED`
- Next executable task: `NONE`
- Pending/stale events: `7`
- Tree-bound events: `0`
- Commit-bound events: `4`
- Legacy unbound events: `3`
- Unresolved fact IDs: `2`
