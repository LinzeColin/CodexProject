# KMFA HANDOFF

## 当前状态

- phase: V014_S16_P1_POST_REMEDIATION_SUBCONTRACT_PROCUREMENT
- roadmap gate: S16-P1｜外协采购归集
- task: KMFA-V014-S16-P1-POST-REMEDIATION-SUBCONTRACT-PROCUREMENT-20260712
- acceptance: ACC-V014-S16-P1-POST-REMEDIATION-SUBCONTRACT-PROCUREMENT
- status: completed_validated_local_only_s16_p1_structure_candidates_zero_transaction_materialization_no_go_upload_deferred
- version: 0.1.4-s16-p1-post-remediation-subcontract-procurement
- decision: NO_GO
- data quality / report grade: Q4 / D
- pursuing_goal_status: active
- S16-P1 / S16-P2 / S16-P3 / Stage 16 review: performed / not performed / not performed / not performed
- GitHub upload / app reinstall: not performed / not performed
- 下一步只能执行 S16-P2
- 不得执行 S16-P3
- 不得执行 GitHub upload

## S16-P1 结果

- 五类结构：外协合同、采购订单、付款申请、发票、项目归属均已只读接入。
- 私有探针：5 个 raw、48 个 XLSX、25 可解析、23 不可解析、4,198 个工作表、1,335 个唯一候选、1,647 个结构关联、274 个跨类型候选、双次不一致 0。
- 当前事实：权威交易行、权威值、已物化交易、项目匹配、未归集成本项目和公开业务值均为 0。
- 检测规则：未归集成本、重复付款、无合同付款、跨项目费用 4 类规则已定义；实际异常候选均为 0。
- legacy 隔离：旧 S16-P1 的 5 条项目匹配、2 条未归集成本和 4 条异常候选仅作历史夹具。
- 页面验收：baseline 54/54，current 13/13 PASS；viewports/lanes/rules/HTTP/navigation=2/10/8/4/4，console/overflow=0/0。
- raw：phase 前后、跨 Stage 15 review 和当前快照一致。
- quality: Q4 / D / NO_GO / 3-9-2-1。

## 关键边界

1. 结构候选计数只证明工作表中存在相关结构，不证明存在有效交易、项目归属、合同关系或付款异常。
2. 缺少权威行级项目绑定时，不得自动生成项目匹配、未归集成本、重复付款、无合同付款或跨项目费用事实。
3. 不推断、不平均、不补零，不忽略 0.01 元，不关闭尚未由权威证据解释的差异。
4. 原始目录只读；不得修改、删除、移动、重命名、覆盖或写入任何原始文件。
5. raw 文件名、成员、工作表、字段、表头、金额、明细、预览和诊断只存在于 ignored private runtime。
6. 采购、付款审批、付款、银行和供应商结算不得自动执行或绕过人工审批。
7. Stage 18 完成并通过最终整体复审、修复 findings 前，不得执行 GitHub upload 或 app reinstall。

## 证据

- manifest: KMFA/stage_artifacts/V014_S16_P1_POST_REMEDIATION_SUBCONTRACT_PROCUREMENT/machine/subcontract_procurement_manifest.json
- summary: KMFA/stage_artifacts/V014_S16_P1_POST_REMEDIATION_SUBCONTRACT_PROCUREMENT/machine/subcontract_procurement_summary.json
- source lanes: KMFA/stage_artifacts/V014_S16_P1_POST_REMEDIATION_SUBCONTRACT_PROCUREMENT/machine/source_lanes_public_safe.json
- matching contract: KMFA/stage_artifacts/V014_S16_P1_POST_REMEDIATION_SUBCONTRACT_PROCUREMENT/machine/project_matching_contract_public_safe.json
- detection rules: KMFA/stage_artifacts/V014_S16_P1_POST_REMEDIATION_SUBCONTRACT_PROCUREMENT/machine/detection_rules_public_safe.json
- workbench: KMFA/stage_artifacts/V014_S16_P1_POST_REMEDIATION_SUBCONTRACT_PROCUREMENT/exports/html/subcontract_procurement_workbench.html
- validator: KMFA/tools/check_v014_s16_p1_post_remediation_subcontract_procurement.py
- focused test: KMFA/tests/test_v014_s16_p1_post_remediation_subcontract_procurement.py
- private raw/probe/browser/difference evidence: KMFA/.codex_private_runtime/v014_s16_p1_post_remediation_subcontract_procurement/

## 验证命令

- PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_v014_s16_p1_post_remediation_subcontract_procurement
- PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_s16_p1_post_remediation_subcontract_procurement.py --require-private-evidence --require-browser-evidence --require-final-evidence
- PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_no_float_money.py
- PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/no_omission_check.py
- PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 scripts/validate_project_governance.py --project KMFA --mode required
- PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 scripts/lean_governance.py validate --project KMFA --mode required
- PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 scripts/validate_governance_sync.py --changed-only

## 原始数据边界

- 原始目录固定为 /Users/linzezhang/Downloads/KMFA_MetaData，Codex 只读。
- 当前 raw 快照没有差异；项目、交易、合同、供应商、期间、单位、公式和精确数值仍未权威绑定。
- 若最终 goal 多次交叉验证仍无法对齐，必须提供全中文最终差异报告。
- 不得提交 raw、zip、Excel、PDF、私有 CSV、凭据、银行流水、合同、薪资或税务材料。

## 未解决风险

- 23 个 XLSX 容器当前无法由 openpyxl 直接解析；不得损伤原文件进行转换。
- 1,335 个候选工作表仅有结构级匹配，没有权威交易行、项目、合同或金额绑定。
- 3 条开放接受差异、9 条非零差异和 1 条未完成比较仍未关闭。
- GitHub main 未上传，app 未重装；统一延期到 Stage 12-18 全部完成、最终整体复审并修复 findings 后一次性执行。

## 推荐下一轮 pursuing goal prompt

继续 KMFA，只执行一个 phase：S16-P2｜项目状态生命周期；不得执行 S16-P3、Stage 16 整体复审或 GitHub upload。
先确认 git root、branch、remote、HEAD、status，并读取最新 HANDOFF、v1.4 Task Pack/Roadmap 的 S16-P2 契约。
基于 S16-P1 的 Q4 / D / NO_GO / 3-9-2-1 和只读 raw 边界，接入生产项目状态、开工、完工、结算、开票和回款的 public-safe 结构与私有候选解析，生成项目生命周期和异常事项；缺少权威项目行时不得虚构生命周期记录。
验收必须包含 focused tests、strict validator、public-safe evidence、ignored private evidence、raw 前后/跨 phase 交叉验证、浏览器/移动端、raw/private/secret scan、governance validators 和 local commit。
本轮不得执行 S16-P3、Stage 16 整体复审、现场施工、安全签字、技术签字、开票、催收、付款、银行、GitHub upload、app reinstall、正式报告、差异关闭、持久业务写入或 business execution。
