# KMFA Model Spec

product_version: 0.1.0-s16-stage-review

## Scope

当前模型说明覆盖 S01 已建立并按 v1.2 重放的治理边界、S02-P1 metadata 协议、S02-P2 不可污染原则、S02-P3 质量等级门禁协议、S03-P1 文件型导入登记模型、S03-P2 数据源检查矩阵模型、S03-P3 源优先级模型、S04-P1 金额工具、S04-P2 字段标准化工具、S04-P3 基础工具测试、Stage 4 整体复审与上传、S05-P1 A0 文件登记、S05-P2 public-safe A0 字段级黄金基准候选合同、S05-P3 public-safe A0 authority baseline lock、Stage 5 整体复审与上传、S06-P1 public-safe zero-delta validator、S06-P2 public-safe cross-source difference queue、S06-P3 public-safe validation evidence output、Stage 6 整体复审与上传、S07-P1 财务文件适配、S07-P2 WPS 文件适配、S07-P3 红圈导出后置策略、Stage 7 整体复审与上传、S08-P1 public-safe 项目组合键、S08-P2 public-safe 业务实体模型、S08-P3 public-safe 匹配质量测试、S09-P1 public-safe 项目成本事实层、S09-P2 public-safe 毛利与现金毛利计算层、S09-P3 public-safe 口径转换与差异核对层、Stage 9 整体复审与 GitHub main 上传、S10-P1 public-safe 报告模板、S10-P2 public-safe 报告可信等级运行时、S10-P3 public-safe 报告导出、Stage 10 整体复审与 GitHub main 上传、S11-P1 public-safe 首页与导航、S11-P2 public-safe 数据源检查板、S11-P3 public-safe 项目成本页面、Stage 11 整体复审与 GitHub main 上传、S12-P1 public-safe 人工处理事件、S12-P2 public-safe 影响预览、S12-P3 public-safe 重跑机制、Stage 12/13/14/15 复审与上传、S16-P1 public-safe 外协采购归集、S16-P2 public-safe 项目状态生命周期、S16-P3 public-safe 客户经营分析，以及 Stage 16 整体复审。不声明 Stage 16 GitHub upload、S17、lineage 完整检查、正式报告生成、采购执行、付款审批、付款执行、银行操作、现场施工、安全签字、技术签字、开票、催收或法律决策已经实现。

## Active Model

### MOD-KMFA-GOV-001

- type: deterministic governance contract
- purpose: 控制 Stage/Phase 边界、GitHub 上传门禁、公开仓库隐私边界和质量优先规则。
- fact_level: EXTRACTED
- evidence: `KMFA/AGENTS.md`, `KMFA/docs/governance/model_registry.yaml`

### MOD-KMFA-METADATA-001

- type: deterministic metadata governance contract
- purpose: 定义 metadata 七类目录、核心标识符、公开仓库隐私边界和协议检查。
- fact_level: EXTRACTED
- evidence: `KMFA/docs/governance/METADATA_PROTOCOL.md`, `KMFA/metadata/protocol/metadata_protocol.yaml`, `KMFA/tools/metadata_protocol_check.py`

### MOD-KMFA-IMMUTABILITY-001

- type: deterministic immutability contract
- purpose: 定义 raw manifest 不可变字段、派生数据版本化、前端/人工控制事件写入边界，防止原始数据污染。
- fact_level: EXTRACTED
- evidence: `KMFA/docs/governance/IMMUTABILITY_POLICY.md`, `KMFA/metadata/imports/raw_manifest_policy.yaml`, `KMFA/tools/immutability_policy_check.py`

### MOD-KMFA-QUALITY-GATE-001

- type: deterministic quality gate contract
- purpose: 定义 Q0-Q5 数据质量等级、A/B/C/D 报告可信等级和报告发布权限门禁。
- fact_level: EXTRACTED
- evidence: `KMFA/docs/governance/QUALITY_GATE_POLICY.md`, `KMFA/metadata/reports/report_release_gate.yaml`, `KMFA/tools/check_report_grade_gate.py`

