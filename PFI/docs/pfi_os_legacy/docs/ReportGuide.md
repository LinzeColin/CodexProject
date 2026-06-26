# ReportGuide

## Report Location

报告默认保存到日期目录。

Reports are saved to a dated directory by default.

```text
~/Downloads/量化回测分析/YYYY-MM-DD/
```

## Report Contents

报告包含执行摘要、决策质量摘要、策略说明、策略研究审查、策略收益来源、研究风险闸门、核心指标、买入持有基准说明、策略诊断、收益曲线、回撤曲线、买卖点图、数据质量摘要、多源交叉校验摘要、最近交易、权益曲线尾部、运行配置与追溯信息和风险提示。

Reports include executive summary, Decision Quality Score, strategy description, strategy research review, strategy return sources, research risk gate, key metrics, buy-and-hold benchmark notes, strategy diagnostics, equity curve, drawdown curve, price and trade markers, data quality summary, cross-source validation summary, recent trades, equity curve tail, run configuration and traceability, and risk notes.

## Integrated Research Validation Standard

PFIOS is the validation layer for the integrated industry research, policy interpretation and trading advice workflow. It does not create live trading instructions and does not replace policy or industry research.

When an industry report or trading advice item asks for PFIOS validation, the report must preserve enough context to verify the idea:

- research source or policy catalyst
- target symbol, market and asset type
- proposed signal or condition to test
- sample period and out-of-sample period
- transaction cost, slippage and market impact assumptions
- benchmark and comparison group
- parameter stability result
- train-test validation result
- walk-forward validation result
- Decision Quality Score
- research risk gate status
- failure regime and deactivation condition

If any required validation evidence is missing, PFIOS output should be treated as `NeedsMoreEvidence`, not as support for actionable trading advice.

## Naming

报告文件名使用规则：`报告名称_DDMMYYYY.docx`。

Report file names use this rule: `ReportName_DDMMYYYY.docx`.

示例：`BacktestReport_03062026.docx` 和 `RunMetadata_03062026.json`。

Example: `BacktestReport_03062026.docx` and `RunMetadata_03062026.json`.

如果同一天已经存在同名报告，系统会自动把报告名称变成 `BacktestReport2_03062026.docx`，避免覆盖旧报告。

If a same-day report with the same name already exists, the system automatically uses a name such as `BacktestReport2_03062026.docx` to avoid overwriting older reports.

报告格式为 Word。

The report format is Word.

实验研究报告默认使用 `ExperimentResearchReport_DDMMYYYY.docx`。

Experiment research reports use `ExperimentResearchReport_DDMMYYYY.docx` by default.

## Executive Summary

执行摘要会提供策略收益与买入持有收益的图表对比，包括总收益和年化收益。

The executive summary provides a chart comparing strategy return with buy-and-hold return, including total return and annualized return.

这张图用于快速判断策略是否只是跟随市场上涨，还是有可能提供超过买入持有的增量价值。

This chart helps quickly judge whether the strategy merely followed market appreciation or may provide incremental value over buy-and-hold.

执行摘要中的结果判读与工作台单标的回测页面使用同一套逻辑。

The result interpretation in the executive summary uses the same logic as the single backtest page in the workbench.

## Strategy Diagnostics

策略诊断用于回答：交易质量是否稳定、交易成本升高后是否仍有效、策略在哪类市场环境下更容易失效。

Strategy diagnostics answer whether trade quality is stable, whether the strategy remains effective under higher modeled costs, and which market regimes may invalidate it.

`交易质量 Trade Quality` 会统计完成交易回合、盈利回合占比、平均单回合收益、盈利因子、盈亏比、平均持仓天数和连续亏损回合。

`Trade Quality` tracks completed round trips, profitable round-trip rate, average round-trip return, profit factor, payoff ratio, average holding days, and consecutive losing round trips.

`成本压力 Cost Stress` 会把已建模交易摩擦按 1x、2x、3x 近似放大，观察调整后总收益是否仍为正。

`Cost Stress` approximates modeled trading friction at 1x, 2x, and 3x to check whether adjusted total return stays positive.

`市场环境分层 Market Regime Breakdown` 会按上涨、下跌、震荡、高波动和低波动环境拆分策略收益、目标收益和相对收益。

`Market Regime Breakdown` separates strategy return, target return, and relative return across up, down, flat, high-volatility, and low-volatility regimes.

如果失效检查中出现 `Review`，该策略应先复核，不应直接作为交易依据。

If any failure check shows `Review`, review the strategy first and do not use it directly as trading input.

