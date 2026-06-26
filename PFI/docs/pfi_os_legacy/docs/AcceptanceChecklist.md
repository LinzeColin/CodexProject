# Acceptance Checklist

## Daily Use

双击 `PFI_OS.app` 可以启动 PFI_OS / PFIOS。

Double-clicking `PFI_OS.app` starts PFI_OS / PFIOS.

双击 `StopPFIOS.command` 可以停止 PFIOS。

Double-clicking `StopPFIOS.command` stops PFIOS.

`scripts/statusPFIOS.sh` 可以检查运行状态且不会打开浏览器。

`scripts/statusPFIOS.sh` checks runtime status without opening a browser.

`scripts/devReadyCheck.sh --summary-json` 是日常开发默认 gate，只检查关键脚本可执行、shell/Python 语法、状态脚本、缓存 dry-run 和 git 状态；工作区未提交只记录为 `Info`，不得触发最终验收、CI smoke、完整测试、浏览器自动化、行情刷新、券商连接、策略 smoke gate、订单、付款或持仓写入。

`scripts/devReadyCheck.sh --summary-json` is the default daily development gate. It checks executable entrypoints, shell/Python syntax, status script, cache dry-run, and git status only; an uncommitted worktree is recorded as `Info`, and it must not trigger release acceptance, CI smoke, the full suite, browser automation, market refresh, broker connections, strategy smoke gates, orders, payments, or holdings writes.

`scripts/macosAcceptance.sh` 是默认用户入口；无参数时必须等价于 `--mode daily --summary-json`，合并 `devReadyCheck` 和 `macosPublicAcceptanceSummary` 的低噪音结果。`daily` 模式不得启动服务、打开浏览器、运行 final acceptance、CI smoke、full pytest、行情刷新、券商连接、订单、付款或持仓写入；`runtime`、`app-runtime` 和 `ui` 必须显式选择。

`scripts/macosAcceptance.sh` is the default user-facing entrypoint; with no arguments it must behave like `--mode daily --summary-json`, combining low-noise `devReadyCheck` and `macosPublicAcceptanceSummary` results. `daily` mode must not start services, open browsers, run final acceptance, CI smoke, full pytest, market refresh, broker connections, orders, payments, or holdings writes; `runtime`, `app-runtime`, and `ui` must be explicitly selected.

`scripts/macosAppAcceptanceLite.sh --json` 可以轻量检查 Desktop、Downloads、Applications 的 `PFI_OS.app`、native launcher、Info.plist、project binding、codesign、launcher dry-run、本地 health 和状态脚本；它不得运行 `finalAcceptanceCheck.sh`、`ciSmoke.sh`、full pytest、浏览器自动化、行情刷新、回测、券商连接、订单、付款或持仓写入。

`scripts/macosAppAcceptanceLite.sh --json` checks Desktop, Downloads, and Applications `PFI_OS.app`, native launcher, Info.plist, project binding, codesign, launcher dry-run, local health, and status script; it must not run `finalAcceptanceCheck.sh`, `ciSmoke.sh`, full pytest, browser automation, market refresh, backtests, broker connections, orders, payments, or holdings writes.

`scripts/macosLifecycleReadiness.sh --json` 可以只读检查启动、停止、heartbeat 自动关闭、缓存清理保护、UI allowlist、状态脚本、cache dry-run 和 App 轻量验收；它不得启动服务、停止服务、删除缓存、运行 `finalAcceptanceCheck.sh`、`ciSmoke.sh`、full pytest、浏览器自动化、行情刷新、回测、券商连接、订单、付款或持仓写入。

`scripts/macosLifecycleReadiness.sh --json` read-only checks start, stop, heartbeat auto-shutdown, cache-clean guards, UI allowlist, status script, cache dry-run, and App Lite Acceptance; it must not start services, stop services, delete cache, run `finalAcceptanceCheck.sh`, `ciSmoke.sh`, full pytest, browser automation, market refresh, backtests, broker connections, orders, payments, or holdings writes.

`scripts/macosRuntimeAcceptance.sh --json` 可以受控启动本地服务、检查 `/_stcore/health`、验证运行中缓存清理拒绝、停止服务、确认停止后 health 消失，并运行停止后 cache dry-run；默认发现已有服务时必须 fail-closed，避免误停当前工作台。

