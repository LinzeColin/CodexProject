# IDS v0.1 STAGE-029 Phase 3 · 压缩包清理白名单专项验证

- Task ID: `IDS-V0_1-STAGE029-P3`
- Acceptance ID: `ACC-STAGE-029`
- Stage: `STAGE-029 · 压缩包清理白名单`
- Phase: `Phase 3 · 专项验证与异常场景`
- Entrance: `IDS 系统运营入口`
- Schema: `ids.stage029.archive_cleanup_allowlist.scenario_validation.v1`
- Implementation: `KM_IDSystem/scripts/check_archive_cleanup_allowlist.py`
- Function: `build_stage029_scenario_report`

## 验证目标

验证 archive cleanup allowlist 在异常压缩包场景下仍只允许清理明确的
staging 临时文件，不清理原始资料、原始压缩包、manifest、evidence、audit、
report、database、index 或 parser output。

## 覆盖场景

`build_stage029_scenario_report` 覆盖以下 6 个结构性场景：

- `path_traversal`
- `absolute_path`
- `archive_bomb`
- `nested_archive`
- `garbled_filename`
- `too_many_files`

对应风险码由上游 safe extraction / archive adversarial layer 产生，并在本
Stage 形成 cleanup allowlist 视角的 validation payload：

- `ARCHIVE_ADVERSARIAL_PATH_TRAVERSAL_BLOCKED`
- `ARCHIVE_ADVERSARIAL_ABSOLUTE_PATH_BLOCKED`
- `ARCHIVE_ADVERSARIAL_TOTAL_SIZE_LIMIT_EXCEEDED`
- `ARCHIVE_ADVERSARIAL_NESTED_DEPTH_LIMIT_EXCEEDED`
- `ARCHIVE_ADVERSARIAL_GARBLED_FILENAME_OWNER_REVIEW_REQUIRED`
- `ARCHIVE_ADVERSARIAL_FILE_COUNT_LIMIT_EXCEEDED`

## Re-ingest 验证

验证解压后安全文件进入后续导入规划：

- `hash`
- `manifest`
- `dedup`
- `parser`

Phase 3 只生成 in-memory validation payload，不创建 import queue，不启动
hash、manifest、dedup、parser、OCR、Embedding、index 或 import job。

目标状态：

- `ARCHIVE_CLEANUP_SCENARIO_VALIDATION_PASSED`
- `ARCHIVE_CLEANUP_REINGEST_VALIDATED`
- `ARCHIVE_CLEANUP_SCENARIO_ALLOWLIST_VALIDATED`

## Cleanup allowlist 验证

清理白名单验证规则：

- 只清理允许的临时文件。
- cleanup target 必须为 `ARCHIVE_STAGING_TEMP_FILE`。
- 原始压缩包不得进入 cleanup allowlist。
- 原始资料、manifest、evidence ledger、audit log、report、database、index、
  parser output 和 raw metadata root 必须保持 protected ref。
- `cleanup_runner_executed=false`。
- `does_not_delete_files=true`。

## Raw data 和真实数据边界

- `/Users/linzezhang/Downloads/IDS_MetaData` 仅作为 path-only read-only real
  database source boundary 记录。
- 不得读取、列出、hash、打开、复制、移动、删除、修改、dump 或扫描
  `/Users/linzezhang/Downloads/IDS_MetaData` 内容。
- 本 Phase 的 focused tests 使用 process-owned temporary archive fixtures，并且
  fixture payload 只来自 Git 已跟踪 governance document bytes。
- 这些 fixture 不是 IDS corpus、database rows、business evidence、raw metadata、
  committed examples 或 user production data。
- 不得使用虚构 IDS 业务数据、虚构数据库行、虚构源文档或伪造证据。

## 禁止副作用

- 不执行 cleanup runner。
- 不自动清理或删除文件。
- 不删除原始资料。
- 不删除原始压缩包。
- 不删除 manifest。
- 不删除 evidence。
- 不删除 audit。
- 不删除报告。
- 不写 archive_cleanup runtime output。
- 不写 archive_manifest runtime output。
- 不写 import queue、report、database、evidence ledger、audit log、index、
  document/chunk/job/import row、JSON output、production cleanup output 或 parser output。
- 不启动 backend、frontend、worker、dependency install 或 external API job。
- 不执行 GitHub upload、PR、merge 或 app reinstall。
- `NO_PHASE4`

## 回滚

Revert `check_archive_cleanup_allowlist.py` Phase 3 additions,
`STAGE029_PHASE3_SCENARIO_VALIDATION.md`, `BATCH021_030_UPLOAD_LOCK.yaml`,
focused tests, Stage005 validator/test updates, compatibility test updates,
roadmap/event changes, and rendered owner files only.

Do not touch `/Users/linzezhang/Downloads/IDS_MetaData`, original archives,
original materials, manifests, evidence ledgers, audit logs, reports, runtime
data, outputs, indexes, app entries, GitHub state, or Phase 4 artifacts.
