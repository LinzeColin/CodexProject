# KMFA HANDOFF

## 当前状态

- phase: V014_S15_P2_POST_REMEDIATION_PERFORMANCE_REVIEW_LIST
- roadmap gate: S15-P2｜绩效复核清单
- task: KMFA-V014-S15-P2-POST-REMEDIATION-PERFORMANCE-REVIEW-LIST-20260711
- acceptance: ACC-V014-S15-P2-POST-REMEDIATION-PERFORMANCE-REVIEW-LIST
- status: completed_validated_local_only_s15_p2_zero_authoritative_fact_rows_six_review_items_no_go_upload_deferred
- version: 0.1.4-s15-p2-post-remediation-performance-review-list
- decision: NO_GO
- data quality / report grade: Q4 / D
- pursuing_goal_status: active
- S15-P1 / S15-P2 / S15-P3 / Stage 15 review: performed / performed / not performed / not performed
- GitHub upload / app reinstall: not performed / not performed
- 下一步只能执行 S15-P3
- 不得执行 Stage 15 整体复审
- 不得执行 GitHub upload

## S15-P2 结果

- 事实表：1 个 public-safe 表结构、6 个字段、0 条权威或合成项目事实行、0 个公开业务值。
- 异常项目：1 个判定方法、6 条字段规则；因权威项目行和值绑定均为 0，实际异常项目为 0。
- 复核清单：6 项字段级事项，全部保持待权威绑定；不含 project_ref、人员、金额、比率或日期明细。
- legacy 隔离：旧 S15-P2 的 4 条合成事实行和 16 条事项只作历史结构夹具，不是当前动态事实。
- S15-P1 依赖：6/6 字段人工复核，权威行/值绑定和绩效事实物化均为 0。
- 私有聚合：5 个 raw、48 个 XLSX 容器、25 可解析、23 不可解析、4,198 个可解析工作表、13 个唯一候选。
- 浏览器：baseline/current=54/54 / 14/14 PASS；viewports/reviews/HTTP/navigation=2/12/4/4，console/overflow=0/0。
- raw：phase 前后、跨 S15-P1 和当前快照一致。
- quality: Q4 / D / NO_GO / 3-9-2-1。

## 关键边界

1. 空事实表只证明结构已定义，不证明任何项目绩效事实已经形成。
2. 没有权威项目、期间、单位、口径和精确值绑定时，不得生成实际异常项目。
3. 六项复核事项均为字段级，不得升级为项目异常、绩效分数、工资或奖金结论。
4. 不推断、不平均、不补零，不忽略 0.01 元，不关闭尚未由权威证据解释的差异。
5. 原始目录只读；不得修改、删除、移动、重命名、覆盖或写入任何原始文件。
6. raw 文件名、成员、工作表、字段、表头、金额、明细、截图与诊断只存在于 ignored private runtime。
7. Stage 18 完成并通过最终整体复审、修复 findings 前，不得执行 GitHub upload 或 app reinstall。

## 证据

- manifest: KMFA/stage_artifacts/V014_S15_P2_POST_REMEDIATION_PERFORMANCE_REVIEW_LIST/machine/performance_review_manifest.json
- summary: KMFA/stage_artifacts/V014_S15_P2_POST_REMEDIATION_PERFORMANCE_REVIEW_LIST/machine/performance_review_summary.json
- fact schema: KMFA/stage_artifacts/V014_S15_P2_POST_REMEDIATION_PERFORMANCE_REVIEW_LIST/machine/performance_fact_table_schema_public_safe.json
- fact table: KMFA/stage_artifacts/V014_S15_P2_POST_REMEDIATION_PERFORMANCE_REVIEW_LIST/machine/performance_fact_table_public_safe.json
- abnormal method: KMFA/stage_artifacts/V014_S15_P2_POST_REMEDIATION_PERFORMANCE_REVIEW_LIST/machine/abnormal_project_method_public_safe.json
- review items: KMFA/stage_artifacts/V014_S15_P2_POST_REMEDIATION_PERFORMANCE_REVIEW_LIST/machine/performance_review_items_public_safe.json
- workbench: KMFA/stage_artifacts/V014_S15_P2_POST_REMEDIATION_PERFORMANCE_REVIEW_LIST/exports/html/performance_review_workbench.html
- validator: KMFA/tools/check_v014_s15_p2_post_remediation_performance_review_list.py
- focused test: KMFA/tests/test_v014_s15_p2_post_remediation_performance_review_list.py
- private raw/diagnostic/browser evidence: KMFA/.codex_private_runtime/v014_s15_p2_post_remediation_performance_review_list/

## 验证命令

- PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_v014_s15_p2_post_remediation_performance_review_list
- PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_s15_p2_post_remediation_performance_review_list.py --require-private-evidence --require-browser-evidence --require-final-evidence
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

继续 KMFA，只执行一个 phase：S15-P3｜与工资项目边界；不得执行 Stage 15 整体复审或 GitHub upload。
先确认 git root、branch、remote、HEAD、status，并读取最新 HANDOFF、v1.4 Task Pack/Roadmap 的 S15-P3 契约。
基于 S15-P2 的 6 列零行业绩效事实表、0 实际异常项目、6 项字段级复核事项和只读 raw 边界，只预留 public-safe 事实输出接口与未来工资系统读取草案；不得生成工资、奖金、薪资导出或最终发放结果。
验收必须包含 focused tests、strict validator、public-safe evidence、ignored private evidence、raw 前后/跨 phase 交叉验证、raw/private/secret scan、governance validators 和 local commit。
本轮不得执行 Stage 15 整体复审、工资计算、奖金审批、薪资导出、最终发放、GitHub upload、app reinstall、正式报告、差异关闭、持久业务写入或 business execution。