`scripts/macosRuntimeAcceptance.sh --json` can start the local service in controlled mode, check `/_stcore/health`, verify cache cleanup refuses while running, stop the service, confirm health disappears, and run post-stop cache dry-run; by default it must fail closed when an existing service is running to avoid stopping the current workbench.

`scripts/macosRuntimeAcceptance.sh --launch-method app --app-path ~/Downloads/PFI_OS.app --json` 必须能通过真实 `.app` 打开路径完成启动、health、缓存保护、停止和停止后复核；native launcher 必须通过本地 `/bin/zsh` 启动 `StartPFIOS.command`，不得通过 Terminal 或 GitHub fallback 启动。

`scripts/macosRuntimeAcceptance.sh --launch-method app --app-path ~/Downloads/PFI_OS.app --json` must complete start, health, cache guard, stop, and post-stop checks through the real `.app` open path; the native launcher must start local `StartPFIOS.command` through `/bin/zsh`, not route through Terminal or GitHub fallback.

工作台状态页必须显示 `macOS 生命周期` 面板，列出 Desktop、Downloads、Applications 三个 app 入口，展示启动、停止、状态、开发检查、轻量验收、生命周期验收、运行时验收、缓存清理和最终验收命令，并只读展示由 `MacOSRuntimeAcceptance_latest.json` ingest 到 private Operational Store 后生成的脱敏运行时验收 read model；页面内只允许执行 allowlisted 本地状态/停止/开发检查/轻量验收/生命周期验收/缓存清理脚本；运行时验收和最终验收只能展示命令和最近证据，不能在页面内 allowlist 执行；缓存清理必须在服务运行时自动拒绝，并展示 dry-run 候选数量和大小。

The workspace status page must show a `macOS Lifecycle` panel with Desktop, Downloads, and Applications app entry points, start/stop/status/dev-ready/lite-acceptance/lifecycle-readiness/runtime-acceptance/cache-clean/final-acceptance commands, plus the sanitized runtime acceptance read model produced after ingesting `MacOSRuntimeAcceptance_latest.json` into the private Operational Store; only allowlisted local status/stop/dev-ready/lite-acceptance/lifecycle-readiness/cache-clean scripts may run from the page; runtime acceptance and final acceptance must be displayed as commands and recent evidence only, not allowlisted in-page actions; cache cleanup must fail closed while the service is running and show dry-run candidate count and size.

`scripts/uiVisualAcceptance.sh --summary-json` 必须能用 headless Chrome 打开本机工作台并验证 `PFI_OS`、`工作台状态`、`macOS 生命周期`、`运行时验收证据` 和生命周期按钮文案可见，同时保存本地截图；它不得运行 final acceptance、CI smoke、full pytest、行情刷新、券商连接、订单、付款或持仓写入。

`scripts/uiVisualAcceptance.sh --summary-json` must open the local workbench with headless Chrome and verify visible `PFI_OS`, workspace status, macOS lifecycle, runtime evidence, and lifecycle action text while saving a local screenshot; it must not run final acceptance, CI smoke, full pytest, market refresh, broker connections, orders, payments, or holdings writes.

`scripts/macosPublicAcceptanceSummary.sh` 必须把 `MacOSRuntimeAcceptance_latest.json` 和 `UIVisualAcceptance_latest.json` 转换成 `PFIOSMacOSPublicAcceptanceSummaryV1`，输出到 `docs/evidence/`，且不得包含 `/Users/`、`/Applications/`、浏览器可执行路径、截图路径、PID、raw logs 或私有数据；它不得启动服务、打开浏览器、运行 final acceptance、CI smoke、full pytest、行情刷新、券商连接、订单、付款或持仓写入。

`scripts/macosPublicAcceptanceSummary.sh` must convert `MacOSRuntimeAcceptance_latest.json` and `UIVisualAcceptance_latest.json` into `PFIOSMacOSPublicAcceptanceSummaryV1` under `docs/evidence/` without `/Users/`, `/Applications/`, browser executable paths, screenshot paths, PIDs, raw logs, or private data; it must not start services, open browsers, run final acceptance, CI smoke, full pytest, market refresh, broker connections, orders, payments, or holdings writes.

