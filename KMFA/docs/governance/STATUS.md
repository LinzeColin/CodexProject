# KMFA Status

更新时间: 2026-06-30

## 当前状态

- project_id: `KMFA`
- version: `0.1.0-s05p3-authority-baseline-lock`
- current_stage: `S05`
- current_phase: `S05-P3 权威基准锁定本地完成，下一步 Stage 5 整体复审`
- status: `s05p3_completed_validated_local_only_public_safe_authority_lock`
- production_ready: `false`
- github_upload_ready: `false_until_stage5_review_and_fix`

## 已完成

- S01-P1 只读计划与范围锁定。
- S01-P2 项目骨架、中文入口、治理配置草案和时间质量规则。
- S01-P2 项目治理验证通过：errors 0 / warnings 0。
- S01-P3 完整需求追溯矩阵、防遗漏检查脚本和 Stage/Phase/Task 状态登记。
- S01-P3 no_omission 检查通过：P0=9、P1=8、tasks=162。
- Stage 1 整体复审通过，复审 finding 已处理或转为隔离上传约束。
- S02-P1 metadata 目录协议完成：七类 metadata 目录、核心标识符规则、公开仓库隐私边界和协议检查器。
- S02-P2 不可污染原则完成：raw manifest append-only 规范、派生版本失效/重跑/对比协议、前端 raw 写入边界和检查器。
- S02-P3 数据质量等级完成：Q0-Q5 数据质量等级、A/B/C/D 报告可信等级、报告发布门禁和检查器。
- Stage 2 整体复审通过：`KMFA/stage_artifacts/S02_STAGE_REVIEW/`。
- Stage 2 已上传 GitHub main：final remote commit `6178b5215f92f12d6facad9a990e8659b3a70ba4`，reviewed content commit `834ff75516405ddbc8289f00ba67579691473709`。
- v1.2 FULL_HTML_NO_OMISSION 完整任务包已承接到 `KMFA/taskpack/v1_2/`。
- v1.2 HTML 样板已承接：45 个 HTML，7 个核心验收样板。
- 原始私有源数据未提交公开仓库；只保存 `source_manifests/用户原始上传数据_SHA256_v1_2.csv`。
- Stage 1 已按 v1.2 重新走完，证据目录为 `KMFA/stage_artifacts/S01_REBASE_V12_FULL_TASKPACK/`。
- S03-P1 文件型导入已完成：`KMFA/tools/file_import_register.py` 支持文件登记、hash/size/import_run/source package metadata、私有 storage ref、zip 安全解包和 WPS/OLE 提示。
- S03-P2 数据源检查矩阵已完成：`KMFA/tools/source_check_matrix.py` 支持矩阵维度生成、五状态枚举和 metadata-only 状态事件。
- S03-P3 源优先级已完成：`KMFA/tools/source_priority.py` 支持源类别优先级、同源失效重跑事件和跨源差异队列 metadata。
- Stage 3 整体复审已通过：`KMFA/stage_artifacts/S03_STAGE_REVIEW/`。
- Stage 3 已整体上传 GitHub main，reviewed content commit `39b0eef52424a12b6c0c8ad368bd878b46300be4`。
- S04-P1 金额工具已完成本地验证：`KMFA/tools/amount_tools.py` 支持金额标准化到整数分，`KMFA/tools/check_no_float_money.py` 阻断业务金额 float 用法。
- S04-P2 字段标准化已完成本地验证：`KMFA/tools/field_standardization.py` 支持字段别名、日期、期间、主体、项目、客户/对手方和合同编号标准化，缺字段进入 metadata 质量状态。
- S04-P3 基础工具测试已完成本地验证：`KMFA/tests/test_basic_tool_boundaries.py` 覆盖 22 个合成边界用例，`KMFA/tools/generate_tool_test_report.py` 可生成 JSON/Markdown 工具函数测试报告。
- Stage 4 整体复审已通过：`KMFA/stage_artifacts/S04_STAGE_REVIEW/` 记录复审报告、测试结果和 machine manifest；owner-readable 金额工具详情缺口已修复。
- Stage 4 final GitHub upload 证据已生成：`KMFA/stage_artifacts/S04_STAGE_REVIEW/human/github_upload_record.md`。
- S05-P1 A0 文件登记已完成本地验证：`KMFA/tools/a0_file_register.py` 生成 8 个 PDF + 1 个 Excel 的 public-safe A0 文件清单和项目候选清单。
- S05-P2 已生成 public-safe 字段合同和 A0 golden fixture 候选结构：`KMFA/tools/a0_golden_fixture.py` 生成 5 个字段合同和 45 条字段候选。
- S05-P2 已对 8 个 PDF A0 候选执行 hash-only 部分回填：40 条字段候选已记录 private value hash/source anchor，1 个 Excel 候选的 5 条字段不写入 A0 baseline，并通过 active downgrade decision 作为 cross-source support only 处理。
- S05-P2 已完成 Excel 候选机器复核记录、owner 决策包、owner decision validator、owner decision intake validator、三种 owner 决策模板、owner decision application preview、active owner/授权降级决策和 completion gate：该 Excel candidate 只作为交叉来源支持，不进入 Q4/Q5 A0 baseline；completion gate 使用 active decision 验证 ready。
- S05-P3 已完成 A0 权威基准锁定：40 条 PDF 字段 hash/source-anchor 记录进入 public-safe Q5 calculation baseline，5 条 Excel 字段依据 active owner/授权降级决策排除为 cross-source support only。
- S05-P3 已生成 `KMFA/metadata/baseline/a0_authority_baseline_manifest.json`、`KMFA/metadata/baseline/a0_authority_baseline_records.jsonl`、`KMFA/tools/a0_authority_baseline_lock.py`、`KMFA/tools/check_a0_authority_baseline_lock.py` 和 `KMFA/stage_artifacts/S05_P3_authority_baseline_lock/`。

## 未完成

- Stage 5 整体复审、复审问题修复和 GitHub upload 尚未完成。
- zero-delta、事实层、lineage 完整检查、报告、UI 和外部接口尚未完成；S05-P3 authority baseline lock 不代表正式报告可发布。

## 阻塞条件

- 不能把 Stage 1 治理基线当成业务 MVP。
- 不能上传原始敏感经营数据。
- S05-P3 已完成 40 条 public-safe hash/source-anchor 字段锁定并排除 5 条 Excel 字段；下一步只能执行 Stage 5 整体复审，不能跳到上传、UI、报告、事实层或 zero-delta。
- 后续所有开发必须建立在 v1.2 完整任务包和 HTML 样板基线上。
