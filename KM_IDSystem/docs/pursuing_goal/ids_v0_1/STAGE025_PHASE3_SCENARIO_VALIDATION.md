# STAGE-025 Phase 3 · 安全解压引擎专项验证

- Task ID: `IDS-V0_1-STAGE025-P3`
- Acceptance ID: `ACC-STAGE-025`
- Schema: `ids.stage025.safe_extraction_engine.scenario_validation.v1`
- Helper: `build_stage025_scenario_report`
- Engine: `ids.stage025.safe_extraction_engine`
- 入口：`IDS 系统运营入口`

## 验证目标

Phase 3 只验证安全解压引擎的异常场景、post-extract re-ingest 计划和 cleanup allowlist，不进入 Phase 4 closeout，不执行 GitHub upload、PR、merge 或 app reinstall。

本轮验证覆盖：

- 路径穿越：期望 `SAFE_EXTRACTION_PATH_TRAVERSAL_BLOCKED`
- 绝对路径：期望 `SAFE_EXTRACTION_ABSOLUTE_PATH_BLOCKED`
- 压缩炸弹：期望 `SAFE_EXTRACTION_TOTAL_SIZE_LIMIT_EXCEEDED`
- 嵌套包：期望 `SAFE_EXTRACTION_NESTED_DEPTH_LIMIT_EXCEEDED`
- 乱码文件名：期望 `SAFE_EXTRACTION_GARBLED_FILENAME_OWNER_REVIEW_REQUIRED`
- 超大文件数：期望 `SAFE_EXTRACTION_FILE_COUNT_LIMIT_EXCEEDED`

## Re-ingest 验证

`build_stage025_scenario_report` 聚合各场景的安全解压条目，只返回内存态 validation payload。安全条目必须进入 `POST_EXTRACT_REINGEST_VALIDATED`，并声明后续仍需经过：

- `hash`
- `manifest`
- `dedup`
- `parser`

本阶段只验证队列和状态，不启动实际 hash、manifest、dedup、parser job，不写 document、chunk、job、index、import row，不写 archive_manifest runtime output。

## Cleanup 验证

cleanup validation 的通过状态为 `SAFE_EXTRACTION_CLEANUP_ALLOWLIST_VALIDATED`。

要求：

- 只清理允许的临时文件
- cleanup target 只能来自 staging temp file allowlist
- 不删除原始文件
- 不清理事实源、证据产物、manifest、audit log 或 report
- 原始压缩包不得出现在 cleanup allowlist 中

## 数据边界

本阶段不得读取、列出、hash、打开、复制、移动、删除、修改、dump 或扫描 `/Users/linzezhang/Downloads/IDS_MetaData`。

测试中的 archive 样例是 process-owned temporary structural archive fixtures，只用于验证路径、大小、嵌套、乱码和文件数边界；这些 fixture 不是 IDS corpus、database rows、business evidence、raw metadata 或 committed user data。

真实 IDS 业务数据、数据库行、事实源、证据产物和 runtime corpus 仍必须来自 owner-approved real data；本阶段不提交任何虚构业务数据或伪造证据。

## 停止条件

- 任何场景需要读取 `/Users/linzezhang/Downloads/IDS_MetaData` 内容。
- 自动清理会触及原始压缩包、事实源、证据产物、manifest、audit log 或 report。
- helper 启动 hash、manifest、dedup、parser、OCR、Embedding、index、import、backend、frontend、worker 或 external API job。
- 写入 runtime report、database、evidence ledger、audit log、index、document/chunk/job/import row 或 archive_manifest runtime output。
- 进入 Phase 4 closeout、GitHub upload、PR、merge 或 app reinstall。

## 本轮边界

NO_PHASE4
