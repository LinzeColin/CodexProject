# KMFA HANDOFF

## 当前状态

- phase: V014_S16_P3_POST_REMEDIATION_CUSTOMER_BUSINESS_ANALYSIS
- roadmap gate: S16-P3｜客户经营分析
- task: KMFA-V014-S16-P3-POST-REMEDIATION-CUSTOMER-BUSINESS-ANALYSIS-20260712
- acceptance: ACC-V014-S16-P3-POST-REMEDIATION-CUSTOMER-BUSINESS-ANALYSIS
- status: completed_validated_local_only_s16_p3_structure_candidates_zero_customer_summary_materialization_no_go_upload_deferred
- version: 0.1.4-s16-p3-post-remediation-customer-business-analysis
- decision: NO_GO
- data quality / report grade: Q4 / D
- pursuing_goal_status: active
- S16-P1 / S16-P2 / S16-P3 / Stage 16 review: performed / performed / performed / not performed
- GitHub upload / app reinstall: not performed / not performed
- 下一步只能执行 Stage 16 整体复审
- 不得执行 S17
- 不得执行 GitHub upload

## S16-P3 结果

- 四类结构：客户价值、项目毛利、回款质量、账龄风险均已只读接入。
- 私有探针：5 个 raw、48 个 XLSX、25 可解析、23 不可解析、4,198 个工作表、3,342 个唯一候选、3,772 个结构关联、374 个跨维候选、双次不一致 0。
- 摘要契约：客户、项目、期间、来源 4 个必需绑定组件和客户价值、项目毛利、回款质量、账龄风险 4 个分析维度。
- 当前事实：权威客户行、项目行、值绑定、客户摘要、风险事项、自动排名和公开业务值均为 0。
- 风险规则：客户价值、项目毛利、回款质量、账龄风险 4 类复核规则已定义，实际事项均为 0。
- 人工门禁：自动排名、客户联络、催收行动、法律决策均不得委托系统、不得自动决定或执行。
- legacy 隔离：旧 S16-P3 的 7 条来源线、4 条价值信号、4 条风险信号、4 条摘要和 4 项交接门禁仅作历史夹具。
- 页面验收：baseline 54/54，current 12/12 PASS；viewports/lanes/rules/HTTP/navigation=2/8/8/4/4，console/overflow=0/0。
- raw：phase 前后、跨 S16-P2 和当前快照一致。
- quality: Q4 / D / NO_GO / 3-9-2-1。

## 关键边界

1. 结构候选计数只证明工作表中存在相关结构，不证明存在有效客户、项目、期间、金额、排名或风险事实。
2. 缺少权威客户、项目和值绑定时，不得生成客户摘要、排名、风险事项或业务动作。
3. 不推断、不平均、不补零，不忽略 0.01 元，不关闭尚未由权威证据解释的差异。
4. 原始目录只读；不得修改、删除、移动、重命名、覆盖或写入任何原始文件。
5. raw 文件名、成员、工作表、字段、表头、客户、项目、日期、金额、明细、预览和诊断只存在于 ignored private runtime。
6. 客户联络、催收、法律决策、开票、付款和银行动作必须保持人工授权边界，本系统不得执行。
7. Stage 18 完成并通过最终整体复审、修复 findings 前，不得执行 GitHub upload 或 app reinstall。

## 证据

- manifest: KMFA/stage_artifacts/V014_S16_P3_POST_REMEDIATION_CUSTOMER_BUSINESS_ANALYSIS/machine/customer_business_analysis_manifest.json
- summary: KMFA/stage_artifacts/V014_S16_P3_POST_REMEDIATION_CUSTOMER_BUSINESS_ANALYSIS/machine/customer_business_analysis_summary.json
- source lanes: KMFA/stage_artifacts/V014_S16_P3_POST_REMEDIATION_CUSTOMER_BUSINESS_ANALYSIS/machine/source_lanes_public_safe.json
- binding contract: KMFA/stage_artifacts/V014_S16_P3_POST_REMEDIATION_CUSTOMER_BUSINESS_ANALYSIS/machine/customer_binding_contract_public_safe.json
- summary contract: KMFA/stage_artifacts/V014_S16_P3_POST_REMEDIATION_CUSTOMER_BUSINESS_ANALYSIS/machine/customer_summary_contract_public_safe.json
- risk rules: KMFA/stage_artifacts/V014_S16_P3_POST_REMEDIATION_CUSTOMER_BUSINESS_ANALYSIS/machine/customer_risk_rules_public_safe.json
- workbench: KMFA/stage_artifacts/V014_S16_P3_POST_REMEDIATION_CUSTOMER_BUSINESS_ANALYSIS/exports/html/customer_business_analysis_workbench.html
- validator: KMFA/tools/check_v014_s16_p3_post_remediation_customer_business_analysis.py
- focused test: KMFA/tests/test_v014_s16_p3_post_remediation_customer_business_analysis.py
- private raw/probe/browser/difference evidence: KMFA/.codex_private_runtime/v014_s16_p3_post_remediation_customer_business_analysis/

## 验证命令

- PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_v014_s16_p3_post_remediation_customer_business_analysis
- PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_s16_p3_post_remediation_customer_business_analysis.py --require-private-evidence --require-browser-evidence --require-final-evidence
- PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_no_float_money.py
- PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/no_omission_check.py
- PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 scripts/validate_project_governance.py --project KMFA --mode required
- PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 scripts/lean_governance.py validate --project KMFA --mode required
- PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 scripts/validate_governance_sync.py --changed-only

## 原始数据边界

- 原始目录固定为 /Users/linzezhang/Downloads/KMFA_MetaData，Codex 只读。
- 当前 raw 快照没有差异；客户、项目、期间、金额、回款和账龄仍未权威行级绑定。
- 若最终 goal 多次交叉验证仍无法对齐，必须提供全中文最终差异报告。
- 不得提交 raw、zip、Excel、PDF、私有 CSV、凭据、银行流水、合同、薪资或税务材料。

## 未解决风险

- 23 个 XLSX 容器当前无法由 openpyxl 直接解析；不得损伤原文件进行转换。
- 3,342 个候选工作表仅有结构级匹配，没有权威客户、项目、期间或值绑定。
- 3 条开放接受差异、9 条非零差异和 1 条未完成比较仍未关闭。
- GitHub main 未上传，app 未重装；统一延期到 Stage 12-18 全部完成、最终整体复审并修复 findings 后一次性执行。

## 推荐下一轮 pursuing goal prompt

继续 KMFA，只执行 Stage 16 整体复审；不得执行 S17 或 GitHub upload。
先确认 git root、branch、remote、HEAD、status，并读取最新 HANDOFF、v1.4 Task Pack/Roadmap 的 Stage 16 契约。
复跑当前 S16-P1/P2/P3 focused tests、strict validators、浏览器/移动端、raw 前后与跨 phase 证据、金额精度、防遗漏、raw/private/secret 和治理 validators；复审外协采购、项目生命周期和客户经营三条链的依赖一致性、legacy 隔离、页面互链、状态文案、移动端和门禁，修复全部 findings 后生成 Stage 16 public-safe 整体复审证据与本地 commit。
本轮不得执行 S17、自动客户排名、客户联络、催收、法律决策、现场施工、安全或技术签字、开票、付款、银行、GitHub upload、app reinstall、正式报告、差异关闭、持久业务写入或 business execution。
