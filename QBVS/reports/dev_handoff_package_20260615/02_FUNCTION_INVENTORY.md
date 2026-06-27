# QBVS 独立交易行为验证系统交接包

生成时间：2026-06-15 20:22:30

项目根目录：`/Users/linzezhang/Documents/Codex/2026-06-02/new-chat-2/outputs/quant_behavior_validation_system`

## 功能清单

- 交易行为策略族生成：已覆盖 200+ 个有意义的行为策略变体。
- 技术指标结合：RSI/BOLL/MA/MACD/ATR 等用于补仓、趋势持有、风控和过滤。
- exact public-history backtest：已完成 200 标的 x 200 策略的 40,000 pair 基线。
- finalist 深度验证：当前主候选及对照组完成 200 标的、多窗口验证。
- synthetic random stress：当前 3 个候选策略各 50,000 条随机路径。
- 多市场/多资产候选 universe：含 Yahoo 公开行情、Moomoo/支付宝可交易模板。
- Moomoo/OpenD 探测与 symbol alias：BRK-B provider symbol 已 snapshot-confirmed 为 US.BRK.B。
- QuantLab 外部证据包：支持 ReviewOnly bundle、manifest、candidate strategy CSV、校验命令。
- readiness audit：将用户目标拆成 passed/partial/blocked/missing。
- PDF-first 报告：当前阶段报告、随机压力报告、readiness audit PDF。
