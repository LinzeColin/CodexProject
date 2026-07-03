# IDS v0.1 STAGE-024 Phase 1 Scope Boundary

## Scope
- Stage: `STAGE-024 · 压缩包威胁模型`
- Task: `IDS-V0_1-STAGE024-P1`
- Acceptance: `ACC-STAGE-024`
- Entrance: `IDS 系统运营入口`
- Phase: `Phase 1 · 范围、输入输出与边界确认`
- Recorded at UTC: `2026-07-03T02:34:11Z`

This phase defines a contract for future safe archive extraction. It does not
extract archives, open archive bodies, enumerate archive entries, create
staging files, or create runtime manifests.

## Contract Fields
- `archive_security_boundary_id`: stable id for the archive threat-model boundary.
- `archive_source_uri`: owner-approved local archive URI, path-only until a later gated extractor exists.
- `original_archive_ref`: immutable reference to the original archive; original archive content remains untouched.
- `archive_staging_area_uri`: approved staging root for future safe extraction.
- `archive_manifest_ref`: future manifest reference; Phase 1 does not write it.
- `archive_manifest_schema`: schema name for the future archive manifest.
- `archive_file_count_limit`: maximum extracted file count before owner review or block.
- `archive_total_size_limit_bytes`: maximum total expanded bytes before owner review or block.
- `archive_single_file_size_limit_bytes`: maximum single extracted file size before owner review or block.
- `archive_nested_depth_limit`: maximum nested archive depth before owner review or block.
- `archive_entry_path_policy`: normalized relative path only; no absolute path, no parent traversal, no drive prefix, no symlink escape.
- `archive_extract_decision_state`: owner-visible extraction gate state.

## Owner And System States
- `ARCHIVE_EXTRACTION_DRAFT`: boundary exists but no owner-approved source or staging decision has been made.
- `ARCHIVE_EXTRACTION_BLOCKED`: source, path policy, size, count, nested depth, or staging boundary is unsafe.
- `ARCHIVE_EXTRACTION_OWNER_REVIEW_REQUIRED`: risk exists and owner must review before any future extraction.
- `ARCHIVE_EXTRACTION_READY_FOR_SAFE_STAGING`: metadata contract permits a future gated safe-staging attempt.
- `ARCHIVE_MANIFEST_DRAFT`: archive manifest is planned but not written by Phase 1.
- `POST_EXTRACT_REINGEST_REQUIRED`: any future extracted files must re-enter `hash`, `manifest`, `dedup`, and `parser` flow before indexing or import.

## Archive Manifest Contract
Future `archive_manifest_schema` must include:
- original archive identity and immutable `original_archive_ref`.
- staging root identity and `archive_staging_area_uri`.
- archive type: `ZIP`, `RAR`, `7Z`, or `TAR`.
- normalized relative entry paths only.
- file count, total expanded size, single-file size, and nested-depth estimates.
- path safety decision and reason codes.
- extraction decision state.
- post-extract re-ingest requirement for `hash`, `manifest`, `dedup`, and `parser`.

## Boundary
- 不自动解压.
- 不覆盖原始压缩包.
- 不写出指定 staging 区.
- 不移动、删除、覆盖原始文件.
- 不写 archive_manifest runtime output.
- 不创建 staging runtime directory.
- 不启动 hash、manifest、dedup、parser、OCR、Embedding、索引或导入.
- 不生成 runtime 输出、screenshot、PDF、JSON output、production report、manifest、database、evidence ledger、audit log、document/chunk/job/index/import row.
- 不安装依赖、不启动服务、不执行 GitHub upload、PR、merge 或 app reinstall.
- 不得读取、列出、hash、打开、复制、移动、删除、修改、dump 或扫描 `/Users/linzezhang/Downloads/IDS_MetaData` 内容.
- 不得使用虚构 IDS 业务数据、虚构数据库行、虚构源文档或伪造证据.
- `NO_PHASE2`: do not implement safe extraction, path filtering, risk marking, quarantine, cleanup allowlist runtime behavior, or post-extract pipeline execution in this run.

## Rollback
Revert this Phase 1 entry contract, scope boundary, focused tests, BATCH021_030
lock update, Stage005 validator/test updates, roadmap/event updates, and rendered
owner-file changes only. Do not touch `/Users/linzezhang/Downloads/IDS_MetaData`,
runtime data, reports, outputs, persisted manifests, evidence ledgers, audit
logs, indexes, app entries, GitHub state, or Phase 2 artifacts.
