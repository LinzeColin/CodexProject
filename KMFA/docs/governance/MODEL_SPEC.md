# KMFA Model Spec

product_version: 0.1.0-s06-p2-cross-source-difference-queue

## Scope

当前模型说明覆盖 S01 已建立并按 v1.2 重放的治理边界、S02-P1 metadata 协议、S02-P2 不可污染原则、S02-P3 质量等级门禁协议、S03-P1 文件型导入登记模型、S03-P2 数据源检查矩阵模型、S03-P3 源优先级模型、S04-P1 金额工具、S04-P2 字段标准化工具、S04-P3 基础工具测试、Stage 4 整体复审与上传、S05-P1 A0 文件登记、S05-P2 public-safe A0 字段级黄金基准候选合同、S05-P3 public-safe A0 authority baseline lock、Stage 5 整体复审与上传、S06-P1 public-safe zero-delta validator，以及 S06-P2 public-safe cross-source difference queue。不声明项目成本事实层、S06-P3、lineage 完整检查或正式报告生成已经实现。

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

## Planned Business Model

### MOD-KMFA-COST-001

- status: planned with S04-P1 amount formula, S04-P2 field standardization formula, S04-P3 boundary validation, S05-P1 A0 file registration, S05-P2 public-safe fixture contract, S05-P3 public-safe authority lock, and Stage 5 review/upload active
- purpose: 后续文件型项目成本分析 MVP。
- dependency: S05 A0 基准、S06 零差异、S09 成本计算、S10 报告等级。
- current limitation: no production data import, no zero-delta, no lineage full check, and no official report generation.

## Counts

- active models: 7
- active formulas: 12
- active parameters: 33
- planned models: 1
- planned formulas: 0
- planned parameters: 3

## Stop Conditions

- 原始敏感经营数据进入公开仓库。
- 业务金额使用 float。
- 0.01 元差异被静默通过。
- 缺数据报告被伪装为完整报告。
- Stage 未完成复审修复即上传 GitHub。
