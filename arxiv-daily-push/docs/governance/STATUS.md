# Project Governance Status

## Snapshot Metadata

- source_base_commit: `97d5abf6f2f22e77c3bbf85b73a97129262c8b41`
- source_tree_hash: `4375e46be3b7c9f712f8b21962a0a0c69da57a3f`
- source_snapshot_hash: `sha256:66397a1ffc7c36e24257059947b1c2dff367e9a83d1f1a682d5b04674df8b1ab`
- snapshot_event_time: `2026-07-16T16:30:00+10:00`
- generator_version: `4.0.1`
- final_commit_binding: `PRECOMMIT_TREE_BOUND_PENDING_CI_ATTESTATION`

## Current State

- Project: `arxiv-daily-push`
- Path: `arxiv-daily-push`
- Product version: `0.23.1`
- Phase/Gate: `V03 / V03_R0_R4_DELIVERED_ZERO_PRODUCTION_SIDE_EFFECTS_AWAITING_OWNER_PILOT_DECISION`
- Models/Formulas/Parameters total: `122 / 124 / 1124`
- Active formulas/parameters: `124 / 1107`
- Machine checked formulas/parameters: `123 / 1107`

## Assurance

| Dimension | Status | Evidence |
|---|---|---|
| structural_completeness | `VERIFIED` | `scripts/validate_project_governance.py` |
| implementation_congruence | `PARTIAL` | `arxiv-daily-push/docs/governance/parameter_registry.csv, arxiv-daily-push/docs/governance/formula_registry.yaml` |
| parameter_source_quality | `VERIFIED` | `arxiv-daily-push/docs/governance/parameter_registry.csv` |
| methodological_rationale | `VERIFIED` | `arxiv-daily-push/docs/governance/MODEL_SPEC.md` |
| empirical_validation | `VERIFIED` | `arxiv-daily-push/docs/governance/delivery_tasks.yaml` |
| operational_validation | `VERIFIED` | `arxiv-daily-push/docs/governance/development_events.jsonl` |
| delivery_evidence | `VERIFIED` | `arxiv-daily-push/docs/governance/delivery_tasks.yaml` |
| evidence_freshness | `PARTIAL` | `arxiv-daily-push/docs/governance/development_events.jsonl` |

## Delivery

- Readiness: `BLOCKED_PERSISTENT_DAILY_OPERATION_AUTHORIZATION_MISSING`
- Release gate: `V03_R0_R4_DELIVERED_ZERO_PRODUCTION_SIDE_EFFECTS_AWAITING_OWNER_PILOT_DECISION`
- V7 contract: `ADP-PRODUCT-CONTRACT-V7.2`
- V7 contract hash: `e123aa93b07ba9a33ed6629ff3446c1ab53ce67191d1c4a587eaaa26d6161c74`
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
- Pending/stale events: `426`
- Tree-bound events: `17`
- Commit-bound events: `13`
- Legacy unbound events: `334`
- Unresolved fact IDs: `1`
