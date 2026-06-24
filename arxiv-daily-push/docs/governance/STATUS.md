# Project Governance Status

## Snapshot Metadata

- source_base_commit: `738887de4034ad42d90347d0fa0db6c0f3ed966f`
- source_tree_hash: `6d67efb26a6ea61fd8b05706dbb3eb2f1d34ab9f`
- source_snapshot_hash: `sha256:faae81238fdcadc99e1c57e38470b198ee99ba66291bd2c8e457bda8ae72a07d`
- snapshot_event_time: `2026-06-24T14:10:00+10:00`
- generator_version: `4.0.0`
- final_commit_binding: `PRECOMMIT_TREE_BOUND_PENDING_CI_ATTESTATION`

## Current State

- Project: `arxiv-daily-push`
- Path: `arxiv-daily-push`
- Product version: `0.23.0`
- Phase/Gate: `S2PC / ARXIV_PRODUCTION_ACCEPTED_MAINTAINED_AND_V7_1_PRODUCT_CONTRACT_AND_AUDIT_LOCKED`
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
- Release gate: `ARXIV_PRODUCTION_ACCEPTED_MAINTAINED_AND_V7_1_PRODUCT_CONTRACT_AND_AUDIT_LOCKED`
- V7 contract: `ADP-PRODUCT-CONTRACT-V7.1`
- V7 contract hash: `e51f306755629870f5a3693a50191c2291131d2224b91a8f3ef976e272eec7ad`
- V7 roadmap hash: `b3e9860042fcbbf67ef5c49c12d3da30dbf0ae217ff1fe44bd25580a52f7c1a6`
- V7.1 parallel audit: `ADP-PARALLEL-AUDIT-V7.1`
- V7.1 audit hash: `f102af13006e5a18de6ad71e6c2e6b9080ba06384dd6d26fd99019a9437dc165`
- Open audit blockers: `P0=8 / P1=37`
- Production-forbidden until: `P0=0; P1=0; S2PMT07 independent review passed`
- Stage 2 stop gate: `INTEGRATED_PRODUCTION_ACCEPTED -> DAILY_OPERATION`
- Stage 2 integrated accepted: `false`
- Next governance task: `S2PCT02`
- Parallel shadow source task: `S2PBT01`
- Next executable task: `S2PCT02`
- Pending/stale events: `94`
- Tree-bound events: `0`
- Commit-bound events: `1`
- Legacy unbound events: `55`
- Unresolved fact IDs: `0`