`scripts/cleanCache.sh --dry-run --json` 可以输出结构化候选清单、文件数量、目录数量和 KB 体积；实际清理不得删除报告、持仓、导入文件、SQLite 数据库、系统迁移源码样本或市场 bar cache。

`scripts/cleanCache.sh --dry-run --json` outputs structured candidates, file count, directory count, and KB size; actual cleanup must not delete reports, holdings, imports, SQLite databases, migrated source samples, or market bar caches.

`scripts/vectorizedResearch.sh --json-only --symbol SPY` 可以从 `data/replay/EventReplay_latest.json` 生成稳定 OHLCV 输入和参数扫描摘要，且不得联网、刷新行情、连接券商、创建订单或修改持仓。

`scripts/vectorizedResearch.sh --json-only --symbol SPY` builds stable OHLCV input and a parameter-scan summary from `data/replay/EventReplay_latest.json` without network access, market refresh, broker connection, order creation, or holdings mutation.

工作台状态页必须只读展示由 `data/vectorized/VectorizedResearch_latest.json` ingest 到 Operational Store 后生成的 compact read model cards、参数扫描表和图表，不得在页面渲染时重新读取 EventReplay records 或重新运行参数扫描。

The workspace status page must display compact read model cards, parameter-scan rows, and charts produced after ingesting `data/vectorized/VectorizedResearch_latest.json` into Operational Store; it must not reload EventReplay records or rerun parameter scans during page rendering.

`scripts/dailyCheck.sh` 可以汇总系统状态、数据源配置和报告资产数量。

`scripts/dailyCheck.sh` summarizes system status, data provider configuration, and report asset counts.

`scripts/dailyCheck.sh --output-dir data/systemAudit` 可以生成日常就绪检查 JSON、Markdown 和 PDF，且不打开浏览器、不刷新行情、不修改持仓。

`scripts/dailyCheck.sh --output-dir data/systemAudit` generates Daily Readiness JSON, Markdown, and PDF without opening a browser, refreshing market data, or mutating holdings.




`scripts/cashFlowCommand.sh --output-dir data/cashflow` 可以生成 Company CashFlow Command JSON、CSV、Markdown、PDF 和 runtime summary，且不得连接银行、支付、工资、税务、会计、券商或交易系统。

Company CashFlow Command 必须生成 `PFIOSCompanyCashFlowRuntimeSummaryV1` compact 运行摘要，并支持 `scripts/cashFlowCommand.sh --summary-json` 只输出低 token 摘要；该摘要不得包含完整 entries，必须展示余额证据、缺证据记录、待复核记录、Runway、净现金流、证据闸门和 no-external-execution 安全边界。

`scripts/cashFlowReviewedInputRefresh.sh --entry-path data/private/cashflow/CompanyCashFlowReviewedInput.json --output-dir data/cashflow` 可以从本地 reviewed input 生成 Company CashFlow Command full snapshot 和 runtime summary；缺少输入时必须返回 `PFIOSCompanyCashFlowReviewedInputRefreshV1 status=Blocked` 且不得写入输出。公共仓库只能包含 `CompanyCashFlowReviewedInput.example.json` 和 schema，真实输入必须留在 `data/private/cashflow`。

`scripts/policyRadar.sh --output-dir data/policy` 可以生成 Policy Intelligence Radar JSON、CSV、Markdown、PDF 和 runtime summary，且不得自动抓取实时政策、登录政府平台、提交申请、付款、法律/税务/合规结论或交易动作。

Policy Intelligence Radar 必须生成 `PFIOSPolicyIntelligenceRuntimeSummaryV1` compact 运行摘要，并支持 `scripts/policyRadar.sh --summary-json` 只输出低 token 摘要；该摘要不得包含完整 opportunities，必须展示政策证据、来源权威、缺证据记录、待复核记录、证据闸门和 no-external-execution 安全边界。

`scripts/policyReviewedInputRefresh.sh --entry-path data/private/policy/PolicyReviewedInput.json --output-dir data/policy` 可以从本地 reviewed input 生成 Policy Intelligence Radar full snapshot 和 runtime summary；缺少输入时必须返回 `PFIOSPolicyReviewedInputRefreshV1 status=Blocked` 且不得写入输出。公共仓库只能包含 `PolicyReviewedInput.example.json` 和 schema，真实输入必须留在 `data/private/policy`。

