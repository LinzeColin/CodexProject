# Memory Atlas v1.2 S06 P2 Low-Value Loops Review

## Identity

- Task ID: `MA-V12-S06P2`
- Acceptance ID: `ACC-MA-V12-S06P2`
- Status: `phase_s06_p2_low_value_loops_completed_pending_s06_p3`
- Next gate: `pending S06 P3`
- Validator: `validate:v1.2-s06-p2`
- Scope: S06 P2 only. No GitHub main upload in this phase.

## Result

S06 P2 已完成低价值循环候选识别。`scripts/build_memory_atlas_low_value_loops.py`
从 `data/derived/behavior_intelligence/events.json` 与
`data/derived/behavior_intelligence/clusters.json` 读取 S05/S06 P1 派生结果，并输出
`data/derived/behavior_intelligence/low_value_loops.json`。

当前输出包含：

- `loop_clusters`：低价值循环候选。
- `decision_debt_ledger`：Decision Debt Ledger。
- `action_half_life`：Action Half-Life。

`atlasctl` 已支持：

- `python scripts/atlasctl.py analyze --stage low-value-loops`
- `python scripts/atlasctl.py analyze --stage low-value-loops --dry-run`
- `python scripts/atlasctl.py audit --check insight-evidence`

## Acceptance

- 已覆盖 `repeated_rework`、`discussion_without_landing`、`over_optimization`、
  `scope_creep` 四类低价值循环候选。
- 每个候选只使用 `候选` 表述，并带有中文摘要、代表事件、观测时间范围和
  `evidence_refs`。
- 每个 loop 都生成对应 Decision Debt Ledger 条目，并包含建议收口问题。
- 每个 loop 都生成 Action Half-Life，且 `action_half_life_days` 为正数。
- `audit --check insight-evidence` 覆盖 clusters、low-value loops、Decision Debt 和
  Action Half-Life，且 `bad_items` 为空。

## Stop Conditions

- 未在没有证据时生成重大结论。
- 未输出心理诊断、人格诊断或个人状态判断。
- 未生成 S06 P3 opportunity cards。
- 未把机会线索变成无限压力清单。

## Boundary

S06 P2 只识别低价值循环候选、Decision Debt Ledger 和 Action Half-Life。
它不生成机会卡片，不修改 raw，不上传 GitHub main，不执行远端 push，不重装 app。
下一步只允许进入 S06 P3。
