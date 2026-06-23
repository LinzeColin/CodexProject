# Project Governance Status

## Snapshot Metadata

- source_base_commit: `738887de4034ad42d90347d0fa0db6c0f3ed966f`
- source_tree_hash: `6d67efb26a6ea61fd8b05706dbb3eb2f1d34ab9f`
- source_snapshot_hash: `sha256:714d0294c2f5ee1cfac75165e35f49c06a6793789c231a2254c715e6f558c3fe`
- snapshot_event_time: `2026-06-23T22:15:00+10:00`
- generator_version: `4.0.0`
- final_commit_binding: `PRECOMMIT_TREE_BOUND_PENDING_CI_ATTESTATION`

## Current State

- Project: `arxiv-daily-push`
- Path: `arxiv-daily-push`
- Product version: `0.23.0`
- Phase/Gate: `S1-A / STRICT_ARXIV_PRODUCTION_ACCEPTANCE_REOPENED_PENDING_S1P5T03R_CLOUD_CI`
- Models/Formulas/Parameters total: `46 / 48 / 359`
- Active formulas/parameters: `48 / 342`
- Machine checked formulas/parameters: `48 / 342`

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
- Release gate: `STRICT_ARXIV_PRODUCTION_ACCEPTANCE_REOPENED_PENDING_S1P5T03R_CLOUD_CI`
- Next executable task: `S1P5T03-R-REAL_ARXIV_30_DAY_BACKFILL_AND_LEDGER_RECONCILE`
- Pending/stale events: `80`
- Tree-bound events: `0`
- Commit-bound events: `1`
- Legacy unbound events: `54`
- Unresolved fact IDs: `3`
