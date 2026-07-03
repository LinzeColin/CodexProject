# STAGE-028 Phase 3 Scenario Validation

- Stage: `STAGE-028 · 压缩包对抗测试`
- Task: `IDS-V0_1-STAGE028-P3`
- Acceptance: `ACC-STAGE-028`
- Entrance: `IDS 系统运营入口`
- Script: `KM_IDSystem/scripts/check_archive_adversarial_tests.py`
- Scenario helper: `build_stage028_scenario_report`
- Schema: `ids.stage028.archive_adversarial_tests.scenario_validation.v1`

## Validated Scenarios

Phase 3 validates the archive adversarial protections required by the v0.1 taskpack:

- 路径穿越: `ARCHIVE_ADVERSARIAL_PATH_TRAVERSAL_BLOCKED`
- 绝对路径: `ARCHIVE_ADVERSARIAL_ABSOLUTE_PATH_BLOCKED`
- 压缩炸弹: `ARCHIVE_ADVERSARIAL_TOTAL_SIZE_LIMIT_EXCEEDED`
- 嵌套包: `ARCHIVE_ADVERSARIAL_NESTED_DEPTH_LIMIT_EXCEEDED`
- 乱码文件名: `ARCHIVE_ADVERSARIAL_GARBLED_FILENAME_OWNER_REVIEW_REQUIRED`
- 超大文件数: `ARCHIVE_ADVERSARIAL_FILE_COUNT_LIMIT_EXCEEDED`

The in-memory scenario report also validates `ARCHIVE_ADVERSARIAL_REINGEST_VALIDATED` for the required `hash`, `manifest`, `dedup`, and `parser` handoff, and `ARCHIVE_ADVERSARIAL_CLEANUP_ALLOWLIST_VALIDATED` for cleanup scope.

## Cleanup Boundary

Automatic cleanup is validated as staging-temp-only: 只清理允许的临时文件，不删除原始文件, fact sources, evidence products, manifests, audit logs, reports, indexes, database rows, or raw metadata. Original archive refs must not appear in `cleanup_allowlist`.

## Data Boundary

`/Users/linzezhang/Downloads/IDS_MetaData` remains a path-only read-only real database source boundary. 不得读取、列出、hash、打开、复制、移动、删除、修改、dump 或扫描 that raw database root.

Focused tests may create process-owned temporary archive fixtures under the operating-system temp directory using bytes from tracked governance documents. These fixtures are not IDS corpus, database rows, business evidence, raw metadata, or committed user data, and they are not committed to Git. 中文边界：这些临时 fixture 不是 IDS corpus、database rows、business evidence、raw metadata 或 committed user data。

## Persistence Guard

Phase 3 returns an in-memory validation report only. It does not write archive adversarial runtime output, archive manifest runtime output, import queues, reports, databases, evidence ledgers, audit logs, indexes, document/chunk/job/import rows, JSON files, screenshots, PDFs, or production parser output.

Phase 3 does not start hash, manifest, dedup, parser, OCR, Embedding, index, import, backend, frontend, worker, dependency install, or external API jobs. It does not upload to GitHub, create or merge a PR, reinstall app entries, or enter Phase 4.

## Stop Marker

`NO_PHASE4`: this run completes only Phase 3. Closeout, archive_manifest samples, safety block logs, rollback guide, and Chinese owner feedback remain Phase 4 work.
