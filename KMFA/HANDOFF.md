# KMFA Handoff

更新时间: 2026-06-30

## 当前目标

v1.2 FULL_HTML_NO_OMISSION 完整任务包已成为 KMFA 后续开发基线，并已按 v1.2 重新走完 Stage 1。Stage 2、Stage 3、Stage 4、Stage 5、Stage 6 和 Stage 7 均已完成本地实现、验证、整体复审和 GitHub main 上传。Stage 5 已完成 `S05-P1｜A0 文件登记`、`S05-P2｜字段级黄金基准`、`S05-P3｜权威基准锁定`、Stage 5 整体复审和 final GitHub upload。S05-P3 基于 S05-P2 active owner/授权降级决策，锁定 40 条 PDF 字段 hash/source-anchor 记录为 public-safe Q5 calculation baseline，并将 5 条 Excel 字段排除为 `cross_source_support_only`。Stage 6 已完成 `S06-P1｜零差异校验器`、`S06-P2｜跨源差异队列`、`S06-P3｜校验证据输出`、整体复审和 final GitHub upload。S07-P1 已完成 `财务文件适配`，生成财务支撑源登记、字段候选映射和只读字段报告。S07-P2 已完成 `WPS 文件适配`，生成 WPS 导出源登记、字段映射、转换提示和映射规则版本。S07-P3 已完成 `红圈导出后置策略`，预留红圈经营、合同、回款、财务四类导出模板，明确 D15 文件型 MVP 不接自动接口，并建立只读、留 hash、可回滚的后续接入控制。Stage 7 整体复审和 final GitHub upload 证据在 `KMFA/stage_artifacts/S07_STAGE_REVIEW/`；下一轮只能做 `S08-P1｜项目组合键`，不能跳到 S08-P2、UI、报告、事实层、lineage 或外部接口。

## 当前状态