### MOD-KMFA-FILE-IMPORT-001

- type: deterministic file metadata registration
- purpose: 对授权本地文件生成 hash、大小、导入批次、来源包记录、私有 storage ref 和操作提示，并安全解包 zip。
- fact_level: EXTRACTED
- evidence: `KMFA/tools/file_import_register.py`, `KMFA/metadata/imports/file_import_policy.yaml`, `KMFA/stage_artifacts/S03_P1_file_import/human/s03_p1_completion_record.md`
- limitation: 只登记 metadata，不解析业务字段，不保存原始文件 bytes，不提交原始文件。

### MOD-KMFA-SOURCE-CHECK-001

- type: deterministic source readiness matrix
- purpose: 按来源系统、业务板块、文件包、主体、账户、频率生成检查矩阵，并以 metadata event 追加状态变化。
- fact_level: EXTRACTED
- evidence: `KMFA/tools/source_check_matrix.py`, `KMFA/metadata/sources/source_check_matrix_policy.yaml`, `KMFA/stage_artifacts/S03_P2_source_check_matrix/human/s03_p2_completion_record.md`
- limitation: 不实现自动选边、业务字段解析或 UI 检查板。

### MOD-KMFA-SOURCE-PRIORITY-001

- type: deterministic source priority contract
- purpose: 固化原始上传/授权导出优先于处理后数据；同源不一致失效缓存并请求重跑；跨源冲突进入人工差异队列。
- fact_level: EXTRACTED
- evidence: `KMFA/tools/source_priority.py`, `KMFA/metadata/sources/source_priority_policy.yaml`, `KMFA/metadata/quality/source_difference_queue.jsonl`, `KMFA/stage_artifacts/S03_P3_source_priority/human/s03_p3_completion_record.md`
- limitation: 不解析金额，不读取真实业务源值，不自动选择跨源冲突一边。

### FORM-KMFA-AMOUNT-001

- type: deterministic amount normalization
- purpose: 将授权来源中的业务金额标准化为整数分，并阻断 float 金额用法。
- fact_level: EXTRACTED
- evidence: `KMFA/tools/amount_tools.py`, `KMFA/tools/check_no_float_money.py`, `KMFA/stage_artifacts/S04_P1_amount_tools/human/s04_p1_completion_record.md`
- boundary_validation: `KMFA/tests/test_basic_tool_boundaries.py`, `KMFA/stage_artifacts/S04_P3_basic_tool_tests/human/tool_function_test_report.md`
- limitation: 不做 zero-delta，不处理源冲突取舍。

### FORM-KMFA-FIELD-STANDARDIZATION-001

- type: deterministic field standardization
- purpose: 将日期、期间、公司主体、项目名称、客户/对手方、合同编号映射到 canonical fields，并把缺字段或异常字段写入 metadata 质量状态。
- fact_level: EXTRACTED
- evidence: `KMFA/tools/field_standardization.py`, `KMFA/metadata/schema_maps/field_alias_dictionary.csv`, `KMFA/metadata/quality/field_quality_status.jsonl`, `KMFA/stage_artifacts/S04_P2_field_standardization/human/s04_p2_completion_record.md`
- boundary_validation: `KMFA/tests/test_basic_tool_boundaries.py`, `KMFA/stage_artifacts/S04_P3_basic_tool_tests/human/tool_function_test_report.md`
- limitation: 不解析真实业务源，不建立事实层，不生成报告。

### VALIDATION-KMFA-S04P3-001

- type: synthetic boundary validation report
- purpose: 用合成值验证金额、日期和期间基础工具边界，生成 JSON/Markdown 工具函数测试报告。
- fact_level: EXTRACTED
- evidence: `KMFA/tools/generate_tool_test_report.py`, `KMFA/stage_artifacts/S04_P3_basic_tool_tests/human/tool_function_test_report.md`
- limitation: 只验证基础工具边界，不替代 A0、zero-delta、事实层或报告验收。

### FORM-KMFA-A0-FILE-REGISTRATION-001

