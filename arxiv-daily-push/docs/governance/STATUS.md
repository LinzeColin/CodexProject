# Project Governance Status

## Snapshot Metadata

- source_base_commit: `738887de4034ad42d90347d0fa0db6c0f3ed966f`
- source_tree_hash: `6d67efb26a6ea61fd8b05706dbb3eb2f1d34ab9f`
- source_snapshot_hash: `sha256:48e00502a65973d52a3101ddcbe9e1cd547cf94a490cb22211bcac6ab2255b69`
- snapshot_event_time: `2026-06-23T09:55:00+10:00`
- generator_version: `4.0.0`
- final_commit_binding: `PRECOMMIT_TREE_BOUND_PENDING_CI_ATTESTATION`

## Current State

- Project: `arxiv-daily-push`
- Path: `arxiv-daily-push`
- Product version: `0.22.0`
- Phase/Gate: `S1-A / ADP-S1-12-TEXT-ONLY-PRODUCTION-ENABLEMENT-PR-READY`
- Models/Formulas/Parameters total: `44 / 46 / 348`
- Active formulas/parameters: `46 / 331`
- Machine checked formulas/parameters: `46 / 331`

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
- Release gate: `ADP-S1-12-TEXT-ONLY-PRODUCTION-ENABLEMENT-PR-READY`
- Next executable task: `S1-12-CONTROLLED_B1_LIVE_EMAIL_DAYS-001`
- Pending/stale events: `75`
- Tree-bound events: `0`
- Commit-bound events: `1`
- Legacy unbound events: `54`
- Unresolved fact IDs: `3`
