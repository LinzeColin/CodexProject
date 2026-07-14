# Memory Atlas v1.2 S11 P3 Workflow/latent/governance visuals

状态：`phase_s11_p3_workflow_latent_governance_visuals_completed_pending_s11_p4`。

任务 ID：`MA-V12-S11P3`。

验收 ID：`ACC-MA-V12-S11P3`。

Validator：`validate:v1.2-s11-p3`。

## 范围

S11 P3 完成 Workflow/latent/governance visuals 的分阶段可用版本。首页新增：

- `agent_decision_sankey`
- `friction_heatmap`
- `latent_radar`
- `evidence_timeline`
- `formula_explorer`

每个图都有中文 insight header、human question 和 action value，并跟随
`source/time/project/task` 过滤。图表不是静态装饰图：每张图都可点击进入
`summary`、`search`、`timeline` 或 `roi` 等现有视图继续复核。

## 决策价值

- `agent_decision_sankey` 回答 Codex/Agent 执行路径哪里失真。
- `friction_heatmap` 回答我在哪些地方反复浪费时间。
- `latent_radar` 回答哪些潜在信号正在增强。
- `evidence_timeline` 回答这个结论从哪些记录来。
- `formula_explorer` 回答这个分数为什么这样算。

这些图使用已有 redacted derived/runtime 节点和治理输出，不读取 raw/private 数据。

## 验收

- `validate:v1.2-s11-p3`
- `ACC-MA-V12-S11P3`
- `MA-V12-S11P3`
- `workflow_latent_governance_visuals.v1_2_s11_p3`
- `agent_decision_sankey`
- `friction_heatmap`
- `latent_radar`
- `evidence_timeline`
- `formula_explorer`
- `source/time/project/task`
- `python3 scripts/atlasctl.py audit --check visual-roi`
- `python3 scripts/audit_memory_atlas_visual_acceptance.py --repo-root .`
- pending S11 P4

## 边界

- No GitHub main upload in this phase。
- No remote push in this phase。
- No raw mutation。
- No proposal apply execution。
- No S11 P4 Human Question Map completion。
- No app reinstall。

Machine-readable boundary summary: Memory Atlas v1.2 S11 P3; MA-V12-S11P3; ACC-MA-V12-S11P3; phase_s11_p3_workflow_latent_governance_visuals_completed_pending_s11_p4; validate:v1.2-s11-p3; Workflow/latent/governance visuals; workflow_latent_governance_visuals.v1_2_s11_p3; agent_decision_sankey; friction_heatmap; latent_radar; evidence_timeline; formula_explorer; source/time/project/task; pending S11 P4; No GitHub main upload in this phase; No raw mutation; No proposal apply execution.
