# Changelog

## 0.1.0-s03p3 - 2026-06-29

- 完成 `S03-P3｜源优先级`。
- 新增 `KMFA/tools/source_priority.py`，支持源类别优先级排序、同源不一致失效重跑事件和跨源差异队列 metadata。
- 新增 `KMFA/tests/test_source_priority.py`，覆盖原始上传/授权导出优先于处理后数据、同源失效重跑、跨源冲突不自动选边和 direct CLI。
- 新增 `KMFA/metadata/sources/source_priority_policy.yaml`、`source_priority_events.jsonl` 和 `KMFA/metadata/quality/source_difference_queue.jsonl`。
- Stage 3 三个 Phase 已本地完成；Stage 3 复审已通过，GitHub 上传尚未执行。
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
