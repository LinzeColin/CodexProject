# IDS v0.1 STAGE-029 Phase 1 Scope Boundary

## Scope
- Stage: `STAGE-029 · 压缩包清理白名单`
- Task: `IDS-V0_1-STAGE029-P1`
- Acceptance: `ACC-STAGE-029`
- Local code: `D05-S006`
- Entrance: `IDS 系统运营入口`
- Phase: `Phase 1 · 范围、输入输出与边界确认`
- Recorded at UTC: `2026-07-03T11:55:12Z`

This phase defines the future archive cleanup allowlist contract. It does not
run cleanup, delete files, open archive bodies, enumerate real archive entries,
extract archives, create staging files, write runtime manifests, write cleanup
logs, or start downstream processing.

## Contract Fields
- `archive_cleanup_allowlist_id`: stable id for one future cleanup allowlist evaluation.
- `archive_security_boundary_id`: stable id linked back to the `STAGE-024` threat model boundary.
- `cleanup_request_ref`: owner-approved future cleanup request reference.
- `archive_source_uri`: owner-approved archive URI, path-only until a later gated run.
- `original_archive_ref`: immutable reference to the original archive; original archive content remains untouched.
- `archive_staging_area_uri`: approved staging root for future temporary extraction files.
- `archive_manifest_ref`: future `STAGE-026` archive manifest reference; Phase 1 does not write it.
- `safe_extraction_ref`: future `STAGE-025` safe extraction reference; Phase 1 does not create it.
- `post_extract_reingest_ref`: future `STAGE-027` re-ingest reference; Phase 1 does not create it.
- `cleanup_candidate_uri`: candidate file URI, path-only until a later gated run.
- `cleanup_candidate_class`: classifies a candidate as `ARCHIVE_STAGING_TEMP_FILE` or protected material.
- `cleanup_allowlist_ref`: future explicit allowlist of temp files allowed for cleanup.
- `cleanup_decision_state`: owner-visible cleanup decision state.
- `cleanup_reason_code`: owner-visible reason for allowed, blocked, or review cleanup decision.
- `cleanup_protected_ref`: reference proving a candidate is protected and must not be cleaned.
- `archive_file_count_limit`: maximum extracted file count before owner review or block.
- `archive_total_size_limit_bytes`: maximum total expanded bytes before owner review or block.
- `archive_single_file_size_limit_bytes`: maximum single extracted file size before owner review or block.
- `archive_nested_depth_limit`: maximum nested archive depth before owner review or block.

## Owner And System States
- `ARCHIVE_CLEANUP_ALLOWLIST_DRAFT`: boundary exists but cleanup request, staging, candidate, manifest, and owner decision are incomplete.
- `ARCHIVE_CLEANUP_BLOCKED_PROTECTED_REF`: candidate matches original archive, original material, manifest, evidence, audit, report, database, index, or raw metadata.
- `ARCHIVE_CLEANUP_OWNER_REVIEW_REQUIRED`: candidate cannot be classified as temp-only or protected-only without owner review.
- `ARCHIVE_CLEANUP_READY_FOR_TEMP_CLEANUP`: metadata-only contract permits a future gated cleanup of explicit staging temp files.

## Candidate Classes
- `ARCHIVE_STAGING_TEMP_FILE`: process-owned temporary file under approved staging only.
- `PROTECTED_ORIGINAL_ARCHIVE`: original archive file or original archive reference.
- `PROTECTED_ORIGINAL_MATERIAL`: original raw material or source evidence.
- `PROTECTED_ARCHIVE_MANIFEST`: manifest and archive_manifest evidence.
- `PROTECTED_EVIDENCE_LEDGER`: evidence ledger and evidence products.
- `PROTECTED_AUDIT_LOG`: audit log.
- `PROTECTED_DELIVERED_REPORT`: generated or delivered reports, PDFs, report metadata, and report evidence.
- `PROTECTED_DATABASE_OR_INDEX`: runtime database, document/chunk/job/import row, index, or parser output.
- `PROTECTED_RAW_METADATA_ROOT`: `/Users/linzezhang/Downloads/IDS_MetaData`.

## Pipeline Rules
- `STAGE-024` threat model defines the security boundary and risk vocabulary.
- `STAGE-025` safe extraction engine must perform any future extraction in approved staging only.
- `STAGE-026` archive manifest must record archive identity, entry manifest, failed items, risk items, cleanup candidates, and original archive reference.
- `STAGE-027` re-ingest rules require future extracted files to enter `hash`, then `manifest`, then `dedup`, then `parser`.
- `STAGE-028` adversarial validation proves cleanup must remain temp-only after path traversal, absolute path, archive bomb, nested archive, garbled filename, and file-count scenarios.
- Cleanup may only use `cleanup_allowlist_ref`; it must not delete original archives, original materials, manifests, evidence ledgers, audit logs, delivered reports, databases, indexes, parser outputs, or raw metadata.

## Boundary
- 不执行 cleanup runner.
- 不自动清理.
- 不删除原始资料.
- 不删除原始压缩包.
- 不删除 manifest.
- 不删除 evidence.
- 不删除 audit.
- 不删除报告.
- 不自动解压.
- 不覆盖原始压缩包.
- 不写出指定 staging 区.
- 不移动、删除、覆盖原始文件.
- 不读取真实压缩包内容.
- 不枚举真实压缩包条目.
- 不写 archive_cleanup runtime output.
- 不写 archive_manifest runtime output.
- 不创建 staging runtime directory.
- 不生成 runtime 输出、screenshot、PDF、JSON output、production report、manifest、database、evidence ledger、audit log、document/chunk/job/index/import row.
- 不启动 hash、manifest、dedup、parser、OCR、Embedding、索引或导入.
- 不安装依赖、不启动服务、不执行 GitHub upload、PR、merge 或 app reinstall.
- 不得读取、列出、hash、打开、复制、移动、删除、修改、dump 或扫描 `/Users/linzezhang/Downloads/IDS_MetaData` 内容.
- 不得使用虚构 IDS 业务数据、虚构数据库行、虚构源文档或伪造证据.
- `NO_PHASE2`: do not implement cleanup runner, safe extraction, path filtering, risk marking, quarantine, cleanup runtime behavior, archive_manifest writes, deletion, or post-extract pipeline execution in this run.

## Rollback
Revert this Phase 1 entry contract, scope boundary, focused tests, BATCH021_030
lock update, Stage005 validator/test updates, roadmap/event updates, and rendered
owner-file changes only. Do not touch `/Users/linzezhang/Downloads/IDS_MetaData`,
runtime data, reports, outputs, persisted manifests, staging files, evidence
ledgers, audit logs, indexes, app entries, GitHub state, or Phase 2 artifacts.
