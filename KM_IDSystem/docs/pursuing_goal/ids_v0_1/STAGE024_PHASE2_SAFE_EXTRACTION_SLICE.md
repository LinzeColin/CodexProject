# IDS v0.1 STAGE-024 Phase 2 Safe Extraction Slice

## Scope
- Stage: `STAGE-024 · 压缩包威胁模型`
- Task: `IDS-V0_1-STAGE024-P2`
- Acceptance: `ACC-STAGE-024`
- Entrance: `IDS 系统运营入口`
- Phase: `Phase 2 · 实现、接入与最小可运行切片`
- Recorded at UTC: `2026-07-03T03:12:44Z`

Phase 2 implements a minimal safe extraction helper:

- script: `KM_IDSystem/scripts/check_archive_threat_model.py`
- primary API: `safe_extract_archive`
- output schema: `ids.stage024.archive_threat_model.v1`
- in-memory archive manifest schema: `ids.stage024.archive_manifest.v1`

## Implemented Contract
- ZIP and TAR: direct safe extraction into an owner-provided staging directory.
- RAR and 7Z: no fake extraction support; they enter `ARCHIVE_EXTRACTION_OWNER_REVIEW_REQUIRED` with `ARCHIVE_FORMAT_REQUIRES_EXTERNAL_ADAPTER`.
- 安全解压: only normalized relative file entries are written under the approved staging root.
- 路径过滤: absolute paths, parent traversal, staging escape, existing staging targets, non-file tar entries, nested-depth overflow, file count overflow, single-file size overflow, and total expanded-size overflow are blocked or quarantined.
- 风险标记: blocked and risky entries are returned in `risk_entries`, `owner_review_entries`, and `quarantine_entries`.
- 解压产物重新进入导入管线: safe staged files build `post_extract_reingest` with required pipeline `hash`, `manifest`, `dedup`, and `parser`.
- Failure, risk, and over-limit files enter owner review or quarantine state; they are not written to staging.
- 清理白名单: `cleanup_allowlist` contains only safe staging temp files and excludes the original archive, fact sources, evidence outputs, manifests, audit logs, databases, reports, and indexes.
- 清理白名单不清理事实源和证据产物.

## States And Risk Codes
- `ARCHIVE_EXTRACTION_READY_FOR_REINGEST`
- `ARCHIVE_EXTRACTION_OWNER_REVIEW_REQUIRED`
- `ARCHIVE_EXTRACTION_BLOCKED`
- `ARCHIVE_FORMAT_REQUIRES_EXTERNAL_ADAPTER`
- `ARCHIVE_FORMAT_UNSUPPORTED`
- `ARCHIVE_SOURCE_BLOCKED_RAW_METADATA_ROOT`
- `ARCHIVE_SOURCE_MISSING`
- `ARCHIVE_PATH_TRAVERSAL_BLOCKED`
- `ARCHIVE_ABSOLUTE_PATH_BLOCKED`
- `ARCHIVE_STAGING_ESCAPE_BLOCKED`
- `ARCHIVE_STAGING_TARGET_EXISTS`
- `ARCHIVE_FILE_COUNT_LIMIT_EXCEEDED`
- `ARCHIVE_TOTAL_SIZE_LIMIT_EXCEEDED`
- `ARCHIVE_ENTRY_SIZE_LIMIT_EXCEEDED`
- `ARCHIVE_NESTED_DEPTH_LIMIT_EXCEEDED`
- `ARCHIVE_NON_FILE_ENTRY_BLOCKED`
- `POST_EXTRACT_REINGEST_REQUIRED`

## No-Side-Effect Boundary
- Does not overwrite original archives.
- Does not write outside the approved staging root.
- Does not write `archive_manifest` runtime output.
- Does not write runtime report, database, evidence ledger, audit log, index, document, chunk, job, import, or parser output.
- Does not start actual `hash`, `manifest`, `dedup`, `parser`, OCR, Embedding, index, import, external API, backend, frontend, or worker jobs.
- Does not install dependencies.
- Does not execute GitHub upload, PR, merge, or app reinstall.
- Does not enter Phase 3.

## Raw Data Boundary
- 不得读取、列出、hash、打开、复制、移动、删除、修改、dump 或扫描 `/Users/linzezhang/Downloads/IDS_MetaData` 内容.
- If the archive URI or staging URI is under `/Users/linzezhang/Downloads/IDS_MetaData`, `safe_extract_archive` returns `ARCHIVE_SOURCE_BLOCKED_RAW_METADATA_ROOT` before file access.
- Test fixtures are process-owned temporary structural ZIP/TAR/RAR/7Z placeholders only. They are not IDS corpus, database rows, business evidence, raw metadata, or committed user data.
- 不得使用虚构 IDS 业务数据、虚构数据库行、虚构源文档或伪造证据.

## Validation Plan
- Focused tests: `python3 -B -m unittest KM_IDSystem.docs.pursuing_goal.ids_v0_1.tests.test_stage024_archive_threat_model -q`
- Stage005 state test: `python3 -B -m unittest KM_IDSystem.docs.pursuing_goal.ids_v0_1.tests.test_stage005_governance_regression.Stage005GovernanceRegressionTests.test_phase_state_allows_stage024_phase2_archive_safe_extraction_slice -q`
- Governance validator: `python3 -B KM_IDSystem/docs/pursuing_goal/ids_v0_1/validate_stage005_governance_regression.py`
- Full pursuing-goal tests: `python3 -B -m unittest discover -s KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests -q`
- Owner render: `scripts/lean_governance.py render/check-render --project KM_IDSystem`

## Rollback
Revert `check_archive_threat_model.py`, this Phase 2 evidence document, focused tests, BATCH021_030 lock changes, Stage005 validator/test updates, roadmap/event updates, and rendered owner-file changes only. Do not touch `/Users/linzezhang/Downloads/IDS_MetaData`, original archives, fact sources, runtime databases, reports, outputs, persisted archive manifests, evidence ledgers, audit logs, indexes, app entries, GitHub state, or Phase 3 artifacts.

## Stop Gate
- Current gate: `IDS-STAGE024-P3-GATE`
- Current status: `phase2_safe_extraction_slice_complete`
- `NO_PHASE3`: this run must not execute path traversal, absolute path, archive bomb, nested archive, garbled filename, or too-many-files scenario matrix validation; must not run whole-stage closeout.
