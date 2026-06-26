# Project Governance Status

## Snapshot Metadata

- source_base_commit: `631c8f65050be8e3c4379af5f4d0fd5753718808`
- source_tree_hash: `00e27599461403192b998e8f9a3f7f0e769e5d8f`
- source_snapshot_hash: `sha256:7c54a3c5bccbba28955e4bbf5c06815c44996965b66c98fe91c7f1069d328342`
- snapshot_event_time: `2026-06-26T12:12:07+10:00`
- generator_version: `4.0.0`
- final_commit_binding: `PRE_COMMIT_PENDING: T904/A026-A027 production gold-label source-boundary hardening is locally generated and focused-validated; remote CI not yet bound. A026/A027 remain open until real operator-supplied production labels meet thresholds, A210 remains open until formal clearance or signed waiver, and A209 remains open until 288/288 zero-failure evidence is promoted and release-ready validation passes.`

## Current State

- Project: `EEI`
- Path: `EEI`
- Product version: `0.1.0`
- Phase/Gate: `D / TASK-T904-A026-A027-GOLD-LABEL-SOURCE-BOUNDARY`
- Models/Formulas/Parameters total: `12 / 12 / 90`
- Active formulas/parameters: `11 / 90`
- Machine checked formulas/parameters: `11 / 90`

## Assurance

| Dimension | Status | Evidence |
|---|---|---|
| structural_completeness | `VERIFIED` | `scripts/validate_project_governance.py` |
| implementation_congruence | `VERIFIED` | `EEI/docs/governance/parameter_registry.csv, EEI/docs/governance/formula_registry.yaml` |
| parameter_source_quality | `VERIFIED` | `EEI/docs/governance/parameter_registry.csv` |
| methodological_rationale | `UNVERIFIED` | `EEI/docs/governance/MODEL_SPEC.md` |
| empirical_validation | `PARTIAL` | `EEI/docs/governance/delivery_tasks.yaml` |
| operational_validation | `PARTIAL` | `EEI/docs/governance/development_events.jsonl` |
| delivery_evidence | `FAILED` | `EEI/docs/governance/delivery_tasks.yaml` |
| evidence_freshness | `PARTIAL` | `EEI/docs/governance/development_events.jsonl` |

## Delivery

- Readiness: `FAILED`
- Release gate: `TASK-T904-A026-A027-GOLD-LABEL-SOURCE-BOUNDARY`
- Next executable task: `TASK-T904`
- Pending/stale events: `101`
- Tree-bound events: `0`
- Commit-bound events: `18`
- Legacy unbound events: `19`
- Unresolved fact IDs: `5`
