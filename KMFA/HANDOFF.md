# KMFA Handoff

更新时间: 2026-06-30

## 当前目标

v1.2 FULL_HTML_NO_OMISSION 完整任务包已成为 KMFA 后续开发基线，并已按 v1.2 重新走完 Stage 1。Stage 2、Stage 3 和 Stage 4 均已完成本地实现、验证、整体复审和 GitHub main 上传。当前 Stage 5 已完成 `S05-P1｜A0 文件登记` 的本地实现与验证；`S05-P2｜字段级黄金基准` 已生成 public-safe 字段合同和 A0 golden fixture 候选结构，但真实字段值、source anchor 和 private value hash 仍因私有源不可用而 pending。Stage 5 尚未整体复审，也未上传 GitHub；下一轮仍需继续 S05-P2 私有字段回填/验证，不能直接进入 S05-P3 锁定。

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
- 本机未找到私有 `销售绩效考核.zip`，所以成员级 `member_sha256` 仍为 `pending_private_zip_unavailable`；当前实现没有把 legacy CRC/指纹伪装成 SHA256。
- `S05-P2` 已生成 public-safe 字段合同和候选结构：新增 `KMFA/tools/a0_golden_fixture.py`、`KMFA/tools/check_a0_golden_fixture.py`、`KMFA/tests/test_a0_golden_fixture.py`、`KMFA/metadata/baseline/a0_golden_fixture_manifest.json`、`KMFA/metadata/baseline/a0_golden_fixture_candidates.jsonl` 和 `KMFA/stage_artifacts/S05_P2_a0_golden_fixture/`。
- S05-P2 当前只生成 5 个字段合同和 45 条字段候选：合同额、支出合计、毛利、毛利率、成本分类；每条候选都有 private raw/normalized value ref、source anchor 状态和 Q3/Q4/Q5 门禁。
- 本机仍未找到私有 `销售绩效考核.zip` 或授权字段抽取 CSV，所以 45 条字段候选的真实字段值 hash 和 source anchor 均为 `pending_private_source_unavailable`；未提交 raw/normalized 字段值。

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
- S05-P2 公开仓库只能保存字段合同、hash/ref/status 和 private refs；不得保存真实 `raw_value`、`normalized_value`、PDF/Excel/zip 或业务明文。

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
- `KMFA/tests/test_file_import_register.py`
- `KMFA/tests/test_source_check_matrix.py`
- `KMFA/tests/test_source_priority.py`
- `KMFA/tests/test_amount_tools.py`
- `KMFA/tests/test_field_standardization.py`
- `KMFA/tests/test_basic_tool_boundaries.py`
- `KMFA/tests/test_a0_file_register.py`
- `KMFA/tests/test_a0_golden_fixture.py`
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
- `KMFA/stage_artifacts/S05_P1_a0_file_registration/*`
- `KMFA/stage_artifacts/S05_P2_a0_golden_fixture/*`
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

- Stage 5 已完成 S05-P1，并生成 S05-P2 public-safe 字段合同/候选结构；S05-P2 真实字段值回填仍 pending，本轮不得上传 GitHub。
- 私有 `销售绩效考核.zip` 当前未在本机找到，9 个成员文件的真实 SHA256 待本地私有 zip 提供后补算；公开仓库不得提交 zip、PDF、Excel 或解包文件。
- S05-P2 真实字段值抽取仍 pending；必须提供本地私有源或授权字段抽取 CSV 后，才能将 45 条字段候选升级为 hash-recorded private fixture 候选。
- zero-delta、lineage 完整检查和运行时报告生成尚未实现。
- S02-P3 只实现 report grade gate 协议；正式报告生成、zero-delta 和 lineage 完整检查仍属后续 Stage。
- Stage 3 已上传 GitHub main；业务导入解析、A0、zero-delta、lineage 和报告生成仍是后续 Stage。
- v1.2 中私有源数据只能本地使用，不能提交公开 GitHub。

## 下一步

下一步若继续开发，仍只执行 `S05-P2｜字段级黄金基准` 的私有字段回填/验证；不扩大到 S05-P3、Stage 5 复审、UI、报告、事实层、zero-delta 或自动接口，且不得提交真实原始业务文件。