- `S01-P1` 已在前序工作目录完成，只读计划证据已迁移到 `KMFA/stage_artifacts/S01_P1_read_only_plan/`。
- `S01-P2` 已创建项目根、三中文入口、模型参数文件、Lean v2 与 v1 兼容治理文件、metadata 草案。
- `S01-P3` 已导入完整需求追溯矩阵、新增正式 `KMFA/tools/no_omission_check.py`、建立 18 Stage / 54 Phase / 162 Task 状态登记。
- Stage 1 总复审已通过，复审产物在 `KMFA/stage_artifacts/S01_STAGE_REVIEW/`。
- Stage 1 已上传到 GitHub main: `ff834578e640dc360e764ab18f9da2003c735e3e`。
- `S02-P1` 已建立 metadata 七类目录、标识符协议、公开仓库隐私边界和 `KMFA/tools/metadata_protocol_check.py`。
- `S02-P2` 已建立 raw manifest append-only 规范、派生版本协议、前端 raw 写入边界和 `KMFA/tools/immutability_policy_check.py`。
- `S02-P3` 已建立 Q0-Q5 数据质量等级、A/B/C/D 报告可信等级、发布门禁和 `KMFA/tools/check_report_grade_gate.py`。
- Stage 2 复审已通过，复审产物在 `KMFA/stage_artifacts/S02_STAGE_REVIEW/`。
- Stage 2 已上传 GitHub main: final remote commit `6178b5215f92f12d6facad9a990e8659b3a70ba4`，reviewed content commit `834ff75516405ddbc8289f00ba67579691473709`。
- v1.2 完整任务包已同步到 `KMFA/taskpack/v1_2/`，源 zip SHA256 为 `3bb2ebf16fb4ad8b9d198484e9d80ea2aed3c19c54c483efebe023b772ad0e66`。
- HTML/UIUX/报告验收样板已同步：45 个 HTML，7 个核心验收样板。
- `90_用户原始上传数据` 未进入公开仓库，只保存 SHA256 登记和禁止提交规则。
- Stage 1 v1.2 重放证据在 `KMFA/stage_artifacts/S01_REBASE_V12_FULL_TASKPACK/`。
- `S03-P1` 已完成本地实现与验证：新增 `KMFA/tools/file_import_register.py`、`KMFA/tests/test_file_import_register.py` 和 `KMFA/stage_artifacts/S03_P1_file_import/`。
- S03-P1 只生成文件登记 metadata、hash、size、import_run、source package、私有 storage ref 和 WPS/OLE 提示；未导入真实原始文件，未解析业务字段。
- `S03-P2` 已完成本地实现与验证：新增 `KMFA/tools/source_check_matrix.py`、`KMFA/tests/test_source_check_matrix.py` 和 `KMFA/stage_artifacts/S03_P2_source_check_matrix/`。
- S03-P2 只生成数据源检查矩阵 metadata 和 append-only 状态事件；未提交真实源行，未做源优先级。
- `S03-P3` 已完成本地实现与验证：新增 `KMFA/tools/source_priority.py`、`KMFA/tests/test_source_priority.py` 和 `KMFA/stage_artifacts/S03_P3_source_priority/`。
- S03-P3 只生成源优先级、同源失效重跑事件和跨源差异队列 metadata；未解析真实业务源值，未自动选边，未上传 GitHub。
- Stage 3 复审已通过，发现的源优先级链路对齐问题已修复，并已上传 GitHub main，reviewed content commit `39b0eef52424a12b6c0c8ad368bd878b46300be4`。
- `S04-P1` 已完成本地实现与验证：新增 `KMFA/tools/amount_tools.py`、`KMFA/tools/check_no_float_money.py`、`KMFA/tests/test_amount_tools.py` 和 `KMFA/stage_artifacts/S04_P1_amount_tools/`。
- S04-P1 只提供金额标准化与 no-float 检查；未做字段标准化、zero-delta、A0 基准、事实层、报告或 UI。
- `S04-P2` 已完成本地实现与验证：新增 `KMFA/tools/field_standardization.py`、`KMFA/tests/test_field_standardization.py`、`KMFA/metadata/schema_maps/field_alias_dictionary.csv`、`KMFA/metadata/schema_maps/field_standardization_policy.yaml`、`KMFA/metadata/quality/field_quality_status.jsonl` 和 `KMFA/stage_artifacts/S04_P2_field_standardization/`。
- S04-P2 只提供字段别名、日期、期间、主体、项目、客户/对手方、合同编号标准化和缺字段质量状态；未做 S04-P3 工具测试报告、zero-delta、A0 基准、事实层、报告或 UI。
- `S04-P3` 已完成本地实现与验证：新增 `KMFA/tests/test_basic_tool_boundaries.py`、`KMFA/tools/generate_tool_test_report.py` 和 `KMFA/stage_artifacts/S04_P3_basic_tool_tests/`，并修复中文完整日期转期间边界。
- S04-P3 只提供基础工具合成边界测试和工具函数测试报告；未做 zero-delta、A0 基准、事实层、报告或 UI。
- Stage 4 整体复审已通过：新增 `KMFA/stage_artifacts/S04_STAGE_REVIEW/`，复跑 S04-P1/P2/P3 工具测试、治理 validator、no-float 检查和敏感文件扫描。
- Stage 4 复审修复了 `功能清单.md` 中 `FEAT-KMFA-016` 金额工具详情缺口。
- Stage 4 final GitHub upload 已生成证据：`KMFA/stage_artifacts/S04_STAGE_REVIEW/human/github_upload_record.md` 和 `KMFA/stage_artifacts/S04_STAGE_REVIEW/machine/stage4_upload_manifest.json`。
- `S05-P1` 已完成本地实现与验证：新增 `KMFA/tools/a0_file_register.py`、`KMFA/tools/check_a0_file_registration.py`、`KMFA/tests/test_a0_file_register.py`、`KMFA/metadata/baseline/a0_file_manifest.json`、`KMFA/metadata/baseline/a0_project_candidates.jsonl` 和 `KMFA/stage_artifacts/S05_P1_a0_file_registration/`。
- S05-P1 只登记 `销售绩效考核.zip` 的公开安全 source package SHA256、8 个 PDF + 1 个 Excel inventory 记录、legacy 指纹、Q3 机器候选和 Q4 未锁定状态；未抽取字段值、未生成 A0 字段级黄金基准、未做 zero-delta、事实层、报告或 UI。
- S05-P1 执行时未提供可验证私有 `销售绩效考核.zip`，所以成员级 `member_sha256` 仍为 `pending_private_zip_unavailable`；S05-P2 后续私有审计发现本机 zip 整包 hash/size 与登记 source package 不匹配，因此不能回填 S05-P1 member SHA256，也没有把 legacy CRC/指纹伪装成 SHA256。
- `S05-P2` 已生成 public-safe 字段合同和候选结构：新增 `KMFA/tools/a0_golden_fixture.py`、`KMFA/tools/check_a0_golden_fixture.py`、`KMFA/tests/test_a0_golden_fixture.py`、`KMFA/metadata/baseline/a0_golden_fixture_manifest.json`、`KMFA/metadata/baseline/a0_golden_fixture_candidates.jsonl` 和 `KMFA/stage_artifacts/S05_P2_a0_golden_fixture/`。
- S05-P2 当前生成 5 个字段合同和 45 条字段候选：合同额、支出合计、毛利、毛利率、成本分类；每条候选都有 private raw/normalized value ref、source anchor 状态和 Q3/Q4/Q5 门禁。
- 本机提供的 `销售绩效考核.zip` 整包 hash/size 与登记 source package 不匹配；过滤 macOS 隐藏文件后 9 个真实业务成员 hash 与 Stage2 Ring4 registry 匹配。当前只据此和 Ring4 前序提取包执行 hash-only 部分回填，不把整包标记为 source package 匹配。
- S05-P2 已将 8 个 PDF 候选的 40 条字段记录为 hash/source anchor recorded；1 个 Excel 候选的 5 条字段仍为 `pending_private_source_unavailable`；未提交 raw/normalized 字段值、私有 CSV、zip、PDF 或 Excel。
- S05-P2 已新增 Excel 候选机器复核记录：Excel workbook 更像交叉来源汇总/支持材料，不得机器合成为单一 A0 项目基准，不得生成占位 hash，不得进入 Q4/Q5；证据在 `KMFA/stage_artifacts/S05_P2_a0_golden_fixture/human/excel_resolution_record.md`。
- S05-P2 已新增 Excel owner 决策包：允许 `provide_private_field_mapping`、`downgrade_to_cross_source_support` 或 `keep_pending` 三类决策；证据在 `KMFA/stage_artifacts/S05_P2_a0_golden_fixture/human/excel_owner_decision_packet.md`。
- S05-P2 已新增 owner 决策包 validator：`KMFA/tools/check_s05_p2_excel_owner_decision.py` 验证决策包、fixture pending 状态、approval/control events 和 Q4/Q5 禁止状态一致。
- S05-P2 已新增 owner 决策 intake contract 和 validator：`KMFA/tools/check_s05_p2_owner_decision_intake.py` 验证 owner/授权决策记录的 public-safe schema、actor role、禁止明文键和 Q4/Q5 边界；active downgrade decision 已通过 intake validator。
- S05-P2 已新增 owner 决策模板和 validator：`KMFA/tools/check_s05_p2_owner_decision_templates.py` 验证三种模板覆盖 allowed decisions，且模板不是 active owner 决策记录。
- S05-P2 已新增 owner decision application preview：`KMFA/tools/preview_s05_p2_owner_decision_application.py` 验证 public-safe 决策如何预览为 private hash backfill、cross-source support downgrade 或继续 pending；active downgrade decision 已输出 ready preview。
- S05-P2 已新增 completion gate validator：`KMFA/tools/check_s05_p2_completion_gate.py` 默认在无 resolving owner/授权决策时返回 `BLOCKED`；使用 active downgrade decision 时返回 `ready`，防止误入 Q4/Q5 但允许本地关闭 S05-P2。
- `S05-P3` 已完成本地实现与验证：新增 `KMFA/tools/a0_authority_baseline_lock.py`、`KMFA/tools/check_a0_authority_baseline_lock.py`、`KMFA/tests/test_s05_p3_authority_baseline_lock.py`、`KMFA/metadata/baseline/a0_authority_baseline_manifest.json`、`KMFA/metadata/baseline/a0_authority_baseline_records.jsonl` 和 `KMFA/stage_artifacts/S05_P3_authority_baseline_lock/`。
- S05-P3 已锁定 baseline version `KMFA-A0-Q5-20260630-S05P3-PUBLIC-SAFE-HASH-LOCK` 和 content hash `sha256:dbb55ffb4e3608e49dbcf91e97fc0f19395a8269ff7c8f4d5c3f8ca398c03670`；40 条字段为 `q5_locked_public_safe_hash_baseline`，5 条字段为 `excluded_cross_source_support_only`。
- S05-P3 不提交 raw business data、zip、Excel、PDF、私有 CSV 或字段明文；`formal_report_allowed=false`。
- Stage 5 整体复审已本地通过：新增 `KMFA/stage_artifacts/S05_STAGE_REVIEW/human/stage5_review_report.md`、`KMFA/stage_artifacts/S05_STAGE_REVIEW/human/test_results.md` 和 `KMFA/stage_artifacts/S05_STAGE_REVIEW/machine/stage5_review_manifest.json`；后续 upload gate 已完成。
- Stage 5 final GitHub upload 已生成证据：`KMFA/stage_artifacts/S05_STAGE_REVIEW/human/github_upload_record.md` 和 `KMFA/stage_artifacts/S05_STAGE_REVIEW/machine/stage5_upload_manifest.json`；upload base `495bcd977a587b7fd8b1923bfd74f5138f12263e`，reviewed content commit `ca6788949c444188b4b93f7db42c94094d90209f`。
- `S06-P1` 已完成本地实现与验证：新增 `KMFA/tools/zero_delta_validator.py`、`KMFA/tests/test_zero_delta_validator.py` 和 `KMFA/stage_artifacts/S06_P1_zero_delta_validator/`。
- S06-P1 只比较 public-safe 已结构化整数分字段；任意 1 分差异失败并输出包含来源、字段、权威值、系统值和差额的 mismatch report。
- S06-P1 不读取真实 Excel、PDF、zip 或私有 CSV，不写 `KMFA/metadata/quality/zero_delta_results.jsonl` 或 `KMFA/metadata/quality/mismatch_report.csv`，不创建 S06-P2 队列，不做 Stage 6 复审或 GitHub upload。
- `S06-P2` 已完成本地实现与验证：新增 `KMFA/tools/cross_source_difference_queue.py`、`KMFA/tools/check_s06_p2_difference_queue.py`、`KMFA/tests/test_cross_source_difference_queue.py` 和 `KMFA/stage_artifacts/S06_P2_cross_source_difference_queue/`。
- S06-P2 只使用 public-safe synthetic PDF/Excel 同项目同字段 1 分差异 fixture；差异进入人工队列，`auto_correction_allowed=false`、`averaging_allowed=false`、`rounding_mask_allowed=false`、`auto_selection_allowed=false`。
- S06-P2 未关闭差异阻断 A 级报告：`report_grade_a_allowed=false`、`maximum_report_grade=B`、`hard_block_reason=unresolved_critical_difference`；不写 metadata/quality 运行时业务差异项，不关闭差异，不做 Stage 6 复审或 GitHub upload。
- `S06-P3` 已完成本地实现与验证：新增 `KMFA/tools/validation_evidence_output.py`、`KMFA/tools/check_s06_p3_validation_evidence.py`、`KMFA/tests/test_validation_evidence_output.py` 和 `KMFA/stage_artifacts/S06_P3_validation_evidence_output/`。
- S06-P3 将 S06-P1/S06-P2 public-safe 结果输出为 `zero_delta_result.json`、sanitized `mismatch_report.csv`、`project_validation_status.jsonl`，并写入 `KMFA/metadata/quality/{zero_delta_results.jsonl,data_quality_results.jsonl,source_difference_queue.jsonl,mismatch_report.csv}`。
- S06-P3 metadata/quality 只保存 hash/ref/status/evidence 和质量门禁状态，不新增字段明文、权威原值、系统原值、PDF 原值或 Excel 原值；不关闭差异，不做 Stage 6 复审或 GitHub upload。
- Stage 6 整体复审已本地通过：新增 `KMFA/stage_artifacts/S06_STAGE_REVIEW/human/stage6_review_report.md`、`KMFA/stage_artifacts/S06_STAGE_REVIEW/human/test_results.md` 和 `KMFA/stage_artifacts/S06_STAGE_REVIEW/machine/stage6_review_manifest.json`。
- Stage 6 复审复跑 S06-P1/S06-P2/S06-P3 validators、全量 KMFA tests、S05-P3 authority baseline dependency、治理 validator、raw/secret scan、JSON/JSONL parse、parameter CSV shape、diff check 和 evidence consistency check；复审步骤本身未执行 GitHub upload。
- Stage 6 final GitHub upload 已生成证据：`KMFA/stage_artifacts/S06_STAGE_REVIEW/human/github_upload_record.md` 和 `KMFA/stage_artifacts/S06_STAGE_REVIEW/machine/stage6_upload_manifest.json`；upload base `fd14057e7427d7f275fdb62a33619936618d0d35`，reviewed content commit `5cd284e500fec5ff215741b0e8ee164912f50268`，reviewed S06-P3 commit `c66c8b44c17ae760a5a6da4b98ab5892d90d73d0`。
- `S07-P1` 已完成本地实现与验证：新增 `KMFA/tools/finance_file_adapter.py`、`KMFA/tools/check_s07_p1_finance_file_adapter.py`、`KMFA/tests/test_finance_file_adapter.py`、`KMFA/metadata/imports/finance_support_source_registry.json`、`KMFA/metadata/schema_maps/finance_file_adapter_manifest.json`、`KMFA/metadata/schema_maps/finance_field_candidates.jsonl` 和 `KMFA/stage_artifacts/S07_P1_finance_file_adapter/`。
- S07-P1 覆盖经营分析、日记账、客户账龄、现金、纳税、开票、账户、贷款、研发费用 9 类财务支撑源；生成 45 条 hash-only 字段候选和 9 条只读字段报告。
- S07-P1 不提交 raw business data、zip、Excel、PDF、私有 CSV、字段明文、来源表头明文或真实业务值；`formal_report_allowed=false`、`q5_calculation_baseline_allowed=false`、`wps_scope_included=false`、`redcircle_scope_included=false`。
- `S07-P2` 已完成本地实现与验证：新增 `KMFA/tools/wps_file_adapter.py`、`KMFA/tools/check_s07_p2_wps_file_adapter.py`、`KMFA/tests/test_wps_file_adapter.py`、`KMFA/metadata/imports/wps_export_source_registry.json`、`KMFA/metadata/schema_maps/wps_file_adapter_manifest.json`、`KMFA/metadata/schema_maps/wps_field_mappings.jsonl`、`KMFA/metadata/schema_maps/wps_mapping_rule_versions.json`、`KMFA/metadata/schema_maps/wps_file_mapping_policy.yaml` 和 `KMFA/stage_artifacts/S07_P2_wps_file_adapter/`。
- S07-P2 覆盖 WPS 回款、应收账龄、生产项目状态、保证金 4 类导出；生成 20 条 hash-only 字段映射、4 条转换提示、4 条只读字段报告和 1 个映射规则版本。
- S07-P2 不提交 raw business data、WPS 原始文件、zip、Excel、PDF、私有 CSV、字段明文、来源表头明文或真实业务值；`formal_report_allowed=false`、`q5_calculation_baseline_allowed=false`、`finance_scope_included=false`、`redcircle_scope_included=false`。
- `S07-P3` 已完成本地实现与验证：新增 `KMFA/tools/redcircle_postponement_policy.py`、`KMFA/tools/check_s07_p3_redcircle_postponement.py`、`KMFA/tests/test_redcircle_postponement_policy.py`、`KMFA/metadata/imports/redcircle_export_source_registry.json`、`KMFA/metadata/schema_maps/redcircle_postponement_manifest.json`、`KMFA/metadata/schema_maps/redcircle_reserved_export_templates.jsonl`、`KMFA/metadata/schema_maps/redcircle_postponement_policy.yaml` 和 `KMFA/stage_artifacts/S07_P3_redcircle_postponement_policy/`。
- S07-P3 只预留红圈经营、合同、回款、财务 4 类导出模板；D15 文件型 MVP 明确不接自动接口；后续接入必须只读、留 hash、可回滚并需人工授权。
- S07-P3 不提交 raw business data、红圈原始导出文件、zip、Excel、PDF、私有 CSV、字段明文、来源表头明文、接口凭证或真实业务值；`formal_report_allowed=false`、`q5_calculation_baseline_allowed=false`、`external_connector_included=false`。
- Stage 7 整体复审已本地通过：新增 `KMFA/stage_artifacts/S07_STAGE_REVIEW/human/stage7_review_report.md`、`KMFA/stage_artifacts/S07_STAGE_REVIEW/human/test_results.md` 和 `KMFA/stage_artifacts/S07_STAGE_REVIEW/machine/stage7_review_manifest.json`。
- Stage 7 复审复跑 S07-P1/S07-P2/S07-P3 validators、全量 KMFA tests、治理 validator、raw/secret scan、YAML/JSON/JSONL/CSV parse、diff check 和 evidence consistency check；复审步骤本身未执行 GitHub upload。
- Stage 7 final GitHub upload 已生成证据：新增 `KMFA/stage_artifacts/S07_STAGE_REVIEW/human/github_upload_record.md` 和 `KMFA/stage_artifacts/S07_STAGE_REVIEW/machine/stage7_upload_manifest.json`。