- type: deterministic public-safe A0 file registration
- purpose: 登记 A0 文件数量、source package SHA256、legacy 指纹、A0 项目候选和 Q3/Q4/Q5 状态，不提交 raw PDF、Excel 或 zip。
- fact_level: EXTRACTED
- evidence: `KMFA/tools/a0_file_register.py`, `KMFA/tools/check_a0_file_registration.py`, `KMFA/stage_artifacts/S05_P1_a0_file_registration/human/s05_p1_completion_record.md`
- limitation: 私有 `销售绩效考核.zip` 不可用时成员 SHA256 保持 pending；不抽取字段值，不完成 Q4/Q5。

### FORM-KMFA-A0-GOLDEN-FIXTURE-001

- type: deterministic public-safe A0 golden fixture candidate contract
- purpose: 为合同额、支出合计、毛利、毛利率、成本分类建立字段合同、private refs、hash/status 和 source anchor 状态。
- fact_level: EXTRACTED
- evidence: `KMFA/tools/a0_golden_fixture.py`, `KMFA/tools/check_a0_golden_fixture.py`, `KMFA/stage_artifacts/S05_P2_a0_golden_fixture/human/s05_p2_completion_record.md`
- limitation: S05-P2 完成本地候选合同和 owner/授权降级决策；Q5 authority lock 由 `FORM-KMFA-A0-AUTHORITY-BASELINE-LOCK-001` 单独约束。

### FORM-KMFA-A0-AUTHORITY-BASELINE-LOCK-001

- type: deterministic public-safe A0 authority baseline lock
- purpose: 将 40 条具备 private hash/source-anchor 证据的 PDF 字段锁定为 Q5 calculation baseline，并将 5 条 Excel 字段按 active owner/授权降级决策排除。
- fact_level: EXTRACTED
- evidence: `KMFA/tools/a0_authority_baseline_lock.py`, `KMFA/tools/check_a0_authority_baseline_lock.py`, `KMFA/metadata/baseline/a0_authority_baseline_manifest.json`, `KMFA/stage_artifacts/S05_P3_authority_baseline_lock/human/s05_p3_completion_record.md`
- limitation: 只保存 public-safe hash/source-anchor baseline，不提交真实字段明文；Stage 5 review/upload 已完成，但不代表 zero-delta、lineage 或正式报告发布完成。

### FORM-KMFA-REDCIRCLE-POSTPONEMENT-001

- type: deterministic redcircle export postponement policy
- purpose: 为红圈经营、合同、回款、财务四类导出预留 public-safe 模板，并明确 D15 文件型 MVP 不接自动接口。
- fact_level: EXTRACTED
- evidence: `KMFA/tools/redcircle_postponement_policy.py`, `KMFA/tools/check_s07_p3_redcircle_postponement.py`, `KMFA/metadata/schema_maps/redcircle_postponement_manifest.json`, `KMFA/stage_artifacts/S07_P3_redcircle_postponement_policy/human/s07_p3_completion_record.md`
- limitation: 只保存 template id、hash/private ref、控制状态和 rollback metadata；不提交红圈原始导出、接口凭证、字段明文、真实业务值，不解锁事实层、lineage、正式报告、UI 或外部接口。

### FORM-KMFA-PROJECT-COMPOSITE-KEY-001

- type: deterministic public-safe project identity matching
- purpose: 用合同编号、项目名称、对手方、主体、时间、金额签名、责任人、来源 hash 八个组件建立项目组合键并输出匹配候选。
- fact_level: EXTRACTED
- evidence: `KMFA/tools/project_composite_key.py`, `KMFA/tools/check_s08_p1_project_composite_key.py`, `KMFA/metadata/schema_maps/project_composite_key_manifest.json`, `KMFA/stage_artifacts/S08_P1_project_composite_key/human/s08_p1_completion_record.md`
- limitation: 只保存组件 hash、private ref、整数权重、匹配状态和人工复核队列；不提交 raw business values、字段明文、Excel/PDF/zip/private CSV；S08-P2 已由业务实体模型覆盖，但不实现 S08-P3、事实层、lineage、正式报告、UI 或外部接口。

