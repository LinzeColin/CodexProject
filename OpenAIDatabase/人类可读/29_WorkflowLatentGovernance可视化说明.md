# 29 Workflow/Latent/Governance 可视化说明

S11 P3 已完成 Workflow/latent/governance visuals。

状态：`phase_s11_p3_workflow_latent_governance_visuals_completed_pending_s11_p4`。

任务 ID：`MA-V12-S11P3`。

验收 ID：`ACC-MA-V12-S11P3`。

Validator：`validate:v1.2-s11-p3`。

## 这次新增了什么

首页新增 5 张治理与潜性图：

- `agent_decision_sankey`：看 Codex/Agent 从目标、执行、复审到治理/授权的路径。
- `friction_heatmap`：看 scope creep、证据缺口、返工循环、授权边界和公式维护的热区。
- `latent_radar`：看资产复利、自动化势能、证据强度、协作清晰和治理安全。
- `evidence_timeline`：看结论沿时间线来自哪些记录。
- `formula_explorer`：看 proxy 公式和参数为什么这样解释。

## 怎么用

先在顶部过滤 `source/time/project/task`。这 5 张图会跟随同一组过滤结果变化。

点击 Sankey、热力格、雷达轴、时间线事件或参数行，会进入已有的总结、搜索、时间线
或 ROI 视图继续复核。它们不是装饰图，而是帮助判断下一轮是否要补证据、降权结论、
收口 run contract 或保留 proposal-only 边界。

## 边界

- 不读取 raw/private 数据。
- 不执行 proposal apply。
- 不修改 active config。
- 不上传 GitHub main。
- 不重装 app 入口。
- S11 P4 Human Question Map 下一轮单独处理。

Machine-readable boundary summary: Memory Atlas v1.2 S11 P3; MA-V12-S11P3; ACC-MA-V12-S11P3; phase_s11_p3_workflow_latent_governance_visuals_completed_pending_s11_p4; validate:v1.2-s11-p3; Workflow/latent/governance visuals; agent_decision_sankey; friction_heatmap; latent_radar; evidence_timeline; formula_explorer; source/time/project/task; pending S11 P4; No GitHub main upload in this phase; No raw mutation; No proposal apply execution.