## Experiment Research Report

实验研究报告从报告中心的实验详情中导出。

Experiment research reports are exported from experiment detail in the report center.

它会汇总最佳参数、最佳运行指标、Top Runs 对比图、参数稳定性、样本内/样本外验证、walk-forward 验证、研究风险闸门和原始文件路径。

It summarizes best parameters, best run metrics, a Top Runs comparison chart, parameter stability, train-test validation, walk-forward validation, the research risk gate, and original file paths.

它还包含总收益、夏普和最大回撤参数热力图，用于判断最佳参数是否处在稳定区域。

It also includes total-return, Sharpe, and max-drawdown parameter heatmaps to judge whether the best parameter sits in a stable region.

实验研究报告用于回答“这个参数是不是偶然最优”以及“样本外是否仍然有效”。

The experiment research report helps answer whether the best parameter is accidental and whether the evidence still works out of sample.

阅读顺序建议为：研究风险闸门、walk-forward 状态、样本外状态、参数稳定性、最佳参数和 Top Runs。

The recommended reading order is research risk gate, walk-forward status, train-test status, parameter stability, best parameters, and Top Runs.

## Bootstrap Robustness

回测 Word 报告包含 Bootstrap 鲁棒性验证。

Backtest Word reports include Bootstrap robustness validation.

它使用历史策略收益重采样生成模拟路径，并展示总收益分布、最大回撤分布、样本路径、亏损概率和达到目标收益概率。

It resamples historical strategy returns to generate simulated paths, then shows total-return distribution, max-drawdown distribution, sample paths, loss probability, and target-return probability.

该部分不是未来预测，只用于检查历史回测结果在路径扰动下是否过于脆弱。

This section is not a forecast; it checks whether historical backtest results are too fragile under path perturbation.

## Candidate Strategy Review Report

候选策略审查报告从策略库的自定义策略候选详情中导出。

Candidate strategy review reports are exported from custom strategy candidate detail in the strategy library.

它会汇总候选档案质量、代码质量、smoke test、确认前综合门禁、确认记录和文件追溯。

It summarizes candidate profile quality, code quality, smoke test, pre-confirmation readiness gate, confirmation records, and file traceability.

候选策略审查报告用于确认前留痕，不证明策略收益有效。

The candidate strategy review report is an audit trail before approval. It does not prove strategy profitability.

报告中心会把候选策略审查报告识别为 `Strategy Review Report`，方便单独统计和查找。

The report center identifies candidate strategy review reports as `Strategy Review Report` for separate counting and lookup.

## Report Center Filters

报告中心的 `总览 Dashboard` 先展示研究资产的高层状态，再进入具体列表。

`总览 Dashboard` in the report center shows high-level research asset status before the detailed lists.

Dashboard 图表包括资产类型、日期活动、运行收益/回撤分布、最近运行趋势、策略表现汇总和实验最佳收益。

Dashboard charts include asset types, activity by date, run return/drawdown distribution, recent run trend, strategy performance summary, and top experiment returns.

报告中心的报告列表支持按报告类型筛选。

The report center report list supports filtering by report type.

默认显示全部研究产物。

All research artifacts are shown by default.

你可以只选择 `Backtest Word Report`、`Experiment Research Report` 或 `Strategy Review Report`，快速查找某类 Word 报告。

You can select only `Backtest Word Report`, `Experiment Research Report`, or `Strategy Review Report` to quickly find one type of Word report.

页面中的 `当前显示 Displayed` 会显示筛选后的数量和全部数量。

The `当前显示 Displayed` line shows the filtered count and the total count.

报告列表也支持按日期目录筛选，适合只查看某一天生成的报告和元数据。

The report list also supports filtering by date folder, which is useful for reviewing reports and metadata generated on one day.

搜索框支持按报告名称、报告类型、日期目录和文件路径检索。

The search box supports searching by report name, report type, date folder, and file path.

报告中心顶部会显示最新 Word 报告摘要。

The report center header shows a summary of the latest Word report.

你可以从报告中心直接打开报告根目录，或打开当前筛选结果中最新 Word 报告所在目录。

You can open the report root folder directly from the report center, or open the folder containing the latest Word report in the current filtered result.

报告中心的 `运行判读 Runs` 会从 RunMetadata 文件汇总每次回测的收益、回撤、成本占比和状态。

`运行判读 Runs` in the report center summarizes return, drawdown, cost ratio, and status from RunMetadata files.

`Pass` 表示收益为正、回撤和成本占比未触发主要关注阈值。

