# KMFA Status

更新时间: 2026-07-01

## 当前状态

- project_id: `KMFA`
- version: `0.1.0-s13-stage-review`
- current_stage: `S13`
- current_phase: `Stage 13 GitHub Upload｜待开始`
- status: `stage13_review_passed_upload_ready_local_only`
- production_ready: `false`
- github_upload_ready: `true_local_only_pending_stage13_upload`

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
- Stage 7 整体复审已本地通过：`KMFA/stage_artifacts/S07_STAGE_REVIEW/` 记录复审报告、测试结果和 machine manifest；复审确认 S07-P1/P2/P3 证据、治理 validator、raw/secret scan 和 evidence consistency check 通过。
- Stage 7 final GitHub upload 已生成证据：`KMFA/stage_artifacts/S07_STAGE_REVIEW/human/github_upload_record.md` 和 `KMFA/stage_artifacts/S07_STAGE_REVIEW/machine/stage7_upload_manifest.json`。
- S08-P1 项目组合键已完成本地验证：`KMFA/tools/project_composite_key.py` 生成 hash-only 项目身份 profile、匹配候选和人工复核队列；`KMFA/tools/check_s08_p1_project_composite_key.py` 验证 8 个组件、整数权重、阈值、单字段缺失不全阻断、manual review queue 和 public-safe 边界。
- S08-P1 证据位于 `KMFA/stage_artifacts/S08_P1_project_composite_key/`；当前中间 Phase 未执行 GitHub upload。
- S08-P2 业务实体模型已完成本地验证：`KMFA/tools/business_entity_model.py` 生成 8 类 public-safe 实体、14 条关系、32 条生命周期状态和 schema 文档；`KMFA/tools/check_s08_p2_business_entity_model.py` 验证 S08-P3、事实层、报告和 GitHub upload scope 均为 false。
- S08-P2 证据位于 `KMFA/stage_artifacts/S08_P2_business_entity_model/`；当前中间 Phase 未执行 GitHub upload。
- S08-P3 匹配质量测试已完成本地验证：`KMFA/tools/entity_matching_quality.py` 生成同名项目、多主体、多账户、多期间 4 类 public-safe 质量场景、4 条 quality cases、3 条人工复核队列记录和 1 份 entity_matching_report；`KMFA/tools/check_s08_p3_entity_matching_quality.py` 验证 Stage 8 review、事实层、lineage、正式报告、UI、外部接口和 GitHub upload scope 均为 false。
- S08-P3 证据位于 `KMFA/stage_artifacts/S08_P3_entity_matching_quality/`；当前中间 Phase 未执行 GitHub upload。
- Stage 8 整体复审已本地通过：`KMFA/stage_artifacts/S08_STAGE_REVIEW/` 记录复审报告、测试结果和 machine manifest；复审确认 S08-P1/P2/P3 validators、治理 validator、raw/secret scan、parse checks 和 evidence consistency check 通过。
- Stage 8 final GitHub upload 已完成：`KMFA/stage_artifacts/S08_STAGE_REVIEW/human/github_upload_record.md` 和 `KMFA/stage_artifacts/S08_STAGE_REVIEW/machine/stage8_upload_manifest.json` 记录 rebase binding、validator、raw/secret scan、dry-run push、push 和 post-push parity 证据。
- S09-P1 项目成本事实层已完成本地验证：`KMFA/tools/project_cost_fact_layer.py` 生成 public-safe project cost fact layer manifest、4 条项目事实记录和 9 条未归集成本池记录；`KMFA/tools/check_s09_p1_project_cost_fact_layer.py` 验证收入、合同额、开票、回款、成本合计、成本分类 slots，9 类成本分类覆盖，S09-P2/S09-P3/Stage 9 review/报告/UI/外部接口/GitHub upload scope 均为 false。
- S09-P1 证据位于 `KMFA/stage_artifacts/S09_P1_project_cost_fact_layer/`；当前中间 Phase 未执行 Stage 9 整体复审或 GitHub upload。
- S09-P2 毛利与现金毛利已完成本地验证：`KMFA/tools/project_margin_cash_margin.py` 生成 public-safe margin/cash margin manifest、4 条 margin records 和 12 条 scope difference summary records；`KMFA/tools/check_s09_p2_margin_cash_margin.py` 验证 authority/system refs 分离、S09-P3/Stage 9 review/报告/UI/外部接口/GitHub upload scope 均为 false。
- S09-P2 证据位于 `KMFA/stage_artifacts/S09_P2_margin_cash_margin/`；当前中间 Phase 未执行 S09-P3、Stage 9 整体复审或 GitHub upload。
- S09-P3 口径转换与差异核对已完成本地验证：`KMFA/tools/project_scope_reconciliation.py` 生成 public-safe scope reconciliation manifest、12 条 reconciliation records 和 6 条 domain controls；`KMFA/tools/check_s09_p3_scope_reconciliation.py` 验证 6 类核对域、必需人工字段、pending owner/授权复核门禁和 public-safe 边界。
- S09-P3 证据位于 `KMFA/stage_artifacts/S09_P3_scope_reconciliation/`；当前中间 Phase 未执行 Stage 9 整体复审或 GitHub upload，派生指标重跑和正式报告仍被阻断。
- Stage 9 整体复审已本地通过：`KMFA/stage_artifacts/S09_STAGE_REVIEW/` 记录 review report、test results 和 machine manifest；复审复跑 S09-P1/P2/P3 validators、`KMFA/tools/check_s09_stage_review.py`、全量 KMFA tests、治理 validator、raw/secret scan 和 parse checks，并修复 high-signal secret scan 误报 finding。
- Stage 9 final GitHub upload 已完成：`KMFA/stage_artifacts/S09_STAGE_REVIEW/human/github_upload_record.md` 和 `KMFA/stage_artifacts/S09_STAGE_REVIEW/machine/stage9_upload_manifest.json` 记录 rebase binding、validator、raw/secret scan、dry-run push、push 和 post-push parity 证据。
- S10-P1 报告模板已完成本地验证：`KMFA/tools/report_templates.py` 生成 2 个 public-safe 报告模板和 11 个管理可读章节；`KMFA/tools/check_s10_p1_report_templates.py` 验证模板覆盖、HTML 样板引用、scope gate 和 public-safe 边界。
- S10-P1 证据位于 `KMFA/stage_artifacts/S10_P1_report_templates/`；当前中间 Phase 未执行 Stage 10 整体复审或 GitHub upload。
- S10-P2 报告可信等级已完成本地验证：`KMFA/tools/report_grade_runtime.py` 基于 S10-P1 模板、S02-P3 质量门禁、S06-P3 zero-delta/data quality 和 S09-P3 reconciliation 状态生成 2 条 public-safe 报告等级记录，均锁定为 `D` 并阻断完整可信报告显示。
- S10-P2 证据位于 `KMFA/stage_artifacts/S10_P2_report_grade_runtime/`；当前中间 Phase 未执行 S10-P3、Stage 10 整体复审或 GitHub upload。
- S10-P3 导出已完成本地验证：`KMFA/tools/report_export_runtime.py` 基于 S10-P1 模板和 S10-P2 D 级门禁生成 2 个 public-safe HTML 报告、2 个 public-safe CSV 附表、2 个 Excel 兼容 CSV 下载记录和 PDF private-runtime-only 策略；`KMFA/tools/check_s10_p3_report_export.py` 验证 `.xlsx/.pdf` 未提交、正式报告和经营决策依据继续阻断。
- S10-P3 证据位于 `KMFA/stage_artifacts/S10_P3_report_export/`；当前仅表示 S10 三个 phase 本地完成，尚未执行 Stage 10 整体复审或 GitHub upload。
- Stage 10 整体复审已本地通过：`KMFA/stage_artifacts/S10_STAGE_REVIEW/` 记录 review report、test results 和 machine manifest；`KMFA/tools/check_s10_stage_review.py` 验证 S10-P1/P2/P3 evidence、D 级阻断、HTML/CSV 导出、无 Excel/PDF 提交和 upload/S11 gate。
- Stage 10 final GitHub upload 已完成：`KMFA/stage_artifacts/S10_STAGE_REVIEW/human/github_upload_record.md` 和 `KMFA/stage_artifacts/S10_STAGE_REVIEW/machine/stage10_upload_manifest.json` 记录 rebase binding、validators、安全扫描、dry-run push、push 和 post-push parity 证据。
- S11-P1 首页与导航已完成本地验证：`KMFA/tools/home_navigation_runtime.py` 生成 8 个首页模块、1 个 public-safe 蓝色商务风 HTML 首页样张、manifest 和 records；`KMFA/tools/check_s11_p1_home_navigation.py` 验证 KM 标识、全中文业务入口、S11-P2/S11-P3 scope false、正式报告阻断和 GitHub upload false。
- S11-P2 数据源检查板已完成本地验证：`KMFA/tools/source_check_board_runtime.py` 生成 13 行 public-safe 来源状态矩阵、固定 11 列、5 种状态、1 个蓝灰商务风 HTML 检查板样张、manifest 和 rows；`KMFA/tools/check_s11_p2_source_check_board.py` 验证状态详情点击、低干扰徽标、S11-P3 scope false、正式报告阻断和 GitHub upload false。
- S11-P3 项目成本页面已完成本地验证：`KMFA/tools/project_cost_page_runtime.py` 生成 4 条 public-safe 项目页面记录、项目列表、项目详情、来源证据、待处理事项、D 级报告预览、1 个蓝色商务风 HTML 页面、manifest 和 records；`KMFA/tools/check_s11_p3_project_cost_page.py` 验证报告预览可直接查看但不可绕过质量等级，Stage 11 review 和 GitHub upload 仍为 false。
- Stage 11 整体复审已本地通过：`KMFA/stage_artifacts/S11_STAGE_REVIEW/` 记录 S11-P1/P2/P3 validators、`KMFA/tools/check_s11_stage_review.py`、全量 132 个 KMFA tests、治理 validator、raw/secret scan、parse checks 和 public-safe 证据一致性；复审未执行 GitHub upload、S12、lineage full check、正式报告或外部接口。
- Stage 11 final GitHub upload 已完成：`KMFA/stage_artifacts/S11_STAGE_REVIEW/human/github_upload_record.md` 和 `KMFA/stage_artifacts/S11_STAGE_REVIEW/machine/stage11_upload_manifest.json` 记录 rebase、validators、raw/secret scan、dry-run push、push 和 post-push parity。
- S12-P1 人工处理事件已完成本地验证：`KMFA/tools/manual_resolution_events.py` 生成 5 条 append-only manual resolution events、manifest 和 HTML 工作台；`KMFA/tools/check_s12_p1_manual_resolution_events.py` 验证字段映射、项目匹配、差异处理、备注、处理人/时间/原因/影响范围/版本和已批准事件只能追加反向事件。
- S12-P2 影响预览已完成本地验证：`KMFA/tools/manual_impact_preview.py` 基于 5 条 S12-P1 人工处理事件生成 5 条 public-safe impact previews、manifest 和 HTML 影响预览；`KMFA/tools/check_s12_p2_manual_impact_preview.py` 验证受影响项目/指标/报告展示、高风险二次确认、未通过不得发布、rerun/formal report/review/upload 均为 false。
- S12-P3 重跑机制已完成本地验证：`KMFA/tools/manual_rerun_mechanism.py` 基于 S12-P1/S12-P2 public-safe 证据生成 2 条 cache invalidation、8 条 rerun step、2 条 same-source consistency check、manifest 和 HTML 重跑机制；`KMFA/tools/check_s12_p3_manual_rerun_mechanism.py` 验证只有通过影响预览的事件进入重跑，blocked preview 不进入重跑，旧版本保留、新版本追加，formal report/review/upload 均为 false。
- Stage 12 整体复审已本地通过：`KMFA/stage_artifacts/S12_STAGE_REVIEW/` 记录 S12-P1/P2/P3 validators、`KMFA/tools/check_s12_stage_review.py`、全量 152 个 KMFA tests、治理 validator、raw/secret scan、parse checks 和 public-safe 证据一致性；复审未执行 GitHub upload、S13、lineage full check、正式报告、差异关闭或外部接口。
- Stage 12 final GitHub upload 已完成：`KMFA/stage_artifacts/S12_GITHUB_UPLOAD/human/github_upload_record.md` 和 `KMFA/stage_artifacts/S12_GITHUB_UPLOAD/machine/stage12_upload_manifest.json` 记录 rebase、validators、安全扫描、dry-run push、push 和 post-push parity。
- S13-P1 财务经营报表已完成本地验证：`KMFA/tools/financial_operating_report.py` 生成 4 条 public-safe 财务经营 source lane、2 条经营周报/月报初稿、2 个 HTML draft、manifest 和 validator；报告等级显示 D，12 条 pending reconciliation 继续阻断正式报告和经营决策依据。
- S13-P2 回款应收账龄已完成本地验证：`KMFA/tools/collection_receivable_aging.py` 生成 5 条 public-safe source lane、4 条回款优先级事项、4 条责任事项、1 个 HTML evidence、manifest 和 validator；报告等级显示 D，12 条 pending reconciliation 继续阻断正式报告、催收/付款/法务动作和经营决策依据。
- S13-P3 跨表复核已完成本地验证：`KMFA/tools/cross_table_review.py` 生成 4 个 public-safe 跨表复核维度、4 条人工差异队列事项、1 份经营报表质量报告和 1 个 HTML evidence；报告等级显示 D，12 条 pending reconciliation 继续阻断正式报告、经营决策依据和自动差异处理。
- Stage 13 整体复审已本地通过：`KMFA/stage_artifacts/S13_STAGE_REVIEW/` 记录 S13-P1/P2/P3 validators、`KMFA/tools/check_s13_stage_review.py`、全量 172 个 KMFA tests、治理 validator、raw/secret scan、parse checks 和 public-safe 证据一致性；复审未执行 GitHub upload、S14、lineage full check、正式报告、差异关闭或外部接口。

