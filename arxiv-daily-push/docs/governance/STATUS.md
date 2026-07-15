# Project Governance Status

## Snapshot Metadata

- source_base_commit: `97d5abf6f2f22e77c3bbf85b73a97129262c8b41`
- source_tree_hash: `4375e46be3b7c9f712f8b21962a0a0c69da57a3f`
- source_snapshot_hash: `sha256:bddaf0e4206cfae0d91300174ff3df5da221ff8096f71ac8d216d3bb98c5a39f`
- snapshot_event_time: `2026-07-15T18:20:00+10:00`
- generator_version: `4.0.1`
- final_commit_binding: `PRECOMMIT_TREE_BOUND_PENDING_CI_ATTESTATION`

## Current State

- Project: `arxiv-daily-push`
- Path: `arxiv-daily-push`
- Product version: `UNKNOWN`
- Phase/Gate: `UNKNOWN / UNKNOWN`
- Models/Formulas/Parameters total: `122 / 124 / 1124`
- Active formulas/parameters: `124 / 1107`
- Machine checked formulas/parameters: `123 / 1107`

## Assurance

| Dimension | Status | Evidence |
|---|---|---|
| structural_completeness | `VERIFIED` | `scripts/validate_project_governance.py` |
| implementation_congruence | `PARTIAL` | `arxiv-daily-push/docs/governance/parameter_registry.csv, arxiv-daily-push/docs/governance/formula_registry.yaml` |
| parameter_source_quality | `VERIFIED` | `arxiv-daily-push/docs/governance/parameter_registry.csv` |
| methodological_rationale | `VERIFIED` | `arxiv-daily-push/docs/governance/MODEL_SPEC.md` |
| empirical_validation | `VERIFIED` | `arxiv-daily-push/docs/governance/delivery_tasks.yaml` |
| operational_validation | `VERIFIED` | `arxiv-daily-push/docs/governance/development_events.jsonl` |
| delivery_evidence | `VERIFIED` | `arxiv-daily-push/docs/governance/delivery_tasks.yaml` |
| evidence_freshness | `PARTIAL` | `arxiv-daily-push/docs/governance/development_events.jsonl` |

## Delivery

- Readiness: `VERIFIED`
- Release gate: `UNKNOWN`
- Next executable task: `NONE`
- Pending/stale events: `405`
- Tree-bound events: `17`
- Commit-bound events: `13`
- Legacy unbound events: `334`
- Unresolved fact IDs: `1`
