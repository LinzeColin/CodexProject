# Handbook

如果只是日常启动、更新持仓、运行回测、查报告或同步系统，先读 `QuickStart.md`。

本手册用于深入解释功能、公式、策略逻辑、参数扫描、报告阅读、风险闸门和复盘方法。

## Purpose

PFIOS 是一个个人量化研究平台，用于学习策略逻辑、运行历史回测、比较参数、保存实验记录和导出研究报告。

PFIOS is a personal quantitative research platform for learning strategy logic, running historical backtests, comparing parameters, saving experiment records, and exporting research reports.

它不是交易软件，不会连接实盘账户，也不会提交真实订单。

It is not trading software, does not connect to live brokerage accounts, and does not submit real orders.

## Daily Use

第一步，启动工作台。

Step one, start the workspace.

最快方式：双击 `PFI_OS.app`。

Fastest way: double-click `PFI_OS.app`.

```text
~/Desktop/PFI_OS.app
~/Downloads/PFI_OS.app
/Applications/PFI_OS.app
```

如果只想快速了解系统状态、数据源配置和报告资产数量，运行日常检查脚本。

If you only want a quick view of system status, data provider configuration, and report asset counts, run the daily check script.

```bash
$PFI_OS_HOME/scripts/dailyCheck.sh
```

如果同时想验证联网数据源，加上 `--network`。

If you also want to validate network data providers, add `--network`.

```bash
$PFI_OS_HOME/scripts/dailyCheck.sh --network
```

联网日常检查会继续运行后续诊断，即使某个第三方数据源临时断开。

The network daily check continues later diagnostics even if one third-party provider disconnects temporarily.

如果只想检查 Moomoo 是否具备只读行情条件，运行 Moomoo 诊断脚本。

If you only want to check whether Moomoo is ready for quote-only data, run the Moomoo diagnostic script.

```bash
$PFI_OS_HOME/scripts/checkMoomoo.sh
```

诊断脚本只检查 `futu-api`、Moomoo OpenD 端口和历史 K 线行情，不会调用交易接口、不会提交订单、不会保存券商账户密码。

The diagnostic script checks only `futu-api`, the Moomoo OpenD port, and historical K-line quote data. It does not use trading APIs, submit orders, or store brokerage passwords.

如果 moomoo 桌面程序已经打开但诊断仍显示 `NeedsOpenD`，说明 OpenD 服务没有监听 `11111` 端口，需要单独启动 OpenD。

If the moomoo desktop app is open but the diagnostic still shows `NeedsOpenD`, the OpenD service is not listening on port `11111` and must be started separately.

macOS 应用入口会自动打开浏览器。`/Applications/PFI_OS.app` 可以放入 Dock，也会出现在 Launchpad。

The macOS app launcher opens the browser automatically. `/Applications/PFI_OS.app` can be kept in the Dock and appears in Launchpad.

如果默认端口 `8501` 被占用，启动文件会自动换到下一个可用端口。

If default port `8501` is busy, the launcher automatically switches to the next available port.

也可以在终端运行。终端脚本不会自动打开浏览器。

You can also run it in Terminal. The terminal script does not open a browser automatically.

```bash
$PFI_OS_HOME/scripts/startPFIOS.sh
```

如果 PFIOS 已经在运行，启动应用会复用现有服务并重新打开工作台，不会重复启动第二个服务。

If PFIOS is already running, the app launcher reuses the existing service and reopens the workspace instead of starting a second service.

`.app` 启动不会弹出 Terminal 窗口。关闭浏览器页面后，后台服务会在心跳超时后自动停止并释放内存；默认容错为 120 秒，避免页面短暂卡顿或电脑休眠导致误关闭。启动日志保存在 `data/cache/pfi_os_macos_app.log`。

The `.app` launcher does not open a Terminal window. After the browser page is closed, the background service stops after the heartbeat timeout and releases memory; the default tolerance is 120 seconds to avoid accidental shutdown during short freezes or sleep. Launch logs are saved to `data/cache/pfi_os_macos_app.log`.

如果要重新生成三个 `.app` 或替换图标，先修改 `assets/PFIOSAppIconConfig.json`，再运行安装脚本。

To rebuild the three `.app` launchers or update the icon, edit `assets/PFIOSAppIconConfig.json` first, then run the installer script.

```bash
$PFI_OS_HOME/scripts/installMacAppLaunchers.sh
```

需要停止 PFIOS 时，双击停止文件。

When you need to stop PFIOS, double-click the stop file.

```text
$PFI_OS_HOME/StopPFIOS.command
```

如果只想检查 PFIOS 是否在运行，使用状态脚本。它不会打开浏览器。

If you only want to check whether PFIOS is running, use the status script. It does not open a browser.

```bash
$PFI_OS_HOME/scripts/statusPFIOS.sh
```

如果只想检查 Desktop、Downloads 和 Applications 的 `PFI_OS.app` 入口是否正常，先运行轻量验收。它不会运行完整 smoke。

If you only want to check whether the Desktop, Downloads, and Applications `PFI_OS.app` entries are valid, run lite acceptance first. It does not run full smoke.

```bash
$PFI_OS_HOME/scripts/macosAppAcceptanceLite.sh --summary-json
```

如果想检查启动、停止、自动关闭、缓存清理保护和 UI allowlist，运行生命周期只读验收。它不会启动服务、停止服务或删除缓存。

If you want to check start, stop, auto-shutdown, cache-clean guards, and UI allowlist, run read-only lifecycle readiness. It does not start, stop, or delete cache.

```bash
$PFI_OS_HOME/scripts/macosLifecycleReadiness.sh --summary-json
```

如果想真实启动并停止本地服务做闭环验收，运行受控运行验收。它不会打开浏览器，且默认发现已有服务时会拒绝继续，避免误停当前工作台。

If you want to actually start and stop the local service for loop acceptance, run controlled runtime acceptance. It does not open a browser and fail-closes by default when an existing service is already running.

```bash
$PFI_OS_HOME/scripts/macosRuntimeAcceptance.sh --summary-json
```

如果想完整验收系统，运行验收脚本。它不会打开浏览器，建议只在发布闸门或完整验收时使用。

If you want to fully verify the system, run the verification script. It does not open a browser and should be reserved for release gates or full acceptance.

```bash
$PFI_OS_HOME/scripts/verifyPFIOS.sh
```

如果只想快速确认报告链路是否正常，运行样例报告脚本。它会生成 Sample 数据的 Word 研究报告、数据质量报告和运行元数据，不会打开浏览器。

If you only want to confirm the report pipeline quickly, run the sample report script. It generates a Word research report, data quality report, and run metadata from Sample data without opening a browser.

```bash
$PFI_OS_HOME/scripts/createSampleReport.sh
```

第二步，选择研究页面，例如单标的回测、组合回测或参数扫描。

Step two, choose a research page such as single backtest, portfolio backtest, or parameter scan.

打开后先查看 `系统自检 System Health`。如果出现 `Review`，先检查启动脚本、报告目录或安全声明。

After opening it, first review `系统自检 System Health`. If `Review` appears, check launch scripts, report directory, or the safety statement first.

首页的 `工作台状态 Workspace Status` 会把自检结果总结成一句可执行说明。

`工作台状态 Workspace Status` on the home page summarizes system checks into one actionable sentence.

首页的 `快速路径 Quick Paths` 用于决定下一步：验证单个标的、比较参数、查找报告或管理策略研究。

`快速路径 Quick Paths` on the home page helps choose the next step: validate one symbol, compare parameters, find reports, or manage strategy research.

首页的 `日常使用 Runbook` 是每日固定流程。先检查系统状态，再用样例数据确认系统能生成报告，然后接入真实数据和多源校验，最后只使用通过风险闸门的研究结果。

`日常使用 Runbook` on the home page is the fixed daily process. Check system status first, confirm report generation with sample data, then use real data and cross-source validation, and finally use only research results that pass the risk gate.

Runbook 的通过规则：

Runbook pass rules:

1. 启动前没有 `Review` 项。
2. 首次运行能够生成 Word 报告、图表、数据质量文件和运行元数据。
3. 真实数据的数据质量为 `Pass` 或 `Info`，多源交叉校验差异在阈值内。
4. 研究决策前确认策略已确认、成本后仍有效、最大回撤可以接受、失效条件已写入报告。

1. No `Review` items before start.
2. The first run generates a Word report, charts, data quality file, and run metadata.
3. Real-data quality is `Pass` or `Info`, and cross-source validation difference stays within tolerance.
4. Before using a result as research input, confirm strategy approval, cost-adjusted effectiveness, acceptable maximum drawdown, and documented failure conditions.

第三步，选择市场、标的、时间区间、策略和参数。

Step three, choose market, symbol, date range, strategy, and parameters.