## 关键决策

- canonical GitHub 目录为 `LinzeColin/CodexProject/KMFA`。
- 本地主仓库 root 为 `/Users/linzezhang/Documents/Codex/CodexProject`；普通开发优先使用项目级长期 worktree，例如 KMFA 使用 `/Users/linzezhang/Documents/Codex/main_worktree/CodexProject/kmfa`。
- 只有并行冲突开发、风险隔离、长期实验或用户明确要求时才创建临时 task worktree；新 worktree 优先 sparse checkout，只展开当前项目和必要根文件。
- 公开仓库不保存原始敏感经营数据，只保存 hash、manifest、状态、证据索引和治理记录。
- 后续所有开发工作以 `KMFA/taskpack/v1_2/` 为任务包基线。
- 涉及 UI、报告、前端或验收的 Stage 必须读取 `KMFA/taskpack/v1_2/20_HTML_UIUX_报告预览/`。
- 每次 run work 最多解决一个 Phase；中间 Phase 不上传 GitHub。
- Stage 完成后先整体复审，修复复审问题后再整体上传 GitHub。
- 当前 canonical checkout 仍有非 KMFA 脏改风险；Stage 2 继续使用隔离 worktree，最终上传必须 clean-worktree 验证。
- S03-P1 新增的文件登记工具不得保存原始文件 bytes 或明文原始文件名到公开仓库；zip 只能安全解包到私有目录。
- S03-P2 新增的状态事件只能写 metadata，`raw_layer_write_allowed=false`。
- S03-P3 新增的跨源差异队列必须 `auto_selection_allowed=false`，同源不一致只能追加 metadata event。
- S04-P1 金额标准化必须输出整数分；业务金额不得使用 float；空白、横杠、井号、异常文本不得静默转 0。
- S04-P2 字段缺失或异常不得静默跳过；只能进入 metadata 质量状态，且不得写 raw 层或提交真实业务字段值。
- S04-P3 工具测试报告只能使用合成边界值，不得引入真实业务源数据。
- S05-P1 只能登记公开安全 metadata；成员 SHA256 未能从私有 zip 复算时必须显式 pending，不能用 legacy CRC/指纹替代 SHA256。
- S05-P2 公开仓库只能保存字段合同、hash/ref/status 和 private refs；不得保存真实 `raw_value`、`normalized_value`、PDF/Excel/zip、私有 CSV 或业务明文。
- S05-P2 Excel 候选只能通过 owner 或授权私有映射明确角色；机器复核记录不能替代 Q4 人工确认，也不能解除 5 条字段 pending。
- S05-P2 owner decision intake validator 只验证未来决策记录的公开安全边界；它不代表 owner 已作出决策，也不允许进入 Q4/Q5。
- S05-P2 owner decision templates 只帮助生成未来决策记录；模板本身不代表 owner 已决策。
- S05-P2 owner decision application preview 只预演决策的 public-safe 应用路径；active downgrade decision 不代表 Q4/Q5 完成。
- S05-P2 completion gate 的 active downgrade ready 结果只代表 S05-P2 可本地关闭，不代表 Stage 5 完成。
- S05-P3 权威基准锁定只允许 hash/source-anchor 完整且 public-safe 的 40 条 PDF 字段进入 Q5 calculation baseline；Excel candidate 依据 active owner/授权降级决策排除，不得用于正式报告。
- S05-P3 lock、Stage 5 review 和 Stage 5 upload 均已完成；仍不代表 zero-delta、lineage、事实层或报告发布完成。
- S06-P1 zero-delta validator、S06-P2 cross-source difference queue、S06-P3 validation evidence output、Stage 6 review/upload、S07-P1 finance adapter、S07-P2 WPS adapter、S07-P3 redcircle postponement policy 和 Stage 7 review/upload 已完成；S08-P1、lineage 和报告发布门禁仍未完成。

