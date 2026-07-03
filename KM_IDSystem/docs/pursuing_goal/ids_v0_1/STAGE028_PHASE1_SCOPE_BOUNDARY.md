# IDS v0.1 STAGE-028 Phase 1 Scope Boundary

## Scope
- Stage: `STAGE-028 · 压缩包对抗测试`
- Task: `IDS-V0_1-STAGE028-P1`
- Acceptance: `ACC-STAGE-028`
- Local code: `D05-S005`
- Entrance: `IDS 系统运营入口`
- Phase: `Phase 1 · 范围、输入输出与边界确认`
- Recorded at UTC: `2026-07-03T09:31:12Z`

This phase defines the future archive adversarial test contract. It does not
create adversarial sample files, open archive bodies, enumerate real archive
entries, extract archives, create staging files, write runtime manifests, or
start downstream processing.

## Contract Fields
- `archive_adversarial_test_id`: stable id for one future adversarial archive test evaluation.
- `archive_security_boundary_id`: stable id linked back to the `STAGE-024` threat model boundary.
- `archive_source_uri`: owner-approved archive URI, path-only until a later gated run.
- `original_archive_ref`: immutable reference to the original archive; original archive content remains untouched.
- `archive_staging_area_uri`: approved staging root for future safe extraction validation.
- `archive_file_count_limit`: maximum extracted file count before owner review or block.
- `archive_total_size_limit_bytes`: maximum total expanded bytes before owner review or block.
- `archive_single_file_size_limit_bytes`: maximum single extracted file size before owner review or block.
- `archive_nested_depth_limit`: maximum nested archive depth before owner review or block.
- `archive_entry_path_policy`: normalized relative path only; no absolute path, no parent traversal, no drive prefix, no symlink escape.
- `adversarial_scenario_id`: one of `path_traversal`, `absolute_path`, `archive_bomb`, `nested_archive`, `garbled_filename`, or `too_many_files`.
- `adversarial_expected_risk_code`: expected owner-visible block or review reason for the scenario.
- `adversarial_expected_decision_state`: expected owner-visible decision state before any future extraction is allowed.
- `archive_manifest_ref`: future `STAGE-026` archive manifest reference; Phase 1 does not write it.
- `safe_extraction_ref`: future `STAGE-025` safe extraction reference; Phase 1 does not create it.
- `cleanup_allowlist_ref`: future cleanup allowlist reference; Phase 1 does not clean files.
- `post_extract_reingest_ref`: future `STAGE-027` re-ingest reference; Phase 1 does not create it.

## Owner And System States
- `ARCHIVE_ADVERSARIAL_TEST_DRAFT`: boundary exists but source, scenario, limits, staging, and expected decision are incomplete.
- `ARCHIVE_ADVERSARIAL_TEST_BLOCKED`: raw-root path, path traversal, absolute path, archive bomb, nested depth, garbled filename, file-count limit, or staging boundary blocks the scenario.
- `ARCHIVE_ADVERSARIAL_OWNER_REVIEW_REQUIRED`: risk exists and owner must review before any future extraction, manifest write, cleanup, or re-ingest handoff.
- `ARCHIVE_ADVERSARIAL_READY_FOR_SAFE_EXTRACTION`: metadata-only contract permits a future gated safe-extraction attempt.
- `ARCHIVE_ADVERSARIAL_MANIFEST_REQUIRED`: future safe extraction result must produce or update archive_manifest evidence.
- `ARCHIVE_ADVERSARIAL_REINGEST_REQUIRED`: future safe extracted files must re-enter `hash`, `manifest`, `dedup`, and `parser`.
- `ARCHIVE_ADVERSARIAL_CLEANUP_ALLOWLIST_REQUIRED`: future cleanup may only remove explicit temporary files listed in a cleanup allowlist.

## Required Scenario Families
- `path_traversal`: normalized path must block `../` escape attempts.
- `absolute_path`: normalized path must block `/`, drive-letter, UNC, and absolute path attempts.
- `archive_bomb`: expanded total size or compression-ratio risk must block or route to owner review.
- `nested_archive`: nested archive depth must block or route to owner review above the configured limit.
- `garbled_filename`: invalid or replacement-character filenames must block or route to owner review.
- `too_many_files`: file count above `archive_file_count_limit` must block or route to owner review.

## Pipeline Rules
- `STAGE-024` threat model defines the security boundary and risk vocabulary.
- `STAGE-025` safe extraction engine must perform any future extraction in approved staging only.
- `STAGE-026` archive manifest must record archive identity, entry manifest, failed items, risk items, and original archive reference.
- `STAGE-027` re-ingest rules require future extracted files to enter `hash`, then `manifest`, then `dedup`, then `parser`.
- Cleanup must use `cleanup_allowlist_ref`; it must not delete original archives, fact sources, evidence ledgers, audit logs, delivered reports, manifests, or raw metadata.

## Boundary
- 不执行压缩包对抗测试 runner.
- 不自动解压.
- 不覆盖原始压缩包.
- 不写出指定 staging 区.
- 不移动、删除、覆盖原始文件.
- 不读取真实压缩包内容.
- 不枚举真实压缩包条目.
- 不写 archive_adversarial runtime output.
- 不写 archive_manifest runtime output.
- 不创建 staging runtime directory.
- 不生成 runtime 输出、screenshot、PDF、JSON output、production report、manifest、database、evidence ledger、audit log、document/chunk/job/index/import row.
- 不启动 hash、manifest、dedup、parser、OCR、Embedding、索引或导入.
- 不安装依赖、不启动服务、不执行 GitHub upload、PR、merge 或 app reinstall.
- 不得读取、列出、hash、打开、复制、移动、删除、修改、dump 或扫描 `/Users/linzezhang/Downloads/IDS_MetaData` 内容.
- 不得使用虚构 IDS 业务数据、虚构数据库行、虚构源文档或伪造证据.
- `NO_PHASE2`: do not implement adversarial sample generation, extraction, path filtering, risk marking, quarantine, cleanup allowlist runtime behavior, archive_manifest writes, or post-extract pipeline execution in this run.

## Rollback
Revert this Phase 1 entry contract, scope boundary, focused tests, BATCH021_030
lock update, Stage005 validator/test updates, roadmap/event updates, and rendered
owner-file changes only. Do not touch `/Users/linzezhang/Downloads/IDS_MetaData`,
runtime data, reports, outputs, persisted manifests, staging files, evidence
ledgers, audit logs, indexes, app entries, GitHub state, or Phase 2 artifacts.
