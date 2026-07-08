# Human Question Map 说明

S11 P4 已完成 Human Question Map。它不是新加一批装饰图，而是把已经进入 P0 的
12 张图谱统一回答三个问题：

- 这张图回答哪个人类问题。
- 看完以后应该采取什么行动。
- 它是否通过 Visual ROI Gate 并允许进入 P0。

当前 P0 图谱覆盖 Clio-like visuals、Economic-like visuals 和
Workflow/latent/governance visuals。首页问题地图支持 `source/time/project/task`
过滤，点击卡片会进入对应的星图、搜索、ROI、总结或时间线视图继续复核。

Visual ROI Gate 不通过的候选不会进入 P0。本 phase 记录的失败候选包括
`decorative_density_cloud` 和 `raw_conversation_heat_glow`，它们只用于说明停用原因，
不作为 P0 图谱展示。

边界：No GitHub main upload in this phase。No raw mutation。No proposal apply execution。
下一步是 S11 Review。
