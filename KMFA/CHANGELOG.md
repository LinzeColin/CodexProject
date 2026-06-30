# Changelog

## 0.1.0-s07p1-finance-file-adapter - 2026-06-30

- 完成 `S07-P1｜财务文件适配` 本地验证，不上传 GitHub。
- 新增 `KMFA/tools/finance_file_adapter.py`、`KMFA/tools/check_s07_p1_finance_file_adapter.py` 和 `KMFA/tests/test_finance_file_adapter.py`。
- 生成 9 类财务支撑源登记、45 条 hash-only 字段候选和 9 条只读字段报告，覆盖经营分析、日记账、客户账龄、现金、纳税、开票、账户、贷款、研发费用。
- 新增 `KMFA/metadata/imports/finance_support_source_registry.json`、`KMFA/metadata/schema_maps/finance_file_adapter_manifest.json`、`KMFA/metadata/schema_maps/finance_field_candidates.jsonl`、`KMFA/metadata/schema_maps/finance_file_mapping_policy.yaml` 和 `KMFA/stage_artifacts/S07_P1_finance_file_adapter/`。
- 公开仓库不提交 raw Excel/PDF/zip/private CSV、字段明文、来源表头明文或真实业务值；WPS、红圈、事实层、lineage、正式报告、UI 和外部接口仍未完成。

## 0.1.0-s06-github-upload - 2026-06-30

- 完成 Stage 6 final GitHub upload gate，目标为 `LinzeColin/CodexProject main`。
- 基于最新 `origin/main` commit `fd14057e7427d7f275fdb62a33619936618d0d35` rebase 完整 Stage 6 栈，并复跑 S06-P1/P2/P3 validators、治理 validator、raw/secret scan、JSON/JSONL parse check 和 evidence consistency check。
- 修复 upload gate finding：rebase 后 Stage 6 review evidence 的 `reviewed_head` 已更新为当前 rebased S06-P3 commit `c66c8b44c17ae760a5a6da4b98ab5892d90d73d0`。
- 修复 upload gate finding：`KMFA/metadata/project/project.yaml` 中重复且过期的 Stage 6 upload policy 已归一。
- 新增 `KMFA/stage_artifacts/S06_STAGE_REVIEW/human/github_upload_record.md` 和 `KMFA/stage_artifacts/S06_STAGE_REVIEW/machine/stage6_upload_manifest.json`。
- 保持 S07 文件适配、lineage、事实层、报告、UI 和外部接口为未完成。

## 0.1.0-s06-stage-review - 2026-06-30

- 完成 Stage 6 整体复审，结果为 `PASS_UPLOAD_READY_LOCAL_ONLY`，尚未 push GitHub。
- 新增 `KMFA/stage_artifacts/S06_STAGE_REVIEW/` 复审证据包，覆盖 S06-P1/P2/P3 validators、治理 validator、raw/secret scan、JSON/JSONL parse checks 和 evidence consistency check。
- 复审确认 S06-P1 对 1 分差异保持 expected failure，S06-P2 未关闭差异继续阻断 A 级报告，S06-P3 metadata/quality 输出保持 public-safe hash/ref/status/evidence。
- 修复 Stage 6 review 证据和治理状态缺口，同步 owner-readable、stage_status、events 和 project governance。
- 保持 lineage 完整检查、事实层、正式报告、UI、外部接口和 GitHub upload 为未完成。

## 0.1.0-s06-p3-validation-evidence-output - 2026-06-30

- 完成 `S06-P3｜校验证据输出` 本地验证，不上传 GitHub。
- 新增 `KMFA/tools/validation_evidence_output.py`、`KMFA/tools/check_s06_p3_validation_evidence.py` 和 `KMFA/tests/test_validation_evidence_output.py`。
- 输出 S06-P3 `zero_delta_result.json`、sanitized `mismatch_report.csv` 和 per-project validation status JSONL。
- 将 public-safe zero-delta summary、data quality status、source difference queue status 和 mismatch index 写入 `KMFA/metadata/quality`。
- metadata/quality 只保存 hash/ref/status/evidence，不新增字段明文、权威原值、系统原值、PDF 原值或 Excel 原值。
- 保持事实层、lineage 完整检查、正式报告、UI、外部接口、Stage 6 复审和 GitHub upload 为未完成。

## 0.1.0-s06-p2-cross-source-difference-queue - 2026-06-30