`scripts/consumptionGuard.sh --output-dir data/consumption` 可以生成 Consumption Guard JSON、CSV、Markdown、PDF 和 runtime summary，且不得连接支付宝、银行、工资、税务、券商、支付系统或执行付款/转账/退款/冻结账户/投资动作。

Consumption Guard 必须生成 `PFIOSConsumptionGuardRuntimeSummaryV1` compact 运行摘要，并支持 `scripts/consumptionGuard.sh --summary-json` 只输出低 token 摘要；该摘要不得包含完整 events，必须展示消费证据、缺证据记录、待复核记录、冲动风险、固定成本、可投资现金流压力、证据闸门和 no-external-execution 安全边界。

`scripts/consumptionReviewedInputRefresh.sh --event-path data/private/consumption/ConsumptionGuardReviewedInput.json --output-dir data/consumption --monthly-investable-budget 1000` 可以从本地 reviewed input 生成 Consumption Guard full snapshot 和 runtime summary；缺少输入时必须返回 `PFIOSConsumptionGuardReviewedInputRefreshV1 status=Blocked` 且不得写入输出。公共仓库只能包含 `ConsumptionGuardReviewedInput.example.json` 和 schema，真实输入必须留在 `data/private/consumption`。



`scripts/commandCenter.sh --output-dir data/commandCenter` 可以生成总控驾驶舱 JSON、Markdown 和 PDF，且不刷新行情、不修改持仓、不打开浏览器、不连接实盘。



`scripts/reportValidation.sh` 是报告/验证链路默认用户入口；无参数时必须等价于 `--mode daily --summary-json`，只读合并报告证据索引、补证据候选和验证优先级摘要。它不得写文件、追加验证队列、执行验证任务、刷新行情、连接券商、创建订单、修改持仓，且不得输出完整 records、完整任务队列、原始行情或本机私有 evidence。

`scripts/reportDecisionSupport.sh --output-dir data/reportDecision` 是高级动作，可以生成报告决策支持索引 JSON、CSV、Markdown 和 PDF，且不修改原报告、不刷新行情、不连接实盘。

报告决策支持索引必须把缺少 `PFIOSReportEvidenceV1`、数据质量、多源交叉校验、风险闸门或 Decision Quality 的报告降级为 `NeedsMoreEvidence` 或 `DoNotUse`。

`scripts/reportGapTasks.sh --dry-run --output-dir data/reportDecision` 可以从证据不足报告生成补证据任务预览 JSON、CSV、Markdown 和 PDF，且不写入验证队列。

`scripts/reportGapTasks.sh --output-dir data/reportDecision` 可以把补证据任务追加到 `data/validationQueue/ValidationTasks.json`，必须保留已有任务并跳过重复任务。

报告补证据任务生成器只能创建待验证任务，不得自动刷新行情、运行验证、修改旧报告、修改持仓、连接实盘或输出交易指令。

`scripts/validationPriorityPlan.sh --output-dir data/validationQueue` 可以生成验证任务优先级计划 JSON、CSV、Markdown 和 PDF，且不得修改原始 `ValidationTasks.json`。

验证任务优先级计划必须把任务分为 `RunFirst`、`PrepareInputs`、`BatchValidate`、`ManualReview`、`Paused` 或 `Completed`，并展示所需输入、验证方式、跳过风险和阻塞项。

数据依赖任务缺少代码或市场时必须进入 `PrepareInputs`，不得直接排入可执行验证。

`scripts/runValidationTask.sh --output-dir data/validationQueue` 可以执行最高优先级 `CrossSourceValidation` 验证任务并生成 JSON、CSV、Markdown 和 PDF 执行记录。

验证任务执行器必须在数据源不足时输出 `Blocked`，不得伪造多源交叉校验通过；执行器不得修改原始 `ValidationTasks.json`。


日常就绪检查必须区分平台研究就绪和真实数据源待配置；API key 或 OpenD 缺失不能被写成策略证据。

Daily Readiness must separate platform research readiness from real-data provider setup; missing API keys or OpenD must not be treated as strategy evidence.

`scripts/dailyCheck.sh --network` 可以在单个第三方数据源失败时继续运行后续诊断，并把失败原因输出在终端。

