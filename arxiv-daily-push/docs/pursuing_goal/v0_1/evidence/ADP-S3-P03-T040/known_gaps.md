# Known gaps · ADP-S3-P03-T040

- **flag 默认 OFF，官方内容尚未成为生产默认（有意，非缺陷）**：`BOARD3_A0_ONLY=false` 部署——**生产 Board 3 仍是媒体、六主题不变**。canary 端点 `/api/a0-canary` **非破坏性**地实抓 gov.cn 政策原文 + 应用 A0 门，证明官方证据率 100%、媒体降 discovery，但**不写生产**。**完整翻转**（flag=true，官方原文成生产默认）待：①A0 适配器 HTML 抓取接进 worker cron（现 canary 每次 1 子请求，接 cron 需按 DIR-007 加每 run 抓取上限，同 R2 shadow）②真实 14 天 shadow 跨日历累计。Owner S3 Exit 已批准方向；翻转本身仍应带真实 shadow 数据。
- **canary 官方内容为实时抓取、非落库**：`/api/a0-canary` 实抓 gov.cn/zhengce/xxgk（1 子请求）取 ≤8 篇政策原文作证据预览；这些原文尚未落 cn_items（落库 = 适配器接 cron 的后续工作）。故 flag=true 时若 cron 未抓官方，Board 3 会 abstain（宁缺毋滥，正确）而非显示媒体。
- **A0 门为最小实现**：`a0Board3Eligible` 按 source_id 白名单 或 .gov.cn 域判官方；真实 verify（主办单位/网站标识码，T033）在落库路径接入时用；本 canary 用域/白名单足够证明门行为。
- **build.json 边缘缓存**：`/build.json` 首次返回旧 build_id 是 Cloudflare 边缘缓存（cache-control）；cache-bust 后为新 build b189d3cc0703；页脚与 canary 路由均证明新 worker 已上线。缓存自愈。
- **回滚双路径**：flag 回滚 = 置 `BOARD3_A0_ONLY=false` 一次部署（当前即此态）；版本回滚 = `wrangler versions deploy 64c8b842`（T023 前态）。
