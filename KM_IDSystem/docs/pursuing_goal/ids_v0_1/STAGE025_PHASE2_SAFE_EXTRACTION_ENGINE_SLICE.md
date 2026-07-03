# IDS v0.1 STAGE-025 Phase 2 Safe Extraction Engine Slice

## Scope
- Stage: `STAGE-025 · 安全解压引擎`
- Task: `IDS-V0_1-STAGE025-P2`
- Acceptance: `ACC-STAGE-025`
- Entrance: `IDS 系统运营入口`
- Phase: `Phase 2 · 实现、接入与最小可运行切片`
- Recorded at UTC: `2026-07-03T05:42:18Z`

This phase adds `KM_IDSystem/scripts/check_safe_extraction_engine.py` and the
`run_safe_extraction_engine` function. It reuses the STAGE-024 archive threat
boundary for low-level archive handling, then emits STAGE-025-owned
`ids.stage025.safe_extraction_engine.v1` evidence.

## Implemented Slice
- 安全解压: ZIP/TAR entries that pass path, limit, staging, and overwrite checks are written only into the owner-approved staging area.
- 路径过滤: path traversal, absolute paths, drive prefixes, staging escapes, and garbled filenames are blocked or routed to review.
- 风险标记: unsafe entries receive `SAFE_EXTRACTION_*` risk codes.
- 重新进入导入管线: safe extracted entries receive a `POST_EXTRACT_REINGEST_REQUIRED` queue for `hash`, `manifest`, `dedup`, and `parser`.
- 人工复核: RAR/7Z adapter cases and mixed safe/risky archives return `SAFE_EXTRACTION_OWNER_REVIEW_REQUIRED`.
- 隔离状态: risk entries are mirrored into quarantine/owner-review entries.
- 清理白名单: only `ARCHIVE_STAGING_TEMP_FILE` staging temp entries are cleanup candidates.

## Risk Codes
- `SAFE_EXTRACTION_PATH_TRAVERSAL_BLOCKED`
- `SAFE_EXTRACTION_ABSOLUTE_PATH_BLOCKED`
- `SAFE_EXTRACTION_STAGING_ESCAPE_BLOCKED`
- `SAFE_EXTRACTION_FILE_COUNT_LIMIT_EXCEEDED`
- `SAFE_EXTRACTION_ENTRY_SIZE_LIMIT_EXCEEDED`
- `SAFE_EXTRACTION_TOTAL_SIZE_LIMIT_EXCEEDED`
- `SAFE_EXTRACTION_NESTED_DEPTH_LIMIT_EXCEEDED`
- `SAFE_EXTRACTION_GARBLED_FILENAME_OWNER_REVIEW_REQUIRED`
- `SAFE_EXTRACTION_STAGING_OVERWRITE_BLOCKED`
- `SAFE_EXTRACTION_ADAPTER_OWNER_REVIEW_REQUIRED`
- `SAFE_EXTRACTION_FORMAT_UNSUPPORTED`
- `SAFE_EXTRACTION_SOURCE_MISSING`
- `SAFE_EXTRACTION_SOURCE_BLOCKED_RAW_METADATA_ROOT`

## Runtime Boundary
- 不得读取、列出、hash、打开、复制、移动、删除、修改、dump 或扫描 `/Users/linzezhang/Downloads/IDS_MetaData` 内容.
- Does not read, list, hash, open, copy, move, delete, modify, dump, scan, normalize, or commit `/Users/linzezhang/Downloads/IDS_MetaData` raw metadata database content.
- Does not write archive_manifest runtime output, runtime reports, persisted manifests, evidence ledgers, audit logs, database rows, indexes, document/chunk/job/import rows, or production parser output.
- Does not start hash, manifest, dedup, parser, OCR, Embedding, index, import, backend, frontend, worker, or external API jobs.
- Does not fake RAR/7Z direct extraction support; those formats require owner-approved adapters.
- Does not push to GitHub, open or merge PRs, reinstall app entries, or enter Phase 3.

## Test Fixture Boundary
Focused tests use process-owned temporary structural archive fixtures only.
Those fixtures 不是 IDS corpus、database rows、business evidence、raw metadata 或 committed user data.

## Rollback
Revert `KM_IDSystem/scripts/check_safe_extraction_engine.py`, this Phase 2
evidence document, focused tests, BATCH021_030 lock update, Stage005
validator/test updates, roadmap/event changes, and rendered owner-file changes
only. Do not touch `/Users/linzezhang/Downloads/IDS_MetaData`, original
archives, fact sources, runtime data, reports, outputs, persisted manifests,
evidence ledgers, audit logs, indexes, app entries, GitHub state, or Phase 3
artifacts.

## Stop Marker
`NO_PHASE3`: this run must not add Phase 3 scenario matrix validation, archive
bomb scenario matrix, nested package scenario matrix, garbled filename scenario
matrix, too-many-files scenario matrix, owner closeout, GitHub upload, PR,
merge, or app reinstall.
