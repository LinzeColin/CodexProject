# Known gaps · ADP-S4-P02-T047

- **SHADOW，代表性 Wave-2 批次（任务边界，非缺陷）**：Wave 2 从**开发环境**实抓 gov.cn/zhengce/xxgk（法规/政策，6）+ stats.gov.cn（5）= 11 真实 A0 文档跨 6 月；生产 worker/cron 未触 → 实时无回归、0 云成本。字面全量 2016+ 随 cron 跨真实时间累计。
- **ndrc-gov / cac-gov 部分（已隔离）**：两源在列表发现文档链接但**未逐条全解析**（DOM 各异，走各自适配器 adapter_stats_ndrc / adapter_cac_nda 的完整解析属后续）→ 记为 partial_sources，**不 crash Wave**（失败源隔离机制），成功源（fagui/stats）不受影响。真实全解析随各适配器接线。
- **单位成本口径**：Wave 1/2 均走 dev-env 实抓 → 0 云成本，在批准区间（DIR-007 免费档，同 T044 成本看板口径）。接 worker cron 后每 fetch=子请求，须核 DIR-007 每 run 上限。
- **raw/version 未落生产**：Wave 2 文档经内容寻址 id + 幂等验证，未写生产 R2/D1（SHADOW）；真实落库随 worker 接线。
- **月份覆盖代表性**：6 月（2019-2026）；gap detector（T043）标未回填月，随 Wave 推进闭合。
