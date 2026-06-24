# EVA_OS｜证值智能中台

`EVA_OS` 是主系统总入口，macOS 应用显示为 `EVA_OS`。QuantLab 保留为主入口中的量化研究与回测子系统，同时承接多系统研究总线、证据治理、报告索引和独立验证入口。

## 系统定位

EVA_OS 是本地优先、证据驱动、Codex 工程化、以经济价值转化为核心目标的个人复合智能中台。它整合公司经营现金流、量化研究、政策机会、消费分析、AI 行业研究、赛事分析和 Codex 交付方法论，用统一的数据、证据、审计、报告和 Token ROI 机制，把 AI 使用转化为可复用资产、决策优势和经济收益。

## 主系统结构

| 编号 | 子系统 | 中文定位 | QuantLab 当前入口 |
| --- | --- | --- | --- |
| 01 | Executive Command Center | 总控驾驶舱 | 研究总线 |
| 02 | Token ROI Ledger | Token经济转化台账 | 研究总线 |
| 03 | Company CashFlow Command | 公司经营现金流系统 | 研究总线 |
| 04 | QuantLab | 量化研究与回测系统 | 单标的回测 |
| 05 | Policy Intelligence Radar | 政策机会情报系统 | 行研报告 |
| 06 | Consumption Guard | 个人消费止血系统 | 个人画像 |
| 07 | AI Research Engine | AI行业研究系统 | 行研报告 |
| 08 | Sports Market Lab | 赛事市场分析系统 | 研究总线 |
| 09 | CodexForge Factory | Codex工程交付工厂 | 研究总线 |

## 共享底座

| 底座 | 中文 | 规则 |
| --- | --- | --- |
| Evidence Layer | 证据层 | 所有输入必须进入证据层。 |
| Data Layer | 数据层 | 所有数据必须记录来源、时间、质量状态和限制条件。 |
| Market Event Layer | 事件驱动行情层 | 行情输入先转成可排序、可去重、可落盘的事件，再供回放、数据湖和模拟内核使用。 |
| Reproducible Data Lake | 可复现数据湖 | 不可变数据资产必须有 manifest、checksum、partition 和 replay cursor。 |
| Event Replay | 事件回放 | 回测和模拟内核必须从确定性 replay batch 读取事件，而不是直接散读原始文件。 |
| Decision Layer | 决策层 | 所有结论必须经过风控层，并在证据不足时降级。 |
| Engineering Layer | 工程层 | 所有系统必须经过 Codex 工程层、测试和可复跑验收。 |
| Value Layer | 价值层 | 所有产出必须进入 Token ROI 台账。 |

当前 Value Layer 的最小实现见 `docs/TokenROI.md`。它会把本地审计、报告、RunMetadata、数据质量和交叉校验产物登记到 `data/value/EVATokenROILedger_latest.*`，但不会在缺少真实金额时伪造收益或 ROI。

当前公司经营现金流系统见 `docs/CompanyCashFlowCommand.md`。它把现金余额、收入、支出、应收和应付记录成可复核证据，输出 `data/cashflow/CompanyCashFlowCommand_latest.*`，但不连接银行、支付或会计系统，也不会执行付款。

当前政策机会情报系统见 `docs/PolicyIntelligenceRadar.md`。它把政策来源、影响行业、机会类型和影响评分整理为 `data/policy/PolicyIntelligenceRadar_latest.*`，但不自动抓取实时政策，不提交申请，不生成法律、税务、合规或投资结论。

当前个人消费止血系统见 `docs/ConsumptionGuard.md`。它把消费事件、账单证据、冲动风险、固定成本和可投资现金流压力整理为 `data/consumption/ConsumptionGuard_latest.*`，但不连接支付宝、银行、工资、税务、券商或支付系统，也不执行付款或投资操作。

当前 Executive Command Center 的实现见 `docs/ExecutiveCommandCenter.md`。它聚合 Daily Readiness、Integration Audit、Data Trust、Token ROI、Company CashFlow Command、Policy Intelligence Radar、Consumption Guard 和最新报告，输出 `ReadyForResearch`、`NeedsReview` 或 `Blocked`，并生成统一行动队列。

当前事件驱动行情层的最小实现见 `docs/MarketEventLayer.md`。它把 Sample 或本地 CSV 的 OHLCV bar 转成 `data/marketEvents/MarketEventLog_latest.*`，为后续可复现数据湖、事件回放和三模式回测/模拟内核提供统一事件契约；它不连接实时行情、不启动 Moomoo OpenD、不推 Kafka、不写 QuestDB/ClickHouse、不连接实盘。

当前可复现数据湖的最小实现见 `docs/ReproducibleDataLake.md`。它扫描本地不可变 event JSONL 和结构化 bar cache，生成 `data/dataLake/DataLakeManifest_latest.*`、资产 checksum、分区摘要和 replay cursor；它不复制数据、不联网、不写外部数据库。

当前事件回放的最小实现见 `docs/EventReplay.md`。它读取 `DataLakeManifest_latest.*` 和不可变 `MarketEventLog_*.jsonl`，生成 `data/replay/EventReplay_latest.*`，为后续 Vectorized Research、Discrete Event Simulation 和 Agent Market Simulation 三模式内核提供确定性事件输入；它不模拟订单、不连接实盘、不连接外部数据库。

## 启动入口

| 位置 | 路径 |
| --- | --- |
| 桌面 | `/Users/linzezhang/Desktop/EVA_OS.app` |
| Downloads | `/Users/linzezhang/Downloads/EVA_OS.app` |
| Applications | `/Applications/EVA_OS.app` |

如果需要重建入口，运行：

```bash
/Users/linzezhang/Documents/Codex/2026-06-13/files-mentioned-by-the-user-eva/outputs/CodexFinance/scripts/installMacAppLaunchers.sh
```

总控报告命令：

```bash
/Users/linzezhang/Documents/Codex/2026-06-13/files-mentioned-by-the-user-eva/outputs/CodexFinance/scripts/commandCenter.sh --output-dir data/commandCenter
```

## 风险边界

EVA_OS 只做研究、分析、验证、复盘、报告和任务编排。系统禁止接入实盘交易，禁止真实下单，禁止自动下注，禁止自动付款，禁止保存真实交易账户密码。

所有结论必须通过证据层、数据层、决策层和风险闸门后，才能作为研究参考；缺少关键证据时，只能输出观察、继续研究、需要更多证据或暂停使用。