## 已改/需看文件

- `KMFA/README.md`
- `KMFA/功能清单.md`
- `KMFA/开发记录.md`
- `KMFA/模型参数文件.md`
- `KMFA/docs/governance/*`
- `KMFA/metadata/*`
- `KMFA/stage_artifacts/S01_P1_read_only_plan/*`
- `KMFA/stage_artifacts/S01_STAGE_REVIEW/*`
- `KMFA/stage_artifacts/S02_P1_metadata_protocol/*`
- `KMFA/stage_artifacts/S02_P2_immutability_policy/*`
- `KMFA/stage_artifacts/S02_P3_quality_gate/*`
- `KMFA/stage_artifacts/S02_STAGE_REVIEW/*`
- `KMFA/stage_artifacts/S01_REBASE_V12_FULL_TASKPACK/*`
- `KMFA/stage_artifacts/S03_P1_file_import/*`
- `KMFA/stage_artifacts/S03_P2_source_check_matrix/*`
- `KMFA/stage_artifacts/S03_P3_source_priority/*`
- `KMFA/stage_artifacts/S04_P1_amount_tools/*`
- `KMFA/stage_artifacts/S04_P2_field_standardization/*`
- `KMFA/stage_artifacts/S04_P3_basic_tool_tests/*`
- `KMFA/stage_artifacts/S04_STAGE_REVIEW/*`
- `KMFA/tools/file_import_register.py`
- `KMFA/tools/source_check_matrix.py`
- `KMFA/tools/source_priority.py`
- `KMFA/tools/amount_tools.py`
- `KMFA/tools/check_no_float_money.py`
- `KMFA/tools/field_standardization.py`
- `KMFA/tools/generate_tool_test_report.py`
- `KMFA/tools/a0_file_register.py`
- `KMFA/tools/check_a0_file_registration.py`
- `KMFA/tools/a0_golden_fixture.py`
- `KMFA/tools/check_a0_golden_fixture.py`
- `KMFA/tools/check_s05_p2_excel_owner_decision.py`
- `KMFA/tools/check_s05_p2_owner_decision_intake.py`
- `KMFA/tools/check_s05_p2_owner_decision_templates.py`
- `KMFA/tools/preview_s05_p2_owner_decision_application.py`
- `KMFA/tools/check_s05_p2_completion_gate.py`
- `KMFA/tools/a0_authority_baseline_lock.py`
- `KMFA/tools/check_a0_authority_baseline_lock.py`
- `KMFA/tools/zero_delta_validator.py`
- `KMFA/tests/test_file_import_register.py`
- `KMFA/tests/test_source_check_matrix.py`
- `KMFA/tests/test_source_priority.py`
- `KMFA/tests/test_amount_tools.py`
- `KMFA/tests/test_field_standardization.py`
- `KMFA/tests/test_basic_tool_boundaries.py`
- `KMFA/tests/test_a0_file_register.py`
- `KMFA/tests/test_a0_golden_fixture.py`
- `KMFA/tests/test_s05_p2_excel_owner_decision.py`
- `KMFA/tests/test_s05_p2_owner_decision_intake.py`
- `KMFA/tests/test_s05_p2_owner_decision_templates.py`
- `KMFA/tests/test_s05_p2_owner_decision_application.py`
- `KMFA/tests/test_s05_p2_completion_gate.py`
- `KMFA/tests/test_s05_p3_authority_baseline_lock.py`
- `KMFA/tests/test_zero_delta_validator.py`
- `KMFA/tests/test_cross_source_difference_queue.py`
- `KMFA/tests/test_validation_evidence_output.py`
- `KMFA/tools/cross_source_difference_queue.py`
- `KMFA/tools/check_s06_p2_difference_queue.py`
- `KMFA/tools/validation_evidence_output.py`
- `KMFA/tools/check_s06_p3_validation_evidence.py`
- `KMFA/metadata/imports/file_import_policy.yaml`
- `KMFA/metadata/sources/source_check_matrix_schema.json`
- `KMFA/metadata/sources/source_check_matrix_policy.yaml`
- `KMFA/metadata/sources/source_check_matrix.jsonl`
- `KMFA/metadata/sources/source_status_events.jsonl`
- `KMFA/metadata/sources/source_priority_policy.yaml`
- `KMFA/metadata/sources/source_priority_events.jsonl`
- `KMFA/metadata/quality/source_difference_queue.jsonl`
- `KMFA/metadata/schema_maps/field_alias_dictionary.csv`
- `KMFA/metadata/schema_maps/field_standardization_policy.yaml`
- `KMFA/metadata/quality/field_quality_status.jsonl`
- `KMFA/metadata/baseline/a0_file_manifest.json`
- `KMFA/metadata/baseline/a0_project_candidates.jsonl`
- `KMFA/metadata/baseline/a0_golden_fixture_manifest.json`
- `KMFA/metadata/baseline/a0_golden_fixture_candidates.jsonl`
- `KMFA/metadata/baseline/a0_authority_baseline_manifest.json`
- `KMFA/metadata/baseline/a0_authority_baseline_records.jsonl`
- `KMFA/stage_artifacts/S05_P1_a0_file_registration/*`
- `KMFA/stage_artifacts/S05_P2_a0_golden_fixture/*`
- `KMFA/stage_artifacts/S05_P3_authority_baseline_lock/*`
- `KMFA/stage_artifacts/S06_P1_zero_delta_validator/*`
- `KMFA/stage_artifacts/S06_P2_cross_source_difference_queue/*`
- `KMFA/stage_artifacts/S06_P3_validation_evidence_output/*`
- `KMFA/stage_artifacts/S06_STAGE_REVIEW/*`
- `KMFA/stage_artifacts/S05_P2_a0_golden_fixture/human/excel_resolution_record.md`
- `KMFA/stage_artifacts/S05_P2_a0_golden_fixture/machine/excel_resolution_manifest.json`
- `KMFA/stage_artifacts/S05_P2_a0_golden_fixture/human/excel_owner_decision_packet.md`
- `KMFA/stage_artifacts/S05_P2_a0_golden_fixture/machine/excel_owner_decision_packet.json`
- `KMFA/stage_artifacts/S05_P2_a0_golden_fixture/machine/excel_owner_decision_intake_contract.json`
- `KMFA/stage_artifacts/S05_P2_a0_golden_fixture/machine/owner_decision_templates/*`
- `KMFA/metadata/approvals/resolution_events.jsonl`
- `KMFA/metadata/approvals/control_events.jsonl`
- `KMFA/taskpack/v1_2/*`
- `KMFA/metadata/baseline/*`
- `KMFA/metadata/protocol/*`
- `KMFA/metadata/{sources,imports,schema_maps,quality,lineage,reports,approvals}/*`
- `governance/projects.yaml`
- `README.md`

