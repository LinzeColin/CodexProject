# KMFA HANDOFF

## 当前状态

- phase: V014_S15_P1_POST_REMEDIATION_PERFORMANCE_FACT_FIELDS
- roadmap gate: S15-P1｜绩效事实字段
- task: KMFA-V014-S15-P1-POST-REMEDIATION-PERFORMANCE-FACT-FIELDS-20260711
- acceptance: ACC-V014-S15-P1-POST-REMEDIATION-PERFORMANCE-FACT-FIELDS
- status: completed_validated_local_only_s15_p1_all_fields_manual_review_no_go_upload_deferred
- version: 0.1.4-s15-p1-post-remediation-performance-fact-fields
- decision: NO_GO
- data quality / report grade: Q4 / D
- pursuing_goal_status: active
- S15-P1 / S15-P2 / S15-P3 / Stage 15 review: performed / not performed / not performed / not performed
- GitHub upload / app reinstall: not performed / not performed
- 下一步只能执行 S15-P2
- 不得执行 S15-P3
- 不得执行 GitHub upload

## S15-P1 结果

- 六字段：开票金额、毛利率、结算速度、回款速度、审计偏差、客情费率 6/6 已定义。
- 结构引用：项目成本/回款 6/6 / 6/6 已连接；只证明 public-safe 结构关联。
- 私有探针：5 个 raw、48 个 XLSX 容器、25 可解析、23 不可解析、4,198 个可解析工作表。
- 候选覆盖：六字段候选=9/1/2/4/2/2；唯一候选=13、跨字段=3、覆盖字段=6。
- 交叉验证：每个可解析容器执行两次只读探针，候选指纹不一致=0。
- 绑定状态：权威行/值绑定=0/0；已物化绩效事实、公开业务值=0/0。
- 人工复核：6/6 字段保持 pending，不自动填值，不形成绩效、工资或奖金结论。
- 历史隔离：旧 S15-P1 的两个非人工复核字段只作结构夹具，不是当前动态事实。
- 浏览器：baseline/current=54/54 / 14/14 PASS；viewports/fields/HTTP/navigation=2/12/4/4，console/overflow=0/0。
- raw：5 个文件在 phase 前后、跨 Stage 14 review 和当前快照一致。
- quality: Q4 / D / NO_GO / 3-9-2-1。

## 关键边界

1. 候选结构不证明同一项目、人员、期间、单位、口径、分母或数值。
2. 项目成本与回款结构引用已连接，不等于权威行或权威值绑定。
3. 六字段均不得自动填值、计算绩效、工资、奖金或作为业务决策依据。
4. 不推断、不平均、不补零，不忽略 0.01 元，不关闭尚未由权威证据解释的差异。
5. 原始目录只读；不得修改、删除、移动、重命名、覆盖或写入任何原始文件。
6. raw 文件名、成员、工作表、字段、表头、金额、明细、截图与诊断只存在于 ignored private runtime。
7. Stage 18 完成并通过最终整体复审、修复 findings 前，不得执行 GitHub upload 或 app reinstall。

## 证据

- manifest: KMFA/stage_artifacts/V014_S15_P1_POST_REMEDIATION_PERFORMANCE_FACT_FIELDS/machine/performance_fact_fields_manifest.json
- summary: KMFA/stage_artifacts/V014_S15_P1_POST_REMEDIATION_PERFORMANCE_FACT_FIELDS/machine/performance_fact_fields_summary.json
- definitions: KMFA/stage_artifacts/V014_S15_P1_POST_REMEDIATION_PERFORMANCE_FACT_FIELDS/machine/performance_fact_field_definitions_public_safe.json
- bindings: KMFA/stage_artifacts/V014_S15_P1_POST_REMEDIATION_PERFORMANCE_FACT_FIELDS/machine/performance_fact_field_binding_status_public_safe.json
- manual review: KMFA/stage_artifacts/V014_S15_P1_POST_REMEDIATION_PERFORMANCE_FACT_FIELDS/machine/performance_fact_manual_review_requirements_public_safe.json
- workbench: KMFA/stage_artifacts/V014_S15_P1_POST_REMEDIATION_PERFORMANCE_FACT_FIELDS/exports/html/performance_fact_fields_workbench.html
- validator: KMFA/tools/check_v014_s15_p1_post_remediation_performance_fact_fields.py
- focused test: KMFA/tests/test_v014_s15_p1_post_remediation_performance_fact_fields.py
- private raw/probe/browser evidence: KMFA/.codex_private_runtime/v014_s15_p1_post_remediation_performance_fact_fields/

## 验证命令

- PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_v014_s15_p1_post_remediation_performance_fact_fields
- PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_s15_p1_post_remediation_performance_fact_fields.py --require-private-evidence --require-browser-evidence --require-final-evidence
- PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_no_float_money.py
- PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/no_omission_check.py
- PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 scripts/validate_project_governance.py --project KMFA --mode required
- PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 scripts/lean_governance.py validate --project KMFA --mode required
- PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 scripts/validate_governance_sync.py --changed-only

## 原始数据边界

- 原始目录固定为 /Users/linzezhang/Downloads/KMFA_MetaData，Codex 只读。
- 当前 raw 快照没有差异；六字段的权威逐行、期间、单位、口径与精确数值绑定仍不足。
- 若最终 goal 多次交叉验证仍无法对齐，必须提供全中文最终差异报告。
- 不得提交 raw、zip、Excel、PDF、私有 CSV、凭据、银行流水、合同、薪资或税务材料。

## 未解决风险

- 23 个 XLSX 容器当前无法由 openpyxl 直接解析；不得损伤原文件进行转换。
- 13 个候选工作表没有权威项目行、人员、期间、单位、公式或数值绑定，不能转换为绩效事实。
- 3 条开放接受差异、9 条非零差异和 1 条未完成比较仍未关闭。
- GitHub main 未上传，app 未重装；统一延期到 Stage 12-18 全部完成、最终整体复审并修复 findings 后一次性执行。

## 推荐下一轮 pursuing goal prompt

继续 KMFA，只执行一个 phase：S15-P2｜绩效复核清单；不得执行 S15-P3 或 GitHub upload。
先确认 git root、branch、remote、HEAD、status，并读取最新 HANDOFF、v1.4 Task Pack/Roadmap 的 S15-P2 契约。
基于 S15-P1 的 6/6 人工复核、0 权威值绑定、0 已物化绩效事实和只读 raw 边界，只输出 public-safe 绩效事实表结构、异常项目方法与复核事项；没有权威逐行证据时不得生成业务项目、金额、绩效分数、工资或奖金结果。
验收必须包含 focused tests、strict validator、public-safe evidence、ignored private evidence、raw 前后/跨 phase 交叉验证、raw/private/secret scan、governance validators 和 local commit。
本轮不得执行 S15-P3、Stage 15 整体复审、工资计算、奖金审批、薪资导出、最终发放、GitHub upload、app reinstall、正式报告、差异关闭、持久业务写入或 business execution。
