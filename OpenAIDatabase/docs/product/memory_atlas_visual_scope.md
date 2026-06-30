# Memory Atlas v1.1.5 Visual Scope and Naming Freeze

- Stage: 0 合同与边界冻结
- Phase: 0.1 Scope & Naming Freeze
- Roadmap tasks: 0.1.1, 0.1.2, 0.1.3
- Status: proposed contract
- Last updated: 2026-06-30

## Phase Goal

将 Memory Atlas v1.1.5 的首批可视化升级范围、中文命名、默认入口决策冻结为后续 Codex 可执行合同。本 phase 只写文档，不改路由、不替换生产 UI、不接入新的数据源。

## In Scope

第一批 v1.1.5 只覆盖以下模块：

1. 记忆总览：默认启动板块，用于展示当前认知状态、趋势、机会、风险和下一步行动。
2. 记忆星系：升级现有 Galaxy 方向，目标是深空星云、Flow Field、星系引力盘、黑洞、新生星云和记忆地形层。
3. 记忆时间河：升级现有 Timeline 方向，目标是动态、可缩放、可交互的时间演化视图。
4. Universe State Snapshot：共享状态层，供记忆总览、记忆星系、记忆时间河、Inspector 和 ROI Dashboard 读取同一套状态判断。

## Out of Scope

1. 不接入新的外部知识源。
2. 不读取 raw export、cookies、sessions、secret、plaintext private data。
3. 不让前端直接写长期记忆；前端只能生成 proposal。
4. 不一次性重构全系统。
5. 不在 Stage 0 直接替换生产 Galaxy 或 Timeline。
6. 不把 Memory Terrain 做成地图控件；它只作为记忆星系里的语义视觉层。
7. 不把记忆星系退回普通点线图，不把记忆时间河退回列表、表格或静态散点。

## Naming Matrix

| Target concept | Frozen Chinese name | Current/legacy label | Contract note |
|---|---|---|---|
| Home / overview | 记忆总览 | 无独立生产入口 | v1.1.5 默认入口目标；Stage 0 只冻结合同，不改路由。 |
| Galaxy / starfield | 记忆星系 | 银河星云 / Galaxy | 后续 UI 文案和文档应收敛到“记忆星系”。 |
| Timeline / river | 记忆时间河 | 时间轴 / Timeline | 后续 UI 文案和文档应收敛到“记忆时间河”。 |
| Shared state | Universe State Snapshot | 派生 snapshot / runtime snapshot | 作为跨板块共享状态层，不替代原 redacted Memory Atlas 数据源。 |
| Weather semantic layer | Memory Weather | 无固定入口 | 只由 Universe State 和模型参数驱动。 |
| Low-value loop | Black Hole | 风险/低价值循环 | 视觉信号与解释层必须可追溯到数据和参数。 |
| Emerging opportunity | Proto-Star | 机会/新主题 | 视觉信号与解释层必须可追溯到数据和参数。 |
| Semantic terrain | Memory Terrain | 知识地形草案 | 只进入记忆星系语义层，不做地图应用。 |

## Default Entry Decision

v1.1.5 的目标默认入口是“记忆总览”。用户打开 Memory Atlas 后，第一屏应先回答：

1. 当前最重要的认知状态是什么。
2. 哪些主题正在上升、衰退、冲突或形成机会。
3. 哪些低价值循环需要被识别为 Black Hole 风险。
4. 下一步建议行动是什么。
5. 记忆星系和记忆时间河分别提供什么深入入口。

Stage 0 Phase 0.1 不修改当前生产 `activeView`、路由、导航顺序或现有 UI 文案；这些实现变更必须等后续 Integration phase 执行。

## Data Boundary

v1.1.5 可视化合同只能使用 redacted derived data：

- `data/derived/visualization/memory_atlas.json`
- 后续 C2/C3 允许新增的 redacted Universe State fixture 或 snapshot
- 后续参数模板中的非私密配置

禁止读取或提交：

- raw OpenAI export
- full Codex transcripts
- cookies / sessions / browser state
- plaintext secrets / private keys / `.env`
- 本地绝对路径作为默认运行依赖

## Acceptance

Phase 0.1 完成必须满足：

1. 范围清晰列出第一批模块：记忆总览、记忆星系、记忆时间河、Universe State Snapshot。
2. 明确无外部知识源接入、无 raw/private 读取、无生产 UI 替换。
3. 命名矩阵固定“记忆总览”“记忆星系”“记忆时间河”。
4. 默认入口决策明确为“记忆总览”，且说明本 phase 不改路由。
5. 文档包含 rollback 和 validation。

## Validation

人工阅读本 Markdown，确认每个 acceptance item 都可被本文件直接证明。自动检查可使用文本搜索确认关键名词和禁止边界存在。

## Rollback

删除 `docs/product/memory_atlas_visual_scope.md`，并删除本 phase 关联的默认入口合同增量。