`scripts/dailyCheck.sh --network` continues later diagnostics when one third-party provider fails and prints the failure reason in the terminal.

`scripts/verifyPFIOS.sh` 可以完整验收系统且不会打开浏览器。

`scripts/verifyPFIOS.sh` verifies the system without opening a browser.

`scripts/finalAcceptanceCheck.sh` 可以检查 macOS `.app` 入口、报告目录、核心文档、关键功能源码、完整测试和日常检查，且不会联网或打开浏览器。它是重 SmokeTest/release gate，本地默认被 `PFI_OS_ALLOW_HEAVY_SMOKE=1` 显式确认门保护。

`scripts/finalAcceptanceCheck.sh` checks macOS `.app` launchers, report directory, core docs, key feature source files, full tests, and daily checks without using network access or opening a browser. It is a heavy SmokeTest/release gate and is protected locally by the explicit `PFI_OS_ALLOW_HEAVY_SMOKE=1` confirmation gate.

`scripts/createSampleReport.sh` 可以快速生成样例 Word 报告且不会打开浏览器。

`scripts/createSampleReport.sh` quickly generates a sample Word report without opening a browser.

样例报告必须生成包含 `PFIOSReportEvidenceV1` 的 RunMetadata；缺少真实多源交叉校验时应降级为 `NeedsMoreEvidence`。

`scripts/setupEnv.sh` 可以创建本地 `.env` 模板且不会覆盖已有密钥文件。

`scripts/setupEnv.sh` creates a local `.env` template without overwriting an existing key file.

`scripts/validateRealData.sh` 可以联网验证 Yahoo Finance 和 AKShare 并生成数据质量报告。

`scripts/validateRealData.sh` validates Yahoo Finance and AKShare through the network and generates data quality reports.

`scripts/checkMoomoo.sh` 可以检查 Moomoo 只读行情环境，缺少 `futu-api` 或 OpenD 未启动时会明确提示。

`scripts/checkMoomoo.sh` checks the Moomoo quote-only environment and clearly reports missing `futu-api` or an unavailable OpenD gateway.

`scripts/validateCrossSource.sh` 可以在配置足够真实数据源后保存多源交叉校验结果；数据源不足时会明确跳过。

`scripts/validateCrossSource.sh` saves cross-source validation results when enough real providers are configured; it clearly skips when providers are insufficient.

## Research Workflow

单标的回测支持选择数据、策略、成本参数并导出 Word 报告。

Single backtest supports data selection, strategy selection, cost settings, and Word report export.

报告页面展示结果判读、核心指标、图表、交易明细和输出文件路径。

The result page shows interpretation, key metrics, charts, trades, and output file paths.

报告页面展示 Decision Quality Score、缺失证据、研究动作和历史模拟暴露统计。

The result page shows Decision Quality Score, missing evidence, research actions, and historical simulated exposure.

报告中心支持按类型、日期、关键词、表现状态和研究门禁状态查找研究产物。

The report center supports finding artifacts by type, date, keyword, performance status, and research gate status.

报告中心提供决策质量 Dashboard，显示研究状态分布、平均质量分、缺失证据和优先复核列表。

The report center provides a Decision Quality Dashboard showing research status distribution, average quality score, missing evidence, and priority review list.

报告中心提供验证任务队列，记录来源报告、研究主题、待验证标的、待验证信号、成本假设、基准、状态和验证报告路径。

The report center provides a validation task queue recording source report, research topic, target symbol, signal to validate, cost assumption, benchmark, status, and validation report path.

行研报告功能区可以按日期和关键词检索本地行研报告，并显示最近 PFIOS 报告、验证任务和研究门禁状态。

The industry research area can search local industry reports by date and keyword, and show recent PFIOS reports, validation tasks, and research gate status.

持仓功能区可以同步支付宝确认持仓、行研上传持仓、消费行为分析持仓和 PFIOS 本地导入持仓，并永久保存到统一持仓簿。

The holdings area can sync confirmed Alipay holdings, industry-uploaded holdings, consumer-analysis holdings, and PFIOS local imports, then persist them to one holdings book.

待确认订单和截图候选持仓必须单独显示，不得计入正式持仓、权重或集中度。