### FORM-KMFA-BUSINESS-ENTITY-MODEL-001

- type: deterministic public-safe business entity schema
- purpose: 定义客户、合同、项目、成本、开票、回款、应收和税务证据 8 类业务实体，以及 14 条关系和 32 个生命周期状态。
- fact_level: EXTRACTED
- evidence: `KMFA/tools/business_entity_model.py`, `KMFA/tools/check_s08_p2_business_entity_model.py`, `KMFA/metadata/schema_maps/business_entity_model_manifest.json`, `KMFA/docs/governance/BUSINESS_ENTITY_MODEL_SCHEMA.md`, `KMFA/stage_artifacts/S08_P2_business_entity_model/human/s08_p2_completion_record.md`
- limitation: 只保存 entity refs、source refs、source hashes、public-safe schema、关系和生命周期 metadata；不提交 raw business values、字段明文、Excel/PDF/zip/private CSV，不实现 S08-P3、事实层、lineage、正式报告、UI、外部接口、Stage 8 review 或 GitHub upload。

### FORM-KMFA-ENTITY-MATCHING-QUALITY-001

- type: deterministic public-safe entity matching quality gate
- purpose: 覆盖同名项目、多主体、多账户、多期间 4 类匹配质量场景，并将中高风险候选送入人工复核。
- fact_level: EXTRACTED
- evidence: `KMFA/tools/entity_matching_quality.py`, `KMFA/tools/check_s08_p3_entity_matching_quality.py`, `KMFA/metadata/quality/entity_matching_quality_manifest.json`, `KMFA/metadata/quality/entity_matching_quality_cases.jsonl`, `KMFA/metadata/quality/entity_matching_review_queue.jsonl`, `KMFA/stage_artifacts/S08_P3_entity_matching_quality/machine/entity_matching_report.json`, `KMFA/stage_artifacts/S08_P3_entity_matching_quality/human/s08_p3_completion_record.md`
- limitation: 只保存 profile/entity/source hash refs、匹配分、风险等级、人工复核状态和 evidence metadata；不提交 raw business values、字段明文、Excel/PDF/zip/private CSV，不执行 Stage 8 review、事实层、lineage、正式报告、UI、外部接口或 GitHub upload。

### FORM-KMFA-PROJECT-COST-FACT-LAYER-001

- type: deterministic public-safe project cost fact layer
- purpose: 为收入、合同额、开票、回款、成本合计、成本分类建立结构化 fact slots，并将未归项目成本进入未归集成本池。
- fact_level: EXTRACTED
- evidence: `KMFA/tools/project_cost_fact_layer.py`, `KMFA/tools/check_s09_p1_project_cost_fact_layer.py`, `KMFA/metadata/reports/project_cost_fact_layer_manifest.json`, `KMFA/metadata/lineage/project_cost_fact_records.jsonl`, `KMFA/metadata/lineage/unallocated_project_cost_pool.jsonl`, `KMFA/stage_artifacts/S09_P1_project_cost_fact_layer/human/s09_p1_completion_record.md`
- limitation: 只保存 metric/category slots、private refs、hash refs、质量阻断状态和 evidence metadata；不提交 raw business values、字段明文、Excel/PDF/zip/private CSV，不执行 S09-P2 毛利/现金毛利、S09-P3 差异核对、Stage 9 review、lineage 完整检查、正式报告、UI、外部接口或 GitHub upload。

### FORM-KMFA-MARGIN-CASH-MARGIN-001

- status: active
- type: deterministic public-safe margin and cash margin calculation contract
- purpose: 建立权威毛利、系统复算毛利、现金毛利和毛利率的整数分/basis points 计算合同，并保留权威显示值与系统复算值分离。
- evidence: `KMFA/tools/project_margin_cash_margin.py`, `KMFA/tools/check_s09_p2_margin_cash_margin.py`, `KMFA/metadata/reports/project_margin_cash_margin_manifest.json`, `KMFA/metadata/lineage/project_margin_cash_margin_records.jsonl`, `KMFA/metadata/quality/scope_difference_summary.jsonl`, `KMFA/stage_artifacts/S09_P2_margin_cash_margin/human/s09_p2_completion_record.md`
- limitation: 只保存 authority/system/cash margin private refs、hash refs、差异摘要状态和 evidence metadata；不提交 raw business values、字段明文、Excel/PDF/zip/private CSV；S09-P3 已单独建立核对层，但 S09-P2 不代表 Stage 9 review、lineage 完整检查、正式报告、UI、外部接口或 GitHub upload 完成。

