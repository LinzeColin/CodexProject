# Project Governance Status

## Snapshot Metadata

- source_base_commit: `f8e34c0ce3919945ca055dd781332128c72dfc4a`
- source_tree_hash: `21090213e25901ab8342dbd710c64da57bd619b7`
- source_snapshot_hash: `sha256:9a7923506eb403fa07e31d1247a204b8aa33f42d66ac1d8484b05e6565cc96dc`
- snapshot_event_time: `2026-07-01T22:22:48+10:00`
- generator_version: `4.0.0`
- final_commit_binding: `PRECOMMIT_TREE_BOUND_PENDING_CI_ATTESTATION`

## Current State

- Project: `arxiv-daily-push`
- Path: `arxiv-daily-push`
- Product version: `0.23.1`
- Phase/Gate: `S2PL / DAILY_OPERATION_PERSISTENT_AUTHORIZATION_REQUEST_READY_NO_RUNTIME_ENABLEMENT`
- Models/Formulas/Parameters total: `121 / 123 / 1108`
- Active formulas/parameters: `123 / 1091`
- Machine checked formulas/parameters: `123 / 1091`

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

- Readiness: `BLOCKED_PRECHECK`
- Release gate: `DAILY_OPERATION_PERSISTENT_AUTHORIZATION_REQUEST_READY_NO_RUNTIME_ENABLEMENT`
- V7 contract: `ADP-PRODUCT-CONTRACT-V7.2`
- V7 contract hash: `a4de9e5d0fcd2be0290916bc50028b0c5cdeb1d84a57191b298ccfe0ec79428d`
- V7 roadmap hash: `7c5f2d842d4f6b909343c953fe39b4a4aa540d168199747a9f7decdb1aad9bd1`
- V7.1 parallel audit: `ADP-V7.2-FINAL-BASELINE-REVIEW`
- V7.1 audit hash: `571b3dbbc78d6dac01bd18472a0358f5ce4c51ac3d590c10d0c02e6453a7ea6c`
- Open audit blockers: `P0=8 / P1=37`
- Current zero-proof open findings: `P0=0 / P1=0`
- Baseline counts mutated: `false`
- Production-forbidden until: `DAILY_OPERATION separately authorized after accepted evidence; daily operation safety preflight passes; persistent operation boundary explicitly approved`
- Stage 2 stop gate: `INTEGRATED_PRODUCTION_ACCEPTED -> DAILY_OPERATION`
- Stage 2 integrated accepted: `true`
- Next governance task: `S2PMT07`
- Parallel shadow source task: `NONE_WHILE_S2PMT07_BLOCKED`
- Next executable task: `S2PMT07-DAILY-OPERATION-PERSISTENT-ENABLEMENT-AUTHORIZATION`
- Pending/stale events: `382`
- Tree-bound events: `13`
- Commit-bound events: `8`
- Legacy unbound events: `330`
- Unresolved fact IDs: `0`
