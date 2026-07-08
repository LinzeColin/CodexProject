# Memory Atlas v1.2 S11 P4 Human Question Map

状态：`phase_s11_p4_human_question_map_completed_pending_s11_review`。

任务 ID：`MA-V12-S11P4`。

验收 ID：`ACC-MA-V12-S11P4`。

Validator：`validate:v1.2-s11-p4`。

## 范围

S11 P4 完成 Human Question Map，把 S11 P1、S11 P2 和 S11 P3 的 P0 图谱统一绑定到
人类问题、行动价值和 Visual ROI Gate。首页新增 `human_question_map.v1_2_s11_p4`
运行时面板，并跟随 `source/time/project/task` 过滤。

纳入 P0 的图谱：

- `cluster_tree`
- `bubble_map`
- `topic_cluster_explorer`
- `task_treemap`
- `automation_vs_augmentation`
- `roi_scatter`
- `opportunity_radar`
- `agent_decision_sankey`
- `friction_heatmap`
- `latent_radar`
- `evidence_timeline`
- `formula_explorer`

## Visual ROI Gate

Human Question Map 只展示 `visual_roi_gate_pass=true` 且 `p0_included=true` 的 P0 图谱。
失败候选不会进入 P0：

- `decorative_density_cloud`
- `raw_conversation_heat_glow`

这保留了 S07 legacy `atlasctl audit --check visual-roi` 的历史 gate，同时用
`机器治理/可视化配置/human_question_map.v1_2_s11_p4.json` 固定 S11 的 12 图问题地图。

## 验收

- `validate:v1.2-s11-p4`
- `ACC-MA-V12-S11P4`
- `MA-V12-S11P4`
- `human_question_map.v1_2_s11_p4`
- `Human Question Map`
- `Visual ROI Gate`
- `source/time/project/task`
- pending S11 Review

## 边界

- No GitHub main upload in this phase。
- No remote push in this phase。
- No raw mutation。
- No proposal apply execution。
- No S11 Review completion。
- No app reinstall。

Machine-readable boundary summary: Memory Atlas v1.2 S11 P4; MA-V12-S11P4; ACC-MA-V12-S11P4; phase_s11_p4_human_question_map_completed_pending_s11_review; validate:v1.2-s11-p4; Human Question Map; Visual ROI Gate; human_question_map.v1_2_s11_p4; cluster_tree; bubble_map; topic_cluster_explorer; task_treemap; automation_vs_augmentation; roi_scatter; opportunity_radar; agent_decision_sankey; friction_heatmap; latent_radar; evidence_timeline; formula_explorer; source/time/project/task; pending S11 Review; No GitHub main upload in this phase; No raw mutation; No proposal apply execution.
