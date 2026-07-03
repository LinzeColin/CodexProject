# IDS v0.1 STAGE-025 Phase 4 Closeout

## Scope

- Stage: `STAGE-025 · 安全解压引擎`
- Task: `IDS-V0_1-STAGE025-P4`
- Acceptance: `ACC-STAGE-025`
- Entrance: `IDS 系统运营入口`
- Phase: `Phase 4 · 安全解压引擎 交付证据、回滚与中文反馈`
- Recorded at UTC: `2026-07-03T06:51:42Z`
- Schema: `ids.stage025.safe_extraction_engine.owner_feedback.v1`

This phase closes out STAGE-025 locally. It records owner-facing safe extraction
engine closeout evidence and whole-stage review results without creating
screenshots, PDF, JSON output files, runtime reports, archive_manifest runtime
output, databases, evidence ledgers, audit logs, indexes, app-entry changes, or
GitHub changes.

## archive_manifest 样例

The closeout helper `build_safe_extraction_engine_owner_feedback_summary(...)`
returns an in-memory `report_sample.archive_manifest_sample` from
`ids.stage025.archive_manifest.v1`. The sample contains:

- `archive_type`
- `original_archive_ref`
- `archive_staging_area_uri`
- `entry_count`
- `entries`
- `runtime_output_written=false`

This is a delivery evidence sample only. It is not persisted as a runtime
archive_manifest file and does not claim production corpus coverage.

## 安全阻断日志

The in-memory safety block log records risk entries from Phase 2 and Phase 3:

- `SAFE_EXTRACTION_PATH_TRAVERSAL_BLOCKED`
- `SAFE_EXTRACTION_ABSOLUTE_PATH_BLOCKED`
- `SAFE_EXTRACTION_TOTAL_SIZE_LIMIT_EXCEEDED`
- `SAFE_EXTRACTION_ENTRY_SIZE_LIMIT_EXCEEDED`
- `SAFE_EXTRACTION_NESTED_DEPTH_LIMIT_EXCEEDED`
- `SAFE_EXTRACTION_GARBLED_FILENAME_OWNER_REVIEW_REQUIRED`
- `SAFE_EXTRACTION_FILE_COUNT_LIMIT_EXCEEDED`
- `SAFE_EXTRACTION_ADAPTER_OWNER_REVIEW_REQUIRED`
- `SAFE_EXTRACTION_SOURCE_BLOCKED_RAW_METADATA_ROOT`
- `SAFE_EXTRACTION_STAGING_OVERWRITE_BLOCKED`

Blocked, owner-review, and quarantine states are owner-visible safety signals.
They are not permissions to continue extraction or parse archive body content.

## 清理白名单

The helper returns `cleanup_allowlist_sample` and
`staging_rollback_and_cleanup` with state
`SAFE_EXTRACTION_STAGING_ROLLBACK_GUIDE_READY`.

- 清理白名单 only allows `ARCHIVE_STAGING_TEMP_FILE`.
- `SAFE_EXTRACTION_CLEANUP_ALLOWLIST_VALIDATED` means cleanup targets are
  staging temp files only.
- 原始压缩包、事实源、证据产物、manifest、audit output、runtime database and
  `/Users/linzezhang/Downloads/IDS_MetaData` are never cleanup targets.

## 自动解压风险边界

- 不覆盖原始压缩包，不移动、删除、重写或修复原始文件。
- 不写出指定 staging 区，不覆盖 staging 中既有文件。
- RAR/7Z、乱码文件名、路径风险、超限和嵌套风险必须进入人工复核或隔离。
- 安全解压产物只进入 hash、manifest、dedup、parser re-ingest 计划，不启动实际处理 job。
- archive_manifest 样例和安全阻断日志只作为 closeout evidence，不写 runtime output。

## 停止条件

- 读取、列出、hash、打开、复制、移动、删除、修改、dump 或扫描 `/Users/linzezhang/Downloads/IDS_MetaData` 内容。
- 清理原始压缩包、事实源、证据产物、manifest、audit output 或 raw metadata。
- 绕过 staging 边界、路径过滤、owner review、quarantine 或 cleanup allowlist。
- 启动 hash、manifest、dedup、parser、OCR、Embedding、index、import、backend、frontend、worker 或 external API job。
- 写 runtime report、database、evidence ledger、audit log、index、document/chunk/job/import row 或 archive_manifest runtime output。
- 不执行 GitHub upload、PR、merge 或 app reinstall。
- `NO_STAGE026`: this run must not start STAGE-026 work.

## staging 区回滚与清理说明

1. Stop after Phase 4 closeout; do not enter STAGE-026 in the same run.
2. If rollback is needed, delete only owner-approved staging temp files listed in cleanup_allowlist.
3. Do not delete, move, overwrite, rewrite, repair, normalize, compact, or deduplicate the original archive or fact sources.
4. Return BATCH021_030 state to STAGE-025 Phase 3 complete and Phase 4 pending if this closeout is reverted.

## Whole-Stage Review

- Result: `passed_with_local_evidence`
- STAGE-025 已在本地完成.
- Completed phases: `Phase 1`, `Phase 2`, `Phase 3`, `Phase 4`
- Acceptance: `ACC-STAGE-025`
- Next gate: `IDS-STAGE026-P1-GATE`
- Batch upload: `push_allowed=false`
- GitHub upload: not started
- App reinstall: not started
- Unresolved findings: none

## Raw Data And Processing Boundary

- 不得读取、列出、hash、打开、复制、移动、删除、修改、dump 或扫描 `/Users/linzezhang/Downloads/IDS_MetaData` 内容.
- 不得使用虚构 IDS 业务数据、虚构数据库行、虚构源文档或伪造证据.
- Focused tests may use process-owned temporary structural archives only; those fixtures are not IDS corpus, database rows, business evidence, raw metadata, or committed user data.
- 不启动 hash、manifest、dedup、parser、OCR、Embedding、index、import、service、worker 或 external API.
- 不写 runtime data、reports、outputs、manifest、database、evidence ledger、audit log、document/chunk/job/index/import row.
