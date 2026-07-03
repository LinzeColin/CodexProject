# Project Governance Status

## Snapshot Metadata

- source_base_commit: `90b297a55451b691c3e0270cfaa64e5d58c5a519`
- source_tree_hash: `d92ec4a0cd884641263c7979f7a5c625229ae83c`
- source_snapshot_hash: `sha256:13ab6ed272aac45973ea469a8cb6a6e481c6de60331b24f19735644717a9737b`
- snapshot_event_time: `2026-07-01T23:35:39+10:00`
- generator_version: `4.0.1`
- final_commit_binding: `COMMIT_BOUND:90b297a55451b691c3e0270cfaa64e5d58c5a519`

## Current State

- Project: `arxiv-daily-push`
- Path: `arxiv-daily-push`
- Product version: `0.23.1`
- Phase/Gate: `S2PL / DAILY_OPERATION_OWNER_DECISION_AFTER_REQUEST_MAINLINE_ATTESTED_KEEP_DISABLED_NO_RUNTIME_ENABLEMENT`
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

- Readiness: `BLOCKED_PERSISTENT_DAILY_OPERATION_AUTHORIZATION_MISSING`
- Release gate: `DAILY_OPERATION_OWNER_DECISION_AFTER_REQUEST_MAINLINE_ATTESTED_KEEP_DISABLED_NO_RUNTIME_ENABLEMENT`
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
- Parallel shadow source task: `NONE_UNTIL_PRODUCTION_BOUNDARY_REVIEW`
- Next executable task: `S2PMT07-DAILY-OPERATION-PERSISTENT-ENABLEMENT-AUTHORIZATION`
- Pending/stale events: `383`
- Tree-bound events: `13`
- Commit-bound events: `10`
- Legacy unbound events: `331`
- Unresolved fact IDs: `0`