Pending orders and screenshot candidate holdings must be shown separately and must not be counted as confirmed holdings, weights, or concentration.

情绪分析功能区可以读取大盘默认、自选对象或持仓对象，并展示情绪分、RSI、20 日趋势、波动率和 60 日最大回撤。

The sentiment analysis area can read default market objects, custom symbols, or holdings objects, then show sentiment score, RSI, 20-day trend, volatility, and 60-day max drawdown.

热点分析功能区可以读取大盘热点、自选对象或持仓对象，并展示热点时间轴、时间切片、热点总览、热力图、气泡图和失败对象；缓存刷新间隔不得超过 3600 秒。

The hotspot analysis area can read market hotspots, custom symbols, or holdings objects, then show time slices, hotspot summary, heatmap, bubble chart, and failed objects; cache refresh TTL must not exceed 3600 seconds.

热点分析生成后必须显示 `PFIOSHotspotRuntimeSummaryV1` compact 运行摘要，包含请求指纹、对象覆盖、切片数量、缓存 TTL、证据状态和只读安全边界；该摘要不得保留原始行情明细、连接券商、创建订单或修改持仓。

After hotspot generation, the page must show an `PFIOSHotspotRuntimeSummaryV1` compact runtime summary with request key, object coverage, slice count, cache TTL, evidence status, and read-only safety boundary; it must not retain raw price frames, connect brokers, create orders, or mutate holdings.

热点分析可以使用 `PFIOSHotspotPersistedCacheV1` 本地派生缓存复用同一请求指纹的已计算结果；缓存必须位于被 Git 忽略的 `data/cache/hotspots/`，必须按 TTL 过期，且不得存储 secrets、原始账户数据、券商 token、订单或持仓修改。

The hotspot area may use `PFIOSHotspotPersistedCacheV1` local derived cache to reuse computed results for the same request key; the cache must live under gitignored `data/cache/hotspots/`, expire by TTL, and must not store secrets, raw account data, broker tokens, orders, or holdings mutations.

热点分析页面必须显示 `PFIOSHotspotCacheStatusV1` 当前请求缓存状态、剩余有效期、缓存目录文件数量，并提供只清除当前请求指纹缓存的按钮；该按钮不得删除市场 bar cache、报告、持仓、SQLite 或其他系统缓存。

The hotspot page must show `PFIOSHotspotCacheStatusV1` current-request cache state, remaining TTL, cache directory file count, and a button that clears only the current request-key cache; it must not delete market bar cache, reports, holdings, SQLite files, or other subsystem caches.

热点分析生成后必须显示 `PFIOSHotspotRequestTraceV1` 每对象请求耗时摘要，至少包含请求数量、成功/失败、总耗时、最慢对象和错误摘要；该 trace 只能保存 compact 诊断字段，不得保存原始 provider payload 或行情明细。

After hotspot generation, the page must show an `PFIOSHotspotRequestTraceV1` per-object request timing summary with request count, success/failure, total elapsed time, slowest objects, and error summaries; this trace may store compact diagnostics only, not raw provider payloads or market-data details.

热点分析和向量化研究的 Plotly 图表必须接入统一研究图表交互配置，至少支持响应式渲染、滚轮缩放、拖拽平移或缩放、悬停辅助线和 PNG 导出；图表交互不得触发新的行情请求、参数扫描、回测、下单或持仓修改。

The hotspot and vectorized research Plotly charts must use the shared research chart interaction config with responsive rendering, scroll zoom, drag pan or zoom, hover spikes, and PNG export; chart interaction must not trigger new market-data requests, parameter scans, backtests, orders, or holdings mutations.

勾选 52ETF 参考后，热点页面必须提供 `PFIOS52ETFHotspotComparisonV1` 只读对照摘要，将公开 A 股云图板块与 PFI_OS 当前热点对象池映射；该对照不得替代本地数据质量闸门，不得写入回测、下单、持仓或交易前证据。

When 52ETF reference is enabled, the hotspot page must provide an `PFIOS52ETFHotspotComparisonV1` read-only comparison summary mapping public A-share market-cloud boards to the current PFI_OS hotspot object pool; it must not replace local data-quality gates or write into backtests, orders, holdings, or pre-trade evidence.

