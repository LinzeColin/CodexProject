# PFI v0.2.4 Stage 0 Phase 0.2 History Deprecation Policy

## Run Boundary

本轮只执行 `PFI v0.2.4 Stage 0 / Phase 0.2 - 历史约束废弃`。

本文件不修改业务 UI、app bundle、launcher 或数据逻辑。Stage 0 仍未完成；
Phase 0.3 和 Stage 0 whole-stage review 仍需后续 run work 执行。

## Deprecated Constraints

| Deprecated constraint | v0.2.4 replacement | Status |
| --- | --- | --- |
| 历史 9 入口正式约束 | 正式一级入口固定 10 个 | deprecated |
| `市场与研究` 不得作为一级入口 | `市场与研究` 是第 9 个正式一级入口 | deprecated |
| 暗色 AI 控制台作为默认视觉方向 | 默认亮色、高质感、人类任务流 | deprecated |
| 样例、演示、模拟财务数据可作为验收 | 只允许真实数据或中文真实空态/阻断状态作为验收依据 | deprecated |

## Retained Reference Principles

历史资料中仍保留以下原则：

- 每轮只执行一个 stage/phase，未经用户验收或明确指令不得进入下一阶段。
- 不得用 README/docs 声明替代真实 evidence。
- 不得使用 `mock`、`sample`、`demo`、`synthetic`、`fixture`、`fake` 财务数据。
- 不得用 long page 或 anchor scroll 冒充真实页面路由。
- 不得用 `localStorage`、`sessionStorage` 或 `IndexedDB` 冒充生产持久化。
- 禁止硬编码图表、净资产、现金、投资市值或趋势线作为正式财务事实。

## Current v0.2.4 Rule

v0.2.4 后续阶段必须以当前 checkout 的真实文件、真实 runtime、真实测试和真实
evidence 为准。来源包 `v0.2.3-repair` 可作为修补意图和验收参考，但其中已经被
当前 main 事实覆盖的 GitHub audit 不得反向覆盖当前 repo 状态。

## Phase 0.2 Task Mapping

| Task | Status | Evidence |
| --- | --- | --- |
| T0.2.1 标记 9 入口约束作废 | done | 本文件 |
| T0.2.2 标记市场与研究禁令作废 | done | 本文件 |
| T0.2.3 标记暗色 AI 控制台方向作废 | done | 本文件 |
| T0.2.4 标记可保留参考原则 | done | 本文件 |