## 验证命令

```bash
python3 -m unittest KMFA.tests.test_basic_tool_boundaries -q
python3 -m unittest KMFA.tests.test_a0_file_register -q
python3 KMFA/tools/check_a0_file_registration.py
python3 -m unittest KMFA.tests.test_a0_golden_fixture -q
python3 KMFA/tools/check_a0_golden_fixture.py
python3 -m unittest KMFA.tests.test_s05_p2_excel_owner_decision -q
python3 KMFA/tools/check_s05_p2_excel_owner_decision.py
python3 -m unittest KMFA.tests.test_s05_p2_owner_decision_intake -q
python3 KMFA/tools/check_s05_p2_owner_decision_intake.py
python3 -m unittest KMFA.tests.test_s05_p2_owner_decision_templates -q
python3 KMFA/tools/check_s05_p2_owner_decision_templates.py
python3 -m unittest KMFA.tests.test_s05_p2_owner_decision_application -q
python3 -m unittest KMFA.tests.test_s05_p2_completion_gate -q
python3 KMFA/tools/check_s05_p2_completion_gate.py --expect-blocked
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest KMFA.tests.test_s05_p3_authority_baseline_lock -q
PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/a0_authority_baseline_lock.py --locked-at 2026-06-30T12:00:00+10:00 --locked-by-ref codex_delegate_s05p3_public_safe_lock_20260630 --check-only
PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/check_a0_authority_baseline_lock.py
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest KMFA.tests.test_zero_delta_validator -q
PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/zero_delta_validator.py --fixture KMFA/stage_artifacts/S06_P1_zero_delta_validator/machine/s06_p1_synthetic_mismatch_fixture.json --result-json KMFA/stage_artifacts/S06_P1_zero_delta_validator/machine/s06_p1_synthetic_zero_delta_result.json --mismatch-report KMFA/stage_artifacts/S06_P1_zero_delta_validator/machine/s06_p1_synthetic_mismatch_report.csv
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest KMFA.tests.test_cross_source_difference_queue -q
PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/cross_source_difference_queue.py --fixture KMFA/stage_artifacts/S06_P2_cross_source_difference_queue/machine/s06_p2_synthetic_pdf_excel_conflict_fixture.json --queue-jsonl KMFA/stage_artifacts/S06_P2_cross_source_difference_queue/machine/s06_p2_synthetic_difference_queue.jsonl --gate-json KMFA/stage_artifacts/S06_P2_cross_source_difference_queue/machine/s06_p2_report_grade_gate.json
PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/check_s06_p2_difference_queue.py
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest KMFA.tests.test_validation_evidence_output -q
PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/validation_evidence_output.py --zero-delta-result KMFA/stage_artifacts/S06_P1_zero_delta_validator/machine/s06_p1_synthetic_zero_delta_result.json --source-mismatch-report KMFA/stage_artifacts/S06_P1_zero_delta_validator/machine/s06_p1_synthetic_mismatch_report.csv --difference-queue KMFA/stage_artifacts/S06_P2_cross_source_difference_queue/machine/s06_p2_synthetic_difference_queue.jsonl --report-gate KMFA/stage_artifacts/S06_P2_cross_source_difference_queue/machine/s06_p2_report_grade_gate.json --output-dir KMFA/stage_artifacts/S06_P3_validation_evidence_output/machine --metadata-quality-dir KMFA/metadata/quality --evidence-time 2026-06-30T14:30:00+10:00
PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/check_s06_p3_validation_evidence.py
python3 KMFA/tools/generate_tool_test_report.py --format json
python3 KMFA/tools/generate_tool_test_report.py --format markdown
python3 -m unittest KMFA.tests.test_field_standardization -q
python3 -m unittest KMFA.tests.test_amount_tools -q
python3 KMFA/tools/check_no_float_money.py
python3 -m unittest KMFA.tests.test_source_priority -q
python3 -m unittest KMFA.tests.test_source_check_matrix -q
python3 -m unittest KMFA.tests.test_file_import_register -q
python3 KMFA/tools/check_required_html.py
python3 KMFA/tools/no_omission_check.py
python3 KMFA/tools/immutability_policy_check.py
python3 KMFA/tools/metadata_protocol_check.py
python3 scripts/lean_governance.py validate --project KMFA
python3 scripts/validate_project_governance.py --project KMFA
python3 KMFA/tools/check_report_grade_gate.py
git diff --check -- README.md governance/projects.yaml KMFA
```

