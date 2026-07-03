# STAGE-026 Phase 2 Archive Manifest Slice

- Stage: `STAGE-026`
- Task: `IDS-V0_1-STAGE026-P2`
- Acceptance: `ACC-STAGE-026`
- Entrance: `IDS 系统运营入口`
- Implemented at: `2026-07-03T03:04:39Z`
- Script: `KM_IDSystem/scripts/check_archive_manifest.py`
- Public helper: `build_archive_manifest`
- Schema: `ids.stage026.archive_manifest.v1`
- Source schema: `ids.stage025.safe_extraction_engine.v1`

## Implemented Slice

Phase 2 implements the in-memory archive manifest wrapper for safe archive ingestion. It records:

- 压缩包 hash: `archive_hash_sha256` for owner-approved non-raw local archive files.
- 解压文件列表: `archive_entry_manifest` with source entry path, normalized path when available, size, state, staging URI when safe, risk code, and nested archive depth.
- 解压体积: `safe_extracted_total_size_bytes` and `safe_extracted_file_count`.
- 嵌套层级: `max_nested_archive_depth_observed`.
- 失败项: `archive_failed_items`.
- 风险项: `archive_risk_items`.
- Post-extract re-entry: `POST_EXTRACT_REINGEST_REQUIRED` with `hash`, `manifest`, `dedup`, and `parser`.
- Cleanup boundary: `cleanup allowlist` only allows `ARCHIVE_STAGING_TEMP_FILE`.

The wrapper reuses the Stage 025 safe extraction engine. Supported direct extraction remains ZIP/TAR through owner-approved `archive_uri` and `staging_area_uri`. RAR/7Z stay in owner review with `ARCHIVE_MANIFEST_ADAPTER_OWNER_REVIEW_REQUIRED`; this phase does not fake RAR/7Z support.

## State Routing

- `ARCHIVE_MANIFEST_READY_FOR_REINGEST`: safe entries are staged and ready for post-extract re-ingest planning.
- `ARCHIVE_MANIFEST_OWNER_REVIEW_REQUIRED`: safe entries may exist but one or more risk/adapter/limit findings require owner review.
- `ARCHIVE_MANIFEST_BLOCKED`: source missing, raw-root source/staging path, unsupported format, or fully blocked archive.
- `ARCHIVE_MANIFEST_ENTRY_QUARANTINE_REQUIRED`: risk, failed, over-limit, traversal, absolute path, nested-depth, overwrite, adapter, or non-file entries are routed to quarantine/manual review.

## Raw Data Boundary

The raw database root is recorded only as a path boundary: `/Users/linzezhang/Downloads/IDS_MetaData`.

This phase does not read, list, hash, open, copy, move, delete, modify, dump, scan, normalize, or commit raw database content under that root. The helper returns `ARCHIVE_MANIFEST_SOURCE_BLOCKED_RAW_METADATA_ROOT` before archive hash or file access when `archive_uri` or `staging_area_uri` is under that root.

All focused tests use process-owned temporary structural archives only. Those fixtures are not IDS corpus, database rows, user evidence, raw metadata, committed examples, or fabricated business data.

## No Runtime Output

Phase 2 returns an in-memory manifest payload only.

It does not write archive_manifest runtime output, runtime reports, JSON output files, databases, evidence ledgers, audit logs, indexes, document/chunk/job/import rows, parser output, screenshots, PDFs, app entries, GitHub state, or service state. It does not start hash, manifest, dedup, parser, OCR, Embedding, index, import, backend, frontend, worker, dependency install, or external API jobs.

## Cleanup And Rollback

The cleanup allowlist is limited to `ARCHIVE_STAGING_TEMP_FILE` paths generated in the owner-approved staging area. It explicitly keeps 不清理事实源和证据产物:

- original archives;
- fact sources;
- evidence products;
- manifests;
- audit outputs;
- raw metadata;
- GitHub/app-entry state.

Rollback for this phase is to revert `KM_IDSystem/scripts/check_archive_manifest.py`, this evidence file, focused tests, Stage005 validator/test updates, `BATCH021_030_UPLOAD_LOCK.yaml`, roadmap/event updates, and rendered owner files. Do not clean original archives, facts, raw metadata, or evidence products.

## Explicit Non-Scope

`NO_PHASE3`: this run does not perform scenario matrix validation, whole-stage closeout, batch upload, GitHub push/PR/merge, issue cleanup, app reinstall, real IDS corpus processing, or production archive ingestion.
