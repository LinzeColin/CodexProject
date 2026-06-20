# 26 - 数据库优先的数据工作台与“真实数据感”

## 1. 结论

界面必须让用户清楚感知：眼前的图不是静态插画，而是由可查询、可追溯、可版本化的数据库生成。实现方式不是堆满表格，而是在每个视觉中持续展示数据边界、快照、记录数、来源、覆盖和新鲜度。

## 2. 全局数据状态条

顶部常驻但紧凑地显示：

- 实体数量；
- 关系数量；
- 事件数量；
- 有效来源数量；
- 当前 data snapshot；
- 当前 score snapshot；
- 最近同步；
- 当前查询耗时；
- 数据健康状态。

示例：`18,426 entities · 96,381 relationships · snapshot D-20260619-04 · 3m ago · 84ms`。

## 3. 每个视觉的数据库元信息

所有主图右上角/底部至少可见：

- `visible / total`；
- 查询筛选摘要；
- as-of；
- freshness；
- coverage；
- source count；
- snapshot id；
- query latency；
- 是否截断/聚合及原因。

## 4. 数据库与来源板块

一级导航 `数据库与来源` 包含：

1. 数据血缘：Source -> Raw Document -> Fact -> Entity/Relationship/Event -> Score -> Visualization；
2. 来源健康矩阵：正常、延迟、失败、人工复核；
3. 表/对象统计：实体、关系、证据、事件、设施、证券、合同、政策；
4. 同步作业：最近运行、耗时、写入、拒绝、错误；
5. 数据新鲜度：按来源语义分别展示；
6. 覆盖缺口：未知、未披露、冲突、低置信度；
7. 数据检索：按实体、关系、证据和快照查询；
8. 原始证据入口：原文定位、观察时间、hash、解析版本。

## 5. 系统记录表

核心表至少包括：

- `entities` / `entity_aliases` / `entity_identifiers`；
- `relationships` / `relationship_evidence`；
- `events` / `event_evidence`；
- `source_documents` / `raw_source_snapshots` / `entity_resolution_candidates` / `ingestion_evidence_chain`；
- `relationship_fact_candidates` / `relationship_fact_candidate_evidence` / `manual_review_queue`；
- `model_versions` / `model_profile_versions` / `parameter_values`；
- `score_runs` / `score_results` / `score_snapshots`；
- `data_snapshots` / `active_snapshots`；
- `ingestion_runs` / `source_health`；
- `transactional_outbox`；
- `operation_logs` / `calibration_runs`；
- `saved_views` / `exploration_sessions`。

## 6. 视觉设计原则

- 数据状态使用小型状态点、微型条形图、覆盖环和时间条，不使用大段系统文案；
- 证据层按需展开，默认显示来源数量和质量；
- 数据缺口可视化为“未知区域”，不能用空白掩盖；
- 同一信息不重复堆叠为 KPI 卡片、表格和文字三份；
- 图与表共享选择，点击数据库记录可在图中高亮，反向亦然；
- 查询状态有 skeleton/progress，不允许无反馈冻结。

## 7. 性能目标

| 操作 | P95 |
|---|---:|
| 当前主体首页首屏（缓存） | < 1.2s |
| 当前主体首页首屏（冷查询） | < 2.5s |
| 选择节点反馈 | < 100ms |
| 详情数据 | < 400ms |
| 一层展开 | < 700ms |
| 参数本地预览 | < 250ms |
| 数据库检索 | < 800ms |
| SSE 更新可见 | < 1.5s |

## 8. 验收

- 默认首页可见数据库记录量、快照和更新时间，但不压缩主图；
- 数据库与来源页面能从来源一路追踪到某条图边；
- 用户能分辨“公开披露、系统推断、冲突、未知”；
- 每次查询显示是否截断；
- mock 数据必须有明显标识，正式构建禁止把 mock 与 live 混合。