结束日期旁边的 `今天 Today` 按钮会把结束日期快速设置为今天。

The `今天 Today` button next to end-date fields quickly sets the end date to today.

周期可以从分钟级到年线选择，包括 `1min`、`5min`、`15min`、`30min`、`60min`、`1d`、`1w`、`1m`、`1q` 和 `1y`。

Intervals can be selected from minute-level to yearly bars, including `1min`, `5min`, `15min`, `30min`, `60min`, `1d`, `1w`, `1m`, `1q`, and `1y`.

当真实数据源不原生支持目标周期时，系统会使用可用的较低周期数据在本地重采样；例如年线可能由月线或日线汇总得到。

When a real data provider does not natively support the target interval, PFIOS resamples from an available lower interval locally; for example, yearly bars may be aggregated from monthly or daily bars.

遇到本地重采样时，数据质量报告的 notes 字段会说明基础周期。

When local resampling is used, the data quality report records the base interval in the notes field.

单标的回测页已经按流程拆成四步：选择数据、选择策略、运行回测、复核风险。

The single backtest page is split into four workflow steps: choose data, choose strategy, run backtest, and review risk.

第一次使用时，建议使用默认的 `Sample`、`US`、`AAPL`、`1d` 和 `MA Crossover`。

For first use, use the defaults: `Sample`, `US`, `AAPL`, `1d`, and `MA Crossover`.

功能区现在按日常研究价值顺序排列，并新增 `热点分析`。主功能区不再提供独立 `策略变更确认` 和 `使用指导` 页面；策略确认保留在 `策略库` 内，功能导航和 `使用指导` 改为左侧侧栏，方便一边阅读一边操作。

Workspace areas are ordered by daily research value and now include `热点分析`. The main workspace no longer has standalone `策略变更确认` or `使用指导` pages; strategy confirmation remains inside `策略库`, and navigation plus `使用指导` have moved to the sidebar so they can stay visible while operating.

左侧 `使用指导` 会自动匹配当前功能区，也可以手动切换其他功能区。它集中整理用途、适用场景、最短操作路径、手把手步骤、关键检查点、产出位置、风险和常用术语悬停说明。建议实际使用时保持侧栏展开，一边按主页面操作，一边用侧栏检查是否漏掉数据源、样本长度、失败对象或风险闸门。

The sidebar guide follows the current workspace area and can also be switched manually. It centralizes purpose, best use cases, step-by-step instructions, checkpoints, outputs, risks, and hover-style term explanations.

热点分析先看 `热点证据闸门`，再看时间轴、热力图和气泡图。闸门会检查数据源、覆盖率、失败率、样本长度、时间切片、刷新粒度、数据新鲜度和热度集中度；只要出现 Review 或 Block，就把结论降级为研究观察。

The hotspot area starts with an evidence gate before the timeline, heatmap, and bubble chart. If any gate row is Review or Block, downgrade the result to research observation.

情绪分析和热点分析中的 `展示开始日期` 不是指标计算起点。系统会自动向前取预热数据，用稳定的历史上下文计算 RSI、波动、回撤、情绪分和热点热度，再只展示你选择的日期范围。同一目标日期或时间切片不应因为展示开始日期不同而大幅变化。热点分析默认看 `平滑热度`，同时保留 `即时热度` 和 `热度变化` 用于追溯短线异动。

In sentiment and hotspot analysis, the display start date is not the indicator calculation start. PFIOS fetches an earlier warm-up window for stable RSI, volatility, drawdown, sentiment, and heat calculations, then displays only the selected range.

高级策略参数和成本参数默认折叠，跑通第一份报告后再逐项调整。

Advanced strategy parameters and cost settings are collapsed by default; adjust them one by one after the first report is generated.

如果使用真实数据源，请先确认数据源、标的格式、时间范围和数据质量报告。

If you use a real data provider, first confirm the provider, symbol format, date range, and data quality report.

单标的回测和数据工具支持联网模糊搜索标的。选择市场后，输入 `A` 可以搜索 A 开头或相关的美股，输入 `1` 可以搜索包含 1 的 A 股或港股代码。

Single backtest and data tools support online fuzzy symbol search. After selecting a market, entering `A` can search related US tickers, and entering `1` can search A-share or HK symbols containing 1.

进入 `数据工具 Data Tools` 后，先查看 `数据源状态 Data Provider Status`。

After opening `数据工具 Data Tools`, first review `数据源状态 Data Provider Status`.

`Ready` 表示本地配置已满足基础条件。

`Ready` means local configuration meets basic requirements.

`NeedsConfig` 表示需要配置对应环境变量，例如 `TUSHARE_TOKEN`、`ALPHA_VANTAGE_API_KEY` 或 `POLYGON_API_KEY`。

`NeedsConfig` means the related environment variable is required, such as `TUSHARE_TOKEN`, `ALPHA_VANTAGE_API_KEY`, or `POLYGON_API_KEY`.

这些 key 可以填在 `$PFI_OS_HOME/.env`。变量名参考 `.env.example`，不要把 key 写进代码、报告或聊天消息。

These keys can be placed in `$PFI_OS_HOME/.env`. Use `.env.example` for variable names, and do not write keys into code, reports, or chat messages.

A 股可以输入 `000001`、`SZ000001` 或 `000001.SZ`，系统会转换成 AKShare 和 TuShare 需要的格式。

For A-shares, you can enter `000001`, `SZ000001`, or `000001.SZ`; the system converts it to AKShare and TuShare formats.

第四步，运行回测并检查收益、回撤、交易记录、费用和报告路径。

Step four, run the backtest and review return, drawdown, trades, costs, and report path.

运行后先看 `结果判读 Result Interpretation`。

After running, review `结果判读 Result Interpretation` first.

`相对买入持有 Versus Buy And Hold` 用于判断策略是否只是跟随市场上涨。

`相对买入持有 Versus Buy And Hold` helps judge whether the strategy merely followed market appreciation.

`最大回撤 Maximum Drawdown` 用于判断亏损深度是否需要关注。

`最大回撤 Maximum Drawdown` helps judge whether the loss depth needs attention.

结果判读里的回撤会显示“策略最大回撤相比买入持有最大回撤为 xxx%”。正数表示策略回撤更小，负数表示策略回撤更大；核心指标里的最大回撤表示策略自身最大回撤。

The drawdown interpretation shows "strategy max drawdown versus buy-and-hold max drawdown is xxx%". Positive means the strategy drawdown is smaller, negative means it is larger; the key metric max drawdown refers to strategy max drawdown.


`交易摩擦 Trading Friction` 用于判断手续费、滑点和冲击成本是否过高。

`交易摩擦 Trading Friction` helps judge whether commission, slippage, and market impact are too high.

滑点基点表示成交价相对开盘价的不利偏移，1 个基点等于 0.01%。

Slippage bps means unfavorable execution price movement versus the open price. 1 bp equals 0.01%.

冲击成本基点表示你的交易本身推动价格造成的额外成本，通常与成交规模和流动性有关。

Market impact bps means extra cost caused by your own order moving the price, usually related to order size and liquidity.

系统不支持做空，回测会把持仓限制为非负。

The system does not support short selling, and backtests constrain positions to non-negative holdings.

第五步，检查数据质量报告，确认数据不是空数据、没有重复时间戳、关键字段没有缺失。

Step five, review the data quality report to confirm that data is not empty, timestamps are not duplicated, and required fields are not missing.

第六步，打开 Word 研究报告，先看数据质量摘要和多源交叉校验摘要，再看策略收益、买入持有基准、回撤和交易记录。

Step six, open the Word research report and review the data quality summary and cross-source validation summary before reading strategy return, buy-and-hold benchmark, drawdown, and trades.

组合回测页面会显示 `组合归因 Portfolio Attribution`，用于检查单一标的是否过度集中、交易成本是否集中在少数标的、期末持仓是否符合预期。

The portfolio backtest page shows `组合归因 Portfolio Attribution` to check whether exposure is overly concentrated, costs are concentrated in a few symbols, and ending holdings match expectations.

策略库页面可以直接新增自定义策略、编辑候选策略档案、编辑内置策略档案，并编辑内置策略默认参数。新增策略时只需要输入中文名称，选择策略逻辑、指标组合和参数设置；系统会自动生成英文名称、策略编号、类别、收益来源、研究假设、失效环境、no-code 可执行策略代码、研究档案、可运行规格 JSON 和待确认记录。

The strategy library page can create custom strategies, edit candidate profiles, edit built-in strategy profiles, and edit built-in strategy default parameters. When adding a strategy, enter the Chinese name and choose logic, indicators, and parameter settings; PFIOS automatically generates the English name, strategy id, category, return sources, thesis, failure regime, no-code executable strategy code, research profile, runnable spec JSON, and pending approval record.

