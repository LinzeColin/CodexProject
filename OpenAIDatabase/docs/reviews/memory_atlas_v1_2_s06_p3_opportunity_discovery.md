# Memory Atlas v1.2 S06 P3 Opportunity Discovery Review

## Identity

- Task ID: `MA-V12-S06P3`
- Acceptance ID: `ACC-MA-V12-S06P3`
- Status: `phase_s06_p3_opportunity_discovery_completed_pending_s06_review`
- Next gate: `pending S06 Review`
- Validator: `validate:v1.2-s06-p3`
- Scope: S06 P3 only. No GitHub main upload in this phase.

## Summary

S06 P3 已完成机会发现。`scripts/build_memory_atlas_opportunities.py`
从 S05 canonical events、S06 P1 clusters 和 S06 P2 low-value loops 读取证据，
输出 `data/derived/behavior_intelligence/opportunities.json`。

当前输出包含 12 条候选机会和 12 张 为什么不是现在 卡片。机会类型覆盖
`automation`、`productization`、`template`、`compounding` 和 `defer`。
所有机会都保持候选语气，必须有 evidence_refs、下一步、半衰期或暂缓理由。

## Outputs

- `opportunity_clusters`：候选机会。
- `why_not_now_card`：每条机会对应的 为什么不是现在 卡片。
- `selection_policy`：最多 12 条，candidate only，不形成压力清单。
- `phase_boundary`：不接外部经济数据库、不输出心理诊断、不修改 raw、不进入 S06 Review。

## Acceptance

- 至少存在行为簇、低价值循环和机会三类输出：
  - `data/derived/behavior_intelligence/clusters.json`
  - `data/derived/behavior_intelligence/low_value_loops.json`
  - `data/derived/behavior_intelligence/opportunities.json`
- 每条机会都有证据、下一步、半衰期或暂缓理由。
- 每条机会都有 为什么不是现在 卡片。
- `atlasctl audit --check insight-evidence` 覆盖 clusters、low-value loops 和 opportunities。
- cluster 与 opportunity 输出不是关键词列表，而是带 evidence_refs 的中文可读结构。

## Validation

- `python scripts/atlasctl.py analyze --stage opportunities --dry-run`
- `python scripts/atlasctl.py analyze --stage opportunities`
- `python scripts/atlasctl.py audit --check insight-evidence`
- `pnpm --dir apps/memory-atlas run validate:v1.2-s06-p3`

## Boundaries

- No GitHub main upload in this phase.
- No remote push in this phase.
- No raw mutation in this phase.
- No external economic database in this phase.
- No psychological diagnosis in this phase.
- No infinite pressure list in this phase.
- No S06 Review in this phase.

S06 P3 只完成机会发现候选和 为什么不是现在 卡片。下一步只允许进入 S06 Review。

