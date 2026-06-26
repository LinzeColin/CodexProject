# QBVS 目标完成度缺口审计

生成时间：2026-06-06T09:34:11

## 当前结论

- 状态：active_not_complete；不严格 blocked。
- readiness：95.00%。
- 当前阶段主候选：`bw99_boll_or_rsi_none_ma_trend_full_none`。
- 当前不能标记目标 complete：真实基金 NAV、OpenD 历史 quota、百万级规模仍未闭合。

## 逐项审计

| 需求 | 状态 | 证据 | 下一步 |
|---|---|---|---|
| 读取 QuantLab 原版支付宝策略 | 完成 | 已读取原版 AlipayStrategy / AlipayEnhancedStrategy，并用本地场景验证用户诊断。 | 保持只读；后续只做 ReviewOnly 候选。 |
| 交易行为策略而非投资组合策略 | 完成 | 候选以 target-weight 行为规则表达：基础仓位、RSI/BOLL 补仓、MA 趋势参与、不因上涨自动卖出。 | QuantLab 展示时继续标注为 behavior strategy。 |
| 平均总收益差不低于 -8% | 完成 | 主候选 12,000 exact run 中 avg_total_gap=-0.0827%。 | 基金 NAV 口径补齐后复核。 |
| 平均年化差不低于 -3% | 完成 | 主候选 12,000 exact run 中 avg_annualized_gap=-0.0052%。 | 基金 NAV 口径补齐后复核。 |
| 下跌保护/回撤改善 | 完成 | 主候选 avg_drawdown_improvement=0.1310%，为正。 | 在真实基金和 Moomoo 200 标的上继续复核。 |
| 至少 200 个有效策略族 | 完成 | readiness audit 显示 200 unique strategy_id，且目录反凑数审计已建立。 | 后续不盲目扩充低价值目录。 |
| 至少 200 个标的 | 完成 | readiness audit 显示 200 unique symbols；current-stage 也覆盖 200 Yahoo 公开行情标的。 | 替换为 Moomoo/Alipay confirmed tradable symbols。 |
| QuantLab 互通 | 完成 | QuantLab ACK valid；当前 bundle 为 external_evidence_only，可供 ReviewOnly 读取。 | QuantLab 侧审批/展示由 QuantLab 主导。 |
| 不修改数据库/只读边界 | 完成 | 所有新增产物位于 QBVS outputs；bundle 标记 writes_quantlab_database=false。 | 策略库写入必须另行用户批准。 |
| 支付宝真实基金口径 | 部分完成 | 已有交易行为画像和 proxy sensitivity；但真实基金 NAV、申赎规则、费率和到账延迟仍不完整。 | 补齐 NAV/proxy mapping 后 rerun fund-rule exact validation。 |
| Moomoo/OpenD 真实 200 标的 | 部分完成 | BRK-B provider code 已 snapshot-confirmed；但 OpenD 历史 K 线 quota 仍限制扩展。 | quota 恢复后先单标的 probe，再 replacement-to-200。 |
| 每策略百万级/极限规模 | 未完成 | Current exact public-history rows=40000; target effective tests across 200 strategies is 200000000. | 需要 distributed/resumable campaign；当前不应伪造生产级完成。 |
| 100 年跨周期 | 部分完成 | 已做跨窗口公开历史验证；但受真实数据历史长度限制，不能把不足百年的资产伪装成 100 年验证。 | 用可得长历史资产、事件窗口和随机压力测试补强。 |
| 最终完整结论与成长报告 | 部分完成 | 已有 current-stage 中文 PDF、规则卡、QuantLab bundle；最终报告需等真实 NAV/OpenD/scale gates。 | 保持阶段性报告，待数据门解除后生成最终生产级报告。 |

## 下一步最短路径

1. 当前主候选保持 ReviewOnly，不写策略库，不接实盘。
2. QuantLab 读取 12,000 exact 样本 bundle 和当前阶段 PDF 进行展示/审批流对齐。
3. OpenD quota 恢复后，只先做 `US.BRK.B` 单标的历史 K 线 probe，再做 replacement-to-200。
4. 补齐支付宝基金真实 NAV/proxy 和申赎规则后，重跑基金口径。
5. 数据门稳定后再排百万级分片 campaign。
