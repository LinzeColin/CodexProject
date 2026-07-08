# 可视化配置

用于放置 human question map、visual ROI gate、多维图谱和图表绑定行动价值的配置。

当前 S07 P2 已完成。Visual ROI Gate 配置已写入
`机器治理/可视化配置/visual_roi_gate.v1_2_s07_p2.json`，并由
`data/derived/information_roi/information_roi_gate.json` 生成可审计 gate 输出。

任务 ID：`MA-V12-S07P2`。

验收 ID：`ACC-MA-V12-S07P2`。

Validator：`validate:v1.2-s07-p2`。

## S07 P2 Visual ROI Gate

Visual ROI Gate 固定 P0 图表准入规则：没有决策价值的图表不进 P0。每个 P0 visual
必须有：

- human question
- action
- evidence refs
- information ROI score
- `visual_roi_gate_pass=true`

当前 P0 visual 包含 `cluster_tree`、`bubble_map`、`task_treemap`、
`automation_augmentation`、`roi_scatter`、`agent_decision_sankey`、
`friction_heatmap`、`latent_radar`、`evidence_timeline` 和 `formula_explorer`。

被排除示例包括 `decorative_word_cloud` 和 `raw_schema_table`，它们不能进入 P0。

## 边界

- 不接入外部经济数据库。
- 不是精确收入预测。
- 不实现 S07 P3 Formula What-if Simulator UI。
- 不修改运行时 UI。
- 不修改 raw。
- No GitHub main upload in this phase。

下一步是 S07 P3。
