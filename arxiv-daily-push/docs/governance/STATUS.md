# Project Governance Status

## Snapshot Metadata

- source_base_commit: `738887de4034ad42d90347d0fa0db6c0f3ed966f`
- source_tree_hash: `6d67efb26a6ea61fd8b05706dbb3eb2f1d34ab9f`
- source_snapshot_hash: `sha256:a8f3a229dfde51ded7413cb7761891c70b2dafdc572bb76b2e169caafae4b416`
- snapshot_event_time: `2026-06-22T18:20:00+10:00`
- generator_version: `4.0.0`
- final_commit_binding: `PRECOMMIT_TREE_BOUND_PENDING_CI_ATTESTATION`

## Current State

- Project: `arxiv-daily-push`
- Path: `arxiv-daily-push`
- Product version: `0.14.0`
- Phase/Gate: `S1-A / ADP-S1-04-SQLITE-DATA-MODEL-READY`
- Models/Formulas/Parameters total: `36 / 38 / 275`
- Active formulas/parameters: `38 / 274`
- Machine checked formulas/parameters: `38 / 274`

## Assurance

| Dimension | Status | Evidence |
|---|---|---|
| structural_completeness | `VERIFIED` | `scripts/validate_project_governance.py` |
| implementation_congruence | `VERIFIED` | `arxiv-daily-push/docs/governance/parameter_registry.csv, arxiv-daily-push/docs/governance/formula_registry.yaml` |
| parameter_source_quality | `VERIFIED` | `arxiv-daily-push/docs/governance/parameter_registry.csv` |
| methodological_rationale | `UNVERIFIED` | `arxiv-daily-push/docs/governance/MODEL_SPEC.md` |
| empirical_validation | `PARTIAL` | `arxiv-daily-push/docs/governance/delivery_tasks.yaml` |
| operational_validation | `PARTIAL` | `arxiv-daily-push/docs/governance/development_events.jsonl` |
| delivery_evidence | `FAILED` | `arxiv-daily-push/docs/governance/delivery_tasks.yaml` |
| evidence_freshness | `PARTIAL` | `arxiv-daily-push/docs/governance/development_events.jsonl` |

## Delivery

- Readiness: `FAILED`
- Release gate: `ADP-S1-04-SQLITE-DATA-MODEL-READY`
- Next executable task: `ADP-PHASE11-PRODUCTION-TRIAL-START-022`
- Pending/stale events: `64`
- Tree-bound events: `0`
- Commit-bound events: `0`
- Legacy unbound events: `54`
- Unresolved fact IDs: `3`
