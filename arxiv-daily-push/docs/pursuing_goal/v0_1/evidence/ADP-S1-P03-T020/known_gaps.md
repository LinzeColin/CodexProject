# Known gaps · ADP-S1-P03-T020

- **P0 准确率为机器保真 provisional**：p0_fact_accuracy=1.0 是「render payload 的 P0 字段逐字等于原文」的抽取保真，非人工核对的语义准确；按 Owner 2026-07-16 决策标 provisional_machine，Owner 按 GOLDEN_SET_RUBRIC.md 抽查 ≥50 条后升 human_verified。
- **Release Gate 未挂 GitHub workflow**：content_release_gate.py 可本地/CI 运行且已验证（正例 RELEASE、负例 BLOCK），接入 .github workflow 属后续部署纪律；接入后内容 bundle 不达标的 PR 会被挡（且只挡内容 bundle）。
- **未接入 worker 渲染**：Golden Set/Gate 作用于 render payload（T018 契约），worker 尚未改为渲染 L0-L3；切换渲染 + 接 Gate 属后续部署任务（须保六主题 + before/after 对照）。
- **board1 样本 217/500**：本窗口 board1 充足；文号/DOI 覆盖随板块分布。
- 独立验证：以 IMPLEMENTATION_READY_FOR_INDEPENDENT_VERIFICATION 结束，实现者不自签。
