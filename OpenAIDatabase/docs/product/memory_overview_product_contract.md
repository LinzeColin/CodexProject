# Memory Overview Product Contract

- Product target: Memory Atlas v1.1.5
- Stage: 0 合同与边界冻结
- Current phase contribution: 0.2.1 记忆总览 Product Contract
- Status: product contract only; no production route or UI implementation
- Last updated: 2026-06-30

## Purpose

“记忆总览”是 Memory Atlas v1.1.5 的默认首页目标。它打开后回答一个问题：当前长期记忆宇宙处于什么状态，哪些主题正在增强、衰退、形成机会或进入低价值循环，下一步最应该做什么。

记忆总览不是普通 dashboard，不以堆叠图表或 KPI 卡片为主体验。它是一个状态判断层和行动入口，必须使用 Universe State Snapshot、Memory Weather、Black Hole、Proto-Star、Mini Starfield、River Pulse 与 Next Actions 共同形成可解释首页。

## Inputs

记忆总览只能消费脱敏派生数据和共享状态层，不直接读取 raw transcript、cookies、sessions、plaintext secrets、本地绝对私有路径或浏览器状态。

Required logical inputs:

1. `Universe State Snapshot`：共享状态判断对象。
2. `source_scope`：总数据源 / ChatGPT / Codex。
3. `time_range`：当前全局时间范围。
4. `filters`：主题、项目、层级、类型、数据源过滤。
5. `selection_state`：当前聚焦 cluster、record、theme 或 action。
6. `inspector_context`：右侧详情面板可读取的派生摘要引用。

Universe State minimum fields for this page:

| Field | Page usage |
|---|---|
| `memory_weather` | 首页主状态和天气一句话 |
| `dominant_clusters` | 主导主题卡片 |
| `rising_clusters` | 上升主题与 Proto-Star 候选 |
| `declining_clusters` | 衰退主题和 stale orbit 提示 |
| `black_holes` | 低价值循环、重复消耗、冲突风险 |
| `proto_stars` | 新生机会、潜在项目、可投资注意力 |
| `river_pulse` | 时间河近期脉冲摘要 |
| `mini_starfield` | 星系预览摘要 |
| `recommended_next_actions` | 下一步行动建议 |
| `confidence` | 首页状态判断可信度 |

## Information Architecture

首页按“先判断状态，再解释来源，再给行动”的顺序组织。

### 1. Memory Weather

Memory Weather 是第一屏主语义，不是装饰文案。它必须用人能直接理解的语言说明当前认知天气，例如：主题集中、机会增强、低价值循环升高、项目切换频繁、某类记忆正在衰退。

Required elements:

1. 当前 weather label。
2. 一句话解释。
3. 主要驱动因素。
4. 可信度和数据覆盖窗口。
5. 点击后同步 Inspector，展示证据摘要。

### 2. Universe State Cards

状态卡片用于承接 Universe State，不是普通指标卡。每张卡必须能回答“这对我有什么意义”和“下一步怎么处理”。

Required card groups:

| Card group | Required content | Primary action |
|---|---|---|
| Dominant | 当前最强主题、项目或行为模式 | 查看证据 / 进入记忆星系 |
| Rising | 增强中的主题或技能轨迹 | 继续投入 / 设置复盘 |
| Declining | 正在衰退或长期未维护主题 | 归档 / 重新激活 |
| Black Hole | 低 ROI 循环、重复错误、冲突区 | 降权 / 创建行动约束 |
| Proto-Star | 早期机会、潜在项目、新兴趣 | 进入验证 / 加入 Next Actions |

Each card must include:

1. `title`
2. `state_type`
3. `human_explanation`
4. `evidence_count`
5. `source_scope`
6. `linked_cluster_ids`
7. `confidence`
8. `recommended_action`

### 3. Next Actions

Next Actions 是首页的行动出口，不能只是文本建议列表。每条建议必须来自 Universe State 或明确的派生规则，并可以跳转到对应证据。

Required action types:

1. Continue：继续投入高 ROI 主题。
2. Review：复盘冲突、低价值循环或衰退主题。
3. Consolidate：把分散记忆合并为项目/能力/偏好。
4. Explore：验证 Proto-Star 机会。
5. Defer：降低噪音或暂缓低价值输入。

Actions must remain proposal-only. 首页不得直接修改长期记忆、偏好文件或 GitHub 数据。

### 4. Mini Starfield

Mini Starfield 是记忆星系的轻量预览，用于显示当前 Universe State 的空间状态，不是完整 WebGL 星系。

Required signals:

1. Dominant clusters 的相对位置和密度。
2. Black Hole 的风险位置。
3. Proto-Star 的机会闪光。
4. 当前筛选范围的视觉覆盖。
5. 点击进入“记忆星系”并携带 selection/filter/state。

Mini Starfield must avoid high GPU cost and must degrade gracefully to a static preview if production performance gates require it.

### 5. River Pulse

River Pulse 是记忆时间河的近期脉冲预览，用于回答“最近发生了什么变化”。

Required signals:

1. 近期活动密度。
2. 主题增强或衰退节奏。
3. Black Hole band 近期扩张或收缩。
4. Proto-Star marker 近期出现时间。
5. 点击进入“记忆时间河”并携带 time range、brush range 和 selection。

### 6. Inspector Handoff

首页所有重要元素必须能同步右侧 Inspector。Inspector 负责显示证据摘要、计算解释、来源范围、更新时间和可审计引用。首页不得把内部字段直接暴露为主要用户语言。

## Shared State Sync

记忆总览必须与记忆星系、记忆时间河、Inspector、ROI Dashboard 共享以下状态：

1. `source_scope`
2. `time_range`
3. `filters`
4. `selection_state`
5. `mode`: Presentation / Analysis
6. `inspector_focus`

Changing source scope changes only analyzed dataset; it must not create fake records or show empty future sources as real selectable data.

## Interaction Contract

Required interactions:

1. Hover state cards: show short explanation and confidence.
2. Click state card: sync Inspector and highlight related Mini Starfield / River Pulse segment.
3. Click Black Hole: open evidence and suggested reduction action.
4. Click Proto-Star: open opportunity evidence and validation action.
5. Click Mini Starfield: navigate to memory starfield with state preserved.
6. Click River Pulse: navigate to memory river with time range preserved.
7. Toggle Presentation / Analysis: Presentation remains clean; Analysis shows formulas, parameters, evidence and debug-lite labels.

No interaction may directly apply writeback. Writeback remains proposal-only and must require agent/human apply outside this page.

## Non-Goals

This phase does not implement the page. It does not:

1. Modify `apps/memory-atlas/src/App.tsx`.
2. Change default `activeView`.
3. Rename existing navigation labels in production code.
4. Build Mini Starfield or River Pulse components.
5. Add new data ingestion.
6. Read raw/private/session/cookie/secret data.
7. Push any active memory writeback.

## Acceptance Criteria

Phase 0.2.1 is accepted when this document clearly defines:

1. 记忆总览 as the target default homepage, not a normal dashboard.
2. Required use of `Universe State Snapshot`.
3. `Memory Weather`.
4. `Black Hole`.
5. `Proto-Star`.
6. `Next Actions`.
7. `Mini Starfield`.
8. `River Pulse`.
9. Module layout and state card structure.
10. Interaction and shared-state sync rules.
11. Non-goals and privacy boundaries.

## Rollback

Revert this document to the Phase 0.1 entry-freeze version or delete the Phase 0.2 additions. No production code rollback is required because this contract phase does not change runtime behavior.
