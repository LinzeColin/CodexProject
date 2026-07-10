# KMFA HANDOFF

## 当前状态
- phase: `V014_REAL_PROJECT_IDENTITY_PRIVATE_REBINDING_AND_PROCESSED_VALUE_MATERIALIZATION`
- task: `KMFA-V014-REAL-PROJECT-IDENTITY-PRIVATE-REBINDING-AND-PROCESSED-VALUE-MATERIALIZATION-20260710`
- status: `completed_validated_local_only_real_identity_rebound_partial_value_materialization_no_go`
- version: `0.1.4-real-project-identity-private-rebinding-and-processed-value-materialization`
- decision: `NO_GO`
- pursuing_goal_status: `active`
- local_commit: `see git log HEAD after local commit`
- GitHub upload: `not performed / deferred`
- app reinstall: `not performed`
- Stage review: `not performed`
- business execution: `not performed`

## 本 phase 结果
- authority candidate groups / unique PDF sources: `4 / 4`
- real project private identity bindings: `4`
- authority margin formula exact: `4 / 4`
- authority gross profit equals contract minus total expense: `1 / 4`
- workbook identity match groups / unique sheet bindings: `3 / 0`
- private integer processed metrics: `32`
- materialized S09 target slots: `28`
- unresolved cash target slots: `12`
- reconciliation comparisons: `12`
- complete / zero / nonzero / incomplete cash: `8 / 2 / 6 / 4`
- global residual differences: `72` (not replayed in this phase)
- raw source files: `5`
- raw before/after exact file snapshot match: `true`

## 关键结论
- 4 个合成项目身份已在 ignored private overlay 中替换为真实权威来源身份；公开仓库不保存项目名、来源、金额或私有 hash。
- 32 条项目指标和 28 个目标槽位均使用 integer cents / basis points，未使用 float。
- 6 条权威值与系统复算值存在非零差异，已原样保留，不自动覆盖或抹平。
- 3 个项目命中多个工作表、1 个项目未命中工作簿身份，因此现金毛利不能唯一物化，12 个目标槽位继续未决。
- 已在 ignored private runtime 生成全中文差异报告；processed consistency 和 business value consistency 尚未验证。

## 证据
- manifest: `KMFA/stage_artifacts/V014_REAL_PROJECT_IDENTITY_PRIVATE_REBINDING_AND_PROCESSED_VALUE_MATERIALIZATION/machine/real_project_identity_private_rebinding_and_processed_value_materialization_manifest.json`
- summary: `KMFA/stage_artifacts/V014_REAL_PROJECT_IDENTITY_PRIVATE_REBINDING_AND_PROCESSED_VALUE_MATERIALIZATION/machine/real_project_identity_private_rebinding_and_processed_value_materialization_summary.json`
- go/no-go: `KMFA/stage_artifacts/V014_REAL_PROJECT_IDENTITY_PRIVATE_REBINDING_AND_PROCESSED_VALUE_MATERIALIZATION/machine/real_project_identity_private_rebinding_and_processed_value_materialization_go_no_go_report.json`
- validator: `KMFA/tools/check_v014_real_project_identity_private_rebinding_and_processed_value_materialization.py`
- focused test: `KMFA/tests/test_v014_real_project_identity_private_rebinding_and_processed_value_materialization.py`
- private difference report: `KMFA/.codex_private_runtime/v014_real_project_identity_private_rebinding_and_processed_value_materialization/private_difference_report_zh.md`

## 验证命令
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_v014_real_project_identity_private_rebinding_and_processed_value_materialization`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_real_project_identity_private_rebinding_and_processed_value_materialization.py --require-private-materialization`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 scripts/validate_project_governance.py --project KMFA`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 scripts/lean_governance.py validate --project KMFA`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 scripts/validate_governance_sync.py --changed-only --base-ref HEAD --enforce-sync`

## 原始数据边界
- 原始目录固定为 `/Users/linzezhang/Downloads/KMFA_MetaData`，Codex 仅只读。
- 本 phase 已对 5 个原始文件执行前后逐文件路径、大小、mtime、inode、mode 和 SHA256 快照，结果完全一致。
- 所有 raw 文件名、archive member、sheet、cell/page、字段、金额、上下文、身份、匹配明细和诊断只存在于 `KMFA/.codex_private_runtime/`。
- 不得提交 raw、zip、Excel、PDF、私有 CSV、凭据、流水、合同、薪资或税务材料。

## 推荐下一轮 pursuing goal prompt
继续 KMFA，只执行一个 phase：cash source private disambiguation and remaining value materialization。
先确认 git root、branch、remote、HEAD、status。
基于本 phase 的 public-safe `NO_GO` evidence 和 ignored private 身份绑定、处理指标及全中文差异报告，只读使用 `/Users/linzezhang/Downloads/KMFA_MetaData`，在 `KMFA/.codex_private_runtime/` 内对 3 个多工作表候选和 1 个未命中项目执行现金来源私有消歧，只有回款与已付成本来源唯一且公式可重放时才物化 12 个剩余现金槽位；6 条现有非零差异必须原样保留。
不得修改、移动、删除或覆盖任何原始文件，不得把任何 raw/private 明文提交 Git。无法稳定交叉验证的继续进入全中文 private 差异报告。不得做 Stage review、GitHub upload、app reinstall 或 business execution。验收必须包含 focused test、validator、public-safe evidence、治理记录、raw immutability evidence、raw/private scan 和 local commit。
