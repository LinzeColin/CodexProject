# IDS v0.1 STAGE-029 Phase 2 Cleanup Allowlist Slice

## Scope
- Stage: `STAGE-029 · 压缩包清理白名单`
- Task: `IDS-V0_1-STAGE029-P2`
- Acceptance: `ACC-STAGE-029`
- Local code: `D05-S006`
- Entrance: `IDS 系统运营入口`
- Phase: `Phase 2 · 实现、接入与最小可运行切片`
- Helper: `KM_IDSystem/scripts/check_archive_cleanup_allowlist.py`
- Main function: `build_archive_cleanup_allowlist`
- Schema: `ids.stage029.archive_cleanup_allowlist.v1`
- Recorded at UTC: `2026-07-03T12:26:00Z`

## Implemented Slice
`build_archive_cleanup_allowlist` composes the earlier archive chain and returns
an in-memory cleanup allowlist plan:

- `STAGE-024` archive threat boundary supplies safe extraction, path filtering, limits, no-overwrite, no-out-of-staging, raw-root blocking, and archive entry risk states.
- `STAGE-025` safe extraction maps the threat boundary into safe extraction states.
- `STAGE-028` archive adversarial slice supplies risk marking, quarantine, owner review, cleanup candidate validation, and post-extract reingest requirements.
- `STAGE-029` adds cleanup allowlist classification, protected refs, cleanup decision state, no-delete guarantees, and no runtime-output guarantees.

The helper uses process-owned temporary archive fixtures in tests. Those fixtures
are built from tracked governance document bytes only. They are not IDS corpus,
database rows, business evidence, raw metadata, committed examples, or user
production data.

## States
- `ARCHIVE_CLEANUP_READY_FOR_TEMP_CLEANUP`: all ready candidates are explicit `ARCHIVE_STAGING_TEMP_FILE` entries under staging and protected refs are preserved.
- `ARCHIVE_CLEANUP_OWNER_REVIEW_REQUIRED`: failed, risky, over-limit, unsupported, or blocked protected cleanup candidates require owner review.
- `ARCHIVE_CLEANUP_BLOCKED_PROTECTED_REF`: a candidate points at original archive, original material, archive_manifest, evidence, audit, report, database, index, parser output, or raw metadata.
- `ARCHIVE_CLEANUP_QUARANTINE_REQUIRED`: risk or over-limit archive entries must remain in quarantine routing instead of cleanup.

## Fields
- `archive_cleanup_allowlist_id`
- `archive_security_boundary_id`
- `cleanup_request_ref`
- `archive_source_uri`
- `original_archive_ref`
- `archive_staging_area_uri`
- `archive_manifest_ref`
- `safe_extraction_ref`
- `post_extract_reingest_ref`
- `cleanup_candidates`
- `cleanup_candidate_uri`
- `cleanup_candidate_class`
- `cleanup_allowlist`
- `cleanup_decision_state`
- `cleanup_reason_code`
- `cleanup_protected_ref`
- `protected_refs`
- `manual_review_routing`
- `reingest_validation`
- `no_persistence_deltas`

## Protected Refs
- `PROTECTED_ORIGINAL_ARCHIVE`
- `PROTECTED_ORIGINAL_MATERIAL`
- `PROTECTED_ARCHIVE_MANIFEST`
- `PROTECTED_EVIDENCE_LEDGER`
- `PROTECTED_AUDIT_LOG`
- `PROTECTED_DELIVERED_REPORT`
- `PROTECTED_DATABASE_OR_INDEX`
- `PROTECTED_RAW_METADATA_ROOT`: `/Users/linzezhang/Downloads/IDS_MetaData`
- `file:///Users/linzezhang/Downloads/IDS_MetaData/...` cleanup candidates are also
  treated as protected raw metadata references.

## Reingest Rules
Extracted files that pass safe extraction are only routed as an in-memory plan
for `hash`, `manifest`, `dedup`, and `parser`.

No hash job, manifest job, dedup job, parser job, OCR job, Embedding job, index
job, import job, external API call, database write, evidence ledger write, audit
log write, report write, runtime output, document row, chunk row, job row, index
row, or import row is started or persisted by this Phase 2 helper.

## Manual Review And Quarantine
解压失败、风险文件、路径穿越、绝对路径、超限文件、嵌套超限、乱码文件名、
unsupported format、adapter-required file, and raw-root blocked sources are
routed to `owner review` or `quarantine`.

The helper does not treat owner review or quarantine routing as deletion
authorization.

## Cleanup Boundary
- 建立清理白名单.
- 只允许 future cleanup candidate class `ARCHIVE_STAGING_TEMP_FILE`.
- 不执行 cleanup runner.
- 不自动清理.
- 不删除任何文件.
- 不删除原始资料.
- 不删除原始压缩包.
- 不删除 manifest.
- 不删除 evidence.
- 不删除 audit.
- 不删除报告.
- 不删除 database、index、parser output、document/chunk/job/import row.
- 不写 archive_cleanup runtime output.
- 不写 archive_manifest runtime output.
- 不生成 runtime 输出、screenshot、PDF、JSON output、production report、manifest、database、evidence ledger、audit log、document/chunk/job/index/import row.
- 不启动 hash、manifest、dedup、parser、OCR、Embedding、索引或导入.
- 不安装依赖、不启动服务、不执行 GitHub upload、PR、merge 或 app reinstall.
- 不得读取、列出、hash、打开、复制、移动、删除、修改、dump 或扫描 `/Users/linzezhang/Downloads/IDS_MetaData` 内容.
- 不得使用虚构 IDS 业务数据、虚构数据库行、虚构源文档或伪造证据.
- `NO_PHASE3`: do not implement adversarial scenario matrix, delivery samples, cleanup execution, deletion, closeout, or owner feedback in this run.

## Test Evidence
- RED/GREEN: `python3 -B -m unittest KM_IDSystem.docs.pursuing_goal.ids_v0_1.tests.test_stage029_archive_cleanup_allowlist -q`
- RED/GREEN: `python3 -B -m unittest KM_IDSystem.docs.pursuing_goal.ids_v0_1.tests.test_stage005_governance_regression.Stage005GovernanceRegressionTests.test_phase_state_allows_stage029_phase2_archive_cleanup_allowlist_slice -q`
- Final validation is recorded in `KM_IDSystem/docs/governance/roadmap.yaml`.

## Rollback
Revert `check_archive_cleanup_allowlist.py`, this Phase 2 evidence file,
STAGE-029 focused tests, Stage005 validator/test updates, BATCH021_030 lock,
roadmap/event updates, compatibility test updates, and rendered owner files.
Do not touch `/Users/linzezhang/Downloads/IDS_MetaData`, original archives,
original materials, manifests, evidence ledgers, audit logs, reports, runtime
data, outputs, indexes, app entries, GitHub state, Phase 3 artifacts, or any
cleanup target outside an owner-approved future staging temp cleanup gate.
