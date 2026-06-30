# KMFA Status

更新时间: 2026-06-30

## 当前状态

- project_id: `KMFA`
- version: `0.1.0-s07p3-redcircle-postponement`
- current_stage: `S07`
- current_phase: `Stage 7 整体复审 待开始`
- status: `s07p3_completed_validated_local_only_stage7_review_not_started`
- production_ready: `false`
- github_upload_ready: `false_until_next_stage_review`

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
- Stage 5 整体复审已本地通过：`KMFA/stage_artifacts/S05_STAGE_REVIEW/` 记录复审报告、测试结果和 machine manifest；复审修复了 Stage 5 review 证据和治理状态缺口。
- Stage 5 final GitHub upload 已生成证据：`KMFA/stage_artifacts/S05_STAGE_REVIEW/human/github_upload_record.md` 和 `KMFA/stage_artifacts/S05_STAGE_REVIEW/machine/stage5_upload_manifest.json`。
- S06-P1 零差异校验器已完成本地验证：`KMFA/tools/zero_delta_validator.py` 对 public-safe 已结构化整数分逐字段比较，任意 1 分差异失败并输出 mismatch report。
- S06-P2 跨源差异队列已完成本地验证：`KMFA/tools/cross_source_difference_queue.py` 将 public-safe PDF/Excel 同项目同字段冲突写入人工队列，禁止自动修正、平均、四舍五入掩盖和自动选边；`KMFA/tools/check_s06_p2_difference_queue.py` 验证未关闭差异阻断 A 级报告。
- S06-P3 校验证据输出已完成本地验证：`KMFA/tools/validation_evidence_output.py` 输出 S06-P3 zero-delta summary、sanitized mismatch index、project validation status，并写入 `KMFA/metadata/quality`；`KMFA/tools/check_s06_p3_validation_evidence.py` 验证 metadata 不新增字段明文或原始金额值。
- Stage 6 整体复审已本地通过：`KMFA/stage_artifacts/S06_STAGE_REVIEW/` 记录复审报告、测试结果和 machine manifest；复审确认 S06-P1/P2/P3 证据、治理 validator、raw/secret scan 和 evidence consistency check 通过。
- Stage 6 final GitHub upload 已完成：`KMFA/stage_artifacts/S06_STAGE_REVIEW/human/github_upload_record.md` 和 `KMFA/stage_artifacts/S06_STAGE_REVIEW/machine/stage6_upload_manifest.json` 记录 rebase binding、validator、raw/secret scan、dry-run push、push 和 post-push parity 证据。
- S07-P1 财务文件适配已完成本地验证：`KMFA/tools/finance_file_adapter.py`、`KMFA/tools/check_s07_p1_finance_file_adapter.py`、`KMFA/tests/test_finance_file_adapter.py`、`KMFA/metadata/imports/finance_support_source_registry.json`、`KMFA/metadata/schema_maps/finance_file_adapter_manifest.json`、`KMFA/metadata/schema_maps/finance_field_candidates.jsonl` 和 `KMFA/stage_artifacts/S07_P1_finance_file_adapter/` 已生成。
- S07-P1 覆盖经营分析、日记账、客户账龄、现金、纳税、开票、账户、贷款、研发费用 9 类财务支撑源，生成 45 条 hash-only 字段候选和 9 条只读字段报告。
- S07-P2 WPS 文件适配已完成本地验证：`KMFA/tools/wps_file_adapter.py`、`KMFA/tools/check_s07_p2_wps_file_adapter.py`、`KMFA/tests/test_wps_file_adapter.py`、`KMFA/metadata/imports/wps_export_source_registry.json`、`KMFA/metadata/schema_maps/wps_file_adapter_manifest.json`、`KMFA/metadata/schema_maps/wps_field_mappings.jsonl`、`KMFA/metadata/schema_maps/wps_mapping_rule_versions.json` 和 `KMFA/stage_artifacts/S07_P2_wps_file_adapter/` 已生成。
- S07-P2 覆盖 WPS 回款、应收账龄、生产项目状态、保证金 4 类导出，生成 20 条 hash-only 字段映射、4 条转换提示、4 条只读字段报告和 1 个映射规则版本。
- S07-P3 红圈导出后置策略已完成本地验证：`KMFA/tools/redcircle_postponement_policy.py`、`KMFA/tools/check_s07_p3_redcircle_postponement.py`、`KMFA/tests/test_redcircle_postponement_policy.py`、`KMFA/metadata/imports/redcircle_export_source_registry.json`、`KMFA/metadata/schema_maps/redcircle_postponement_manifest.json`、`KMFA/metadata/schema_maps/redcircle_reserved_export_templates.jsonl`、`KMFA/metadata/schema_maps/redcircle_postponement_policy.yaml` 和 `KMFA/stage_artifacts/S07_P3_redcircle_postponement_policy/` 已生成。
- S07-P3 预留红圈经营、合同、回款、财务 4 类导出模板，明确 D15 文件型 MVP 不接自动接口，并建立只读、留 hash、可回滚、需人工授权的后续接入控制。

## 未完成

- Stage 7 整体复审、Stage 7 GitHub upload、事实层、lineage 完整检查、报告、UI 和外部接口尚未完成；S05-P3 authority baseline lock、Stage 6 upload、S07-P1 finance adapter、S07-P2 WPS adapter 和 S07-P3 redcircle postponement policy 不代表正式报告可发布。

## 阻塞条件

- 不能把 Stage 1 治理基线当成业务 MVP。
- 不能上传原始敏感经营数据。
- S05-P3 已完成 40 条 public-safe hash/source-anchor 字段锁定并排除 5 条 Excel 字段，Stage 5 review/upload、S06-P1、S06-P2、S06-P3、Stage 6 review/upload、S07-P1 finance adapter、S07-P2 WPS adapter 和 S07-P3 redcircle postponement policy 已完成；下一步只能执行 Stage 7 整体复审，不能跳到 S08、UI、报告、事实层、lineage 或外部接口。
- 后续所有开发必须建立在 v1.2 完整任务包和 HTML 样板基线上。
