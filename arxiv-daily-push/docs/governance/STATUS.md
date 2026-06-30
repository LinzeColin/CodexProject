# Project Governance Status

## Snapshot Metadata

- source_base_commit: `fd90a208c7b009aa11bc26c4629a7ea92679c5ff`
- source_tree_hash: `c44d743a2833842b3cc0dd9e098fb70017cdc5a2`
- source_snapshot_hash: `sha256:33d61400aa5e461ec4512d546b2ceca25cac9804e4261e1a994ba1e9aa56fc01`
- snapshot_event_time: `2026-06-30T15:31:00+10:00`
- generator_version: `4.0.0`
- final_commit_binding: `PRECOMMIT_TREE_BOUND_PENDING_CI_ATTESTATION`

## Current State

- Project: `arxiv-daily-push`
- Path: `arxiv-daily-push`
- Product version: `0.23.1`
- Phase/Gate: `S2PL / S2PMT07_FINAL_BUNDLE_S2PLT02_CAPTURE_COMMAND_SYNC_BLOCKED_NO_PRODUCTION`
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
- Release gate: `S2PMT07_FINAL_BUNDLE_S2PLT02_CAPTURE_COMMAND_SYNC_BLOCKED_NO_PRODUCTION`
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
- Pending/stale events: `332`
- Tree-bound events: `1`
- Commit-bound events: `4`
- Legacy unbound events: `289`
- Unresolved fact IDs: `0`