- 完成 `S06-P2｜跨源差异队列` 本地验证，不上传 GitHub。
- 新增 `KMFA/tools/cross_source_difference_queue.py`、`KMFA/tools/check_s06_p2_difference_queue.py` 和 `KMFA/tests/test_cross_source_difference_queue.py`。
- PDF 与 Excel 同项目同字段金额冲突进入人工差异队列；禁止自动修正、平均、四舍五入掩盖和自动选边。
- 未关闭差异阻断 A 级报告：`report_grade_a_allowed=false`、`maximum_report_grade=B`、`hard_block_reason=unresolved_critical_difference`。
- 新增 `KMFA/stage_artifacts/S06_P2_cross_source_difference_queue/` 证据包，使用 synthetic fixture，不读取或提交真实业务文件。
- 保持 S06-P3 metadata/quality 运行时证据输出、lineage、事实层、报告、UI 和外部接口为未完成。

## 0.1.0-s06-p1-zero-delta-validator - 2026-06-30

- 完成 `S06-P1｜零差异校验器` 本地验证，不上传 GitHub。
- 新增 `KMFA/tools/zero_delta_validator.py` 和 `KMFA/tests/test_zero_delta_validator.py`，逐字段比较 public-safe 已结构化整数分。
- 任意 1 分差异返回失败，并输出包含来源、字段、权威值、系统值和差额的 mismatch report。
- 新增 `KMFA/stage_artifacts/S06_P1_zero_delta_validator/` 证据包，使用 synthetic fixture，不读取或提交真实业务文件。
- 保持 S06-P2 差异队列、S06-P3 metadata/quality 运行时证据输出、lineage、事实层、报告、UI 和外部接口为未完成。

## 0.1.0-s05-github-upload - 2026-06-30

- 完成 Stage 5 final GitHub upload gate，目标为 `LinzeColin/CodexProject main`。
- 基于最新 `origin/main` commit `495bcd977a587b7fd8b1923bfd74f5138f12263e` rebase 完整 Stage 5 栈，并复跑 S05-P1/P2/P3 validators、治理 validator、raw/secret scan 和 JSONL parse check。
- 修复 upload gate finding：rebase 后 Stage 5 review evidence 的 `reviewed_head` 已更新为当前 rebased S05-P3 commit `c3314e47ce11cfb8bf56e44d4a38a77904584495`。
- 新增 `KMFA/stage_artifacts/S05_STAGE_REVIEW/human/github_upload_record.md` 和 `KMFA/stage_artifacts/S05_STAGE_REVIEW/machine/stage5_upload_manifest.json`。
- 保持 S06 zero-delta、lineage、事实层、报告、UI 和外部接口为未完成。

## 0.1.0-s05-stage-review - 2026-06-30

- 完成 Stage 5 整体复审，结果为 `PASS_UPLOAD_READY_LOCAL_ONLY`，尚未 push GitHub。
- 新增 `KMFA/stage_artifacts/S05_STAGE_REVIEW/` 复审证据包，覆盖 S05-P1/P2/P3 validators、治理 validator、raw/secret scan 和 JSON/JSONL parse checks。
- 复审确认 40 条 PDF 字段保持 public-safe Q5 calculation baseline，5 条 Excel 字段保持 cross-source support only，不进入正式报告。
- 修复 Stage 5 review 证据和治理状态缺口，同步 owner-readable、stage_status、events 和 project governance。
- 保持 zero-delta、lineage、事实层、报告、UI、外部接口和 GitHub upload 为未完成。

## 0.1.0-s05p3-authority-baseline-lock - 2026-06-30

- 完成 `S05-P3｜权威基准锁定` 本地验证，不上传 GitHub。
- 新增 `KMFA/tools/a0_authority_baseline_lock.py` 和 `KMFA/tools/check_a0_authority_baseline_lock.py`，生成并验证 public-safe A0 authority baseline manifest/records。
- 新增 `KMFA/tests/test_s05_p3_authority_baseline_lock.py`，覆盖 40 条 Q5 hash/source-anchor lock、5 条 Excel exclusion、禁止明文字段键和文件输出。
- 新增 `KMFA/metadata/baseline/a0_authority_baseline_manifest.json`、`KMFA/metadata/baseline/a0_authority_baseline_records.jsonl` 和 `KMFA/stage_artifacts/S05_P3_authority_baseline_lock/` 证据。
- 保持 Stage 5 整体复审、zero-delta、lineage、事实层、报告、UI 和 GitHub upload 为未完成。

## 0.1.0-s05p2-private-backfill-partial - 2026-06-30