### FORM-KMFA-SCOPE-RECONCILIATION-001

- status: active
- type: deterministic public-safe scope reconciliation contract
- purpose: 将 S09-P2 的口径差异摘要转换为 owner-readable reconciliation records，并覆盖合同/项目收入、项目成本/财务费用、银行回款/应收账龄、开票/合同结算/税务、研发费用/项目人员证据、权威 PDF/Excel 与系统复算 6 类核对域。
- evidence: `KMFA/tools/project_scope_reconciliation.py`, `KMFA/tools/check_s09_p3_scope_reconciliation.py`, `KMFA/metadata/reports/project_scope_reconciliation_manifest.json`, `KMFA/metadata/quality/scope_reconciliation_records.jsonl`, `KMFA/metadata/quality/scope_reconciliation_domain_controls.jsonl`, `KMFA/stage_artifacts/S09_P3_scope_reconciliation/human/s09_p3_completion_record.md`
- limitation: 只保存 source refs、private refs、hash refs、原因候选、依据 refs、影响范围、责任角色、reviewer 和 pending 状态；不提交 raw business values、字段明文、Excel/PDF/zip/private CSV，不关闭差异，不实际重跑派生指标或正式报告；Stage 9 review 已本地通过但不代表 lineage 完整检查、UI、外部接口或 GitHub upload 完成。

### FORM-KMFA-REPORT-TEMPLATE-001

- status: active
- type: deterministic public-safe report template contract
- purpose: 建立项目成本专题报告和经营总览报告模板，锁定管理可读章节与 v1.2 HTML/报告样板引用。
- evidence: `KMFA/tools/report_templates.py`, `KMFA/tools/check_s10_p1_report_templates.py`, `KMFA/metadata/reports/report_template_manifest.json`, `KMFA/metadata/reports/report_templates.jsonl`, `KMFA/metadata/reports/report_template_sections.jsonl`, `KMFA/stage_artifacts/S10_P1_report_templates/human/s10_p1_completion_record.md`
- limitation: 只保存模板结构、管理可读章节、source refs、HTML 验收样板引用、status 和 evidence metadata；不提交 raw business values、字段明文、Excel/PDF/zip/private CSV，不判定 A/B/C/D 可信等级，不生成 HTML/CSV/Excel/PDF 导出，不执行 Stage 10 review、lineage 完整检查、UI、外部接口或 GitHub upload。

### FORM-KMFA-REPORT-GRADE-RUNTIME-001

- status: active
- type: deterministic public-safe report grade runtime
- purpose: 基于数据质量、zero-delta、pending reconciliation、lineage、人工确认和时效状态判定 A/B/C/D 报告可信等级，并在证据不足时阻断完整可信报告显示。
- fact_level: EXTRACTED
- evidence: `KMFA/tools/report_grade_runtime.py`, `KMFA/tools/check_s10_p2_report_grade_runtime.py`, `KMFA/metadata/reports/report_grade_runtime_manifest.json`, `KMFA/metadata/reports/report_grade_runtime_records.jsonl`, `KMFA/stage_artifacts/S10_P2_report_grade_runtime/human/s10_p2_completion_record.md`
- limitation: 当前 2 条报告等级记录均为 D；只保存等级、版本绑定、hash/ref、scope gate 和 evidence metadata；不提交 raw business values、字段明文、Excel/PDF/zip/private CSV；HTML/CSV 导出由 `FORM-KMFA-REPORT-EXPORT-001` 单独约束；不执行 Stage 10 review、lineage 完整检查、UI、外部接口或 GitHub upload。