`Pass` means return is positive and drawdown and cost ratio did not trigger major watch thresholds.

`Watch` 或 `Review` 表示需要进一步检查，不代表自动交易信号。

`Watch` or `Review` means further inspection is required; it is not an automated trading signal.

## Strategy Research Review

每份报告都应回答七个问题。

Each report should answer seven questions.

第一，我赚的是什么钱？

First, what money does the strategy try to earn?

第二，这个规律为什么会长期存在？

Second, why might the pattern persist?

第三，数据是否支持？

Third, does the data support it?

第四，扣除手续费、滑点和当前模型内成本后是否仍有效？

Fourth, is it still effective after fees, slippage, and currently modeled costs?

当前成本模型包含佣金、滑点和冲击成本基点。

The current cost model includes commission, slippage, and market impact basis points.

公式：`ExecutionPrice = OpenPrice * (1 + TradeSide * (SlippageBps + MarketImpactBps) / 10000)`。

Formula: `ExecutionPrice = OpenPrice * (1 + TradeSide * (SlippageBps + MarketImpactBps) / 10000)`.

公式：`ModeledTradingFriction = CommissionCost + SlippageCost + MarketImpactCost`。

Formula: `ModeledTradingFriction = CommissionCost + SlippageCost + MarketImpactCost`.

第五，最大回撤能不能接受？

Fifth, is maximum drawdown acceptable?

第六，什么市场环境下会失效？

Sixth, when might it fail?

第七，失效后系统如何停止交易？

Seventh, how should the system stop after failure?

注意：PFIOS 禁止实盘交易，因此这里的停止交易是研究层面的停用条件，不是自动下单系统的交易停止指令。

Note: PFIOS prohibits live trading, so stop trading here means a research-level deactivation condition, not an automated order system instruction.

## Research Risk Gate

研究风险闸门会在 Word 报告前部给出 `ContinueResearch`、`WatchOnly`、`NeedsMoreEvidence` 或 `DoNotUse`。

The research risk gate appears near the front of the Word report and outputs `ContinueResearch`, `WatchOnly`, `NeedsMoreEvidence`, or `DoNotUse`.

`ContinueResearch` 表示当前报告没有触发主要研究停用条件，但仍需要继续监控未来数据、成本和样本外表现。

`ContinueResearch` means the current report did not trigger major research deactivation conditions, but future data, costs, and out-of-sample evidence still need monitoring.

`WatchOnly` 表示报告结果只适合作为观察线索，例如成本偏高、参数稳定性不足或验证结果进入观察区间。

`WatchOnly` means the result is only suitable as an observation lead, such as high costs, weak parameter stability, or validation results in the watch zone.

`NeedsMoreEvidence` 表示关键证据缺失，包括数据质量、多源交叉校验、参数稳定性、样本外验证或 walk-forward 验证。

`NeedsMoreEvidence` means critical evidence is missing, including data quality, cross-source validation, parameter stability, out-of-sample validation, or walk-forward validation.

`DoNotUse` 表示不要把该策略作为研究决策参考，直到触发原因被复核或修复。

`DoNotUse` means the strategy should not be used as a research decision reference until the triggered reasons are reviewed or fixed.

风险分数是加总评分，不是收益预测。

The risk score is an additive score, not a return forecast.

默认假设：最大回撤阈值为 `-25.00%`，交易摩擦占期末权益阈值为 `8.00%`。

Default assumptions: the maximum drawdown limit is `-25.00%`, and the trading friction ratio limit is `8.00%` of ending equity.

公式：`TradingFrictionRatio = TotalModeledTradingFriction / EndingEquity`。

Formula: `TradingFrictionRatio = TotalModeledTradingFriction / EndingEquity`.

如果数据质量状态不是 `Pass` 或 `Info`，风险闸门会提高风险分数并建议先复核数据。

If data quality status is not `Pass` or `Info`, the risk gate increases the risk score and suggests reviewing data first.

研究风险闸门不是实盘交易指令，不会连接券商，也不会提交真实订单。

The research risk gate is not a live trading instruction, does not connect to brokers, and does not submit real orders.

## Decision Quality Score

Decision Quality Score 用于评价一次研究结论是否足够完整，评分维度包括 Thesis 清晰度、证据质量、风险识别、退出与停用条件、暴露纪律、情绪冲动风险、反方观点质量、流动性风险、数据质量和回测验证充分度。

Decision Quality Score evaluates whether a research conclusion is complete across thesis clarity, evidence quality, risk identification, exit and deactivation conditions, exposure discipline, emotional impulse risk, counterargument quality, liquidity risk, data quality, and backtest validation sufficiency.

