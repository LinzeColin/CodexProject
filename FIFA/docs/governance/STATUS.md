# Project Governance Status

## Snapshot Metadata

- source_base_commit: `738887de4034ad42d90347d0fa0db6c0f3ed966f`
- source_tree_hash: `6d67efb26a6ea61fd8b05706dbb3eb2f1d34ab9f`
- source_snapshot_hash: `sha256:530356704dc42bfb7daf833344320167bde1a78e4623046130ddc691d6d6f76a`
- snapshot_event_time: `2026-06-22T00:24:25Z`
- generator_version: `4.0.0`
- final_commit_binding: `CI_ATTESTED:governance/run_manifests/GOV-REVIEW6-FINAL-PORTFOLIO-001.json`

## Current State

- Project: `FIFA`
- Path: `FIFA`
- Product version: `0.1.0`
- Phase/Gate: `B / GOV-SEMANTIC-FIFA-in-progress`
- Models/Formulas/Parameters total: `11 / 11 / 117`
- Active formulas/parameters: `10 / 108`
- Machine checked formulas/parameters: `10 / 91`

## Assurance

| Dimension | Status | Evidence |
|---|---|---|
| structural_completeness | `VERIFIED` | `scripts/validate_project_governance.py` |
| implementation_congruence | `PARTIAL` | `FIFA/docs/governance/parameter_registry.csv, FIFA/docs/governance/formula_registry.yaml` |
| parameter_source_quality | `PARTIAL` | `FIFA/docs/governance/parameter_registry.csv` |
| methodological_rationale | `UNVERIFIED` | `FIFA/docs/governance/MODEL_SPEC.md` |
| empirical_validation | `UNVERIFIED` | `FIFA/docs/governance/delivery_tasks.yaml` |
| operational_validation | `FAILED` | `FIFA/docs/governance/development_events.jsonl` |
| delivery_evidence | `UNVERIFIED` | `FIFA/docs/governance/delivery_tasks.yaml` |
| evidence_freshness | `PARTIAL` | `FIFA/docs/governance/development_events.jsonl` |

## Delivery

- Readiness: `UNVERIFIED`
- Release gate: `GOV-SEMANTIC-FIFA-in-progress`
- Next executable task: `TASK-FIFA-C-001`
- Pending/stale events: `4`
- Tree-bound events: `0`
- Commit-bound events: `5`
- Legacy unbound events: `3`
- Unresolved fact IDs: `6`
