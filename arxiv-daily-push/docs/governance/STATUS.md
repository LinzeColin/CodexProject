# Project Governance Status

## Snapshot Metadata

- source_base_commit: `fd90a208c7b009aa11bc26c4629a7ea92679c5ff`
- source_tree_hash: `c44d743a2833842b3cc0dd9e098fb70017cdc5a2`
- source_snapshot_hash: `sha256:5d1e25e69f353a9b13a3f9d463b25d2f9ed93fb69d2ee3f860bedf4ac199fb98`
- snapshot_event_time: `2026-06-29T23:21:34+10:00`
- generator_version: `4.0.0`
- final_commit_binding: `PRECOMMIT_TREE_BOUND_PENDING_CI_ATTESTATION`

## Current State

- Project: `arxiv-daily-push`
- Path: `arxiv-daily-push`
- Product version: `0.23.1`
- Phase/Gate: `S2PL / S2PLT02_TERMINAL_DELIVERY_PROOF_CAPTURE_PLAN_READY_NO_WRITE_NO_PRODUCTION`
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
- Release gate: `S2PLT02_TERMINAL_DELIVERY_PROOF_CAPTURE_PLAN_READY_NO_WRITE_NO_PRODUCTION`
- V7 contract: `ADP-PRODUCT-CONTRACT-V7.2`
- V7 contract hash: `a4de9e5d0fcd2be0290916bc50028b0c5cdeb1d84a57191b298ccfe0ec79428d`
- V7 roadmap hash: `7c5f2d842d4f6b909343c953fe39b4a4aa540d168199747a9f7decdb1aad9bd1`
- V7.1 parallel audit: `ADP-V7.2-FINAL-BASELINE-REVIEW`
- V7.1 audit hash: `571b3dbbc78d6dac01bd18472a0358f5ce4c51ac3d590c10d0c02e6453a7ea6c`
- Open audit blockers: `P0=8 / P1=37`
- Production-forbidden until: `inherited V7.1 P0=0; inherited V7.1 P1=0; S2PLT04 completed; final bundle present; S2PMT07 independent review passed`
- Stage 2 stop gate: `INTEGRATED_PRODUCTION_ACCEPTED -> DAILY_OPERATION`
- Stage 2 integrated accepted: `false`
- Next governance task: `S2PMT07`
- Parallel shadow source task: `NONE_WHILE_S2PMT07_BLOCKED`
- Next executable task: `S2PLT02-TERMINAL-DELIVERY-PROOF`
- Latest evidence sync: `S2PLT02-TERMINAL-DELIVERY-PROOF-CAPTURE-PLAN` adds a no-write ordered plan for the future terminal delivery proof capture/review sequence. Current missing inputs remain the second real delivery day, eight real emails, real scheduler proof, and `FINAL_ACCEPTANCE_BUNDLE/s2plt02_terminal_delivery_proof.json`; `next_executable_step=CAPTURE_SECOND_REAL_M1_M4_SMTP_DAY`, `artifact_written=false`, `real_smtp_send_enabled=false`, `scheduler_install_enabled=false`, current 2026-06-29/2026-06-30 capture evidence remains dry-run/scheduler-disabled, and S2PLT02/S2PLT03/S2PLT04/final bundle/production acceptance remain blocked.
- Pending/stale events: `314`
- Tree-bound events: `1`
- Commit-bound events: `4`
- Legacy unbound events: `274`
- Unresolved fact IDs: `0`