内置策略 `追跌杀涨 Buy Dips Sell Rallies` 位于单标的回测的策略下拉框。它用于研究你定义的追跌杀涨式操作规则，不会连接券商账户，也不会下真实订单。

The built-in `追跌杀涨 Buy Dips Sell Rallies` strategy is available in the single-symbol backtest strategy selector. It studies your buy-dips-sell-rallies operating rule and does not connect to brokerage accounts or place real orders.

默认规则：A 股使用 `14:30` 作为收盘前半小时决策点；如果数据是日线且没有盘中时间，系统使用当日收盘价作为 14:30 决策近似。

Default rule: A-shares use `14:30` as the pre-close decision point; if the data is daily and has no intraday time, PFIOS uses the daily close as the 14:30 proxy.

买入规则：当前价格相对上一交易日收盘价下跌 `x%`，买入 `floor(abs(x%) * 100000)` 元。例子：`-3.54%` 对应买入 `3540` 元。金额按元取整，现金不足则跳过。

Buy rule: if current price is down `x%` versus the previous session close, buy `floor(abs(x%) * 100000)` yuan. Example: `-3.54%` becomes a `3540` yuan buy. Amounts are rounded down to whole yuan, and insufficient cash skips the order.

卖出规则：当天上涨且当前持仓收益率达到阈值时卖出；系统使用最高档，`10%` 卖 `1/4`，`15%` 卖 `1/2`，`20%` 全卖。

Sell rule: on an up day, sell when current position return reaches a threshold; PFIOS uses the highest reached threshold: sell `1/4` at `10%`, sell `1/2` at `15%`, and sell all at `20%`.

持仓收益率口径：由于该交易策略的展示规则不是公开回测接口，系统采用近似公式 `PositionReturn = CurrentPrice / WeightedAverageBuyCost - 1`。

Position-return definition: because the exact external display formula is not available as a backtest interface, PFIOS uses the proxy `PositionReturn = CurrentPrice / WeightedAverageBuyCost - 1`.

执行限制：一天最多执行一次、只能一个方向、不能当天买入后当天卖出、不支持 short sell。

Execution limits: at most one action per day, one direction only, no same-day buy-then-sell, and no short selling.

内置策略 `追跌杀涨增强 Buy Dips Sell Rallies Enhanced` 是为了研究“下限高、上限尽量高”的版本。它不替代原策略，而是作为可比较的增强候选。

The built-in `追跌杀涨增强 Buy Dips Sell Rallies Enhanced` strategy studies the goal of a higher floor and a higher practical ceiling. It does not replace the original strategy; it is a comparable enhanced candidate.

增强版使用 RSI、布林带、快慢均线和 MACD。RSI 或布林带显示超卖时，系统会提高低吸金额；慢均线和快均线显示弱趋势时，系统会降低低吸金额；快均线高于慢均线、价格在慢均线上方且 MACD 柱为正时，系统会小额参与上涨。

The enhanced version uses RSI, Bollinger Bands, fast/slow moving averages, and MACD. When RSI or Bollinger Bands indicate oversold conditions, PFIOS increases dip-buying size; when fast/slow moving averages indicate a weak trend, it discounts dip-buying size; when fast MA is above slow MA, price is above slow MA, and MACD histogram is positive, it makes small trend-participation buys.

增强版卖出会区分趋势状态。强趋势且未超买时，不会在原始 10% 或 15% 阈值立刻大幅卖出，而是使用强趋势延迟卖出缓冲，减少上涨行情中卖飞。

Enhanced selling depends on trend state. In a strong non-overbought trend, it does not immediately sell heavily at the original 10% or 15% thresholds; it uses a trend-hold buffer to reduce premature exits during uptrends.

使用增强版后，重点看 `核心指标对比 Core Metrics Comparison`、`市场环境分层 Market Regime Breakdown` 和 `成本压力 Cost Stress`。如果上涨环境仍明显输给买入持有，可以提高趋势参与买入倍数或提高最大仓位；如果下跌亏损扩大，应降低最大仓位或降低弱趋势买入倍数。

After using the enhanced version, focus on `核心指标对比 Core Metrics Comparison`, `市场环境分层 Market Regime Breakdown`, and `成本压力 Cost Stress`. If up-market returns still lag buy-and-hold materially, increase trend participation or max position weight; if downside loss expands, lower max position weight or reduce the weak-trend buy multiplier.

如果找不到报告，在工作台进入 `报告中心 Report Center`。

If you cannot find a report, open `报告中心 Report Center` in the workspace.

报告中心的 `总览 Dashboard` 用于快速判断研究资产是否健康：看报告类型分布、日期活动、运行收益/回撤分布、最近运行趋势、策略表现汇总和实验最佳收益。

`总览 Dashboard` in Report Center helps quickly judge whether research assets are healthy: review asset type distribution, activity by date, run return/drawdown distribution, recent run trend, strategy performance summary, and top experiment returns.

报告中心的 `报告列表 Reports` 会显示 Word 报告、运行元数据、数据质量文件和实验 summary。

`报告列表 Reports` in the report center shows Word reports, run metadata, data quality files, and experiment summaries.

你可以按报告类型、日期目录和关键词搜索报告。

You can search reports by report type, date folder, and keyword.

需要查看文件时，点击 `打开报告目录 Open Report Folder`。

When you need to inspect files, click `打开报告目录 Open Report Folder`.

报告中心的 `实验记录 Experiments` 会显示参数扫描实验、最佳 run、最佳收益和最佳夏普。

`实验记录 Experiments` in the report center shows parameter scan experiments, best run, best return, and best Sharpe.

选择一个实验后，`实验详情 Experiment Detail` 会显示最佳参数、最佳总收益、夏普、最大回撤、交易摩擦和交易次数。

After selecting an experiment, `实验详情 Experiment Detail` shows best parameters, best total return, Sharpe, maximum drawdown, trading friction, and trade count.

查看实验时不要只看总收益。应同时比较最大回撤、交易摩擦、交易次数和参数是否过度集中。

When reviewing an experiment, do not look only at total return. Compare maximum drawdown, trading friction, trade count, and whether the best parameters are overly concentrated.

参数扫描页会显示总收益、夏普和最大回撤热力图。理想情况不是只有一个格子最好，而是最佳参数附近也有较好表现。

The parameter scan page shows total-return, Sharpe, and max-drawdown heatmaps. A better result is not one isolated best cell, but a nearby region that also performs reasonably well.

参数扫描工作台现在先选择数据源、标的、周期和策略，再用 `参数名=值1,值2` 填写网格。内置策略使用普通参数名，例如 `short_window=10,20,30`；已确认自定义策略使用 `indicator.parameter=...` 覆盖策略库参数，并可用 `weight=...` 扫描仓位权重。

The parameter scan workspace now starts with provider, symbol, interval, and strategy selection, then uses `parameter=value1,value2` grid text. Built-in strategies use normal parameter names such as `short_window=10,20,30`; approved custom strategies use `indicator.parameter=...` to override strategy-library settings and can scan `weight=...`.

未确认的自定义策略不会出现在参数扫描下拉框。先到策略库补全研究假设、收益来源、失效环境、参数说明和确认状态，再进入正式扫描。

Unapproved custom strategies do not appear in the parameter-scan selector. Complete the thesis, return source, failure regime, parameter notes, and approval status in the strategy library first.

Top N 参数组合对比图用于比较最佳参数组的收益和夏普，避免只看单个最高收益。

The Top N parameter-combination chart compares return and Sharpe across the best parameter sets, reducing reliance on a single highest-return run.

参数扫描页面最下方新增 `参数扫描专业术语说明`，集中解释参数网格、短均线、长均线、总收益率、年化收益率、Sharpe、最大回撤、热力图、参数稳定性、Train-Test 验证、Walk-Forward 验证、泛化比率、过拟合和交易摩擦等概念。

The bottom of the parameter scan page now includes `参数扫描专业术语说明`, which explains parameter grids, short and long moving averages, total return, annualized return, Sharpe, maximum drawdown, heatmaps, parameter stability, Train-Test validation, Walk-Forward validation, generalization, overfitting, and trading friction.

使用参数扫描结果时，先阅读术语说明，再同时检查收益、回撤、Sharpe、稳定性、样本外验证和交易摩擦，不要只按最高收益选参数。

When using parameter scan results, read the term explanations first, then evaluate return, drawdown, Sharpe, stability, out-of-sample validation, and trading friction together. Do not select parameters only by the highest return.

单标的回测页会显示 `Bootstrap 鲁棒性 Bootstrap Robustness`。它用历史策略收益重采样生成多条模拟路径，用于观察结果在扰动下是否仍然稳健。