### FORM-KMFA-REPORT-EXPORT-001

- status: active
- type: deterministic public-safe report export runtime
- purpose: 基于 S10-P1 模板和 S10-P2 D 级阻断记录生成 public-safe HTML 预览、CSV/Excel-compatible 附表和 PDF private runtime policy。
- fact_level: EXTRACTED
- evidence: `KMFA/tools/report_export_runtime.py`, `KMFA/tools/check_s10_p3_report_export.py`, `KMFA/metadata/reports/report_export_manifest.json`, `KMFA/metadata/reports/report_export_records.jsonl`, `KMFA/stage_artifacts/S10_P3_report_export/human/s10_p3_completion_record.md`
- limitation: 只提交 HTML/CSV/manifest/records/evidence metadata；不提交 raw business values、字段明文、Excel workbook、PDF、zip、sqlite 或 private CSV；2 条报告仍为 D 级阻断，不能作为正式经营决策依据；不执行 Stage 10 review、lineage 完整检查、UI、外部接口或 GitHub upload。

### FORM-KMFA-HOME-NAVIGATION-001

- status: active
- type: deterministic public-safe home navigation runtime
- purpose: 生成 KMFA 首页与导航的 public-safe manifest、模块 records 和蓝色商务风 HTML 样张，覆盖 8 个 S11-P1 必需入口。
- fact_level: EXTRACTED
- evidence: `KMFA/tools/home_navigation_runtime.py`, `KMFA/tools/check_s11_p1_home_navigation.py`, `KMFA/tests/test_home_navigation_runtime.py`, `KMFA/metadata/reports/home_navigation_manifest.json`, `KMFA/metadata/reports/home_navigation_modules.jsonl`, `KMFA/stage_artifacts/S11_P1_home_navigation/human/s11_p1_completion_record.md`
- limitation: 只提交首页导航结构、公开安全摘要和 HTML 样张；不提交 raw business values、字段明文、Excel workbook、PDF、zip、sqlite 或 private CSV；S11-P2 已由数据源检查板覆盖，但 S11-P1 不实现 S11-P3 项目成本详情、Stage 11 review、正式报告、lineage full check、外部接口或 GitHub upload。

### FORM-KMFA-SOURCE-CHECK-BOARD-001

- status: active
- type: deterministic public-safe source check board runtime
- purpose: 生成 KMFA 数据源检查板的 public-safe manifest、来源状态 rows 和蓝灰商务风 HTML 样张，覆盖固定 11 列、5 种状态和状态点击详情。
- fact_level: EXTRACTED
- evidence: `KMFA/tools/source_check_board_runtime.py`, `KMFA/tools/check_s11_p2_source_check_board.py`, `KMFA/tests/test_source_check_board_runtime.py`, `KMFA/metadata/reports/source_check_board_manifest.json`, `KMFA/metadata/reports/source_check_board_rows.jsonl`, `KMFA/stage_artifacts/S11_P2_source_check_board/human/s11_p2_completion_record.md`
- limitation: 只提交公开安全来源类别、业务板块、包引用、主体分组、账户/报表分组、状态、影响和下一步；不提交 raw business values、字段明文、真实源文件名、真实账号、Excel workbook、PDF、zip、sqlite 或 private CSV；不实现 S11-P3 项目成本详情、Stage 11 review、正式报告、lineage full check、外部接口或 GitHub upload。

### FORM-KMFA-PROJECT-COST-PAGE-001