如果任一关键证据缺失，状态只能是 `NeedsMoreEvidence`。

If any critical evidence is missing, the status must be `NeedsMoreEvidence`.

## Report Center Review Tabs

`行研报告` 功能区按日期索引本地行研 PDF、Word 或文本报告。默认目录为 `~/Downloads/行研报告`，可用环境变量 `PFI_INDUSTRY_REPORT_DIR` 覆盖。

The `行研报告` area indexes local industry PDF, Word, or text reports by date. The default directory is `~/Downloads/行研报告`, and it can be overridden with `PFI_INDUSTRY_REPORT_DIR`.

`持仓` 功能区会同步支付宝确认持仓、行研上传持仓、消费行为分析持仓和 PFIOS 本地导入持仓，并保存到统一持仓簿 `data/holdings/HoldingsBook.json`。待确认订单和截图候选持仓单独显示，不计入正式持仓、权重或集中度。

The `持仓` area syncs confirmed Alipay holdings, industry-uploaded holdings, consumer-analysis holdings, and PFIOS local imports into `data/holdings/HoldingsBook.json`. Pending orders and screenshot candidate holdings are shown separately and are not counted in confirmed holdings, weights, or concentration.

`个人画像` 功能区优先读取统一持仓簿，再结合回测元数据、复盘记录和验证任务输出行为习惯、风险画像和行为优化。

The `个人画像` area first reads the canonical holdings book, then combines run metadata, review records, and validation tasks into behavior habits, risk profile, and behavior optimization.

持仓集中度公式：`Top1Weight = LargestHoldingValue / TotalHoldingValue`，`Top3Weight = TopThreeHoldingValue / TotalHoldingValue`，`HHI = Sum(Weight^2)`。

Holding concentration formulas: `Top1Weight = LargestHoldingValue / TotalHoldingValue`, `Top3Weight = TopThreeHoldingValue / TotalHoldingValue`, and `HHI = Sum(Weight^2)`.

`情绪分析` 功能区输出大盘默认、自选对象或持仓对象的情绪分、RSI、20 日趋势、波动率和 60 日最大回撤。情绪分析只作为研究环境观察，不进入实盘交易指令。

The `情绪分析` area outputs sentiment score, RSI, 20-day trend, volatility, and 60-day max drawdown for default market objects, custom symbols, or holdings objects. Sentiment analysis is research-environment observation only and does not become a live trading instruction.

报告中心的“验证任务”页签用于记录行研、政策、新闻或手工研究提出的待验证问题。

The Report Center `验证任务` tab records validation questions from industry research, policy analysis, news, or manual research.

验证任务字段包括来源报告、来源段落、研究主题、待验证标的、待验证信号、样本区间、成本假设、基准、当前状态和验证报告路径。

Validation task fields include source report, source paragraph, research topic, target symbol, signal to validate, sample period, cost assumption, benchmark, status, and validation report path.

报告中心的“决策质量”页签展示研究门禁状态分布、平均质量分、缺失证据数量、质量分与回测收益关系，以及优先复核列表。

The Report Center `决策质量` tab shows research gate status distribution, average quality score, missing evidence count, the relationship between quality score and backtest return, and the priority review list.

报告中心的“复盘错误”页签用于保存手工复盘记录，并统计纪律执行率、平均盈亏、最常见错误类型和错误画像。

The Report Center `复盘错误` tab stores manual review records and summarizes discipline execution rate, average PnL, most common error type, and error profile.

这些记录用于改进研究质量和复盘质量，不代表系统生成实盘操作建议。

These records are used to improve research and review quality; they do not mean the system has generated live action advice.

## Portfolio Risk View

组合轮动结果会展示组合风险视图，包含市场暴露、货币暴露、主题暴露、现金权重、总暴露、下跌情景损失、回本所需涨幅和单一标的冲击。

Portfolio rotation results show a portfolio risk view covering market exposure, currency exposure, theme exposure, cash weight, gross exposure, downside scenario loss, rebound needed to recover, and single-symbol shock.

下跌情景默认使用持仓资产同步下跌 10%、20%、30% 和 50% 的简化压力测试。

Downside scenarios use a simplified stress test where held assets fall 10%, 20%, 30%, and 50% together by default.

公式：`AccountLossRatio = PositionValue * Abs(Shock) / EndingEquity`。

Formula: `AccountLossRatio = PositionValue * Abs(Shock) / EndingEquity`.

公式：`ReboundNeeded = AccountLossRatio / (1 - AccountLossRatio)`。

