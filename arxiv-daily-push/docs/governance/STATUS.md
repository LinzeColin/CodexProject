# Project Governance Status

## Snapshot Metadata

- source_base_commit: `738887de4034ad42d90347d0fa0db6c0f3ed966f`
- source_tree_hash: `6d67efb26a6ea61fd8b05706dbb3eb2f1d34ab9f`
- source_snapshot_hash: `sha256:d39c8be3fed272f236414566df58c4d9dd650fe2106c2ebccc7a8e04af51a66b`
- snapshot_event_time: `2026-06-27T05:25:16+10:00`
- generator_version: `4.0.0`
- final_commit_binding: `PRECOMMIT_TREE_BOUND_PENDING_CI_ATTESTATION`

## Current State

- Project: `arxiv-daily-push`
- Path: `arxiv-daily-push`
- Product version: `0.23.1`
- Phase/Gate: `S2PM / S2PMT07_P1_C002_TECHNICAL_REVIEW_NO_CLOSURE_NO_PRODUCTION`
- Models/Formulas/Parameters total: `106 / 108 / 921`
- Active formulas/parameters: `108 / 904`
- Machine checked formulas/parameters: `108 / 904`

## Latest Local Update

- latest_task: `S2PMT07-P1-C002-TECHNICAL-REVIEW`
- latest_status: `finding_level_technical_review_passed_no_p1_closure_no_production`
- latest_findings: `C-002`
- evidence: `governance/run_manifests/ADP-S2PMT07-P1-C002-TECHNICAL-REVIEW-20260628.json`; `governance/run_manifests/ADP-S2PIT02-OWNER-STATUS-C002-RUNTIME-STATES-20260628.json`; `arxiv-daily-push/docs/phase_records/PHASE_S2PMT07_P1_C002_TECHNICAL_REVIEW.md`; `governance/run_manifests/ADP-S2PMT07-P1-INDEPENDENT-REVIEW-RECEIPT-20260626.json`
- production_boundary: inherited blockers remain `P0=8 / P1=37`; `stage2_integrated_production_accepted=false`; no SMTP, scheduler, Release, CURRENT/V7 contract, public schema, DB, production queue, source adapter, or ranking change.

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

- Readiness: `VERIFIED`
- Release gate: `S2PMT07_P1_C002_TECHNICAL_REVIEW_NO_CLOSURE_NO_PRODUCTION`
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
- Next executable task: `S2PLT01`
- Pending/stale events: `187`
- Tree-bound events: `0`
- Commit-bound events: `4`
- Legacy unbound events: `148`
- Unresolved fact IDs: `0`
