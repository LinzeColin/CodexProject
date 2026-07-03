# IDS v0.1 STAGE-024 Phase 3 Scenario Validation

stage_id: STAGE-024
phase_id: IDS-STAGE024-P3
task_id: IDS-V0_1-STAGE024-P3
acceptance_id: ACC-STAGE-024
schema_version: ids.stage024.archive_threat_model.scenario_validation.v1
script: KM_IDSystem/scripts/check_archive_threat_model.py
helper: build_stage024_scenario_report

## 目标

Phase 3 用路径穿越、绝对路径、压缩炸弹、嵌套包、乱码文件名和超大文件数六类结构性样例验证 STAGE-024 压缩包威胁模型。验证对象是 Phase 2 的 safe_extract_archive 安全解压 helper、风险标记、owner review/quarantine 状态、post-extract re-ingest 计划和 cleanup allowlist。

本阶段不使用 IDS 业务样本、不使用虚构数据库行、不提交归档样例文件；测试只在进程自有临时目录创建结构性 ZIP/TAR/RAR/7Z 占位样本，用于验证防护逻辑。这些样本不是 IDS corpus、数据库内容、业务证据、raw metadata 或 committed user data。

## 异常场景矩阵

| scenario_id | 中文场景 | expected_risk_code | expected_state |
| --- | --- | --- | --- |
| path_traversal | 路径穿越 | ARCHIVE_PATH_TRAVERSAL_BLOCKED | ARCHIVE_ENTRY_BLOCKED_PATH_TRAVERSAL |
| absolute_path | 绝对路径 | ARCHIVE_ABSOLUTE_PATH_BLOCKED | ARCHIVE_ENTRY_BLOCKED_ABSOLUTE_PATH |
| archive_bomb | 压缩炸弹 | ARCHIVE_TOTAL_SIZE_LIMIT_EXCEEDED | ARCHIVE_EXTRACTION_BLOCKED_TOTAL_SIZE_LIMIT |
| nested_archive | 嵌套包 | ARCHIVE_NESTED_DEPTH_LIMIT_EXCEEDED | ARCHIVE_ENTRY_QUARANTINED_NESTED_LIMIT |
| garbled_filename | 乱码文件名 | ARCHIVE_GARBLED_FILENAME_OWNER_REVIEW_REQUIRED | ARCHIVE_ENTRY_QUARANTINED_GARBLED_FILENAME |
| too_many_files | 超大文件数 | ARCHIVE_FILE_COUNT_LIMIT_EXCEEDED | ARCHIVE_ENTRY_QUARANTINED_FILE_COUNT_LIMIT |

build_stage024_scenario_report 汇总每个 scenario 的 archive_threat_model、risk_codes、expected_risk_observed 和 scenario_state。全部必需样例覆盖且预期 risk code 命中时，validation_state 为 ARCHIVE_THREAT_SCENARIO_VALIDATION_PASSED。

## Re-ingest 验证

Phase 3 验证安全解压后的文件必须重新进入 hash、manifest、dedup、parser 流程，状态为 POST_EXTRACT_REINGEST_VALIDATED。

- hash: POST_EXTRACT_HASH_REQUIRED
- manifest: POST_EXTRACT_MANIFEST_REQUIRED
- dedup: POST_EXTRACT_DEDUP_REQUIRED
- parser: POST_EXTRACT_PARSER_REQUIRED

processing_guard 必须保持 actual_hash_jobs_started、actual_manifest_jobs_started、actual_dedup_jobs_started、actual_parser_jobs_started、actual_ocr_jobs_started、actual_embedding_jobs_started、actual_index_jobs_started、actual_import_jobs_started 和 actual_external_api_calls_started 全部为 0。

## Cleanup 验证

Phase 3 验证自动清理只清理允许的临时文件，cleanup state 为 ARCHIVE_CLEANUP_ALLOWLIST_VALIDATED。

- 只清理允许的临时文件: cleanup_class 只能是 ARCHIVE_STAGING_TEMP_FILE。
- 不删除原始文件: original_archive_ref 不得进入 cleanup_allowlist。
- 不清理事实源和证据产物: cleanup_policy.does_not_clean_fact_source_or_evidence 必须为 true。
- 不清理 manifest 或 audit runtime output: cleanup_policy.does_not_clean_manifest_or_audit_outputs 必须为 true。

## Raw Data Boundary

/Users/linzezhang/Downloads/IDS_MetaData 是本机真实数据库根目录，只作为路径级 read-only raw data boundary 记录。Phase 3 不得读取、列出、hash、打开、复制、移动、删除、修改、dump 或扫描该目录内容，也不得将其中任何本机原始数据写入 GitHub。

## 非目标

- 不执行 Phase 4 closeout，不写 archive_manifest 样例交付包。
- 不启动 hash、manifest、dedup、parser、OCR、Embedding、index、import、report、backend、frontend 或 worker job。
- 不写 runtime report、database、evidence ledger、audit log、index、document/chunk/job/import row 或 archive_manifest runtime output。
- 不安装依赖，不启动服务，不调用外部 API。
- 不 push GitHub，不创建 PR，不 merge PR，不 reinstall app entries。
- NO_PHASE4