Formula: `ReboundNeeded = AccountLossRatio / (1 - AccountLossRatio)`.

## Return Sources

报告中的策略研究审查和收益来源来自统一策略档案。

Strategy research review and return sources in reports come from the unified strategy profile.

如果新增策略没有策略档案，报告会提示该策略研究假设未定义。

If a new strategy has no strategy profile, the report will indicate that the strategy thesis is undefined.

收益来源分为六类：风险溢价、行为偏差、信息优势、结构性约束、执行优势和组合优势。

Return sources are grouped into six categories: risk premium, behavioral bias, information advantage, structural constraint, execution advantage, and portfolio advantage.

风险溢价表示承担别人不愿承担的风险，例如小盘、价值、波动率和期限结构。

Risk premium means taking risks others are unwilling to take, such as size, value, volatility, and term structure.

行为偏差表示利用市场参与者非理性，例如追涨杀跌、反应不足和过度反应。

Behavioral bias means exploiting irrational market behavior, such as trend chasing, underreaction, and overreaction.

信息优势表示更快、更系统地处理信息，例如公告、财报、新闻和产业链数据。

Information advantage means processing information faster or more systematically, such as announcements, earnings reports, news, and supply chain data.

结构性约束表示利用机构限制或市场制度，例如指数调仓、资金流和期货展期。

Structural constraint means using institutional limits or market rules, such as index rebalancing, capital flows, and futures roll.

执行优势表示更低成本或更优成交，例如拆单、限价和滑点控制。

Execution advantage means lower costs or better execution, such as order splitting, limit orders, and slippage control.

组合优势表示不依赖单笔交易，而依赖多因子、多资产或多策略分散。

Portfolio advantage means relying on diversified factors, assets, or strategies rather than one individual trade.

## Metrics Formatting

指标表使用中英对照。

The metrics table uses Chinese-English labels.

百分比指标保留两位小数，例如 `12.34%`。

Percentage metrics use two decimal places, such as `12.34%`.

买入持有总收益率表示从第一根可用价格买入并一直持有到最后一根价格的收益，不使用策略信号，不调仓。

Buy And Hold Total Return means buying at the first available price and holding to the last available price without strategy signals or rebalancing.

公式：`BuyAndHoldTotalReturn = EndingClose / StartingClose - 1`。

Formula: `BuyAndHoldTotalReturn = EndingClose / StartingClose - 1`.

买入持有年化收益率用于把上述收益按 252 个交易期近似年化。

Buy And Hold Annualized Return annualizes the benchmark return using 252 trading periods.

公式：`BuyAndHoldAnnualizedReturn = (1 + BuyAndHoldTotalReturn) ^ (252 / PricePeriods) - 1`。

Formula: `BuyAndHoldAnnualizedReturn = (1 + BuyAndHoldTotalReturn) ^ (252 / PricePeriods) - 1`.

## Charts

收益曲线展示策略账户权益随时间变化。

The equity curve shows how strategy account equity changes over time.

回撤曲线展示权益相对历史高点的跌幅。

The drawdown curve shows the decline from the historical equity peak.

买卖点图展示收盘价和回测成交点，仅在单标的回测且价格序列可用时生成。

The price and trade marker chart shows close prices and simulated trade points. It is generated only when a single-symbol price series is available.

## Data Quality And Cross-Source Validation

数据质量摘要用于检查数据源、标的、周期、数据行数、缺失值、重复时间戳、校验码和质量状态。

The data quality summary checks provider, symbol, interval, row count, missing values, duplicate timestamps, checksum, and quality status.

多源交叉校验摘要用于比较同一标的在多个数据源中的重叠收盘价差异。

The cross-source validation summary compares overlapping close prices for the same symbol across multiple providers.

如果质量状态为 `Review`、`Empty`、`NoOverlap` 或 `InsufficientData`，应先检查数据再解读策略结果。

If the status is `Review`, `Empty`, `NoOverlap`, or `InsufficientData`, review the data before interpreting strategy results.

## Run Configuration And Traceability

运行配置与追溯信息用于复现报告。

Run configuration and traceability information is used to reproduce the report.

它包含策略编号、策略版本、策略参数、初始资金、佣金率、滑点和是否允许做空等信息。

It includes strategy id, strategy version, strategy parameters, initial cash, commission rate, slippage, and whether short selling is allowed.

报告会先用自然语言解释这些字段，再保留原始元数据 JSON，便于人工阅读和程序复核。

The report first explains these fields in plain language and then preserves the raw metadata JSON for human review and programmatic audit.
