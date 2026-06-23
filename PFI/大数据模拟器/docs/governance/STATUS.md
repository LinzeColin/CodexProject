# Project Governance Status

## Snapshot Metadata

- source_base_commit: `738887de4034ad42d90347d0fa0db6c0f3ed966f`
- source_tree_hash: `6d67efb26a6ea61fd8b05706dbb3eb2f1d34ab9f`
- source_snapshot_hash: `sha256:fd24bf9f219db8c72deda2fece6e6f0244793d018f41cda88688bfd3cf8bfbe5`
- snapshot_event_time: `2026-06-22T00:24:25Z`
- generator_version: `4.0.0`
- final_commit_binding: `CI_ATTESTED:governance/run_manifests/GOV-REVIEW6-FINAL-PORTFOLIO-001.json`

## Current State

- Project: `PFI_BIG_DATA_SIMULATOR`
- Path: `PFI/大数据模拟器`
- Product version: `0.1.0`
- Phase/Gate: `B / GOV-SEMANTIC-PFI-in-progress`
- Models/Formulas/Parameters total: `15 / 15 / 213`
- Active formulas/parameters: `15 / 213`
- Machine checked formulas/parameters: `15 / 211`

## Assurance

| Dimension | Status | Evidence |
|---|---|---|
| structural_completeness | `VERIFIED` | `scripts/validate_project_governance.py` |
| implementation_congruence | `PARTIAL` | `PFI/大数据模拟器/docs/governance/parameter_registry.csv, PFI/大数据模拟器/docs/governance/formula_registry.yaml` |
| parameter_source_quality | `PARTIAL` | `PFI/大数据模拟器/docs/governance/parameter_registry.csv` |
| methodological_rationale | `UNVERIFIED` | `PFI/大数据模拟器/docs/governance/MODEL_SPEC.md` |
| empirical_validation | `UNVERIFIED` | `PFI/大数据模拟器/docs/governance/delivery_tasks.yaml` |
| operational_validation | `FAILED` | `PFI/大数据模拟器/docs/governance/development_events.jsonl` |
| delivery_evidence | `UNVERIFIED` | `PFI/大数据模拟器/docs/governance/delivery_tasks.yaml` |
| evidence_freshness | `PARTIAL` | `PFI/大数据模拟器/docs/governance/development_events.jsonl` |

## Delivery

- Readiness: `UNVERIFIED`
- Release gate: `GOV-SEMANTIC-PFI-in-progress`
- Next executable task: `TASK-PFI-B-001`
- Pending/stale events: `4`
- Tree-bound events: `0`
- Commit-bound events: `1`
- Legacy unbound events: `3`
- Unresolved fact IDs: `14`
