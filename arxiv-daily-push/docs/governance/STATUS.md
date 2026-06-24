# Project Governance Status

## Snapshot Metadata

- source_base_commit: `738887de4034ad42d90347d0fa0db6c0f3ed966f`
- source_tree_hash: `6d67efb26a6ea61fd8b05706dbb3eb2f1d34ab9f`
- source_snapshot_hash: `sha256:fb97edae1ae538692313a2e23e88936f0ece73d5f9a3a7caa0e30a5144bad390`
- snapshot_event_time: `2026-06-24T20:55:00+10:00`
- generator_version: `4.0.0`
- final_commit_binding: `PRECOMMIT_TREE_BOUND_PENDING_CI_ATTESTATION`

## Current State

- Project: `arxiv-daily-push`
- Path: `arxiv-daily-push`
- Product version: `0.23.0`
- Phase/Gate: `S2PC / ARXIV_PRODUCTION_ACCEPTED_MAINTAINED_AND_V7_2_PRODUCT_CONTRACT_CURRENT`
- Models/Formulas/Parameters total: `52 / 54 / 381`
- Active formulas/parameters: `54 / 364`
- Machine checked formulas/parameters: `54 / 364`

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
- Release gate: `ARXIV_PRODUCTION_ACCEPTED_MAINTAINED_AND_V7_2_PRODUCT_CONTRACT_CURRENT`
- V7 contract: `ADP-PRODUCT-CONTRACT-V7.2`
- V7 contract hash: `a433a4e5d153d8ee849799a21b188a9c4e39036d1de75dd3f91c6ab315e7d5c6`
- V7 roadmap hash: `aa1aa0b1b0b532a7dc092d6ed124cddb3c9b097a67b969ee2c8d58eed2bd9378`
- V7.1 parallel audit: `ADP-V7.2-FINAL-BASELINE-REVIEW`
- V7.1 audit hash: `d0e8976a64334f48bce338cff93304ad8684ce25bd5c6b32bd651709326c97fb`
- Open audit blockers: `P0=8 / P1=37`
- Production-forbidden until: `inherited V7.1 P0=0; inherited V7.1 P1=0; S2PMT07 independent review passed`
- Stage 2 stop gate: `INTEGRATED_PRODUCTION_ACCEPTED -> DAILY_OPERATION`
- Stage 2 integrated accepted: `false`
- Next governance task: `S2PCT02`
- Parallel shadow source task: `S2PBT01`
- Next executable task: `S2PCT02`
- Pending/stale events: `98`
- Tree-bound events: `0`
- Commit-bound events: `1`
- Legacy unbound events: `59`
- Unresolved fact IDs: `0`
