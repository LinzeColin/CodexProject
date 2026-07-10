# KMFA HANDOFF

## 当前状态
- phase: `V014_REMAINING_TWO_PROJECT_CASH_COLLECTION_EVIDENCE_OR_FINAL_DIFFERENCE_ACCEPTANCE`
- task: `KMFA-V014-REMAINING-TWO-PROJECT-CASH-COLLECTION-EVIDENCE-OR-FINAL-DIFFERENCE-ACCEPTANCE-20260710`
- status: `completed_validated_local_only_third_cash_project_materialized_final_cash_project_difference_accepted_no_go`
- version: `0.1.4-remaining-two-project-cash-collection-evidence-or-final-difference-acceptance`
- decision: `NO_GO`
- pursuing_goal_status: `active`
- local_commit: `see git log HEAD after local commit`
- GitHub upload: `not performed / deferred`
- app reinstall: `not performed`
- Stage review: `not performed`
- business execution: `not performed`

## 本 phase 结果
- raw archives / accessible non-ledger OOXML workbooks: `3 / 19`
- raw collection candidates / strict source records: `48 / 4`
- unique balanced collection links / balanced receivable vouchers: `2 / 2`
- cash project candidates: `4`
- resolved / unresolved projects: `3 / 1`
- final difference accepted projects: `1`
- private cash metrics: `9`
- newly materialized / materialized / unresolved target slots: `3 / 37 / 3`
- reconciliation comparisons: `12`
- complete / zero / nonzero / incomplete cash: `11 / 2 / 9 / 1`
- WPS/OLE secure content readable: `0`
- forced-zero materializations: `0`
- global residual differences: `72` (not replayed in this phase)
- raw source files: `5`
- raw before/after exact file snapshot match: `true`

## 关键结论
- 其中一个未决项目由 4 条严格来源记录归并为 2 条不同的唯一银行入账链；每条链同时具备项目维度、客户维度、非公式正向金额、唯一等额银行借方、同凭证应收贷方和借贷平衡。
- 第三个项目因此新增物化 3 个私有现金槽位；现金收款按唯一银行凭证去重后重放，现金毛利只使用 integer cents。
- 最后一个项目在主账、银行、应收、可访问 OOXML 和 WPS/OLE 兼容层的重复交叉核验中仍无正向收款证据；3 个槽位保持未决，缺失值未写成零。
- 9 条非零差异原样保留；所有文件名、项目、客户、字段、金额、工作表、交易、凭证和全中文最终差异接受报告只存在于 ignored private runtime。

## 证据
- manifest: `KMFA/stage_artifacts/V014_REMAINING_TWO_PROJECT_CASH_COLLECTION_EVIDENCE_OR_FINAL_DIFFERENCE_ACCEPTANCE/machine/remaining_two_project_cash_collection_evidence_or_final_difference_acceptance_manifest.json`
- summary: `KMFA/stage_artifacts/V014_REMAINING_TWO_PROJECT_CASH_COLLECTION_EVIDENCE_OR_FINAL_DIFFERENCE_ACCEPTANCE/machine/remaining_two_project_cash_collection_evidence_or_final_difference_acceptance_summary.json`
- go/no-go: `KMFA/stage_artifacts/V014_REMAINING_TWO_PROJECT_CASH_COLLECTION_EVIDENCE_OR_FINAL_DIFFERENCE_ACCEPTANCE/machine/remaining_two_project_cash_collection_evidence_or_final_difference_acceptance_go_no_go_report.json`
- validator: `KMFA/tools/check_v014_remaining_two_project_cash_collection_evidence_or_final_difference_acceptance.py`
- focused test: `KMFA/tests/test_v014_remaining_two_project_cash_collection_evidence_or_final_difference_acceptance.py`
- private final difference report: `KMFA/.codex_private_runtime/v014_remaining_two_project_cash_collection_evidence_or_final_difference_acceptance/private_final_difference_acceptance_report_zh.md`

## 验证命令
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_v014_remaining_two_project_cash_collection_evidence_or_final_difference_acceptance`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_remaining_two_project_cash_collection_evidence_or_final_difference_acceptance.py --require-private-evidence`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 scripts/validate_project_governance.py --project KMFA`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 scripts/lean_governance.py validate --project KMFA`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 scripts/validate_governance_sync.py --changed-only --base-ref HEAD --enforce-sync`

## 原始数据边界
- 原始目录固定为 `/Users/linzezhang/Downloads/KMFA_MetaData`，Codex 仅只读。
- 本 phase 已对 5 个原始文件执行前后逐文件路径、大小、mtime、inode、mode 和 SHA256 快照，结果完全一致。
- 所有 raw 文件名、archive member、sheet/row、项目、客户、字段、金额、交易、凭证、身份、匹配明细和诊断只存在于 `KMFA/.codex_private_runtime/`。
- 不得提交 raw、zip、Excel、PDF、私有 CSV、凭据、流水、合同、薪资或税务材料。

## 推荐下一轮 pursuing goal prompt
继续 KMFA，只执行一个 phase：global residual difference queue replay or authoritative exclusion。
先确认 git root、branch、remote、HEAD、status。
基于本 phase 的 public-safe `NO_GO` evidence、37 个已物化目标槽位、3 个最终差异接受现金槽位和 ignored private 差异报告，只读使用 `/Users/linzezhang/Downloads/KMFA_MetaData`，重放全局 72 条 residual difference queue。
每条记录必须按现有 source reference、owner-authorized exclusion、formula/non-numeric mapping 和 private fingerprint evidence 分类；只有来源唯一、整数公式可重放且不覆盖现有 9 条非零差异时才关闭。无法证明的继续进入全中文 private 差异报告，不得推导零、自动平均或静默选边。不得做 Stage review、GitHub upload、app reinstall 或 business execution。验收必须包含 focused test、validator、public-safe evidence、治理记录、raw immutability evidence、raw/private scan 和 local commit。