The single-symbol backtest page shows `Bootstrap 鲁棒性 Bootstrap Robustness`. It resamples historical strategy returns to generate simulated paths and checks whether results remain robust under perturbation.

重点看亏损概率、达到目标收益概率、模拟最大回撤分布和样本路径是否大面积跌破可接受范围。

Focus on loss probability, target-return probability, simulated max-drawdown distribution, and whether sample paths frequently fall below acceptable ranges.

Bootstrap 不是未来收益预测；它只说明历史收益序列在重排和重采样后是否脆弱。

Bootstrap is not a return forecast; it only shows whether the historical return sequence is fragile after reshuffling and resampling.

参数稳定性状态分为 `Stable`、`Watch`、`Fragile` 和 `Review`。

Parameter stability status is grouped into `Stable`, `Watch`, `Fragile`, and `Review`.

`Stable` 表示最佳参数附近和前 20% 参数整体仍然较强，但仍需要样本外验证。

`Stable` means nearby parameters and the top 20% parameter group remain reasonably strong, but out-of-sample validation is still required.

`Fragile` 表示收益可能集中在少数参数点，过拟合风险较高。

`Fragile` means performance may be concentrated around only a few parameter points, so overfitting risk is higher.

样本内/样本外验证会先用训练期选择最佳参数，再把同一组参数放到测试期回测。

Train-test validation first selects the best parameter set in the training period and then backtests the same parameter set in the test period.

泛化比率表示测试期分数相对训练期分数的比例。

Generalization ratio measures the test-period score as a percentage of the training-period score.

公式：`GeneralizationRatio = TestScore / TrainScore`。

Formula: `GeneralizationRatio = TestScore / TrainScore`.

如果测试期收益或测试期夏普明显衰减，即使训练期表现很好，也应把策略列入观察或失败。

If test-period return or test-period Sharpe decays materially, the strategy should be treated as watch or failed even if training-period performance is strong.

滚动样本外验证会把历史数据切成多个训练窗口和测试窗口，重复执行“训练期选参数，测试期验证”的流程。

Walk-forward validation splits history into multiple training windows and testing windows, repeatedly running the process of selecting parameters in training and validating them in testing.

相比单次样本外验证，walk-forward 更能发现策略只在某一段历史有效的问题。

Compared with a single train-test validation, walk-forward validation is better at finding strategies that only worked during one historical period.

如果 walk-forward 多数窗口失败，即使整体回测收益较高，也应优先视为过拟合或市场环境依赖较强。

If most walk-forward windows fail, the strategy should be treated as overfit or highly regime-dependent even if the full-period backtest return is high.

研究风险闸门和 Decision Quality Score 会输出 `ContinueResearch`、`WatchOnly`、`NeedsMoreEvidence` 或 `DoNotUse`。

The research risk gate and Decision Quality Score output `ContinueResearch`, `WatchOnly`, `NeedsMoreEvidence`, or `DoNotUse`.

Word 报告也会显示决策质量摘要和研究风险闸门。阅读报告时建议先看研究状态、质量分数、缺失证据、触发原因和研究动作，再看总收益和年化收益。

The Word report also shows Decision Quality Score and the research risk gate. When reading a report, review research status, quality score, missing evidence, triggered reasons, and research actions before total return and annualized return.

`NeedsMoreEvidence` 表示关键证据缺失，只能用于研究复盘。`DoNotUse` 表示暂停把该结果作为研究决策参考，直到数据、回撤、成本、样本外验证或 walk-forward 问题被修复。

`NeedsMoreEvidence` means critical evidence is missing and the result is only suitable for research review. `DoNotUse` means pausing the result as a research decision reference until data, drawdown, cost, out-of-sample validation, or walk-forward issues are fixed.

这不是实盘交易指令，也不会连接券商或提交订单。

This is not a live trading instruction and does not connect to brokers or submit orders.

报告中心的 `安全清理 Safe Cleanup` 只删除 `.DS_Store` 和旧 HTML 报告，不删除 Word、JSON、CSV。

`安全清理 Safe Cleanup` only deletes `.DS_Store` and legacy HTML reports. It does not delete Word, JSON, or CSV files.

## Simple Commands

`工作台状态` 下的 `macOS 生命周期` 面板会显示本机 app 入口、当前运行状态、状态检查、停止服务、缓存预览、缓存清理、轻量验收、生命周期验收、运行时验收和最终验收命令。页面内只允许执行 allowlisted 状态检查、确认后的停止服务、停止状态下的缓存清理，以及只读验收检查；启动、运行时验收和最终验收仍建议在 Terminal 或 PFI_OS.app 执行。

The `macOS Lifecycle` panel under `Workspace Status` shows app entry points, runtime status, status check, stop, cache preview, cache clean, lite acceptance, lifecycle readiness, runtime acceptance, and final acceptance commands. The page only runs allowlisted status checks, confirmed stop actions, cache cleanup when the service is stopped, and read-only acceptance/readiness checks; start, runtime acceptance, and final acceptance should still be run from Terminal or PFI_OS.app.

启动工作台。

Start the workspace.

```bash
$PFI_OS_HOME/scripts/startPFIOS.sh
```

运行测试。

Run tests.

```bash
$PFI_OS_HOME/scripts/runTests.sh
```

清理缓存。

Clean caches.

```bash
$PFI_OS_HOME/scripts/cleanCache.sh
```

预览缓存清理范围。

Preview cache cleanup scope.

```bash
$PFI_OS_HOME/scripts/cleanCache.sh --dry-run --json
```

缓存清理只覆盖 Python bytecode、pytest/tool cache、`.DS_Store` 和根 `data/cache` 运行日志；不会删除报告、持仓、导入文件、SQLite 数据库、系统迁移源码样本或市场 bar cache。

Cache cleanup only covers Python bytecode, pytest/tool cache, `.DS_Store`, and root-level `data/cache` runtime logs. It does not delete reports, holdings, imports, SQLite databases, migrated source samples, or market bar caches.

清理报告目录杂项文件。

Clean report directory junk files.

```bash
$PFI_OS_HOME/scripts/cleanReportJunk.sh
```

打开报告目录。

Open the report directory.

```bash
$PFI_OS_HOME/scripts/openReports.sh
```

## Result Interpretation

总收益表示最终权益相对初始资金的变化。

Total return measures the final equity change relative to initial cash.

公式：`TotalReturn = EndingEquity / InitialCash - 1`。

Formula: `TotalReturn = EndingEquity / InitialCash - 1`.

最大回撤表示资金曲线从历史高点到后续低点的最大跌幅。

Maximum drawdown measures the largest decline from an equity curve peak to a later trough.

公式：`MaxDrawdown = Equity / CumMax(Equity) - 1`。

Formula: `MaxDrawdown = Equity / CumMax(Equity) - 1`.

夏普比率用于衡量单位波动下的收益，但不能单独证明策略可靠。

Sharpe ratio measures return per unit of volatility, but it cannot prove strategy reliability by itself.

公式：`Sharpe = Mean(Returns) * AnnualizationPeriods / Volatility`。

Formula: `Sharpe = Mean(Returns) * AnnualizationPeriods / Volatility`.

买入持有总收益表示不使用策略，在一开始买入标的并一直持有到结束的收益。

Buy And Hold Total Return means buying the symbol at the beginning and holding it to the end without using the strategy.

公式：`BuyAndHoldTotalReturn = EndingClose / StartingClose - 1`。

Formula: `BuyAndHoldTotalReturn = EndingClose / StartingClose - 1`.

买入持有年化收益表示把买入持有总收益按 252 个交易期近似年化。

Buy And Hold Annualized Return annualizes the buy-and-hold return using 252 trading periods.

公式：`BuyAndHoldAnnualizedReturn = (1 + BuyAndHoldTotalReturn) ^ (252 / PricePeriods) - 1`。

Formula: `BuyAndHoldAnnualizedReturn = (1 + BuyAndHoldTotalReturn) ^ (252 / PricePeriods) - 1`.

## Strategy Diagnostics

策略诊断是回测结果里的第二层判断，比单纯看收益率更重要。

Strategy diagnostics are the second layer of judgment in a backtest result and are more important than looking only at return.

先看 `失效检查 Failure Checks`。如果最大回撤、交易摩擦、连续亏损、成本压力或高波动表现出现 `Review`，说明策略需要继续复核。

First check `Failure Checks`. If maximum drawdown, trading friction, consecutive losses, cost stress, or high-volatility performance shows `Review`, the strategy needs more review.

再看 `交易质量 Trade Quality`。重点看完成回合数是否足够、盈利回合占比是否稳定、盈利因子是否大于 1、连续亏损是否过长。

Then check `Trade Quality`. Focus on whether completed round trips are sufficient, profitable round-trip rate is stable, profit factor is above 1, and consecutive losses are not too long.

