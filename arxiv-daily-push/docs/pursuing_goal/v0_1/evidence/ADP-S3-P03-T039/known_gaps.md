# Known gaps · ADP-S3-P03-T039

- **SHADOW，不切换（任务边界，非缺陷）**：release_mode=SHADOW；**不切换任何东西**。真正把媒体降为 discovery、官方原文成默认证据是 **T040 canary**，且须过 **Owner S3 Exit 门**。本任务只做对比 + 纪律框架 + 代表性报告。
- **14 周期报告为代表性、非 14 个真实日历日**：把可得真实样本（board3 媒体 85 条 vs A0 官方流）分桶为 14 个日周期以演示框架与验收。**字面 14 天跨真实日历时间**由试点 cron 累计（同 T023 的 7 日 shadow 需跨真实时间）。真实每日 latency/coverage/cost 随真实运行填充。
- **A0 流指标基于 T037 门 + 合成官方**：A0 流权威率 100%/污染 0% 来自 T037 门（官方 A0/A1 + primary 才准入）作用于官方适配器输出；真实运行的漏抓（coverage_misses）/误报（false_positives）随真实抓取暴露，本任务建模为 0（当前门 + resolver 设计上无误纳）。
- **成本为结构性建模**：cost_per_accepted = A0 流请求数 / 已接受项（本报告 ~3 请求/8 接受 = 0.375）；真实值接 worker cron 后按 Worker 子请求核 DIR-007。
- **决策不在本任务**：框架给出 READY/CONTINUE 建议，但**最终 A0 晋级由 Owner S3 Exit 门决定**；本任务不自行切换、不自签晋级。