- 对 `S05-P2｜字段级黄金基准` 执行本地私有 hash-only 部分回填，不上传 GitHub。
- 使用仓库外私有 CSV 回填 8 个 PDF A0 候选的 40 条字段候选 hash/source anchor；1 个 Excel 候选的 5 条字段候选继续 pending。
- 记录审计结论：本机提供的 `销售绩效考核.zip` 整包 hash/size 与登记 source package 不匹配，但 9 个真实业务成员 hash 与 Stage2 Ring4 registry 匹配；Ring4 前序包 hash 匹配登记值。
- 新增 S05-P2 private backfill public-safe 证据；公开仓库仍不提交 raw PDF/Excel/zip、私有 CSV、真实字段 raw value 或 normalized value。
- 保持 S05-P2 未完成、S05-P3 权威锁定未开始、Stage 5 复审和 GitHub upload 不允许。

## 0.1.0-s05p2-contract - 2026-06-30

- 生成 `S05-P2｜字段级黄金基准` 的 public-safe 字段合同和 A0 golden fixture 候选结构，保持本阶段本地验证，不上传 GitHub。
- 新增 `KMFA/tools/a0_golden_fixture.py` 和 `KMFA/tools/check_a0_golden_fixture.py`，为合同额、支出合计、毛利、毛利率、成本分类生成 private refs、source anchor 状态和 hash-only 输出能力。
- 新增 `KMFA/tests/test_a0_golden_fixture.py`，覆盖无私有源 pending 输出、合成私有 CSV hash-only 输出、公开 metadata 禁止 raw/normalized 明文键。
- 新增 `KMFA/metadata/baseline/a0_golden_fixture_manifest.json` 和 `KMFA/metadata/baseline/a0_golden_fixture_candidates.jsonl`，当前 45 条字段候选均为 private values pending。
- 保持 S05-P2 真实字段值、S05-P3 权威锁定、zero-delta、事实层、报告、UI 和 GitHub upload 为未完成。

## 0.1.0-s05p1 - 2026-06-30

- 完成 `S05-P1｜A0 文件登记` 的 public-safe 登记和本地验证，不上传 GitHub。
- 新增 `KMFA/tools/a0_file_register.py` 和 `KMFA/tools/check_a0_file_registration.py`，登记 `销售绩效考核.zip` source package SHA256、8 个 PDF、1 个 Excel、legacy inventory 指纹和 Q3/Q4 状态。
- 新增 `KMFA/tests/test_a0_file_register.py`、`KMFA/metadata/baseline/a0_file_manifest.json`、`KMFA/metadata/baseline/a0_project_candidates.jsonl` 和 S05-P1 证据包。
- 私有 `销售绩效考核.zip` 未找到，成员级 SHA256 显式记录为 pending，不用 legacy CRC/指纹冒充 SHA256。
- 保持字段级黄金基准、S05-P3 权威锁定、zero-delta、事实层、报告、UI 和 GitHub upload 为未完成。

## Stage 4 Review - 2026-06-29

- 完成 Stage 4 整体复审，结果为 `PASS_UPLOAD_READY_LOCAL_ONLY`，尚未 push GitHub。
- 新增 `KMFA/stage_artifacts/S04_STAGE_REVIEW/` 复审证据包。
- 修复 `功能清单.md` 中 `FEAT-KMFA-016` 金额标准化与 no-float 检查详情缺口。
- 复跑 S04-P1/S04-P2/S04-P3 工具测试、治理 validator、no-float 检查和敏感文件扫描。
- 保持 A0 基准、zero-delta、事实层、报告、UI 和外部接口为未完成。

## Stage 4 GitHub Upload - 2026-06-29

- 完成 Stage 4 final GitHub upload 证据记录，目标为 `LinzeColin/CodexProject main`。
- 基于 `origin/main` commit `e6e69d387fc842102931090ffbffe18e54b63c0c` 纳入完整 Stage 4 提交栈。
- reviewed content commit 为 `25c85dcee55679d0789f8462a7c7875188d0aa9f`。
- 新增 `KMFA/stage_artifacts/S04_STAGE_REVIEW/human/github_upload_record.md` 和 `KMFA/stage_artifacts/S04_STAGE_REVIEW/machine/stage4_upload_manifest.json`。

## 0.1.0-s04p3 - 2026-06-29

- 完成 `S04-P3｜基础工具测试`，保持本 Phase 本地验证，不上传 GitHub。
- 新增 `KMFA/tests/test_basic_tool_boundaries.py`，覆盖金额小数、负数、万元、异常字符，以及日期/期间中文日期、年月、空值边界。
- 新增 `KMFA/tools/generate_tool_test_report.py`，生成 S04-P3 工具函数测试报告，支持 JSON 和 Markdown 输出。
- 修复 `KMFA/tools/field_standardization.py` 的中文完整日期转期间边界。
- 新增 `KMFA/stage_artifacts/S04_P3_basic_tool_tests/` 证据包。
- Stage 4 三个 Phase 已全部本地验证；Stage 4 整体复审、复审问题修复和 GitHub 上传尚未完成。

