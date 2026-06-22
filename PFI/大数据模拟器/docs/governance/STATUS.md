# Project Governance Status

## Snapshot Metadata

- source_base_commit: `3ce9066664bab17253a25da11529d8146d8b314f`
- source_snapshot_hash: `sha256:e25d489476560b5156602d62479643c3cef56bfdc51923e32a9c55346d9bcf54`
- snapshot_event_time: `2026-06-22T00:24:25Z`
- generator_version: `2.0.0`
- final_commit_binding: `CI_ATTESTATION_REQUIRED`

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
| structural_validation | `pass` | `scripts/validate_project_governance.py` |
| implementation_congruence | `partial` | `PFI/大数据模拟器/docs/governance/parameter_registry.csv, PFI/大数据模拟器/docs/governance/formula_registry.yaml` |
| empirical_validation | `unknown` | `PFI/大数据模拟器/docs/governance/delivery_tasks.yaml` |
| operational_evidence | `blocked` | `PFI/大数据模拟器/docs/governance/development_events.jsonl` |

## Delivery

- Readiness: `conditional`
- Release gate: `GOV-SEMANTIC-PFI-in-progress`
- Next executable task: `GOV-SEMANTIC-PFI-001`
- Pending/stale events: `4`
- Unresolved fact IDs: `14`
