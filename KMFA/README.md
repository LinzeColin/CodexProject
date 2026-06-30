# KMFA｜经营分析系统

KMFA 是面向 C-level management / board 的经营分析系统。当前优先级是文件型项目成本分析 MVP：先建立项目治理、数据治理、金额精度、零差异、差异队列、人工处理事件、重跑链路和可追溯经营报告基础。

## 当前状态

| 项目 | 内容 |
|---|---|
| project_id | `KMFA` |
| 当前版本 | `0.1.0-s05-github-upload` |
| 当前 Stage | `S06｜零差异校验与差异处理队列` |
| 当前 Phase | `S06-P1｜零差异校验器待开始` |
| 当前 Task | `S6PAT01-S6PAT03` |
| 风险等级 | `T3`，涉及经营数据、金额、税务、隐私和公开仓库边界 |
| GitHub 目录 | `LinzeColin/CodexProject/KMFA` |
| 当前基线 | `KMFA/taskpack/v1_2`，源包 SHA256 `3bb2ebf16fb4ad8b9d198484e9d80ea2aed3c19c54c483efebe023b772ad0e66` |
| Stage 上传规则 | 中间 Phase 不上传 GitHub；Stage 5 已完成三个 Phase、整体复审和 GitHub upload，S06 尚未开始 |

## 双平面结构

### 人类可读面

| 文件 | 用途 |
|---|---|
| `README.md` | 项目入口、范围、状态、运行边界 |
| `功能清单.md` | 面向 owner 的功能、限制、证据和下一任务 |
| `开发记录.md` | Stage -> Phase -> Task 开发记录、验收、风险、回滚 |
| `模型参数文件.md` | 模型、公式、参数、质量门禁和验证状态 |
| `HANDOFF.md` | 跨线程交接摘要 |

### 机器可读面

| 文件/目录 | 用途 |
|---|---|
| `docs/governance/project.yaml` | Lean v2 项目事实 |
| `docs/governance/roadmap.yaml` | Lean v2 Roadmap 事实 |
| `docs/governance/events.jsonl` | Lean v2 事件 |
| `docs/governance/*` | v1 兼容治理文件 |
| `metadata/project/project.yaml` | KMFA 内部项目配置草案 |
| `metadata/stage_status.jsonl` | Stage/Phase/Task 状态登记草案 |
| `metadata/model_registry.yaml` | KMFA 内部模型参数机器镜像草案 |
| `metadata/imports/file_import_policy.yaml` | S03-P1 文件型导入登记、安全解包、WPS/OLE 提示和公开仓库禁止项 |
| `metadata/sources/source_check_matrix_policy.yaml` | S03-P2 数据源检查矩阵维度、状态枚举和 metadata-only 状态事件策略 |
| `metadata/sources/source_priority_policy.yaml` | S03-P3 原始/授权/处理后数据优先级、同源失效重跑和跨源差异队列策略 |
| `metadata/schema_maps/field_standardization_policy.yaml` | S04-P2 字段标准化、缺字段质量状态和 no-raw-write 策略 |
| `metadata/schema_maps/field_alias_dictionary.csv` | S04-P2 通用字段别名字典和中文字段映射 |
| `metadata/quality/field_quality_status.jsonl` | S04-P2 缺字段/无效字段质量状态协议 |
| `metadata/baseline/source_package_v1_2.json` | v1.2 完整任务包机器清单、源包 hash、复制/排除策略 |
| `metadata/baseline/html_acceptance_samples_v1_2.json` | 45 个 HTML 样板与 7 个核心样板的机器清单 |
| `metadata/baseline/a0_authority_baseline_manifest.json` | S05-P3 A0 权威基准锁定 manifest，记录版本、hash、锁定角色、锁定时间和报告/upload gate |
| `metadata/baseline/a0_authority_baseline_records.jsonl` | S05-P3 public-safe field lock/exclusion 记录，不保存字段明文 |
| `metadata/traceability/requirements.csv` | 完整需求追溯矩阵，P0/P1 绑定任务、验收、测试、证据 |
| `tools/no_omission_check.py` | 正式防遗漏检查脚本，可在 CI/本地运行 |
| `tools/check_required_html.py` | v1.2 HTML/UIUX/报告样板强制门禁 |
| `tools/file_import_register.py` | S03-P1 文件登记、hash/manifest、私有 storage ref 和 zip 安全解包工具 |
| `tools/source_check_matrix.py` | S03-P2 数据源检查矩阵 row 和状态事件生成工具 |
| `tools/source_priority.py` | S03-P3 源优先级、同源不一致事件和跨源差异队列 metadata 工具 |
| `tools/amount_tools.py` | S04-P1 金额标准化到整数分工具 |
| `tools/check_no_float_money.py` | S04-P1 业务金额 no-float 检查器 |
| `tools/field_standardization.py` | S04-P2 字段别名、日期、期间、主体、项目、客户/对手方和合同编号标准化工具 |
| `tools/generate_tool_test_report.py` | S04-P3 基础工具边界测试报告生成器 |
| `tools/a0_authority_baseline_lock.py` | S05-P3 A0 权威基准锁定生成器 |
| `tools/check_a0_authority_baseline_lock.py` | S05-P3 A0 权威基准锁定 validator |
| `taskpack/v1_2/` | v1.2 FULL_HTML_NO_OMISSION 可提交基线 |
| `stage_artifacts/` | Stage/Phase 证据包 |