然后看 `成本压力 Cost Stress`。如果 2x 或 3x 成本后总收益变负，说明策略对手续费、滑点或冲击成本敏感。

Then check `Cost Stress`. If total return turns negative under 2x or 3x costs, the strategy is sensitive to commission, slippage, or market impact.

最后看 `市场环境分层 Market Regime Breakdown`。如果策略只在单一环境赚钱，例如只在上涨市场赚钱，下跌或高波动环境明显亏损，应降低对策略泛化能力的信任。

Finally check `Market Regime Breakdown`. If the strategy only works in one regime, such as up markets, and loses in down or high-volatility regimes, reduce confidence in generalization.

## Reading A Report

如果是实验研究报告，先看决策质量摘要和研究风险闸门，再看 walk-forward 状态，然后看样本外验证和参数稳定性。

For an experiment research report, first check Decision Quality Score and the research risk gate, then walk-forward status, then train-test validation and parameter stability.

不要只因为某个参数组合的收益最高就采纳它。最佳参数需要同时通过稳定性、样本外和滚动验证检查。

Do not adopt a parameter set only because it has the highest return. Best parameters should also pass stability, out-of-sample, and walk-forward checks.

## Review And Error Profile

复盘与错误画像在报告中心的“复盘错误”页签中。

Review and error profiling is in the Report Center `复盘错误` tab.

每条复盘记录会保存标的、市场、策略、研究状态、Decision Quality Score、原始研究计划、观察或执行理由、关联 Word 报告、实际执行时间、实际价格、是否按计划执行、是否违反纪律、最终盈亏、盈亏来源归因、错误类型和市场环境。

Each review record stores symbol, market, strategy, research status, Decision Quality Score, original research plan, observation or execution reason, linked Word report, actual execution time, actual price, whether the plan was followed, discipline violation, final PnL, return attribution, error type, and market environment.

错误类型包括信息错误、估值错误、时间错误、仓位错误、纪律错误、情绪错误、成本错误、数据错误、外部冲击、运气因素和无明显错误。

Error types include information error, valuation error, timing error, exposure error, discipline error, emotional error, cost error, data error, external shock, luck factor, and no obvious error.

复盘模块只记录和统计，不连接券商，不生成实盘操作指令。

The review module records and summarizes only. It does not connect to brokers and does not create live action instructions.

## Portfolio Risk View

组合轮动运行后会显示组合风险视图。

The portfolio risk view appears after a portfolio rotation run.

先看现金权重、总暴露、最大单标的权重和前三权重，判断组合是否过度集中。

First check cash weight, gross exposure, maximum single-symbol weight, and top-three weight to judge concentration.

然后看市场、货币和主题暴露，确认组合是否集中在单一国家、单一币种或单一主题。

Then check market, currency, and theme exposure to see whether the portfolio is concentrated in one country, one currency, or one theme.

最后看下跌 10%、20%、30%、50% 情景下的账户损失和回本所需涨幅，再看单一标的冲击。

Finally check account loss and rebound needed to recover under 10%, 20%, 30%, and 50% downside scenarios, then review single-symbol shock.

## Validation Task Queue

验证任务队列在报告中心的“验证任务”页签中。

The validation task queue is in the Report Center `验证任务` tab.

当行研、政策、新闻或手工研究产生一个需要 PFIOS 验证的问题时，先记录来源报告、来源段落、研究主题、待验证标的、待验证信号、样本区间、成本假设和基准。

When industry research, policy analysis, news, or manual research produces a question that needs PFIOS validation, first record the source report, source paragraph, research topic, target symbol, signal to validate, sample period, cost assumption, and benchmark.

完成回测或参数扫描后，把 Word 验证报告路径填回任务记录，状态改为已完成。

After running a backtest or parameter scan, put the Word validation report path back into the task record and mark the status as completed.

验证任务队列只管理研究问题，不生成实盘操作指令。

The validation task queue only manages research questions and does not create live action instructions.

## Industry Research Reports

`行研报告` 功能区默认读取 `~/Downloads/行研报告`。

The `行研报告` area reads `~/Downloads/行研报告` by default.

进入页面后先看报告数量、可用系统、最新报告日期和验证任务数量。

After opening the page, first check report count, ready systems, latest report date, and validation task count.

用开始日期、结束日期和关键词筛选报告。报告名中包含 `DDMMYYYY` 或 `YYYYMMDD` 时，系统会自动识别报告日期。

Filter reports by start date, end date, and keyword. When a filename contains `DDMMYYYY` or `YYYYMMDD`, the system automatically detects the report date.

选择报告后可以打开报告或打开所在目录。下方会同时显示最近 PFIOS Word 报告、验证任务和研究门禁状态。

After selecting a report, you can open the report or its folder. The lower area also shows recent PFIOS Word reports, validation tasks, and research gate status.

## Personal Profile

`个人画像` 功能区会综合持仓、回测、复盘和验证任务。

The `个人画像` area combines holdings, backtests, review records, and validation tasks.

消费行为分析系统持仓默认读取 `data/external/consumerHoldings`。PFIOS 持仓默认读取 `data/holdings`。

Consumer-analysis holdings default to `data/external/consumerHoldings`. PFIOS holdings default to `data/holdings`.

支付宝账本默认只读取项目内 `data/private/alipay`。如果要接入行研报告系统或其他私有目录，在 `.env` 中填写 `PFI_ALIPAY_LEDGER_DIR`，多个目录用英文冒号分隔。

The Alipay ledger defaults to project-local `data/private/alipay`. To connect the industry-research system or another private directory, set `PFI_ALIPAY_LEDGER_DIR` in `.env`; separate multiple directories with a colon.

同步持仓时，如果来源目录存在但没有可解析的正式持仓文件，系统会保留现有持仓簿，不会自动清空。只有你手动删除或提供新的确认持仓文件，正式持仓才会变化。

During holdings sync, if source directories exist but no parseable confirmed holdings file is found, PFIOS keeps the existing holdings book and does not clear it automatically. Confirmed holdings change only after manual deletion or a new confirmed holdings file is provided.

持仓文件支持 CSV、XLSX 和 JSON。建议字段包括代码、名称、市场、数量、市值、浮动盈亏和权重。

Holding files support CSV, XLSX, and JSON. Recommended fields include symbol, name, market, quantity, market value, unrealized PnL, and weight.

画像输出包括行为习惯、风险画像和行为优化。它用于复盘和质量控制，不输出实盘买卖指令。

Profile output includes behavior habits, risk profile, and behavior optimization. It is for review and quality control and does not output live buy or sell instructions.

先看策略库确认状态。未确认策略不应进入正式研究结论。

First check the strategy-library confirmation status. Unconfirmed strategies should not be used for formal research conclusions.

再看数据质量状态。如果数据为空、缺失值较多、重复时间戳较多或多源价格差异过大，应先修复数据问题。

Then check data quality status. If data is empty, has many missing values, has duplicated timestamps, or has large cross-source price differences, fix the data issue first.

接着比较策略收益和买入持有收益。如果策略没有明显优于买入持有，还需要继续研究费用、回撤、交易次数和参数稳定性。

Next compare strategy return with buy-and-hold return. If the strategy does not clearly outperform buy-and-hold, continue reviewing costs, drawdown, trade count, and parameter stability.

最后看图表。收益曲线用于观察增长是否平稳，回撤曲线用于观察最坏资金压力，买卖点图用于检查交易是否符合策略直觉。

Finally review the charts. The equity curve shows growth stability, the drawdown curve shows worst capital pressure, and the price and trade marker chart checks whether trades match the strategy intuition.

执行摘要里的收益对比图用于比较策略收益和买入持有收益。

The return comparison chart in the executive summary compares strategy return with buy-and-hold return.

单标的页面的核心指标现在使用表格展示，列为策略、买入持有和相对差值。

The single-symbol page now shows core metrics in a table with strategy, buy-and-hold, and relative-difference columns.

相对收益等于策略收益率减去目标走势收益率。

Relative return equals strategy return minus target price return.

胜率表示已完成买卖回合中盈利回合的占比。

Win rate means the percentage of completed round trips that ended with profit.

买入持有没有同口径的买卖回合，因此胜率显示为不适用。

Buy-and-hold has no comparable round-trip trading unit, so win rate is shown as N/A.

如果策略收益不如买入持有，或者只是略高但回撤和交易成本明显更大，应谨慎对待。

If strategy return is below buy-and-hold, or only slightly higher with materially larger drawdown and transaction costs, treat it cautiously.

## Strategy Questions

进入策略研究前，先打开 `策略库 Strategy Library`，确认策略研究假设、收益来源、失效环境和参数设置。

Before starting strategy research, open `策略库 Strategy Library` and confirm the strategy thesis, return source, failure regime, and parameter settings.