## 0.1.0-s04p2 - 2026-06-29

- 完成 `S04-P2｜字段标准化`，保持本 Phase 本地验证，不上传 GitHub。
- 新增 `KMFA/tools/field_standardization.py`，支持日期、期间、公司主体、项目名称、客户/对手方、合同编号标准化。
- 新增 `KMFA/tests/test_field_standardization.py`，覆盖中文字段映射、缺字段质量状态、异常字段质量状态和 CLI。
- 新增 `KMFA/metadata/schema_maps/field_alias_dictionary.csv`、`field_standardization_policy.yaml` 和 `KMFA/metadata/quality/field_quality_status.jsonl`。
- 更新 mapping version 登记、字段字典、目录 manifest 和 S04-P2 证据包。
- 保持 S04-P3 基础工具测试报告、A0 基准、zero-delta、事实层、报告、UI 和外部接口为未完成。

## 0.1.0-s04p1 - 2026-06-29

- 完成 `S04-P1｜金额工具`，保持本 Phase 本地验证，不上传 GitHub。
- 新增 `KMFA/tools/amount_tools.py`，提供 `normalize_amount_to_cents`，支持元、万元、千元、千分位、负数和括号负数，输出整数分。
- 新增 `KMFA/tools/check_no_float_money.py`，检查 KMFA Python 文件中的 float literal、`float()` 调用和 float 标注。
- 新增 `KMFA/tests/test_amount_tools.py`，覆盖金额标准化、float 禁止、异常输入不默认为 0、CLI 和 no-float 检查。
- 新增 `KMFA/stage_artifacts/S04_P1_amount_tools/` 证据包。
- 保持 S04-P2 字段标准化、S04-P3 工具测试报告、A0 基准、zero-delta、事实层、报告、UI 和外部接口为未完成。

## 0.1.0-s03p3 - 2026-06-29

- 完成 `S03-P3｜源优先级`。
- 新增 `KMFA/tools/source_priority.py`，支持源类别优先级排序、同源不一致失效重跑事件和跨源差异队列 metadata。
- 新增 `KMFA/tests/test_source_priority.py`，覆盖原始上传/授权导出优先于处理后数据、同源失效重跑、跨源冲突不自动选边和 direct CLI。
- 新增 `KMFA/metadata/sources/source_priority_policy.yaml`、`source_priority_events.jsonl` 和 `KMFA/metadata/quality/source_difference_queue.jsonl`。
- Stage 3 三个 Phase 已本地完成；Stage 3 复审已通过，并已整体上传 GitHub main。
- 保持业务字段解析、金额、事实层、报告和外部接口为未完成；中间 Phase 不上传 GitHub。

## 0.1.0-s03p2 - 2026-06-29

- 完成 `S03-P2｜数据源检查矩阵`。
- 新增 `KMFA/tools/source_check_matrix.py`，支持来源系统、业务板块、文件包、主体、账户、频率矩阵行生成。
- 新增 `KMFA/tests/test_source_check_matrix.py`，覆盖矩阵维度、五个中文状态枚举和 metadata-only 状态事件。
- 新增 `KMFA/metadata/sources/source_check_matrix_schema.json`、`source_check_matrix_policy.yaml`、`source_check_matrix.jsonl`、`source_status_events.jsonl`。
- 保持 S03-P3 源优先级、业务字段解析、金额、事实层、报告和外部接口为未完成；中间 Phase 不上传 GitHub。

## 0.1.0-s03p1 - 2026-06-29

- 完成 `S03-P1｜文件型导入`。
- 新增 `KMFA/tools/file_import_register.py`，支持 `zip/xlsx/xls/csv/pdf` 文件登记、hash/size/import_run/source package metadata、私有 storage ref 和 zip 安全解包。
- 新增 `KMFA/tests/test_file_import_register.py`，覆盖登记隐私边界、WPS/OLE 操作提示和 zip traversal 防护。
- 新增 `KMFA/metadata/imports/file_import_policy.yaml`，扩展 raw manifest schema/policy、import runs、raw file manifest 和 source registry 的 S03-P1 能力记录。
- 新增 `KMFA/stage_artifacts/S03_P1_file_import/` 证据包。
- 保持 S03-P2 数据源检查矩阵、S03-P3 源优先级、业务字段解析、金额、事实层、报告和外部接口为未完成；中间 Phase 不上传 GitHub。

