# PFI v0.2.4 Pre Stage 0 Context Lock

## Positioning

PFI v0.2.4 is treated as the repair package that follows the completed
v0.2.3 closeout. The source package provided by the user is named
`v0.2.3-repair`; this run maps that package into the new target version
`v0.2.4`.

This run is `pre stage 0`, not Stage 0. It only converges local facts,
source-package facts, current GitHub `main`, and the next run contract.

## Current Run Boundary

- Target version: `v0.2.4`
- Source package version: `v0.2.3-repair`
- Current unit: `Pre Stage 0 / Phase P0.0`
- Maximum work per run: one phase
- Stage 0 executed in this run: no
- Business UI changes in this run: no
- Data logic changes in this run: no
- GitHub main source of truth: `git@github.com:LinzeColin/CodexProject.git`
- Local worktree: `/Users/linzezhang/Documents/Codex/main_worktree/CodexProject/pfi`

## Fixed Product Rules Carried Forward

The official first-level navigation remains fixed at 10 entries:

1. 首页总览
2. 账户与资产
3. 账本流水
4. 投资管理
5. 消费管理
6. 数据源与上传
7. 建议与复盘
8. 报告与洞察
9. 市场与研究
10. 设置

Deprecated constraints remain deprecated:

- historical 9-entry first-level navigation;
- treating `市场与研究` as forbidden at first level;
- dark AI-console default direction;
- README/docs-only completion claims;
- mock/sample/demo/synthetic/fixture/fake financial data acceptance.

## Stop Condition

Stop after pre stage 0 and wait for user acceptance or an explicit instruction
to enter v0.2.4 Stage 0. Do not execute the TaskPack Stage 0 prompt in this run.

