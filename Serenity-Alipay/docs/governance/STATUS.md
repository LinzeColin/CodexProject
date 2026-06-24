# Project Governance Status

## Snapshot Metadata

- source_base_commit: `738887de4034ad42d90347d0fa0db6c0f3ed966f`
- source_tree_hash: `6d67efb26a6ea61fd8b05706dbb3eb2f1d34ab9f`
- source_snapshot_hash: `sha256:8a5a8e00e84ed1ecf112cd0876b1cbbd34aa812c5d09691be581f5c2f1e6f856`
- snapshot_event_time: `2026-06-22T00:24:25Z`
- generator_version: `4.0.0`
- final_commit_binding: `CI_ATTESTED:governance/run_manifests/GOV-REVIEW6-FINAL-PORTFOLIO-001.json`

## Current State

- Project: `Serenity-Alipay`
- Path: `Serenity-Alipay`
- Product version: `0.1.0`
- Phase/Gate: `B / GOV-REVIEW6-B-SEMANTIC-EXTRACT`
- Models/Formulas/Parameters total: `5 / 12 / 49`
- Active formulas/parameters: `12 / 49`
- Machine checked formulas/parameters: `12 / 49`

## Assurance

| Dimension | Status | Evidence |
|---|---|---|
| structural_completeness | `VERIFIED` | `scripts/validate_project_governance.py` |
| implementation_congruence | `VERIFIED` | `Serenity-Alipay/docs/governance/parameter_registry.csv, Serenity-Alipay/docs/governance/formula_registry.yaml` |
| parameter_source_quality | `VERIFIED` | `Serenity-Alipay/docs/governance/parameter_registry.csv` |
| methodological_rationale | `UNVERIFIED` | `Serenity-Alipay/docs/governance/MODEL_SPEC.md` |
| empirical_validation | `UNVERIFIED` | `Serenity-Alipay/docs/governance/delivery_tasks.yaml` |
| operational_validation | `PARTIAL` | `Serenity-Alipay/docs/governance/development_events.jsonl` |
| delivery_evidence | `UNVERIFIED` | `Serenity-Alipay/docs/governance/delivery_tasks.yaml` |
| evidence_freshness | `PARTIAL` | `Serenity-Alipay/docs/governance/development_events.jsonl` |

## Delivery

- Readiness: `UNVERIFIED`
- Release gate: `GOV-REVIEW6-B-SEMANTIC-EXTRACT`
- Latest remediation task: `S3PCT03` completed with mocked/temporary lifecycle evidence only
- Next executable task: `NONE`
- Pending/stale events: `4`
- Tree-bound events: `0`
- Commit-bound events: `1`
- Legacy unbound events: `3`
- Unresolved fact IDs: `2`

## Latest Other8 Evidence

- `S3PCT03`: Serenity OpenD auto-wake ownership, close-cleanup, package atomicity, and launchd tick wrapper contracts passed focused local unittest evidence.
- Evidence refs: `governance/stage_gates/s3pc/serenity_lifecycle_matrix.csv`, `governance/stage_gates/s3pc/serenity_process_cleanup.log`, `governance/stage_gates/s3pc/serenity_persistence_recovery.log`.
- Boundary: no real OpenD process, mail send, trade, production package path, production data path, empirical calibration, or owner readiness approval was used or implied.