## 0.1.0-s02p3-v12baseline - 2026-06-29

- 承接 `KMFA_ChatGPT_Stage3_Codex_Delivery_Pack_v1_2_FULL_HTML_NO_OMISSION.zip` 为后续正式开发基线。
- 新增 `KMFA/taskpack/v1_2/`，保存可提交的 v1.2 TaskPack、Roadmap、HTML/UIUX/报告样板、前序散件、工具和机器清单。
- 完整纳入 HTML 验收面：45 个 HTML 文件，7 个核心 HTML 验收样板。
- 新增 `KMFA/tools/check_required_html.py`，并强化 `KMFA/tools/no_omission_check.py` 检查 v1.2 基线与私有源数据禁提交边界。
- 只保存 `90_用户原始上传数据` 的 SHA256 登记和禁止提交规则，未提交原始 zip、mov、Excel、PDF 或数据库类文件。
- 按 v1.2 重新走完 Stage 1，新增证据目录 `KMFA/stage_artifacts/S01_REBASE_V12_FULL_TASKPACK/`。

## 0.1.0-s02p3 - 2026-06-29

- 完成 `S02-P3｜数据质量等级`。
- 新增 `Q0-Q5` 数据质量等级协议，定义预览、内部复核和正式内部报告的质量边界。
- 新增 `A/B/C/D` 报告可信等级协议，要求 A 级报告必须满足 `Q5`、zero-delta、关键差异关闭和人工确认。
- 新增报告发布门禁，缺少门禁证据时默认阻断发布或降级。
- 新增 `KMFA/tools/check_report_grade_gate.py`，验证质量等级、报告等级和发布权限映射。
- S02 三个 Phase 已完成；Stage 2 整体复审已通过，并已上传 GitHub main。

## 0.1.0-s02p2 - 2026-06-29

- 完成 `S02-P2｜不可污染原则`。
- 新增 raw manifest append-only schema 和 policy，禁止修改原始文件、原始抽取值和不可变 manifest 字段。
- 新增派生数据版本协议，支持失效、重跑、对比，禁止覆盖旧版本。
- 新增前端/人工控制事件写入边界，禁止直接写 raw 层。
- 新增 `KMFA/tools/immutability_policy_check.py`，验证不可污染原则。
- 保持中间 Phase 不上传 GitHub；S02-P3 与 Stage 2 复审尚未完成。

## 0.1.0-s02p1 - 2026-06-29

- 完成 `S02-P1｜metadata目录协议`。
- 创建 metadata 七类目录：sources、imports、schema_maps、quality、lineage、reports、approvals。
- 定义 `import_run_id`、`source_id`、`file_hash`、`formula_version`、`mapping_version` 标识符协议。
- 新增 `KMFA/tools/metadata_protocol_check.py`，验证目录、协议文件、标识符和公开仓库隐私边界。
- 保持中间 Phase 不上传 GitHub；S02-P2/S02-P3 与 Stage 2 复审尚未完成。

## 0.1.0-s01p3 - 2026-06-29

- 完成 `S01-P3｜防遗漏基线`。
- 导入完整需求追溯矩阵：20 条需求，P0=9，P1=8。
- 新增正式 `KMFA/tools/no_omission_check.py`，可本地/CI 运行。
- 建立完整 Stage/Phase/Task 状态登记：18 Stage、54 Phase、162 Task、234 JSONL 记录。
- 同步 `docs/governance/TRACEABILITY_MATRIX.csv` 到 20 条治理追溯记录。
- Stage 1 整体复审通过；上传限定为基于 `origin/main` 的隔离 worktree，避免混入非 KMFA 变更。

## 0.1.0-s01p2 - 2026-06-29

- 创建 KMFA 项目骨架与中文入口。
- 建立人类可读面: `README.md`, `功能清单.md`, `开发记录.md`, `模型参数文件.md`, `HANDOFF.md`。
- 建立机器可读面: `docs/governance/*`, `metadata/*`, `stage_artifacts/S01_P1_read_only_plan`。
- 注册 root `governance/projects.yaml` 与 root `README.md` 项目表。
- 明确 Stage 完成复审修复后再上传 GitHub，中间 Phase 不上传。
- 明确时间只是参考，质量门禁通过可提前交付，未通过不得交付。
- 未实现业务导入、金额工具、zero-delta 正式脚本、UI、报告或外部接口。