## 未完成

- Stage 13 GitHub upload、lineage 完整检查、正式报告、差异关闭和外部接口尚未完成；S13-P1/S13-P2/S13-P3 和 Stage 13 整体复审均仅为 public-safe 本地验证产物，S09-P3 reconciliation layer 仍有 12 条 pending owner/授权复核记录，不代表正式报告可发布。

## 阻塞条件

- 不能把 Stage 1 治理基线当成业务 MVP。
- 不能上传原始敏感经营数据。
- S05-P3 已完成 40 条 public-safe hash/source-anchor 字段锁定并排除 5 条 Excel 字段，Stage 5 review/upload、S06-P1、S06-P2、S06-P3、Stage 6 review/upload、S07-P1 finance adapter、S07-P2 WPS adapter、S07-P3 redcircle postponement policy、Stage 7 review/upload、S08-P1 project composite key、S08-P2 business entity model、S08-P3 matching quality test、Stage 8 review/upload、S09-P1 project cost fact layer、S09-P2 margin/cash margin layer、S09-P3 scope reconciliation、Stage 9 review/upload、S10-P1 report templates、S10-P2 report grade runtime、S10-P3 report export、Stage 10 review/upload、S11-P1 home navigation、S11-P2 source check board、S11-P3 project cost page、Stage 11 review/upload、S12-P1 manual resolution events、S12-P2 impact preview、S12-P3 rerun mechanism、Stage 12 review、Stage 12 final GitHub upload、S13-P1 financial operating report、S13-P2 collection receivable aging、S13-P3 cross table review 和 Stage 13 review 已完成；下一步只能作为新 run work 执行 Stage 13 GitHub upload gate，不能直接进入 S14、lineage full check、正式报告或外部接口。
- 后续所有开发必须建立在 v1.2 完整任务包和 HTML 样板基线上。
