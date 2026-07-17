# Known gaps · ADP-S8-P02-T089（PARTIAL）｜14 日浸泡与停线演练

## ★T089 未完成（诚实）★
- 验收 **clause 1「14 次真实日运行无 Sev-1/2」= 日历约束**：需连续 14 天 daily cron 无 Sev-1/2。**单次自主 session 不可压缩、不可编造**。`t089_complete=False`。
- **★但 soak 已 LIVE 自累积（非 day 0 静态框架）★**：soak 直接读**生产 cn_run_log**（每日 cron 写一行 result）——`result != 失败` 即健康日。**当前 live 2/14 连续健康日**（2026-07-15 正常 + 2026-07-16 降级，均非失败）。soak **自动累积、无需 agent 动作**，daily cron 每天加一行，14/14 无失败即 T089 clause 1 **自动闭合**。`soak_progress()` 载重（一个 失败 断连续、14 健康日即 complete）。故 T089 的**开发已完成**（停线演练 + soak live 读取器 + 框架），剩的纯是**日历时间**（约 12 个健康 cron 日）。
- 本任务只交付 **clause 2（停线演练）+ 浸泡框架**；**T089 不计入完成**，**88/90 仍为单次自主 session 完成上限**。**T090（终交付）deps T089 完成** → 亦阻塞于 14 日。

## 范围（诚实）
- **停线演练 = 对真实检测门的隔离演练**：8 触发各注入失败条件→断言对应门**触发停线**（load-bearing:良性负控制不触发）。3 个触发用确定性阈值镜像真实机制(P95 >20%、DIR-007 guardFrac 0.9、3rd 失败)——因这些门在生产运行/预算路径里，隔离演练用同阈值的确定性检查代表；5 个用真实门(visual_regression_ci/validate_evidence/dataset_snapshot)。
- **未做真实生产放量/真实 incident**：本任务不真实触发生产停线、不真实跑 14 日——那是 clause 1 的日历部分。停线**机制**已演练证其会停。
- **浸泡框架**：定义 daily manifest schema + 14 日累加器 + SLA/quality/cost trend 结构;真实每日填充留待操作方 14 日运行。

## NOT_DEPLOYED
- live 仍 `b189d3cc0703`；演练隔离、不部署、不改生产。
