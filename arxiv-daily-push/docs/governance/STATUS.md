# Project Governance Status

## Snapshot Metadata

- source_base_commit: `989b481dcc32d5a754281ae5863551fdae89da55`
- source_tree_hash: `PRECOMMIT_TREE_BOUND_PENDING_CI_ATTESTATION`
- source_snapshot_hash: `sha256:b46b66adca9fff016c8699d25d2f20031291631ddbc6e9ee00fc360126a9647f`
- snapshot_event_time: `2026-06-28T04:13:16+10:00`
- generator_version: `4.0.0`
- final_commit_binding: `PRECOMMIT_TREE_BOUND_PENDING_CI_ATTESTATION`

## Current State

- Project: `arxiv-daily-push`
- Path: `arxiv-daily-push`
- Product version: `0.23.1`
- Phase/Gate: `S2PM / S2PMT07_P0_P1_TECHNICAL_CANDIDATE_READINESS_BLOCKED_NO_PRODUCTION`
- Models/Formulas/Parameters total: `117 / 119 / 995`
- Active formulas/parameters: `119 / 978`
- Machine checked formulas/parameters: `119 / 963`

## Assurance

| Dimension | Status | Evidence |
|---|---|---|
| structural_completeness | `VERIFIED` | `scripts/validate_project_governance.py` |
| implementation_congruence | `PARTIAL` | `arxiv-daily-push/docs/governance/parameter_registry.csv, arxiv-daily-push/docs/governance/formula_registry.yaml` |
| parameter_source_quality | `PARTIAL` | `arxiv-daily-push/docs/governance/parameter_registry.csv` |
| methodological_rationale | `VERIFIED` | `arxiv-daily-push/docs/governance/MODEL_SPEC.md` |
| empirical_validation | `VERIFIED` | `arxiv-daily-push/docs/governance/delivery_tasks.yaml` |
| operational_validation | `VERIFIED` | `arxiv-daily-push/docs/governance/development_events.jsonl` |
| delivery_evidence | `VERIFIED` | `arxiv-daily-push/docs/governance/delivery_tasks.yaml` |
| evidence_freshness | `PARTIAL` | `arxiv-daily-push/docs/governance/development_events.jsonl` |

## Delivery

- Readiness: `VERIFIED`
- Release gate: `S2PMT07_P0_P1_TECHNICAL_CANDIDATE_READINESS_BLOCKED_NO_PRODUCTION`
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
- Next executable task: `S2PMT07 final closure decision or S2PLT04 final-bundle prerequisite work`
- Pending/stale events: `227`
- Tree-bound events: `0`
- Commit-bound events: `4`
- Legacy unbound events: `188`
- Unresolved fact IDs: `1`