## 未解决风险

- Stage 5 已完成 S05-P1、S05-P2、S05-P3、整体复审和 GitHub upload；S05-P3 已锁定 40 条 public-safe hash/source-anchor 字段并排除 5 条 Excel 字段；S06-P1、S06-P2、S06-P3、Stage 6 review 和 Stage 6 upload 已完成。
- S05-P1 成员级 SHA256 仍未补算；S05-P2 后续私有审计只确认本机 zip 的 9 个真实业务成员 hash 与 Stage2 Ring4 registry 匹配，但整包 hash/size 与登记 source package 不匹配。公开仓库不得提交 zip、PDF、Excel 或解包文件。
- S05-P3、Stage 5 review/upload、S06-P1、S06-P2、S06-P3、Stage 6 review 和 Stage 6 upload 只完成 A0 authority baseline lock、零差异校验器、跨源差异队列、校验证据输出、整体复审和上传；不能把它扩展解释为正式项目成本事实层、差异关闭或报告发布。
- S08-P1 项目组合键、lineage 完整检查和运行时报告生成尚未实现。
- S02-P3 只实现 report grade gate 协议；正式报告生成和 lineage 完整检查仍属后续 Stage。
- Stage 3 已上传 GitHub main；业务导入解析、A0、zero-delta、lineage 和报告生成仍是后续 Stage。
- v1.2 中私有源数据只能本地使用，不能提交公开 GitHub。

## 下一步

下一步若继续开发，只执行 `S08-P1｜项目组合键`：先确认 git root、branch、remote、HEAD、status；读取 v1.2 roadmap S08-P1 和 Stage 7 upload evidence；只建立 public-safe 组合键匹配 metadata、validator、tests 和证据；不得提交 raw Excel/PDF/zip/private CSV，不得扩大到 S08-P2、UI、正式报告、事实层、lineage 或自动接口。
