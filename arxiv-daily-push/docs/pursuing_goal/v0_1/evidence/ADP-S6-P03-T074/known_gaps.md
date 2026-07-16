# Known gaps · ADP-S6-P03-T074

- **鲁棒阈值以召回换精度（诚实披露）**：模型判异常静默用 **median + k·MAD**（k=3）——比基线的"简单 median"更宽容源自身的发布变异，故**不误报自然变异源**（精度更高）。代价：极宽 MAD 的源，一个**边界**异常（略超 median 但未超 median+k·MAD）理论上可能被漏报，而简单 median 基线会抓到。**本任务不宣称模型普遍支配基线**，而是演示模型在**真实失败模式**上更好——(a) 变异源误报、(b) 采集故障区分——且**真异常（远超变异）仍被模型抓到**（fixture 案例 6 已验）。k 可调（更小 k → 更敏感更多误报；更大 k → 更少误报可能漏边界）。
- **采集故障判据 = recent_fetch_errors**：模型据"近期抓取错误 > 0"判 collection_failure（我方抓取器坏，非源静默）。真实 recent_fetch_errors 由**抓取日志/源健康账**提供（T012/T013 registry 的 3-连败自动禁用即此类信号）。fetch 错误存在时优先判 collection_failure——因为**抓取坏时无法判断源是否真静默**（collection_failure 是诚实、保守的判断）。
- **评估指标**：`evaluate` 对模型与基线在**同一 labeled set、同一真值**打分（公平比较）；`false_alarm_rate=false_alarms/normal_total`（无 normal 案例时 0.0，不除零）；`human_value=correct_catches×value`（正确的异常静默/采集故障早捕获 × 价值）。**从不报虚高价值**（只计正确 catch）。
- **SHADOW release_mode**：predictions 在 **dev/shadow 环境**计算，**不推送给用户、不作用于生产**；生产 worker/cron/data 未触、实时 build b189d3cc0703 不变、0 云成本、DIR-007 不受影响。上线/停止决策由 **T076**（完整 Horizon Shadow：Brier skill 正且稳定、校准可接受、领先价值明确才上线，否则停止）。
- **无时钟/随机/网络**：确定性；as_of 与日期（day ordinal）传入。**模型调用 0**（本地统计，无 LLM）。
- 后接 **T075（主题加速与中央—地方扩散预测，size M）、T076（完整 Horizon Shadow 与上线/停止决策）**。
