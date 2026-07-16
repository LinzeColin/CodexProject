# Known gaps · ADP-S5-P04-T068

- **validity 由 T026 content_hash 驱动（单一事实源）**：知识失效判定复用 T026 `version_engine.content_hash`（正文 + 附件 + 状态的 substantive signature）。故**状态/附件变更 DO 触发失效**、噪声再渲染**不触发**（无 churn）；**纯 facet 元数据变更**（agency/region 等）不触发——与 T066「实质变化」单一定义一致，不另立标准。真实生产的 validity 触发接入 D1 版本链由部署阶段负责。
- **131 项为 ADP 自建 parity registry（非外部 canonical 清单）**：仓库无预置 131 清单，本任务据 9 类真实竞品（Elicit/Consensus/Scite/ResearchRabbit/Litmaps/Semantic Scholar/Connected Papers/参考管理器/通用学术工具）枚举其**真实用户收益**。状态**诚实且可复核**：`delivered` 引真实交付任务（T057-T068，S5 库层 NOT_DEPLOYED 故「delivered」= 库/工具层已交付而非已上生产 UI）；substrate 存在但未完全构建者（如 similarity graph、seed-expansion map、topic timeline）**诚实降级 partial**，不虚标 delivered；`planned` 指向具体未来阶段（S6/S7/S8）；`not_applicable` 带原因。**owner 具名**（ADP-research/content/library/core），无 no-owner。
- **partial → delivered 的推进**：19 项 partial 与 15 项 planned 在 **S6-S8 及部署阶段**推进（如 consensus meter/TLDR/dashboards/visual graph 需 S7 前端、shared/citation-style 需 S8）。本任务保证**状态明确、有 owner、可复核**，非保证全部已 delivered——验收要求「无未知/无人负责」而非「全部 delivered」。
- **无时钟**：validity 比较**源哈希**而非 wall-time（确定性、可重放）。真实「失效时钟」由部署阶段定期比对当前源触发。
- **NOT_DEPLOYED**：不接 worker/cron/D1/R2，不改生产数据。实时无回归（live build_id b189d3cc0703 == T040）。**收尾 S5-P04（Watchlist、资料与知识有效性）与整个 Stage S5（多板块深度与竞品收益对齐）**；后续进入 S6。