- status: active
- type: deterministic public-safe project cost page runtime
- purpose: 生成 KMFA 项目成本页面的 public-safe manifest、项目页面 records 和蓝色商务风 HTML 页面，覆盖项目列表、毛利状态、成本结构、回款状态、差异状态、项目详情、来源证据、待处理事项和报告预览。
- fact_level: EXTRACTED
- evidence: `KMFA/tools/project_cost_page_runtime.py`, `KMFA/tools/check_s11_p3_project_cost_page.py`, `KMFA/tests/test_project_cost_page_runtime.py`, `KMFA/metadata/reports/project_cost_page_manifest.json`, `KMFA/metadata/reports/project_cost_page_projects.jsonl`, `KMFA/stage_artifacts/S11_P3_project_cost_page/human/s11_p3_completion_record.md`
- limitation: 只提交公开安全项目分组、状态、成本分类标签、证据引用、待处理事项、HTML 样张、manifest 和 records；不提交 raw business values、字段明文、真实源文件名、真实账号、Excel workbook、PDF、zip、sqlite/db 或 private CSV；报告预览可直接查看但必须显示 D 级且不可绕过质量等级；Stage 11 review/upload 已完成，但不代表 S12、正式报告、lineage full check 或外部接口完成。

### FORM-KMFA-MANUAL-RESOLUTION-EVENT-001

- status: active
- type: deterministic public-safe manual resolution event contract
- purpose: 建立 S12-P1 人工处理事件的 append-only 记录、manifest 和 HTML 工作台样张，覆盖字段映射、项目匹配、差异处理和备注。
- fact_level: EXTRACTED
- expression: `manual_resolution_events_valid = manual_event_count == 5 AND manual_action_kind_count == 4 AND approved_event_count == 1 AND reverse_event_count == 1 AND raw_layer_write_allowed == false AND impact_preview_publish_allowed == false AND derived_rerun_allowed == false AND formal_report_allowed == false AND stage12_review_allowed == false AND github_upload_allowed == false`
- evidence: `KMFA/tools/manual_resolution_events.py`, `KMFA/tools/check_s12_p1_manual_resolution_events.py`, `KMFA/tests/test_manual_resolution_events.py`, `KMFA/metadata/approvals/manual_resolution_event_manifest.json`, `KMFA/metadata/approvals/manual_resolution_events.jsonl`, `KMFA/stage_artifacts/S12_P1_manual_resolution_events/human/s12_p1_completion_record.md`
- limitation: 只提交公开安全事件类型、角色引用、时间、原因码、影响范围、版本和证据引用；不提交 raw business values、字段明文、真实金额、Excel workbook、PDF、zip、sqlite/db、private CSV 或 credentials；不发布 S12-P2 影响预览，不执行 S12-P3 派生重跑，不做 Stage 12 review/upload、lineage full check、正式报告或外部接口。

## Planned Business Model

### MOD-KMFA-COST-001

- status: planned with S04-P1 amount formula, S04-P2 field standardization formula, S04-P3 boundary validation, S05-P1 A0 file registration, S05-P2 public-safe fixture contract, S05-P3 public-safe authority lock, Stage 5 review/upload, Stage 6 review/upload, S07-P1 finance file adapter, S07-P2 WPS file adapter, S07-P3 redcircle postponement policy, Stage 7 review/upload, S08-P1 project composite key, S08-P2 business entity model, S08-P3 entity matching quality, S09-P1 project cost fact layer, S09-P2 margin/cash margin layer, S09-P3 scope reconciliation, Stage 9 review/upload, S10-P1 report templates, S10-P2 report grade runtime, S10-P3 report export, S11-P1 home navigation, S11-P2 source check board, S11-P3 project cost page, Stage 11 review/upload, S12-P1 manual resolution events, S12-P2 impact preview and S12-P3 rerun mechanism active
- purpose: 后续文件型项目成本分析 MVP。
- dependency: S05 A0 基准、S06 零差异、S08 项目身份匹配、S09 成本计算、S10 报告等级。
- current limitation: Stage 12 review/upload, lineage full check, official report generation, and external connectors are not implemented; S10-P3 exports and S11 public-safe pages remain D-grade/public-safe previews and are not decision-grade reports.

## Counts

- active models: 7
- active formulas: 45
- active parameters: 219
- planned models: 1
- planned formulas: 0
- planned parameters: 1

## Stop Conditions

- 原始敏感经营数据进入公开仓库。
- 业务金额使用 float。
- 0.01 元差异被静默通过。
- 缺数据报告被伪装为完整报告。
- Stage 未完成复审修复即上传 GitHub。
