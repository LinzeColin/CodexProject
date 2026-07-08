# Clio-like 多维可视化说明

当前阶段：S11 P1 已完成。

本阶段新增首页内的 Clio-like 多维图谱，用于回答：当前筛选后的记忆里，哪些主题簇最值得继续看？

## 图谱集合

- `cluster_tree`：层级簇树，问题是“我最近主要在关注哪些主题层级？”，行动价值是先定位主题重心，再决定进入搜索、星图或后续 ROI 图谱。
- `bubble_map`：Bubble Map，问题是“高频、机会、风险如何分布？”，行动价值是优先打开高 ROI 且近期活跃的簇。
- `topic_cluster_explorer`：Topic/Cluster Explorer，问题是“哪个主题簇最值得继续追问？”，行动价值是用代表记录进入搜索视图复核证据。

## 过滤方式

图谱跟随当前页面的 `source/time/project/task` 状态：

- `source` 来自全局数据源过滤。
- `time` 来自共享 timeline time range。
- `project` 对应主题或 cluster 过滤。
- `task` 对应任务类别过滤。

## 边界

- 本阶段不是 S11 P2，不实现 Task Treemap、Automation vs Augmentation、ROI Scatter 或 Opportunity Radar。
- 本阶段不是 S11 P3，不实现 Sankey、Friction Heatmap、Latent Radar、Evidence Timeline 或 Formula Explorer。
- 本阶段不是完整 S11 P4，只提供每个新增图的中文问题和行动价值。
- No GitHub main upload in this phase。

下一步是 S11 P2。
