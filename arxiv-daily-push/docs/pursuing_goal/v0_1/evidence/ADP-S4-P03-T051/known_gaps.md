# Known gaps · ADP-S4-P03-T051（重点城市级 A1 cohort, SHADOW）

目标：按**用户价值**分批接入重点城市级 A1（省会/副省级/计划单列/关键创新制造金融外贸城市）；每城市有明确价值 + 官方原文；**不为凑数量启用低价值源**。诚实边界：

1. **本任务=选择 + 身份 + 游标（非抓取执行）**：交付物是 city cohort manifests + official identity + 2016 cursors——**选择/配置产物**，与 T045（A0 cohort 选择）同构。实际原文抓取是执行阶段（T050 批处理机制 + 后续 city 批次）。本任务不 backfill 文档。

2. **「官方原文」= 官方原文发布者身份核验**：每个入选城市经 T033 verify_identity 核验为**官方城市 .gov.cn、非中央 → A1**（媒体/聚合器 category 恒非 A1，永不入选）。这是「官方原文发布者」层面的核验；**不是**已抓取的具体原文。

3. **⚠ 0 个城市原文在服务器端实抓成功（诚实披露）**：城市/直辖市门户从服务器 stdlib 环境**多为 JS 渲染或 TLS 挡或仅出新闻**（recon 实测：上海/深圳/广州/武汉/重庆 JS；天津/青岛/宁波/杭州等 TLS 挡；苏州仅新闻路径）。故 18 个入选城市全 `original_fetch_status=pending_headless`。**municipality tier 的原文真实可抓由北京证明**（北京=直辖市，已在 T049/T050 省级 cohort 实抓真实原文）——同 tier 的可行性 proof-of-concept。city 原文抓取待 headless fetcher（承 T049/T050 已知边界）。`reachable_server_side` 是诚实 metadata，**非入选门**（入选门=价值+身份）。

4. **价值门非凑数量**：`value_score`=0.7×tier 权限 + role bonus（创新/金融/外贸/制造/枢纽），`STOP_THRESHOLD=0.6`。**负控制**：普通地级市（value 0.3<0.6）被拒；媒体聚合器（nominal value 0.93≥0.6 但 category=media → 非 A1）被拒——证明价值≠入选、非官方永不入选。18 入选全为真高价值（3 直辖市 + 5 副省级计划单列 + 6 副省级 + 4 关键经济），非凑数。

5. **NOT_DEPLOYED/SHADOW**：manifest + identity + cursors，未接 worker/生产。live build 仍 b189d3cc0703（==T040），六主题/MVP 不变。
