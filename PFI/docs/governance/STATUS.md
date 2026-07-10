# Project Governance Status

## Snapshot Metadata

- source_base_commit: `47d36e0227d85849b2f7624c137c1f644bef13a0`
- source_tree_hash: `5f05ad339e9519bd5981b54e788f0dbeefbcac9c`
- source_snapshot_hash: `sha256:217a35eea7d1656c901b5557f43488ed2c0b1e70fcc226ec262ee2476c71d050`
- snapshot_event_time: `2026-07-10T17:50:45+10:00`
- generator_version: `4.0.1`
- final_commit_binding: `PRECOMMIT_TREE_BOUND_PENDING_CI_ATTESTATION`

## Current State

- Project: `PFI`
- Path: `PFI`
- Product version: `v0.2.2 数据库治理 Stage 4`
- Phase/Gate: `CF-L2 / ACC-CF-L2-20260710-BLOCKED-BY-WORKERS-AUTH`
- Models/Formulas/Parameters total: `1 / 1 / 23`
- Active formulas/parameters: `1 / 23`
- Machine checked formulas/parameters: `0 / 0`

## Assurance

| Dimension | Status | Evidence |
|---|---|---|
| structural_completeness | `VERIFIED` | `scripts/validate_project_governance.py` |
| implementation_congruence | `PARTIAL` | `PFI/docs/governance/parameter_registry.csv, PFI/docs/governance/formula_registry.yaml` |
| parameter_source_quality | `PARTIAL` | `PFI/docs/governance/parameter_registry.csv` |
| methodological_rationale | `VERIFIED` | `PFI/docs/governance/MODEL_SPEC.md` |
| empirical_validation | `UNVERIFIED` | `PFI/docs/governance/delivery_tasks.yaml` |
| operational_validation | `UNVERIFIED` | `PFI/docs/governance/development_events.jsonl` |
| delivery_evidence | `FAILED` | `PFI/docs/governance/delivery_tasks.yaml` |
| evidence_freshness | `PARTIAL` | `PFI/docs/governance/development_events.jsonl` |

## Delivery

- Readiness: `FAILED`
- Release gate: `ACC-CF-L2-20260710-BLOCKED-BY-WORKERS-AUTH`
- Next executable task: `CF-L2-20260710`
- Pending/stale events: `7`
- Tree-bound events: `0`
- Commit-bound events: `0`
- Legacy unbound events: `6`
- Unresolved fact IDs: `2`
