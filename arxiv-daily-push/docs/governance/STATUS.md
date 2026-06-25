# Project Governance Status

## Snapshot Metadata

- source_base_commit: `738887de4034ad42d90347d0fa0db6c0f3ed966f`
- source_tree_hash: `6d67efb26a6ea61fd8b05706dbb3eb2f1d34ab9f`
- source_snapshot_hash: `sha256:4a8e16cb413af24c0988cb6f2b687aa726591fcf6115ff8cea1089f618f23961`
- snapshot_event_time: `2026-06-25T09:20:00+10:00`
- generator_version: `4.0.0`
- final_commit_binding: `PRECOMMIT_TREE_BOUND_PENDING_CI_ATTESTATION`

## Current State

- Project: `arxiv-daily-push`
- Path: `arxiv-daily-push`
- Product version: `0.23.0`
- Phase/Gate: `S2PF / S2PFT04_SPECIAL_ZONE_DISCOVERY_READY_NO_PRODUCTION`
- Models/Formulas/Parameters total: `68 / 70 / 497`
- Active formulas/parameters: `70 / 480`
- Machine checked formulas/parameters: `70 / 480`

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
- Release gate: `S2PFT04_SPECIAL_ZONE_DISCOVERY_READY_NO_PRODUCTION`
- V7 contract: `ADP-PRODUCT-CONTRACT-V7.2`
- V7 contract hash: `f6fe50017a2b91fda85dee2b5b0b36ad8847bf4d823ecbbe00f9202d6f96cae8`
- V7 roadmap hash: `fdca7b6c2deb3216794cfa764e220aa69beccbdd3b581950c78acb74087d1a56`
- V7.1 parallel audit: `ADP-V7.2-FINAL-BASELINE-REVIEW`
- V7.1 audit hash: `571b3dbbc78d6dac01bd18472a0358f5ce4c51ac3d590c10d0c02e6453a7ea6c`
- Open audit blockers: `P0=8 / P1=37`
- Production-forbidden until: `inherited V7.1 P0=0; inherited V7.1 P1=0; S2PMT07 independent review passed`
- Stage 2 stop gate: `INTEGRATED_PRODUCTION_ACCEPTED -> DAILY_OPERATION`
- Stage 2 integrated accepted: `false`
- Next governance task: `S2PFT05`
- Parallel shadow source task: `S2PBT01`
- Next executable task: `S2PFT05`
- Pending/stale events: `104`
- Tree-bound events: `0`
- Commit-bound events: `1`
- Legacy unbound events: `65`
- Unresolved fact IDs: `0`