如果策略库中没有该策略，先补充策略档案并完成策略修改确认，再把它用于正式研究。

If the strategy is not in the strategy library, add a strategy profile and complete strategy change approval or confirmation before using it for formal research.

新增策略时，先在 `策略库 Strategy Library` 使用新增自定义策略。系统会根据策略逻辑、指标组合和参数设置推断类别、收益来源、研究假设和失效环境，生成 no-code 可执行代码、档案、规格 JSON 和 `Pending` 确认记录，但不会自动批准策略。

When adding a strategy, use Add Custom Strategy in `策略库 Strategy Library`. PFIOS infers category, return sources, thesis, and failure regime from strategy logic, indicator combination, and parameter settings, then creates no-code executable code, profile, spec JSON, and a `Pending` approval record, but it does not approve the strategy automatically.

生成后必须复核 no-code 信号逻辑、参数范围、失效环境、数据验证和风险说明；如果需要更复杂规则，再修改生成的策略代码，最后在 `策略库` 里手动确认当前版本。

After generation, review the no-code signal logic, parameter ranges, failure regimes, data validation, and risk notes. If more complex rules are needed, edit the generated strategy code, then manually confirm the current version inside `策略库`.

自定义策略规格永久保存到 `data/strategyLibrary/CustomStrategySpecs.json`。确认后会显示在单标的回测的策略下拉框；未确认时系统会阻止回测。

Custom strategy specs persist in `data/strategyLibrary/CustomStrategySpecs.json`. After approval they appear in the single-symbol backtest strategy selector; before approval, the system blocks backtesting.

修改自定义策略规格时，系统会保存为下一版本，写入 `data/strategyLibrary/CustomStrategySpecHistory.json`，并创建新的 `Pending` 确认记录。确认后才会作为正式研究策略运行。

When editing a custom strategy spec, PFIOS saves it as the next version, writes `data/strategyLibrary/CustomStrategySpecHistory.json`, and creates a new `Pending` approval record. It can run as a formal research strategy only after confirmation.

修改后，系统会同步更新 `src/pfi_os/strategies/custom/*.py` 的对应策略代码文件。这样从工作台运行和从策略代码运行会使用同一版本。

After editing, PFIOS synchronizes the matching strategy code file under `src/pfi_os/strategies/custom/*.py`. This keeps workbench execution and direct strategy-code execution on the same version.

Word 回测报告会读取自定义策略规格，不会再用“未知策略”的默认解释覆盖自定义策略的收益来源、研究假设和失效环境。

Word backtest reports read custom strategy specs and no longer replace custom strategy return sources, thesis, and failure regime with the default unknown-strategy explanation.

如果只是查看当前版本，可以在策略库打开 `当前版本确认 Current Version Approval`；如果要确认，点击 `确认当前版本 Approve Current Version`。

To review the current version, open `当前版本确认 Current Version Approval` in the strategy library. To confirm it, click `确认当前版本 Approve Current Version`.

内置策略档案编辑会永久保存到 `data/strategyLibrary/StrategyProfileOverrides.json`。删除该文件可回到系统默认内置策略档案。

Built-in strategy profile edits persist in `data/strategyLibrary/StrategyProfileOverrides.json`. Delete that file to return to default built-in strategy profiles.

内置策略默认参数编辑会永久保存到 `data/strategyLibrary/BuiltInStrategyParameters.json`。保存或恢复默认参数时必须勾选确认，系统会写入一条策略变更确认记录。单标的回测页面会自动读取这些默认参数。

Built-in strategy default parameter edits persist in `data/strategyLibrary/BuiltInStrategyParameters.json`. Saving or resetting default parameters requires confirmation and creates a strategy-change confirmation record. The single-symbol backtest page automatically reads these default parameters.

如果某个内置参数组合手工改坏，系统会回退到源码系统默认值，避免工作台因为错误参数无法打开。删除 `BuiltInStrategyParameters.json` 可恢复全部内置策略默认参数。

If a built-in parameter set is manually corrupted, PFIOS falls back to the source-code system defaults so the workspace can still open. Delete `BuiltInStrategyParameters.json` to restore all built-in strategy default parameters.

策略库中的 `策略顺序设置` 可以调整内置策略展示顺序，并同步更新单标的回测里的默认策略下拉顺序。顺序会永久保存到 `data/strategyLibrary/StrategyOrder.json`。

The `策略顺序设置` section in the strategy library changes the built-in strategy display order and synchronizes the default strategy selector order in single-symbol backtests. The order persists in `data/strategyLibrary/StrategyOrder.json`.

使用 `上移`、`下移` 调整顺序；使用 `恢复默认顺序` 可以回到系统默认顺序。组合轮动策略会在策略库中显示，但不会出现在单标的回测策略下拉中。

Use `上移` and `下移` to adjust order; use `恢复默认顺序` to return to the system default. Portfolio rotation appears in the strategy library but does not appear in the single-symbol strategy selector.

策略库中的 `Candidate` 只表示候选档案可审查，不表示策略已经批准。

`Candidate` in the strategy library only means the profile is available for review. It does not mean the strategy is approved.

`ReadyForReview` 只表示候选档案字段完整，不表示策略有效、盈利或已经确认。

`ReadyForReview` only means the candidate profile fields are complete. It does not mean the strategy is effective, profitable, or approved.

如果显示 `Incomplete`，先补齐缺失项，再进入代码审查、数据验证和确认确认。

If it shows `Incomplete`, complete the missing items before code review, data validation, and approval confirmation.

`CodeDraft` 表示策略代码仍像模板草稿，可能是空仓逻辑、缺少核心结构或缺少参数校验提示。

`CodeDraft` means the strategy code still looks like a draft template, may contain flat logic, miss core structure, or miss parameter validation hints.

`CodeReadyForReview` 只表示代码结构达到审查起点，不表示策略已经确认或能够盈利。

`CodeReadyForReview` only means the code structure is ready to be reviewed. It does not mean the strategy is approved or profitable.

综合状态 `NotReady` 表示档案、代码、smoke test 或确认至少有一项未达标。

Readiness status `NotReady` means at least one of profile, code, smoke test, or approval is not ready.

综合状态 `ReadyForReview` 表示档案和代码可以进入人工审查，但还没有确认通过。

Readiness status `ReadyForReview` means profile and code can enter manual review, but approval is not complete.

综合状态 `ApprovedForResearch` 表示档案、代码、smoke test 和确认均通过，可以进入受控研究验证，但仍然不是实盘交易许可。

Readiness status `ApprovedForResearch` means profile, code, smoke test, and approval passed, so controlled research validation can start, but it is still not live trading permission.

`SmokePass` 只表示策略代码能在 Sample 数据上产出合法信号和目标权重，不表示策略有收益。

`SmokePass` only means the strategy code can produce valid signals and target weights on Sample data. It does not mean the strategy is profitable.

`SmokeFail` 表示代码运行异常、信号为空、缺少必要字段、权重缺失，或目标权重超出 `[-1.00, 1.00]`。

`SmokeFail` means code raised an error, signals are empty, required fields are missing, weights are missing, or target weights are outside `[-1.00, 1.00]`.

确认前可以在策略库导出候选策略审查报告，把档案质量、代码质量、smoke test、综合门禁和确认记录保存为 Word 留痕。

Before confirmation, export the candidate strategy review report from the strategy library to preserve profile quality, code quality, smoke test, readiness gate, and confirmation records in Word.

每个策略都必须回答：我赚的是什么钱？

Every strategy must answer: what money does it try to earn?

每个策略都必须回答：这个规律为什么会长期存在？

Every strategy must answer: why might this pattern persist?

每个策略都必须回答：数据是否支持？

Every strategy must answer: does the data support it?

每个策略都必须回答：扣除手续费、滑点和冲击成本后是否仍有效？

Every strategy must answer: is it still effective after fees, slippage, and market impact?

当前回测模型已经包含佣金、滑点和冲击成本基点。

The current backtest model includes commission, slippage, and market impact basis points.

公式：`ExecutionPrice = OpenPrice * (1 + TradeSide * (SlippageBps + MarketImpactBps) / 10000)`。

Formula: `ExecutionPrice = OpenPrice * (1 + TradeSide * (SlippageBps + MarketImpactBps) / 10000)`.

公式：`CommissionCost = Max(Abs(Notional) * CommissionRate, MinimumCommission)`。

Formula: `CommissionCost = Max(Abs(Notional) * CommissionRate, MinimumCommission)`.

公式：`ModeledTradingFriction = CommissionCost + SlippageCost + MarketImpactCost`。

Formula: `ModeledTradingFriction = CommissionCost + SlippageCost + MarketImpactCost`.

每个策略都必须回答：最大回撤能不能接受？

Every strategy must answer: is maximum drawdown acceptable?

