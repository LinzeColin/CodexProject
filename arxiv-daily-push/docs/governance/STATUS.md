# Project Governance Status

## Snapshot Metadata

- source_base_commit: `738887de4034ad42d90347d0fa0db6c0f3ed966f`
- source_tree_hash: `6d67efb26a6ea61fd8b05706dbb3eb2f1d34ab9f`
- source_snapshot_hash: `sha256:9a47cab9234c7cb0f931d28f30987b1852ea39cc9cbe70cb615f0995b50c1d15`
- snapshot_event_time: `2026-06-23T22:15:00+10:00`
- generator_version: `4.0.0`
- final_commit_binding: `PRECOMMIT_TREE_BOUND_PENDING_CI_ATTESTATION`

## Current State

- Project: `arxiv-daily-push`
- Path: `arxiv-daily-push`
- Product version: `0.23.0`
- Phase/Gate: `S1-A / ARXIV_PRODUCTION_ACCEPTED`
- Models/Formulas/Parameters total: `46 / 48 / 359`
- Active formulas/parameters: `48 / 342`
- Machine checked formulas/parameters: `48 / 342`

## Assurance

| Dimension | Status | Evidence |
|---|---|---|
| structural_completeness | `VERIFIED` | `scripts/validate_project_governance.py` |
| implementation_congruence | `VERIFIED` | `arxiv-daily-push/docs/governance/parameter_registry.csv, arxiv-daily-push/docs/governance/formula_registry.yaml` |
| parameter_source_quality | `VERIFIED` | `arxiv-daily-push/docs/governance/parameter_registry.csv` |
| methodological_rationale | `VERIFIED` | `arxiv-daily-push/docs/governance/MODEL_SPEC.md` |
| empirical_validation | `VERIFIED` | `arxiv-daily-push/docs/governance/delivery_tasks.yaml` |
| operational_validation | `VERIFIED` | `arxiv-daily-push/docs/governance/development_events.jsonl` |
| delivery_evidence | `VERIFIED` | `arxiv-daily-push/docs/governance/delivery_tasks.yaml` |
| evidence_freshness | `PARTIAL` | `arxiv-daily-push/docs/governance/development_events.jsonl` |

## Delivery

- Readiness: `VERIFIED`
- Release gate: `ARXIV_PRODUCTION_ACCEPTED`
- Next executable task: `ADP-PHASE12-EMAIL-HUMAN-FORMAT-036`
- Pending/stale events: `79`
- Tree-bound events: `0`
- Commit-bound events: `1`
- Legacy unbound events: `54`
- Unresolved fact IDs: `0`