## P0 MVP 边界

P0 是文件型项目成本分析 MVP，目标链路如下：

```text
上传/登记权威项目成本资料
-> 原始文件hash与manifest
-> 字段映射
-> A0黄金基准
-> 金额整数分标准化
-> 零差异校验
-> 差异队列
-> 人工处理事件
-> 重跑派生链路
-> 项目成本报告
-> 经营总览摘要
```

当前 `S04-P1` 已建立金额工具：`normalize_amount_to_cents` 使用 `Decimal` 和整数分输出，支持元、万元、千元、千分位、负数和括号负数；`check_no_float_money.py` 阻断 KMFA Python 代码中的 float literal、`float()` 调用和 float 标注。当前 `S04-P2` 已建立字段标准化工具：日期标准化为 `YYYY-MM-DD`，期间标准化为 `YYYY-MM`，公司主体、项目名称、客户/对手方、合同编号进入 canonical field，缺字段进入 `field_quality_status` metadata 且 `field_skipped_silently=false`。当前 `S04-P3` 已完成基础工具边界测试和工具函数测试报告，覆盖金额小数、负数、万元、异常字符、中文日期、年月和空值。Stage 4 整体复审已通过并修复 owner-readable 金额工具详情缺口，final GitHub upload 证据已生成。

当前 Stage 5 的 S05-P1、S05-P2、S05-P3、整体复审和 GitHub upload 已完成：S05-P1 登记 8 个 PDF + 1 个 Excel 的 public-safe A0 文件清单；S05-P2 生成字段合同和 45 条候选，并通过 active owner/授权降级决策将 Excel candidate 排除为 cross-source support only；S05-P3 将 40 条 PDF 字段 hash/source-anchor 记录锁定为 public-safe Q5 calculation baseline，5 条 Excel 字段不进入正式报告；Stage 5 复审和上传证据位于 `KMFA/stage_artifacts/S05_STAGE_REVIEW/`。仍不实现 zero-delta、事实层、lineage 完整检查、报告或 UI。

## 禁止事项

- 不提交原始敏感数据到公开 GitHub。
- 不自动付款、报税、开票、发工资或发奖金。
- 不对外发送完整经营报告。
- 不在金额计算中使用 float。
- 不把缺数据报告伪装成完整报告。
- 不自动选择 PDF 或 Excel 冲突的一边。
- 不用工具化、营销化、非真实软件感的前端或报告文案。

## 验证命令

当前 Stage 5 upload gate / S06 entry 验证:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest KMFA.tests.test_s05_p3_authority_baseline_lock -q
PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/a0_authority_baseline_lock.py --locked-at 2026-06-30T12:00:00+10:00 --locked-by-ref codex_delegate_s05p3_public_safe_lock_20260630 --check-only
PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/check_a0_authority_baseline_lock.py
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest KMFA.tests.test_a0_file_register KMFA.tests.test_a0_golden_fixture KMFA.tests.test_s05_p2_excel_owner_decision KMFA.tests.test_s05_p2_owner_decision_intake KMFA.tests.test_s05_p2_owner_decision_templates KMFA.tests.test_s05_p2_owner_decision_application KMFA.tests.test_s05_p2_completion_gate KMFA.tests.test_s05_p3_authority_baseline_lock -q
python3 -m unittest KMFA.tests.test_basic_tool_boundaries -q
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
python3 KMFA/tools/check_report_grade_gate.py
python3 KMFA/tools/immutability_policy_check.py
python3 KMFA/tools/metadata_protocol_check.py
python3 scripts/lean_governance.py validate --project KMFA
python3 scripts/validate_project_governance.py --project KMFA
git diff --check -- KMFA
```
