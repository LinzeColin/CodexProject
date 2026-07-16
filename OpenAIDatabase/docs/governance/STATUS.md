# Project Governance Status

## Snapshot Metadata

- source_base_commit: `00f4187f43960a3b25fc696ae2a15951f4431763`
- source_tree_hash: `6d67efb26a6ea61fd8b05706dbb3eb2f1d34ab9f`
- source_snapshot_hash: `sha256:71ff588f5cf2ec841b04e1ffc399d071fe2bee694040fcf243cdec99d54ae30f`
- snapshot_event_time: `2026-07-13T10:16:00+10:00`
- generator_version: `4.0.1`
- final_commit_binding: `PRECOMMIT_TREE_BOUND_PENDING_CI_ATTESTATION`

## Current State

- Project: `OpenAIDatabase`
- Path: `OpenAIDatabase`
- Product version: `0.2.0`
- Phase/Gate: `SM-P0-RUN1 / ACC-OAIDB-SM-P0-R1-PASSED-LOCAL`
- Models/Formulas/Parameters total: `12 / 12 / 99`
- Active formulas/parameters: `12 / 99`
- Machine checked formulas/parameters: `9 / 27`

## Assurance

| Dimension | Status | Evidence |
|---|---|---|
| structural_completeness | `VERIFIED` | `scripts/validate_project_governance.py` |
| implementation_congruence | `PARTIAL` | `OpenAIDatabase/docs/governance/parameter_registry.csv, OpenAIDatabase/docs/governance/formula_registry.yaml` |
| parameter_source_quality | `PARTIAL` | `OpenAIDatabase/docs/governance/parameter_registry.csv` |
| methodological_rationale | `UNVERIFIED` | `OpenAIDatabase/docs/governance/MODEL_SPEC.md` |
| empirical_validation | `UNVERIFIED` | `OpenAIDatabase/docs/governance/delivery_tasks.yaml` |
| operational_validation | `FAILED` | `OpenAIDatabase/docs/governance/development_events.jsonl` |
| delivery_evidence | `FAILED` | `OpenAIDatabase/docs/governance/delivery_tasks.yaml` |
| evidence_freshness | `PARTIAL` | `OpenAIDatabase/docs/governance/development_events.jsonl` |

## Delivery

- Readiness: `FAILED`
- Release gate: `ACC-OAIDB-SM-P0-R1-PASSED-LOCAL`
- Next executable task: `TASK-OAI-B-001`
- Pending/stale events: `22`
- Tree-bound events: `0`
- Commit-bound events: `3`
- Legacy unbound events: `6`
- Unresolved fact IDs: `10`

- 2026-07-15 炸弹A归档卸载：5 个大归档（6.08GB / 101 分片）经校验迁至 AgentDatabase，数据零丢失，仓库瘦身。见 GOV-BOMBA-ARCHIVES-20260715.json。

## Root Workflow Consolidation

- Local gate: `ACC.CodexProject.REPO1.0005 = PASS`
- Executable workflow: `.github/workflows/openai-database-ci.yml`
- Invalid nested workflow count: `0`
- Product/runtime impact: `NONE`
- Remote Actions evidence: `PENDING_WHOLE_PACKAGE_PUBLICATION`

## MacData Main-Only Migration

- Local gate: `TSK.OpenAIDatabase.CLEAN1.0001 = PASS_LOCAL_ENGINEERING`
- airM2 snapshot: `17 files / 90278 bytes / aggregate 9f0484dccd4a9e1ee684541fe59804425cda3a93a5049c0e552c4f5967bada15`
- proM2 snapshot: `17 files / 101713 bytes / aggregate 58fae909126367abd9733b1add8cd9b23b058be5eb609f04511ae55811724828`
- Publisher: `main-only Automation C short-lived PR with trusted Settlement and exact merge/file verification`
- GitHub mutations this Run: `0`
- Formal remote acceptance: `PENDING_WHOLE_PACKAGE_PUBLICATION`

## Repository Hygiene

- Local gate: `TSK.CodexProject.REPO1.0006 = PASS_LOCAL_ENGINEERING`
- Regular tracked blob limit: `1048576 bytes`
- Retained large objects / archives: `53 / 4`, all unique baseline-OID rules
- Tracked runtime noise / forbidden backup producers: `0 / 0`
- Scheduled raw-session archive commit producer: `DISABLED`
- History rewrite: `DEFERRED_NOT_AUTHORIZED`
- Product version/readiness impact: `NONE`
- Formal remote acceptance: `PENDING_WHOLE_PACKAGE_PUBLICATION`
