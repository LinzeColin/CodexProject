# Known gaps · ADP-S0-P02-T006

- **FACT-013 套餐/账单仍 UNVERIFIED_PRIVATE**：wrangler CLI 不暴露套餐等级与账单。用量（D1 1.05MB、24h rows_read 221,565 / rows_written 13,426）落在 D1 免费档典型日限内，但**这不等于确认账户在免费档**。真实套餐/账单需 Owner 后台确认 → S0 Exit。
- **FACT-015 私有分支/未提交代码 UNVERIFIED**：需 Owner/仓库只读盘点；不在本任务只读 Cloudflare 范围内。
- **FACT-014 严格逐 host build 相等 = PARTIAL**：已确认当前 adp-cloud 版本 455afd98 + 公开面相似度 0.9973（T004），但「adp.linzezhang.com 与 workers.dev 每次部署后恒为同一 version」未逐 host 单独证实（wrangler 按 Worker 而非按自定义域名报版本）。
- **R2 未开启，未代开**：R2 NOT_ENABLED（code 10042）；开启属 dashboard/计费动作，Owner 不愿代按，本任务只读、0 资源创建，故不代开。若后续需要对象存储（原文/历史），需 Owner 自行在后台开 R2 或另定方案。
- **遗留 mirror 表**：线上 D1 有 6 张 R6 时代残留表（events_inbox/lessons_mirror/manifests_mirror/mirror_meta/review_mirror/selections_mirror，共约 19 行）；本任务只登记为 DRIFT-FACT-011，不清理（清理属后续任务且需回滚方案）。
- **secret 安全**：OAuth token / API key 一律未记录；raw 输出经 token 扫描 clean 后才入证据。
- 独立验证：本报告以 `IMPLEMENTATION_READY_FOR_INDEPENDENT_VERIFICATION` 结束，PASS/FAIL 由独立上下文判定，实现者不自签。