`scripts/site52etfSnapshot.sh --output-dir data/integrations/site52etf` 可以生成 `PFIOS52ETFPublicSnapshotV1` latest JSON，记录 52ETF 公开页面的板块、指标、操作提示、8 秒刷新提示、证据闸门和只读安全边界；该 snapshot 不得保存 raw HTML、cookies、登录态、行情明细、回测输入、订单或持仓修改。热点页面必须优先读取本地 latest snapshot，缺失时才按缓存在线读取公开页面。

`scripts/site52etfSnapshot.sh --output-dir data/integrations/site52etf` generates `PFIOS52ETFPublicSnapshotV1` latest JSON with public boards, metrics, operating notes, 8-second refresh hint, evidence gates, and read-only safety boundary; it must not store raw HTML, cookies, session state, market-data detail, backtest input, orders, or holdings mutations. The hotspot page must prefer local latest snapshot before cached live fetch.

热点分析必须显示热点证据闸门，至少检查数据源、数据覆盖率、失败率、样本长度、时间切片、刷新粒度、数据新鲜度和热度集中度；任一 Review 或 Block 必须降级为研究观察。

The hotspot analysis area must show a hotspot evidence gate covering source, coverage, failure rate, sample length, time slices, refresh cadence, freshness, and concentration; any Review or Block downgrades the result to research observation.

情绪分析和热点分析必须分离指标预热窗口与展示窗口；同一数据源、同一对象、同一结束日期或时间切片下，改变展示开始日期不应导致同一目标结果大幅跳变。

Sentiment and hotspot analysis must separate the indicator warm-up window from the display window; changing the display start date must not materially change the same target timestamp under the same provider and object set.

功能导航和使用指导必须在左侧侧栏展示，且主功能区不得显示独立 `使用指导` 或 `策略变更确认` 入口。

Navigation and the operating guide must be shown in the sidebar, and the main workspace must not show standalone `使用指导` or `策略变更确认` entries.

个人画像功能区可以读取统一持仓簿，并结合回测元数据、复盘记录和验证任务输出行为习惯、风险画像和行为优化。

The personal profile area can read the canonical holdings book, then combine run metadata, review records, and validation tasks into behavior habits, risk profile, and behavior optimization.

报告中心提供复盘与错误画像，复盘记录会永久保存到本地 JSON 文件，程序关闭后不丢失。

The report center provides review and error profiling. Review records are persistently saved to a local JSON file and survive app restarts.

组合轮动页面提供组合风险视图，显示市场、货币、主题暴露，下跌情景损失，回本所需涨幅和单一标的冲击。

The portfolio rotation page provides a portfolio risk view showing market, currency, and theme exposure, downside scenario loss, rebound needed to recover, and single-symbol shock.

数据工具显示数据源状态、代码格式示例、A 股代码转换和多源交叉校验。

Data tools show provider status, symbol examples, A-share symbol conversion, and cross-source validation.

真实数据源至少覆盖 TuShare、AKShare、Yahoo Finance、Alpha Vantage 和 Polygon 的接入状态、配置说明和可用性检查。

Real data sources cover at least TuShare, AKShare, Yahoo Finance, Alpha Vantage, and Polygon connection status, configuration guidance, and availability checks.

Moomoo 作为优先真实数据入口，具备只读行情诊断、端口检查、行情拉取检查和数据质量报告。

Moomoo, as the primary real-data entry, has quote-only diagnostics, port checks, quote fetch checks, and data quality reports.

## Safety

系统禁止实盘交易、真实下单和保存券商账户密码。

The system prohibits live trading, real order submission, and brokerage password storage.

策略修改需要确认或明确确认。

Strategy changes require approval or explicit confirmation.

系统不得输出实盘买入、卖出、推荐、建议仓位或今天操作指令。

The system must not output live buy, sell, recommendation, suggested position, or same-day action instructions.

## Verification

验收命令：

Verification command:

```bash
$PFI_OS_HOME/scripts/finalAcceptanceCheck.sh
```

代码验收命令：

Code verification command:

```bash
$PFI_OS_HOME/scripts/verifyPFIOS.sh
```

成品状态：软件功能闭环已完成；真实数据源仍受网络、API Key、第三方额度和数据覆盖影响。

Product status: the software workflow is complete; real data providers still depend on network access, API keys, third-party quotas, and data coverage.
