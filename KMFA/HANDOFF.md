# KMFA HANDOFF

## 当前状态

- phase: `V014_GLOBAL_RESIDUAL_DIFFERENCE_QUEUE_REPLAY_OR_AUTHORITATIVE_EXCLUSION`
- task: `KMFA-V014-GLOBAL-RESIDUAL-DIFFERENCE-QUEUE-REPLAY-OR-AUTHORITATIVE-EXCLUSION-20260710`
- status: `completed_validated_local_only_61_closed_or_excluded_11_open_no_go`
- version: `0.1.4-global-residual-difference-queue-replay-or-authoritative-exclusion`
- decision: `NO_GO`
- pursuing_goal_status: `active`
- local_commit: `see git log HEAD after local commit`
- GitHub upload: `not performed / deferred`
- app reinstall: `not performed`
- Stage review: `not performed`
- business execution: `not performed`

## 本 phase 结果

- global residual queue / classified: `72 / 72`
- current private target value replay: `37`
- integer gross-profit / gross-margin formula replay: `16`
- replayed numeric records: `53`
- owner-authorized non-numeric exclusions: `8`
- closed or excluded / open: `61 / 11`
- open ambiguous cost-component sources: `8`
- open final accepted cash differences: `3`
- preserved nonzero / zero / incomplete comparisons: `9 / 2 / 1`
- forced-zero materializations: `0`
- raw source files / exact before-after match: `5 / true`

## 关键结论

- 历史 72 条 `materialized` 记录只是治理占位，不能直接视为已对账；本 phase 已按当前真实私有数据重新逐条分类。
- 37 条 current target slots 与当前比较或现金指标一致；16 条毛利/毛利率记录通过唯一项目来源和整数公式重放，并与对应 comparison target 交叉验证。
- 4 条计算执行引用和 4 条成本分类属于非数值字段，经 owner authorization 从数值差异队列排除，不伪造数值。
- 8 条利息/差旅分项仍有多候选且没有直接指纹或记录引用唯一匹配；3 条现金槽位虽已接受差异，但没有可证明数值。上述 11 条继续未决。
- 9 条非零差异、2 条零差异和 1 条未完成比较原样保留；未推导零、未平均、未静默选边。

## 证据

- manifest: `KMFA/stage_artifacts/V014_GLOBAL_RESIDUAL_DIFFERENCE_QUEUE_REPLAY_OR_AUTHORITATIVE_EXCLUSION/machine/global_residual_difference_queue_replay_or_authoritative_exclusion_manifest.json`
- summary: `KMFA/stage_artifacts/V014_GLOBAL_RESIDUAL_DIFFERENCE_QUEUE_REPLAY_OR_AUTHORITATIVE_EXCLUSION/machine/global_residual_difference_queue_replay_or_authoritative_exclusion_summary.json`
- go/no-go: `KMFA/stage_artifacts/V014_GLOBAL_RESIDUAL_DIFFERENCE_QUEUE_REPLAY_OR_AUTHORITATIVE_EXCLUSION/machine/global_residual_difference_queue_replay_or_authoritative_exclusion_go_no_go_report.json`
- validator: `KMFA/tools/check_v014_global_residual_difference_queue_replay_or_authoritative_exclusion.py`
- focused test: `KMFA/tests/test_v014_global_residual_difference_queue_replay_or_authoritative_exclusion.py`
- private difference report: `KMFA/.codex_private_runtime/v014_global_residual_difference_queue_replay_or_authoritative_exclusion/private_global_residual_difference_report_zh.md`

## 验证命令

- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_v014_global_residual_difference_queue_replay_or_authoritative_exclusion`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_global_residual_difference_queue_replay_or_authoritative_exclusion.py --require-private-evidence`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 scripts/validate_project_governance.py --project KMFA`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 scripts/lean_governance.py validate --project KMFA`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 scripts/validate_governance_sync.py --changed-only --base-ref HEAD --enforce-sync`

## 原始数据边界

- 原始目录固定为 `/Users/linzezhang/Downloads/KMFA_MetaData`，Codex 仅只读。
- 本 phase 对 5 个原始文件执行前后逐文件路径、大小、mtime、inode、mode 和 SHA256 快照，结果完全一致。
- 所有 raw 文件名、项目、字段、金额、目标槽位、来源引用、指纹、候选和全中文差异报告只存在于 ignored private runtime。
- 不得提交 raw、zip、Excel、PDF、私有 CSV、凭据、流水、合同、薪资或税务材料。

## 推荐下一轮 pursuing goal prompt

继续 KMFA，只执行一个 phase：remaining eleven residual difference source trace or final acceptance。
先确认 git root、branch、remote、HEAD、status。
基于本 phase 的 72 条完整分类、61 条已关闭或权威排除记录、8 条缺唯一权威来源的利息/差旅成本分项、3 条最终差异接受现金槽位和 9 条已保留非零差异，只读使用 `/Users/linzezhang/Downloads/KMFA_MetaData`。
对 8 条成本分项仅在真实项目身份、字段语义、记录引用和整数值均唯一时绑定；对 3 条现金槽位仅在新增唯一收款证据存在时重放。多次交叉验证仍不唯一的，维持未决并更新全中文 private 最终差异报告，不得推导零、自动平均、静默选边或覆盖 9 条非零差异。不得做 Stage review、GitHub upload、app reinstall 或 business execution。验收必须包含 focused test、validator、public-safe evidence、治理记录、raw immutability evidence、raw/private scan 和 local commit。
