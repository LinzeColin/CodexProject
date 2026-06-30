# Memory Overview Product Contract

- Product target: Memory Atlas v1.1.5
- Stage: 0 合同与边界冻结
- Current phase contribution: 0.1.3 默认入口冻结
- Status: phase 0.1 entry decision only; full product contract remains pending for Phase 0.2
- Last updated: 2026-06-30

## Default Entry Freeze

v1.1.5 的目标默认入口为“记忆总览”。它是 Memory Atlas 打开后的第一判断层，不是普通 dashboard，也不是现有 Galaxy 的重命名。

记忆总览必须在后续实现中承担以下入口职责：

1. 展示当前认知状态和 Memory Weather。
2. 展示 dominant / rising / declining clusters 的可解释摘要。
3. 展示 Black Hole 风险和 Proto-Star 机会。
4. 给出下一步行动建议。
5. 提供进入记忆星系、记忆时间河、Inspector、ROI Dashboard 的明确路径。

## Stage 0 Boundary

本文件当前只冻结默认入口决策。不得把本文件视为 Phase 0.2 的完整首页产品合同，也不得据此直接修改生产路由。

本 phase 不做：

- 不修改 `apps/memory-atlas/src/App.tsx` 的默认 `activeView`。
- 不改现有导航顺序。
- 不新增首页组件。
- 不读取 raw/private/session/cookie/secret 数据。
- 不生成 writeback 或长期记忆写入。

## Acceptance for Task 0.1.3

1. 明确默认启动板块目标为“记忆总览”。
2. 明确“记忆总览”不是普通 dashboard。
3. 明确当前 phase 只写合同，不改生产路由。
4. 明确后续完整信息架构属于 Phase 0.2。

## Rollback

删除本文件，或在 Phase 0.2 前撤销其中“记忆总览”为默认入口的合同决策。
