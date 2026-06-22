# Project Governance Status

## Snapshot Metadata

- source_base_commit: `05c69c6522a74901f33350e03046f03a6f47b061`
- source_tree_hash: `a661be1db22d99ff3afe6183ac1ae8f4c444be18`
- source_snapshot_hash: `sha256:219dba2050c014ba4571151b914dc620d46eeec6b80e89c2247b28642976bcb7`
- snapshot_event_time: `2026-06-22T13:40:00+10:00`
- generator_version: `3.0.0`
- final_commit_binding: `PRECOMMIT_TREE_BOUND_PENDING_CI_ATTESTATION`

## Current State

- Project: `arxiv-daily-push`
- Path: `arxiv-daily-push`
- Product version: `0.12.4`
- Phase/Gate: `E / ADP-PHASE12-MANUAL-DELIVERY-INTERNAL-RELEASE-DEDUPE-PREPARED`
- Models/Formulas/Parameters total: `34 / 36 / 185`
- Active formulas/parameters: `36 / 184`
- Machine checked formulas/parameters: `36 / 184`

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
- Release gate: `ADP-PHASE12-MANUAL-DELIVERY-INTERNAL-RELEASE-DEDUPE-PREPARED`
- Next executable task: `ADP-PHASE12-MANUAL-DELIVERY-INTERNAL-RELEASE-DEDUPE-035`
- Pending/stale events: `59`
- Tree-bound events: `0`
- Commit-bound events: `0`
- Legacy unbound events: `54`
- Unresolved fact IDs: `3`
