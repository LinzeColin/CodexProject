# Known gaps · ADP-S5-P04-T066

- **实质变化定义 = T026 content_hash（单一事实源，不分叉）**：`run_digest` 用 T026 `version_engine.content_hash`（覆盖**正文 + 附件集 + 状态**的 substantive signature，噪声不敏感）判断是否实质变化。因此**状态变更（如 published→revoked）与附件变更 DO 触发通知**（content_hash 含 status/attachments）；而**纯 facet/元数据重分类**（agency/region/topic/entity/doc_number 或纯日期 reflow）在正文/附件/状态不变时**不触发**——这与「只推实质变化」一致，且**复用 T026 对"实质变化"的唯一定义、不在本任务另立标准**。若 Owner 要求把文号/生效日期变更也视作实质变化，属扩展 substantive signature（T026 契约范围），须走其门、不在本任务静默决定。
- **通知去重键 = (watch_id, canonical_id, content_hash)**：重跑幂等靠 `state.seen`。**A→B→A 回退**：回到旧 content_hash 时该键已在 seen → 不再通知（视作"回到已知状态"）；若需把"回退"也当新变化，可在键中并入序号/时间戳（本任务确定性、不读时钟，故未并）。两个 watch 匹配同一条目 → **独立键各自通知**（正确，不折叠）。
- **state 持久化**：本任务用**内存 state** 证明"重跑不重复"（run_digest 不原地改调用方 state、返回新 state）。真实持久化（D1/KV 存 seen 键）由部署阶段提供；本任务出确定性契约与幂等证明。
- **period 由调用方传入**：daily/weekly 由 `period` 参数区分，**不读时钟**（确定性、可重放）。真实调度的周期边界由部署阶段的 cron 提供。**daily 与 weekly 应各用独立 seen-set（或 weekly = daily 通知的 rollup）**——若二者共用同一 seen-set，daily 先跑会让 weekly 重跑变空。本任务用单一 seen-set 证明幂等；分 cadence 的 seen-set 由部署阶段落地。
- **silence 语义**：被监测 watch 本周期无**新**实质变化 → 静默信号（源可能沉默/失效，本身是信号）；含匹配但全为已见（无新变化）亦静默，符合"本周期无变化"。
- **NOT_DEPLOYED**：不接 worker/cron/D1/R2，不改生产数据。实时无回归（live build_id b189d3cc0703 == T040）。开启 **S5-P04（Watchlist、资料与知识有效性）**；后继 T067/T068 在此监测底座上扩展。
