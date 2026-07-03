# IDS v0.1 STAGE-026 Phase 1 Scope Boundary

## Scope
- Stage: `STAGE-026 · 压缩包 Manifest`
- Task: `IDS-V0_1-STAGE026-P1`
- Acceptance: `ACC-STAGE-026`
- Entrance: `IDS 系统运营入口`
- Phase: `Phase 1 · 范围、输入输出与边界确认`
- Recorded at UTC: `2026-07-03T02:46:58Z`

This phase defines the future archive_manifest contract for safe archive
processing. It does not execute extraction, open archive bodies, enumerate real
archive entries, compute real archive hashes, create staging files, or create
runtime manifests.

## Contract Fields
- `archive_manifest_id`: stable id for one future archive manifest record.
- `archive_manifest_schema`: schema name for the future manifest payload.
- `archive_source_uri`: owner-approved local archive URI; path-only until a future gated run.
- `original_archive_ref`: immutable reference to the original archive; original archive content remains untouched.
- `archive_staging_area_uri`: approved staging root for future safe extraction results.
- `archive_hash_sha256`: future hash observation of the original archive; Phase 1 does not compute it.
- `archive_type`: future adapter classification such as ZIP, TAR, RAR, 7Z, or unsupported.
- `archive_entry_manifest`: future normalized extracted-entry list; Phase 1 does not enumerate real entries.
- `archive_entry_path_policy`: normalized relative path only; no absolute path, no parent traversal, no drive prefix, no symlink escape, no overwrite of existing files.
- `archive_file_count_limit`: maximum extracted file count before owner review or block.
- `archive_total_size_limit_bytes`: maximum total expanded bytes before owner review or block.
- `archive_single_file_size_limit_bytes`: maximum single extracted file size before owner review or block.
- `archive_nested_depth_limit`: maximum nested archive depth before owner review or block.
- `archive_failed_items`: future list of failed extraction or adapter items, with owner-visible reasons.
- `archive_risk_items`: future list of blocked or review-required entries, with risk codes and evidence refs.
- `archive_manifest_decision_state`: owner-visible archive_manifest gate state.

## Owner And System States
- `ARCHIVE_MANIFEST_DRAFT`: manifest boundary exists but no owner-approved source, staging area, or limits have been approved.
- `ARCHIVE_MANIFEST_BLOCKED`: source, hash identity, path policy, size, count, nested depth, overwrite risk, raw-data boundary, or staging boundary is unsafe.
- `ARCHIVE_MANIFEST_OWNER_REVIEW_REQUIRED`: failed items or risk items exist and owner must review before any future extraction can proceed.
- `ARCHIVE_MANIFEST_READY_FOR_SAFE_EXTRACTION`: metadata contract permits a future gated safe-extraction attempt.
- `POST_EXTRACT_REINGEST_REQUIRED`: any future extracted files must re-enter `hash`, `manifest`, `dedup`, and `parser` flow before indexing or import.

## Archive Manifest Contract
Future `archive_manifest_schema` must include:
- `archive_manifest_id`.
- original archive identity and immutable `original_archive_ref`.
- source URI and `archive_source_uri`.
- original archive `archive_hash_sha256`.
- staging root identity and `archive_staging_area_uri`.
- archive type and adapter decision.
- `archive_entry_manifest` with normalized relative entry paths only.
- file count, total expanded size, single-file size, and nested-depth estimates.
- path safety decision and reason codes.
- overwrite decision and reason codes.
- `archive_failed_items`.
- `archive_risk_items`.
- `archive_manifest_decision_state`.
- post-extract re-ingest requirement for `hash`, `manifest`, `dedup`, and `parser`.
- cleanup eligibility class for staging temp files only.

## Post-Extract Re-Ingest Rules
- Future extracted files cannot enter index/import directly from staging.
- Future extracted files must produce a new `hash` observation.
- Future extracted files must be included in a new or updated `manifest`.
- Future extracted files must pass `dedup` before parsing.
- Future extracted files must enter `parser` only after owner-approved staging and dedup state.
- Phase 1 records the rule only; it does not start hash, manifest, dedup, parser, OCR, Embedding, index, or import jobs.

## Boundary
- 不执行解压.
- 不覆盖原始压缩包.
- 不写出指定 staging 区.
- 不读取真实压缩包内容.
- 不枚举真实压缩包条目.
- 不计算真实压缩包 hash.
- 不移动、删除、覆盖原始文件.
- 不写 archive_manifest runtime output.
- 不创建 staging runtime directory.
- 不启动 hash、manifest、dedup、parser、OCR、Embedding、索引或导入.
- 不生成 runtime 输出、screenshot、PDF、JSON output、production report、manifest、database、evidence ledger、audit log、document/chunk/job/index/import row.
- 不安装依赖、不启动服务、不执行 GitHub upload、PR、merge 或 app reinstall.
- 不得读取、列出、hash、打开、复制、移动、删除、修改、dump 或扫描 `/Users/linzezhang/Downloads/IDS_MetaData` 内容.
- 不得使用虚构 IDS 业务数据、虚构数据库行、虚构源文档或伪造证据.
- `NO_PHASE2`: do not implement extraction, archive_manifest runtime output, manifest persistence, path filtering, risk marking, quarantine, cleanup allowlist runtime behavior, or post-extract pipeline execution in this run.

## Rollback
Revert this Phase 1 entry contract, scope boundary, focused tests, BATCH021_030
lock update, Stage005 validator/test updates, roadmap/event updates, and rendered
owner-file changes only. Do not touch `/Users/linzezhang/Downloads/IDS_MetaData`,
runtime data, reports, outputs, persisted manifests, evidence ledgers, audit
logs, indexes, app entries, GitHub state, or Phase 2 artifacts.
