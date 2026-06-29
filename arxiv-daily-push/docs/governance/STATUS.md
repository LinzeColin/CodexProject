# Project Governance Status

## Snapshot Metadata

- source_base_commit: `fd90a208c7b009aa11bc26c4629a7ea92679c5ff`
- source_tree_hash: `c44d743a2833842b3cc0dd9e098fb70017cdc5a2`
- source_snapshot_hash: `sha256:a4bb2aa1529ab2e719e847c15e7cc53103a1ca90b644ee225041f9a63769c9aa`
- snapshot_event_time: `2026-06-29T11:06:42+10:00`
- generator_version: `4.0.0`
- final_commit_binding: `PRECOMMIT_TREE_BOUND_PENDING_CI_ATTESTATION`

## Current State

- Project: `arxiv-daily-push`
- Path: `arxiv-daily-push`
- Product version: `0.23.1`
- Phase/Gate: `S2PL / S2PLT02_ZERO_PROOF_READINESS_SYNC_BLOCKED_NO_ACCEPTANCE`
- Models/Formulas/Parameters total: `118 / 120 / 1072`
- Active formulas/parameters: `120 / 1055`
- Machine checked formulas/parameters: `120 / 1055`

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
- Release gate: `S2PLT02_ZERO_PROOF_READINESS_SYNC_BLOCKED_NO_ACCEPTANCE`
- V7 contract: `ADP-PRODUCT-CONTRACT-V7.2`
- V7 contract hash: `a4de9e5d0fcd2be0290916bc50028b0c5cdeb1d84a57191b298ccfe0ec79428d`
- V7 roadmap hash: `7c5f2d842d4f6b909343c953fe39b4a4aa540d168199747a9f7decdb1aad9bd1`
- V7.1 parallel audit: `ADP-V7.2-FINAL-BASELINE-REVIEW`
- V7.1 audit hash: `571b3dbbc78d6dac01bd18472a0358f5ce4c51ac3d590c10d0c02e6453a7ea6c`
- P0/P1 zero-proof artifact: `pass`
- S2PLT02 P0/P1 readiness: `P0_ZERO=true / P1_ZERO=true`
- Historical V7.1 baseline ledger: `P0=8 / P1=37` remains read-only context, not a current S2PLT02 remaining blocker after zero-proof validation.
- Production-forbidden until: `S2PLT01 terminal acceptance; two consecutive real days; eight real emails; real scheduler proof; S2PLT03 terminal resilience; S2PLT04 completion report; final bundle; independent signoff; final command execution; scheduler/SMTP/Release/restore all pass`
- Stage 2 stop gate: `INTEGRATED_PRODUCTION_ACCEPTED -> DAILY_OPERATION`
- Stage 2 integrated accepted: `false`
- Next governance task: `S2PMT07`
- Parallel shadow source task: `NONE_WHILE_S2PMT07_BLOCKED`
- Next executable task: `S2PMT07-S2PLT04-COMPLETION-REPORT`
- Pending/stale events: `288`
- Tree-bound events: `0`
- Commit-bound events: `4`
- Legacy unbound events: `249`
- Unresolved fact IDs: `0`
