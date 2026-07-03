# STAGE-028 Phase 2 Archive Adversarial Slice

- Stage: `STAGE-028 · 压缩包对抗测试`
- Task: `IDS-V0_1-STAGE028-P2`
- Acceptance: `ACC-STAGE-028`
- Entrance: `IDS 系统运营入口`
- Script: `KM_IDSystem/scripts/check_archive_adversarial_tests.py`
- Schema: `ids.stage028.archive_adversarial_tests.v1`

## Delivery

Phase 2 implements the local archive adversarial testing slice by composing the existing Stage 025 safe extraction wrapper. The slice runs safe extraction, 路径过滤, 风险标记, 人工复核 routing, 隔离 routing, `cleanup allowlist` validation, and `post_extract_reingest` planning for safely extracted archive entries.

The returned in-memory report records:

- `ARCHIVE_ADVERSARIAL_PATH_TRAVERSAL_BLOCKED`
- `ARCHIVE_ADVERSARIAL_ABSOLUTE_PATH_BLOCKED`
- `ARCHIVE_ADVERSARIAL_FILE_COUNT_LIMIT_EXCEEDED`
- `ARCHIVE_ADVERSARIAL_NESTED_DEPTH_LIMIT_EXCEEDED`
- `ARCHIVE_ADVERSARIAL_GARBLED_FILENAME_OWNER_REVIEW_REQUIRED`
- `ARCHIVE_ADVERSARIAL_SOURCE_BLOCKED_RAW_METADATA_ROOT`
- `hash`, `manifest`, `dedup`, and `parser` as required post-extract pipeline stages
- zero started jobs and zero persistence deltas

## Data Boundary

`/Users/linzezhang/Downloads/IDS_MetaData` is recorded as a path-only read-only real database source boundary. This phase must not read, list, hash, open, copy, move, delete, modify, dump, scan, normalize, rename, compact, or commit raw database content from that local root.

中文边界：不得读取、列出、hash、打开、复制、移动、删除、修改、dump 或扫描 `/Users/linzezhang/Downloads/IDS_MetaData` 原始数据库内容。

Tests may create process-owned temporary ZIP files under the operating-system temp directory using bytes from tracked governance documents as payload. These temporary ZIP files are not IDS corpus, database rows, business evidence, raw metadata, committed examples, or user production data. They are deleted by the test process and are not written to Git.

## Persistence Guard

Phase 2 does not write `archive_adversarial` runtime output, `archive_manifest` runtime output, runtime reports, databases, evidence ledgers, audit logs, indexes, document rows, chunk rows, job rows, import rows, parser output, screenshots, PDFs, JSON files, or app-entry artifacts.

Phase 2 does not start hash, manifest, dedup, parser, OCR, Embedding, index, import, backend, frontend, worker, dependency install, or external API jobs. It does not create an import queue. It does not upload to GitHub, create or merge a PR, reinstall app entries, or enter Phase 3.

## Real Data Only

All committed business-facing records must use real user-approved data. 不得使用虚构 IDS 业务数据, fake database rows, fake source documents, placeholder corpora, or fabricated evidence.

## Stop Marker

`NO_PHASE3`: this run completes only Phase 2. Scenario validation for path traversal, absolute path, archive bomb, nested archives, garbled filenames, too many files, re-ingest behavior, and cleanup allowlist behavior remains Phase 3 work.