每个策略都必须回答：什么市场环境下会失效？

Every strategy must answer: when might it fail?

每个策略都必须回答：失效后系统如何停止交易？

Every strategy must answer: how should the system stop after failure?

PFIOS 只研究不实盘，因此这里的停止交易表示停止研究使用、停止把该策略作为决策参考，而不是向券商发送指令。

PFIOS is research-only, so stop trading here means stopping research use and stopping decision-reference use, not sending broker instructions.

## Return Sources

风险溢价：承担别人不愿承担的风险，例如小盘、价值、波动率、期限结构。

Risk premium: taking risks others are unwilling to take, such as size, value, volatility, and term structure.

行为偏差：利用市场参与者非理性，例如追涨杀跌、反应不足、过度反应。

Behavioral bias: exploiting irrational market behavior, such as trend chasing, underreaction, and overreaction.

信息优势：更快、更系统地处理信息，例如公告、财报、新闻、产业链数据。

Information advantage: processing information faster or more systematically, such as announcements, earnings reports, news, and supply chain data.

结构性约束：利用机构限制或市场制度，例如指数调仓、资金流、期货展期。

Structural constraint: using institutional limits or market rules, such as index rebalancing, capital flows, and futures roll.

执行优势：更低成本、更优成交，例如拆单、限价、滑点控制。

Execution advantage: lower cost or better execution, such as order splitting, limit orders, and slippage control.

组合优势：不靠单笔交易，而靠多因子、多资产、多策略分散。

Portfolio advantage: relying on diversified factors, assets, and strategies rather than one trade.

## Holdings Board

持仓板块用于把支付宝账本、行研报告上传目录、消费行为分析系统和 PFIOS 本地导入文件整理为一个正式持仓簿。

The holdings board consolidates the Alipay ledger, industry-report upload directories, consumer-analysis files, and PFIOS local imports into one canonical holdings book.

第一步，进入 `持仓` 页面，点击 `同步持仓`。

Step one, open the `持仓` page and click `同步持仓`.

第二步，查看顶部卡片：持仓总市值、正式持仓数量、最大单一权重、前三权重、市场数量和待确认订单数量。

Step two, review the top cards: total position value, confirmed holding count, top single weight, top three weight, market count, and pending order count.

第三步，打开 `当前持仓`，确认代码、名称、市场、数量、持仓金额、权重、来源文件和更新时间。

Step three, open `当前持仓` and check symbol, name, market, quantity, position value, weight, source file, and update time.

第四步，打开 `待确认订单`，复核支付宝中付款成功但份额、净值或状态尚未确认的订单。这些订单不会计入正式持仓。

Step four, open `待确认订单` and review Alipay orders that are paid but not yet confirmed by units, NAV, or status. These orders are not counted as confirmed holdings.

第五步，如有缺失，到 `手动维护` 填写代码、名称、市场、数量、持仓金额、成本和浮动盈亏，保存后会写入本地持仓簿。

Step five, if data is missing, use `手动维护` to enter symbol, name, market, quantity, position value, cost, and unrealized PnL. Saving writes the record to the local holdings book.

正式持仓永久保存到 `$PFI_OS_HOME/data/holdings/HoldingsBook.json`。

Confirmed holdings are permanently saved to `$PFI_OS_HOME/data/holdings/HoldingsBook.json`.

同步历史保存到 `$PFI_OS_HOME/data/holdings/HoldingsImportHistory.json`。

Sync history is saved to `$PFI_OS_HOME/data/holdings/HoldingsImportHistory.json`.

持仓导入目录是 `$PFI_OS_HOME/data/holdings/imports`。

The holdings import directory is `$PFI_OS_HOME/data/holdings/imports`.

## Sentiment Analysis

情绪分析板块用于观察大盘、自选对象和持仓对象的短期情绪状态。

The sentiment analysis board observes short-term sentiment for market objects, custom watchlists, and holdings.

第一步，选择数据源。真实研究优先使用 Moomoo、Yahoo Finance 或 AKShare；如果真实数据源暂时不可用，可用 Sample 熟悉流程。

Step one, choose the data provider. For real research, prioritize Moomoo, Yahoo Finance, or AKShare. If real providers are unavailable, use Sample to learn the workflow.

第二步，选择市场和分析范围。`大盘默认` 会加载系统预设对象，`自选对象` 允许输入代码，`持仓对象` 会读取持仓簿里的代码。

Step two, choose market and scope. `大盘默认` loads preset objects, `自选对象` accepts typed symbols, and `持仓对象` reads symbols from the holdings book.

第三步，设置日期区间。情绪分析至少需要 30 个交易日，日常建议使用一年左右样本。

Step three, set the date range. Sentiment analysis requires at least 30 trading days, and daily use should keep roughly one year of data.

第四步，点击 `生成情绪观察`，先看对象数量、平均情绪分、偏热比例、偏冷比例、研究状态和失败对象，然后检查情绪证据闸门。

Step four, click `生成情绪观察`, then check object count, average sentiment score, hot ratio, cold ratio, research status, failed objects, and the sentiment evidence gate.

情绪证据闸门会检查数据源、对象覆盖、失败率、样本长度、数据新鲜度和情绪集中度。出现 `Review` 或 `Block` 时，先修正数据或补证据，不要把分数当成交易前参考。

The sentiment evidence gate checks data provider, object coverage, failure rate, sample length, data freshness, and sentiment concentration. If it shows `Review` or `Block`, fix data or add evidence before using the score as pre-trade research context.

第五步，看情绪卡片和情绪分对比图。重点检查 1 日涨跌、20 日涨跌、RSI、60 日最大回撤和研究解读是否一致。

Step five, review sentiment cards and the score comparison chart. Focus on whether one-day return, 20-day return, RSI, 60-day max drawdown, and research reading agree.

情绪分公式口径：基础分 50，叠加 20 日趋势、相对 20 日均线、1 日涨跌和 RSI，扣除高波动和较大回撤影响。波动率对象会反向处理，因为波动率上升通常代表风险情绪升温。

Sentiment score formula: base score 50, adjusted by 20-day trend, distance from the 20-day moving average, one-day return, and RSI, with deductions for high volatility and large drawdown. Volatility objects are inverted because rising volatility usually means risk sentiment is heating up.

情绪分析只用于研究观察，不预测未来涨跌，不生成买入、卖出或仓位建议。

Sentiment analysis is research observation only. It does not predict future price direction and does not generate buy, sell, or position-sizing advice.

## Market Hotspots

`热点分析` 用热点时间轴、热力图、气泡图和时间切片观察大盘、行业、风格、避险资产和持仓对象的短期强弱扩散。

`热点分析` observes short-term strength diffusion across market, sector, style, defensive assets, and holdings with a hotspot timeline, heatmaps, bubble charts, and time slices.

第一步，选择数据源、市场和时间粒度。`60min` 用于小时级热点，`1d` 用于日线热点。

Step one, choose data provider, market, and time granularity. `60min` is for hourly hotspots, while `1d` is for daily hotspots.

同时选择 `工作台模式`。默认 `快速预览` 会限制对象数和时间切片数，用于日常快速查看；`标准分析` 保留更多切片；`完整复盘` 适合报告前深度复核但运行更慢。

Also choose `工作台模式`. The default `快速预览` limits object count and time slices for daily review; `标准分析` keeps more slices; `完整复盘` is for deeper report-stage review and runs slower.

如需对照公开市场云图，可勾选 `显示 52ETF 公开参考`。系统只读取 `https://52etf.site/` 公开页面的板块和操作提示，不能把它当作正式行情、回测数据或交易信号。

For public market-cloud comparison, enable `显示 52ETF 公开参考`. The system reads only the public `https://52etf.site/` page for boards and operating notes; do not treat it as official market data, backtest input, or a trading signal.

如需减少页面等待，可先运行 `scripts/site52etfSnapshot.sh --output-dir data/integrations/site52etf` 生成本地 `PFIOS52ETFPublicSnapshotV1`。热点页面会优先读取 latest snapshot，缺失时才按缓存在线读取公开页面。

To reduce page waiting, run `scripts/site52etfSnapshot.sh --output-dir data/integrations/site52etf` first to generate a local `PFIOS52ETFPublicSnapshotV1`. The hotspot page prefers the latest local snapshot and only falls back to cached live fetch when it is missing.

生成热点后，页面会显示 `52ETF 与 PFI 热点对照`。该对照把 52ETF 公开 A 股云图板块映射到 PFI_OS 当前热点对象池，用于检查对象覆盖、交互口径和 UI 学习价值；如果当前市场不是 CN、公开页面不可用或映射不足，对照会降级为 Review。

