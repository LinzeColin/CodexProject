# Project Governance Status

## Snapshot Metadata

- source_base_commit: `05c69c6522a74901f33350e03046f03a6f47b061`
- source_tree_hash: `a661be1db22d99ff3afe6183ac1ae8f4c444be18`
- source_snapshot_hash: `sha256:29af55ec14928c4da350aef629622f2ab4b267ecf0fe332c2353dfe053189a7b`
- snapshot_event_time: `2026-06-22T13:05:00+10:00`
- generator_version: `3.0.0`
- final_commit_binding: `PRECOMMIT_TREE_BOUND_PENDING_CI_ATTESTATION`

## Current State

- Project: `arxiv-daily-push`
- Path: `arxiv-daily-push`
- Product version: `0.12.3`
- Phase/Gate: `E / ADP-PHASE12-MANUAL-DELIVERY-RELEASE-DEDUPE-PREPARED`
- Models/Formulas/Parameters total: `34 / 36 / 184`
- Active formulas/parameters: `36 / 183`
- Machine checked formulas/parameters: `36 / 183`

## Assurance

| Dimension | Status | Evidence |
|---|---|---|
| structural_completeness | `VERIFIED` | `scripts/validate_project_governance.py` |
| implementation_congruence | `VERIFIED` | `arxiv-daily-push/docs/governance/parameter_registry.csv, arxiv-daily-push/docs/governance/formula_registry.yaml` |
| parameter_source_quality | `VERIFIED` | `arxiv-daily-push/docs/governance/parameter_registry.csv` |
| empirical_validation | `PARTIAL` | `arxiv-daily-push/docs/governance/delivery_tasks.yaml` |
| operational_validation | `PARTIAL` | `arxiv-daily-push/docs/governance/development_events.jsonl` |
| delivery_evidence | `FAILED` | `arxiv-daily-push/docs/governance/delivery_tasks.yaml` |
| evidence_freshness | `PARTIAL` | `arxiv-daily-push/docs/governance/development_events.jsonl` |

## Delivery

- Readiness: `FAILED`
- Release gate: `ADP-PHASE12-MANUAL-DELIVERY-RELEASE-DEDUPE-PREPARED`
- Next executable task: `ADP-PHASE12-MANUAL-DELIVERY-RELEASE-DEDUPE-034`
- Pending/stale events: `58`
- Tree-bound events: `0`
- Commit-bound events: `0`
- Legacy unbound events: `54`
- Unresolved fact IDs: `3`