After generating hotspots, the page shows `52ETF 与 PFI 热点对照`. It maps the public 52ETF A-share market-cloud boards to the current PFI_OS hotspot object pool for coverage, interaction, and UI review. If the current market is not CN, the public page is unavailable, or mapping is weak, the comparison downgrades to Review.

第二步，选择分析范围。`大盘热点` 是系统默认板块/风格代理，`我的持仓` 读取持仓簿，`自选代码` 用于临时观察。

Step two, choose scope. `大盘热点` uses preset sector/style proxies, `我的持仓` reads the holdings book, and `自选代码` is for temporary watchlists.

第三步，设置日期区间。小时级热点建议至少保留 30 个交易日，日线热点建议保留 6-12 个月。

Step three, set the date range. Hourly hotspots should keep at least 30 trading days, and daily hotspots should keep 6-12 months where possible.

第四步，使用 `时间切片` 拖动查看不同小时或日期的热点变化。页面缓存 TTL 为 3600 秒；开启自动刷新时，页面每小时刷新一次。

Step four, use `时间切片` to review different hours or dates. Page cache TTL is 3600 seconds; when auto refresh is enabled, the page refreshes hourly.

点击 `生成热点分析` 后先看 `热点运行摘要`。它显示本次请求指纹、对象覆盖、切片数量、缓存 TTL 和证据状态；同一数据源、对象、日期、粒度和工作台模式在 TTL 内复用缓存，页面不保留原始行情明细、不连接券商、不创建订单。

After clicking `生成热点分析`, review `热点运行摘要` first. It shows the request key, object coverage, slice count, cache TTL, and gate status; the same provider, objects, dates, interval, and workbench mode reuse the cached history within the TTL without retaining raw price frames, broker calls, or order creation.

热点页面还会把已计算的热点结果写入本地 `data/cache/hotspots/` 派生缓存。下次使用同一请求指纹时，即使 Streamlit 内存缓存已经失效或工作台重启，也可以在 TTL 内直接读取已计算结果，避免重复拉取行情和重算热度。该目录已被 Git 忽略，只存派生热点行和 compact metadata，不存 secrets、原始账户数据或下单信息。

The hotspot page also writes derived computed results to local `data/cache/hotspots/`. When the same request key is used again, the workbench can reuse the computed result within the TTL even after the in-memory Streamlit cache expires or the app restarts. The directory is gitignored and stores only derived hotspot rows plus compact metadata, not secrets, raw account data, or order information.

热点时间轴、热力图和气泡图使用统一研究图表交互：支持鼠标滚轮缩放、拖拽平移或框选缩放、十字光标/悬停辅助线、时间轴范围滑块、快捷区间按钮和 PNG 导出。图表交互只作用于已经生成的 compact 结果，不会重新请求行情、修改缓存 TTL、连接券商或生成订单。

The hotspot timeline, heatmap, and bubble chart use the shared research chart interaction layer: scroll zoom, pan or box zoom, crosshair-style hover spikes, timeline range slider, quick range buttons, and PNG export. Chart interaction only works on the already generated compact result; it does not refetch market data, change cache TTL, connect brokers, or create orders.

第五步，先看热力图，再看气泡图。热力图红色偏强、绿色偏弱；气泡图右上角表示近 1 期和近 5 期同步偏强，左下角表示同步偏弱。

Step five, review the heatmap first, then the bubble chart. Red means stronger and green means weaker on the heatmap; the bubble chart upper-right means both one-period and five-period returns are positive, while lower-left means both are weak.

热点热度综合近 1 期、近 5 期、近 20 期涨跌、RSI、波动和回撤。VIX 等波动率对象会反向处理，因为波动率上升通常代表风险温度上升。`即时热度` 反映单个时间切片，`平滑热度` 反映短期连续状态；优先用平滑热度判断热点是否持续。

Hotspot heat combines one-period, five-period, and twenty-period returns with RSI, volatility, and drawdown. Volatility objects such as VIX are inverted because rising volatility usually means risk temperature is rising.

热点分析只用于研究观察，不预测未来涨跌，不生成买入、卖出或仓位建议。

Hotspot analysis is research observation only. It does not predict future price direction and does not generate buy, sell, or position-sizing advice.

## Market Feel Training

`盘感训练` 用技术面指标训练读图能力。它把一个对象拆成四个模块：趋势、动能、风险和量价确认。

`盘感训练` trains chart-reading discipline with technical indicators. It splits each object into trend, momentum, risk, and price-volume confirmation.

第一步，选择数据源、市场和对象来源。对象来源可以是大盘对象、我的持仓或自选代码。

Step one, choose data provider, market, and object source. Sources can be market presets, holdings, or custom symbols.

第二步，设置日期区间。盘感训练至少需要 60 个交易日，日常训练建议保留一年以上样本。

Step two, set the date range. Market feel training requires at least 60 trading days, and daily practice should keep more than one year of data where possible.

第三步，选择训练难度。`入门` 只判断方向，适合建立读图习惯；`中等` 判断方向和收益区间，适合训练趋势幅度感；`专家` 判断方向、区间和更精确涨跌幅，适合复盘误差来源。

Step three, choose the training level. Beginner asks for direction only, intermediate asks for direction and return range, and expert asks for direction, range, and a more precise return estimate.

第四步，设置判断周期和限时秒数。系统会隐藏未来答案区间，只显示判断前已经发生的行情；开始后页面会实时自动倒计时，倒计时归零后仍可提交，但会记录为超时。

Step four, set the answer horizon and time limit. PFIOS hides the future answer window and only shows information that existed before the judgement point; after starting, the page auto-counts down, and submission still records timeout from start and submit timestamps.

第五步，按固定顺序读图：价格和 MA20/MA60 判断结构，20 日支撑/压力判断近期需求区和供给区，Bollinger 判断位置，RSI 判断强弱，MACD 判断动能变化，ATR、波动、回撤和成交量判断风险是否被确认。

Step five, read the chart in order: price and MA20/MA60 for structure, 20-day support/resistance for nearby demand and supply zones, Bollinger for location, RSI for strength, MACD for momentum change, and ATR, volatility, drawdown, and volume for risk confirmation.

第六步，提交判断后查看答案。页面会显示实际方向、实际收益区间、是否超时、得分、事前技术分析和揭示后多维复盘。

Step six, submit your judgement and reveal the answer. The page shows actual direction, actual return range, timeout status, score, pre-result technical analysis, and post-result multi-dimensional review.

事前技术分析只使用揭示前的数据。它不能根据真实结果倒推分析过程。

Pre-result technical analysis only uses data before the reveal point. It must not reverse-engineer the analysis from the actual outcome.

如果技术面倾向和实际走势不一致，系统会提示从事实面、基本面、价值面、交易面和市场环境补证据：公告、财报、政策、行业消息、盈利预期、估值分位、资金流、流动性、指数权重、汇率和风险偏好。

If technical evidence disagrees with the actual path, PFIOS prompts evidence checks across facts, fundamentals, valuation, trading flow, and market regime: announcements, earnings, policy, industry news, earnings expectations, valuation percentile, fund flows, liquidity, index weight, FX, and risk appetite.

盘感分公式口径：基础分 50，叠加价格相对 MA20/MA60、20 日和 60 日趋势、RSI、MACD 和成交量确认，扣除 Bollinger 极端位置、ATR、波动率和回撤风险。

Market feel score formula: base score 50, adjusted by price distance from MA20/MA60, 20-day and 60-day trend, RSI, MACD, and volume confirmation, with deductions for extreme Bollinger position, ATR, volatility, and drawdown risk.

训练结论只回答“当前技术结构怎么理解”和“下一步应该重点观察什么证据”。它不预测未来涨跌，不生成买入、卖出或仓位建议。

The training conclusion only explains how to read the current technical structure and what evidence should be watched next. It does not predict future price direction and does not generate buy, sell, or position-sizing advice.

## Metadata

运行元数据不是给你直接判断赚钱能力的指标，而是用于复现、审计和追踪结果来源的记录。

Run metadata is not a direct profitability metric. It is a record for reproduction, audit, and traceability.

它保留策略编号、版本、参数、初始资金、佣金、滑点、做空假设等内容。

It preserves strategy id, version, parameters, initial cash, commission, slippage, and short-selling assumptions.

当你以后看到同一个策略有不同结果时，先比较元数据，通常可以找到差异来自参数、费用、数据源或时间范围。

When the same strategy produces different results later, compare metadata first. The difference usually comes from parameters, costs, data provider, or date range.

## Safety

如果数据源、策略参数或交易成本假设不准确，回测结果可能严重偏离真实交易表现。

If data sources, strategy parameters, or transaction cost assumptions are inaccurate, backtest results may materially differ from real trading outcomes.

任何报告都只能作为研究依据，不应被视为保证收益。

Every report is research evidence only and must not be treated as guaranteed profit.
