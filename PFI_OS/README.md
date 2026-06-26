# PFI_OS｜证值智能中台

## PFI-First Transition Notice

`PFI OS` is the target product direction. This `PFI_OS/` directory is the
current renamed product workspace after the Phase 0 transition.

Read the PFI-001 contracts before new development:

| Contract | Path |
| --- | --- |
| Product constitution | `docs/product/PFI_OS_PRODUCT_CONSTITUTION.md` |
| Six-workspace information architecture | `docs/product/PFI_OS_INFORMATION_ARCHITECTURE.md` |
| Feature disposition | `docs/product/PFI_FEATURE_DISPOSITION.md` |
| Data boundaries | `docs/data/PFI_DATA_BOUNDARIES.md` |
| Source of truth | `docs/data/PFI_SOURCE_OF_TRUTH.md` |
| UX contract | `docs/ux/PFI_UX_CONTRACT.md` |
| Target architecture | `docs/architecture/PFI_TARGET_ARCHITECTURE.md` |
| Development record and backlog | `docs/development/PFI_PHASE_0_TO_A_RECORD.md` |
| PFI-goal matrix | `docs/development/PFI_GOAL_GATE_MATRIX.md` |
| Reproducible environment | `docs/development/PFI_REPRODUCIBLE_ENV.md` |
| PFI-003 durable job store | `docs/development/PFI003_DURABLE_JOB_STORE.md` |
| PFI V0.2 Stage 0 compatibility audit | `docs/pfi_v02/STAGE0_COMPATIBILITY_AUDIT.md` |
| Legacy migration record | `docs/archive/legacy-migration.md` |

PFI-002 has retired the old value-ledger product surface from active code,
scripts, tests, navigation, command center output, and formal docs. New work
must follow PFI-first constraints: one PFI OS entry, the PFI V0.2 target
8-entry IA, the current 6-workspace Web Shell kept as a compatibility shell
until Stage 1 UI migration, strategy backtesting as a core workflow, market
feel training retained as a Strategy Lab training mode, no autonomous live
trading, and no private runtime data in public Git.

PFI V0.2 Stage 0 is closed by the compatibility contract in
`docs/pfi_v02/STAGE0_COMPATIBILITY_AUDIT.md`: existing entries remain
accessible, `PFI/大数据模拟器` maps to `投资管理 > 策略实验室 / 大数据模拟器`,
and the active runtime paths are not moved.

`PFI_OS` 是主系统总入口，macOS 应用显示为 `PFI_OS`。PFIOS 是其中的量化研究与回测主入口，并继续承接研究总线、持仓、报告、独立验证和跨系统证据流。

PFIOS 是个人自用的量化研究、分析、回测和实验记录平台。

PFIOS is a personal platform for quantitative research, analysis, backtesting, and experiment tracking.

当前版本已经形成个人日常使用的完整研究闭环。

The current version provides a complete daily personal research workflow.

本系统禁止接入实盘交易，禁止真实下单，禁止保存交易账户密码。

This system must not connect to live trading, must not place real orders, and must not store brokerage account passwords.

系统产出的报告和结果可以作为你进行实盘交易前的研究依据和参考，因此每个结果都必须尽可能准确、可验证、可追溯。

Reports and results produced by the system may support your real trading decisions, so each output must be as accurate, verifiable, and traceable as possible.

## Start Here

日常使用先读：

```text
$PFI_OS_HOME/docs/QuickStart.md
```

Agent 接手优先读：

```text
AGENT_CONTINUITY.md
HANDOFF.md
docs/development/PFI_PHASE_0_TO_A_RECORD.md
15_OPEN_QUESTIONS.md
UPLOAD_MANIFEST.md
```

最短路径：

1. 双击 `PFI_OS.app`。
2. 在 `总控驾驶舱` 检查系统状态、现金流、政策、消费、证据来源、行动队列和最新报告，并先看 `统一下一步` 决定进入热点、参数扫描、报告验证或 macOS 验收。
3. 进入 `单标的回测` 跑策略，或进入 `持仓` 更新持仓。
4. 在 `报告中心` 阅读 Word 报告。
5. 如需跨系统同步，运行 `scripts/syncResearchSystemsOnce.sh`。

常用目录：

| 项目 | 路径 |
| --- | --- |
| 工作台工程 | `$PFI_OS_HOME` |
| 快速使用说明 | `docs/QuickStart.md` |
| 文档索引 | `docs/Index.md` |
| PFI_OS 架构 | `docs/PFI_OS.md` |
| 总控驾驶舱 | `docs/ExecutiveCommandCenter.md` |
| 行情事件层 | `docs/MarketEventLayer.md` |
| 可复现数据湖 | `docs/ReproducibleDataLake.md` |
| 事件回放 | `docs/EventReplay.md` |
| 公司现金流 | `docs/CompanyCashFlowCommand.md` |
| 政策雷达 | `docs/PolicyIntelligenceRadar.md` |
| 消费守卫 | `docs/ConsumptionGuard.md` |
| 报告验证工作台 | `docs/ReportValidationHub.md` |
| 报告目录 | `~/Downloads/量化回测分析` |
| 共享研究总线 | `data/researchBus/ResearchBus.sqlite` |
| 正式持仓簿 | `data/holdings/HoldingsBook.json` |

故障优先处理：

```bash
$PFI_OS_HOME/scripts/statusPFIOS.sh
$PFI_OS_HOME/scripts/stopPFIOS.sh
```

总控报告：

```bash
$PFI_OS_HOME/scripts/commandCenter.sh --output-dir data/commandCenter
```

行情事件日志：

```bash
$PFI_OS_HOME/scripts/marketEventLayer.sh --output-dir data/marketEvents
```

数据湖 Manifest：

```bash
$PFI_OS_HOME/scripts/dataLakeManifest.sh --output-dir data/dataLake
```

事件回放：

```bash
scripts/eventReplay.sh --output-dir data/replay
```

公司现金流快照：

```bash
$PFI_OS_HOME/scripts/cashFlowCommand.sh --output-dir data/cashflow
```

低 token 检查可只输出现金流 compact 运行摘要。

For low-token checks, print only the compact cashflow runtime summary.

```bash
$PFI_OS_HOME/scripts/cashFlowCommand.sh --summary-json
```

政策雷达快照：

```bash
$PFI_OS_HOME/scripts/policyRadar.sh --output-dir data/policy
```

低 token 检查可只输出政策 compact 运行摘要。

For low-token checks, print only the compact policy runtime summary.

```bash
$PFI_OS_HOME/scripts/policyRadar.sh --summary-json
```

消费守卫快照：

```bash
$PFI_OS_HOME/scripts/consumptionGuard.sh --output-dir data/consumption
```

低 token 检查可只输出消费守卫 compact 运行摘要。

For low-token checks, print only the compact consumption runtime summary.

```bash
$PFI_OS_HOME/scripts/consumptionGuard.sh --summary-json
```

报告验证工作台。默认只读合并报告证据、补证据候选和验证优先级，低 token 输出，不入队、不执行验证：

```bash
$PFI_OS_HOME/scripts/reportValidation.sh
```

高级动作。确认要写入产物、入队或执行验证时再使用：

```bash
$PFI_OS_HOME/scripts/reportDecisionSupport.sh --output-dir data/reportDecision
```

```bash
$PFI_OS_HOME/scripts/reportGapTasks.sh --output-dir data/reportDecision
```

```bash
$PFI_OS_HOME/scripts/validationPriorityPlan.sh --output-dir data/validationQueue
```

```bash
$PFI_OS_HOME/scripts/runValidationTask.sh --output-dir data/validationQueue
```

## Integrated Research Role

PFIOS 在行研报告、政府文件解读和交易策略建议系统中只承担验证层职责。它应输出回测对象、样本区间、成本假设、参数稳定性、样本外验证、walk-forward 结果、研究风险闸门、失效环境和停用条件。

如果行研或政策系统引用某个 PFIOS 结果，必须同时引用数据质量、多源交叉校验、成本假设和风险闸门状态。验证不足时，结论只能作为观察或待验证线索，不能升级为实盘交易建议。

PFIOS 现在增加 Decision Quality Score，用来判断一次研究结论是否完整。状态分为 `ContinueResearch`、`WatchOnly`、`NeedsMoreEvidence` 和 `DoNotUse`。

Decision Quality Score evaluates whether a research conclusion is complete. Status values are `ContinueResearch`, `WatchOnly`, `NeedsMoreEvidence`, and `DoNotUse`.

报告中心新增复盘与错误画像，用于手工记录原始研究计划、实际执行偏差、最终盈亏、盈亏来源和错误类型。该模块只做复盘统计，不生成实盘操作指令。

The report center now includes review and error profiling for recording original research plans, execution deviation, final PnL, return attribution, and error types. This module is for review statistics only and does not create live action instructions.

组合轮动页面新增组合风险视图，展示市场、货币、主题暴露，现金权重，总暴露，下跌情景损失，回本所需涨幅和单一标的冲击。

The portfolio rotation page now includes a portfolio risk view covering market, currency, and theme exposure, cash weight, gross exposure, downside scenario loss, rebound needed to recover, and single-symbol shock.

报告中心新增验证任务队列，用于记录来源报告、来源段落、研究主题、待验证标的、待验证信号、样本区间、成本假设、基准、当前状态和验证报告路径。

The report center now includes a validation task queue for source report, source paragraph, research topic, target symbol, signal to validate, sample period, cost assumption, benchmark, status, and validation report path.

报告中心可把 `NeedsMoreEvidence` 或 `DoNotUse` 报告的缺失证据自动拆成验证任务。该流程只追加待办任务，不联网、不跑验证、不改旧报告、不连接实盘。

The report center can convert missing evidence from `NeedsMoreEvidence` or `DoNotUse` reports into validation tasks. This process only appends tasks; it does not refresh data, run validation, change old reports, or connect to live trading.

验证任务队列可以生成优先级计划，把任务按 `RunFirst`、`PrepareInputs`、`BatchValidate`、`ManualReview` 等处理桶排序，并输出所需输入、验证方式、跳过风险和阻塞项。

The validation queue can generate a priority plan that ranks tasks into `RunFirst`, `PrepareInputs`, `BatchValidate`, and `ManualReview`, with required inputs, verification method, skip risk, and blockers.

验证任务执行器可以对最高优先级 `CrossSourceValidation` 任务生成执行记录。数据源不足时输出 `Blocked`，不会伪造通过。

The validation task executor can run the top-priority `CrossSourceValidation` task and write an execution record. If provider coverage is insufficient, it outputs `Blocked` instead of fabricating a pass.

统一研究数据总线已接入 PFIOS、行研系统、消费行为系统、独立验证系统、FIFA/TAB 研究系统和政府文件/政策解读系统。共享 SQLite 数据库位于 `data/researchBus/ResearchBus.sqlite`，JSON 快照位于 `data/researchBus/ResearchBusSnapshot.json`。它会同步行研报告索引、行研正文拆出的待验证任务、PFIOS 回测结果、统一持仓主数据、消费行为系统内部状态、独立验证运行状态、子系统注册表和子系统产物索引。

The unified research data bus now connects PFIOS, AI-Research-System, the independent validation system, FIFA/TAB research, and the government policy interpretation system. The shared SQLite database is `data/researchBus/ResearchBus.sqlite`, and the JSON snapshot is `data/researchBus/ResearchBusSnapshot.json`.

共享 schema 合约保存在 `docs/ResearchBusSchema.json`。后续新聊天、其他 agent 或 automation 增删字段时，应先对齐该 schema，再修改 PFIOS 和行研系统两侧的 bridge。

The shared schema contract is `docs/ResearchBusSchema.json`.

跨系统互通审计可用 `scripts/auditResearchBusInterop.sh --json` 一键检查。审计结果保存到 `data/researchBus/ResearchBusInteropAudit.json`，覆盖共享 schema、共享 SQLite、系统注册表、子系统产物索引、双向 API、任意聊天框输入、行研报告解析、PFIOS 结果回写、消费行为同步、统一持仓、独立验证入口、独立验证两级架构、系统心跳、行研桥接输出和行研 automation 保留状态。

The interoperability audit is available through `scripts/auditResearchBusInterop.sh --json`; the machine-readable output is `data/researchBus/ResearchBusInteropAudit.json`.

只读证据审计可用 `PYTHONPATH=src .venv/bin/python -m pfi_os.examples.data_trust_audit --output-dir /private/tmp/pfi_os-data-trust` 生成。它会检查项目控制文件、数据源 Provider、策略库、持仓、ResearchBus、验证任务、独立验证、参数实验和报告目录，把文件分为 `RECONCILED`、`NEEDS_REVIEW`、`PARSED_CANDIDATE`、`REJECTED` 等状态，避免把候选数据、损坏文件或不完整实验误当成可用研究结论。

The read-only Data Trust audit is available through `pfi_os.examples.data_trust_audit`; it classifies project controls, providers, strategies, holdings, ResearchBus, validation tasks, independent validation, experiments, and reports into evidence statuses.

实体注册摘要会在持仓代码同步时生成，区分 `TradableSymbol`、`ProxyMapped` 和 `MissingSymbol`。代理映射只代表研究代理，不代表真实可交易证券；缺失代码对象不能进入回测、情绪或热点分析。

The entity registry summary classifies holdings into `TradableSymbol`, `ProxyMapped`, and `MissingSymbol`.

实体注册也可以导出为独立派生产物：`data/entityRegistry/EntityRegistry.json`、`EntityRegistry.csv` 和 `EntityRegistry.md`。这些文件只从持仓和本地代理规则派生，不覆盖正式持仓簿。

The entity registry can also be exported as `data/entityRegistry/EntityRegistry.json`, `EntityRegistry.csv`, and `EntityRegistry.md`. These files are derived outputs and do not overwrite the holdings book.

母系统编排入口是 `scripts/orchestrateSystems.sh`。PFIOS 作为母系统登记每个子系统的根目录、独立启动命令、健康检查命令、同步命令、能力和输出产物；子系统仍可直接运行自己的脚本，不依赖 PFIOS 页面。FIFA/TAB 系统默认使用 `scripts/run_tab_fifa_daily_automation.sh` 和 `scripts/verify_fifa_automation_readiness.sh`；政府文件/政策系统默认使用 `scripts/run_policy_report.sh` 和 `python3 -m source_registry ... status --json`。

The mother-system orchestrator is `scripts/orchestrateSystems.sh`. Subsystems remain independently runnable through their own commands.

行研系统通过 `research-bus-sync` 写入报告索引并拉取 PFIOS 结果；PFIOS 通过 `scripts/syncResearchBus.sh` 读取共享库、批量推送验证任务并把回测结论回写给行研系统。独立验证系统通过 `scripts/runIndependentValidation.sh` 生成 manifest 和分片运行记录，支持百亿级数据量的 dry-run 调度登记，也支持 `checksum` 模式逐片流式校验和本机 worker pool 并行校验。

The AI research system uses `research-bus-sync`; PFIOS uses `scripts/syncResearchBus.sh`; independent validation uses `scripts/runIndependentValidation.sh`.

研究数据总线也提供双向 API 表：`bus_api_requests`、`bus_chat_inputs`、`bus_system_outbox` 和 `bus_heartbeats`。任意对话框可以通过 `scripts/researchBusApi.sh submit-chat` 写入自然语言输入，系统会自动分类为验证任务、持仓更新候选、同步请求、独立验证请求或普通备注。

The research bus also provides bidirectional API tables for requests, chat input, outbox messages, and heartbeats.

Workflow Layer 已提供统一只读输入视图 `workflow_inputs_frame()`，把自然语言输入、dropbox 文件和直接 API 请求统一成可追溯记录。聊天输入会随 linked request 从 `Pending` 变为 `Processing`、`Completed` 或 `Failed`；持仓和交易候选进入 `PendingReview` 后不会被自动覆盖为正式持仓。畸形 API payload 会被拒绝入队，重复 dropbox 文件会移动到唯一 processed 文件名，避免覆盖旧证据。

The workflow layer provides `workflow_inputs_frame()` as a read-only trace view for chat inputs, dropbox files, and direct API requests.

Report Evidence Layer 已接入回测 Word 报告和 RunMetadata JSON。每份报告会增加 `报告证据层`，列明数据质量状态、多源校验状态、实体状态、工作流输入编号、关联请求编号、成本假设完整性、风险闸门和决策质量状态。缺少关键证据时，报告会把结论降级为 `NeedsMoreEvidence`，只作为研究线索或复盘材料。

The report evidence layer writes data quality, cross-source validation, entity status, workflow lineage, cost assumptions, risk gate status, and decision quality status into Word reports and run metadata.

最终集成审计入口：

```bash
bash $PFI_OS_HOME/scripts/auditPFIIntegration.sh --no-write
```

它只读检查 Data Trust、Entity Registry、Workflow Inputs、Report Evidence、ResearchBus 互通和禁止实盘边界。输出状态为 `Pass`、`Review` 或 `Fail`；`Review` 表示证据缺口或环境权限限制，需要补齐后再作为日常稳定验收。

首页已新增 `大数据模拟` 功能区，可直接调用独立验证系统生成百万、千万、一亿、十亿或自定义规模的分片验证记录。自然语言入口支持 `百万`、`千万`、`一亿`、`十亿`、`亿万级`、`million`、`hundred million` 和 `billion`，也支持 `checksum` 逐片校验模式。

The home navigation includes `大数据模拟` for independent validation scale tests from million to billion rows.

通用聊天投递箱位于 `data/researchBus/chatInbox`。把 `.txt`、`.md` 或 `.json` 文件放入该目录后，`process-dropbox` 或后台同步脚本会自动写入 ResearchBus，成功文件移到 `processed`，失败文件移到 `failed` 并生成错误记录。这个入口适合任何聊天框、快捷指令或自动化系统把文本投递给 PFIOS/行研系统。

The generic chat dropbox is `data/researchBus/chatInbox`. `.txt`, `.md`, and `.json` files placed there are imported into ResearchBus and moved to `processed` or `failed`.

本地 HTTP/Webhook 入口可通过 `scripts/researchBusWebhook.sh` 启动，默认只监听 `127.0.0.1:8765`，支持 `POST /chat`、`POST /request`、`POST /webhook` 和 `GET /health`。该入口用于本机快捷指令、其他本地系统或聊天工具把文本/JSON 写入 ResearchBus，不对公网开放。

The local HTTP/Webhook entry is `scripts/researchBusWebhook.sh`; it binds to `127.0.0.1` only.

功能导航和 `使用指导` 已统一放到左侧侧栏，方便边看步骤、检查点和术语说明边操作。`总控驾驶舱` 另有 `统一下一步`，用只读路由把热点快速预检、参数扫描预检、报告验证和 macOS 日常验收聚合成少数入口，减少在多个页面之间试错。侧栏会显示当前功能区的用途、适用场景、最短操作路径、优先检查点、产出、风险和常用术语悬停解释。功能区包含 `情绪分析`、`热点分析`、`盘感训练`、`持仓`、`行研报告` 和 `个人画像`。行研报告默认读取 `~/Downloads/行研报告`，个人画像会优先读取 PFIOS 持仓簿，再综合回测元数据、复盘记录和验证任务生成行为习惯、风险画像和优化方向。

Navigation and `使用指导` now live in the sidebar so you can read steps, checkpoints, and term help while operating the page. `总控驾驶舱` also includes `统一下一步`, a read-only action router that consolidates hotspot preflight, parameter-scan preflight, report validation, and macOS daily acceptance into a few next-step links. Workspace areas include `情绪分析`, `热点分析`, `盘感训练`, `持仓`, `行研报告`, and `个人画像`. Industry reports default to `~/Downloads/行研报告`; the personal profile first reads the PFIOS holdings book, then combines run metadata, review records, and validation tasks into behavior habits, risk profile, and improvement actions.

持仓文件支持 CSV、XLSX 和 JSON。建议字段：`symbol/代码`、`name/名称`、`market/市场`、`quantity/持仓数量`、`position_value/市值`、`weight/权重`。

Holding files support CSV, XLSX, and JSON. Recommended fields: `symbol/代码`, `name/名称`, `market/市场`, `quantity/持仓数量`, `position_value/市值`, and `weight/权重`.

持仓页面会同步支付宝持仓账本、行研报告上传目录、消费行为分析系统目录和 PFIOS 本地导入目录。正式持仓永久保存到 `$PFI_OS_HOME/data/holdings/HoldingsBook.json`，同步历史保存到 `HoldingsImportHistory.json`，待确认订单单独显示，不计入正式持仓。

The holdings page syncs the Alipay ledger, industry-report upload directories, consumer-analysis directories, and PFIOS local import directories. Confirmed holdings are permanently saved to `$PFI_OS_HOME/data/holdings/HoldingsBook.json`; sync history is saved to `HoldingsImportHistory.json`; pending orders are shown separately and are not counted as confirmed holdings.

外部支付宝账本和跨系统私有目录必须通过 `.env` 显式配置 `PFI_ALIPAY_LEDGER_DIR`。默认只扫描项目内 `data/private/alipay`，且正式持仓文件、导入目录和私有目录已加入 `.gitignore`。

External Alipay ledgers and cross-system private directories must be explicitly configured with `PFI_ALIPAY_LEDGER_DIR` in `.env`. By default PFIOS only scans project-local `data/private/alipay`, and confirmed holdings, imports, and private folders are ignored by Git.

如果来源文件为空、损坏或不可解析，系统会保留现有正式持仓并显示警告；不会用空结果覆盖上一次有效持仓。

If source files are empty, corrupted, or unreadable, the system keeps the existing confirmed holdings and shows a warning instead of overwriting the last valid book with an empty result.

情绪分析页面支持大盘默认、自选对象和持仓对象。系统会先展示情绪证据闸门，检查数据源、对象覆盖、失败率、样本长度、数据新鲜度和情绪集中度，再根据短期涨跌、20 日趋势、RSI、波动率和 60 日最大回撤生成 0-100 情绪分。任何闸门项需要复核时，结果只能作为观察线索，不作为实盘买卖指令。

The sentiment analysis page supports default market objects, custom watchlists, and holdings objects. It generates a 0-100 sentiment score from short-term return, 20-day trend, RSI, volatility, and 60-day max drawdown. It is research observation only and not a live trading instruction.

情绪分析和热点分析已经分离 `指标预热窗口` 与 `展示窗口`。你选择的展示开始日期只决定页面显示哪段时间；系统会自动向前多取历史数据计算 RSI、波动、回撤和热度，避免同一目标日期因为开始日期不同出现不合理跳变。热点分析进一步区分 `即时热度` 和 `平滑热度`：即时热度用于发现单个切片异动，页面默认总览、热力图和气泡图使用平滑热度判断持续性。

Sentiment and hotspot analysis separate the indicator warm-up window from the display window. Changing the display start date should not recalculate the same target timestamp with a different historical context.

热点分析页面用热点时间轴、热力图、气泡图和时间切片观察大盘、行业、风格、避险资产和持仓对象的短期强弱扩散。页面会先显示 `热点证据闸门`，检查数据源、数据覆盖率、失败率、样本长度、时间切片、刷新粒度、数据新鲜度和热度集中度。页面缓存刷新间隔为 1 小时，并可开启每小时自动刷新当前页；真实数据是否更新取决于数据源权限和行情延迟。热点热度只用于研究观察，不生成买卖或仓位指令；同一对象、同一数据源、同一时间切片下，展示窗口变化不应改变即时热度或平滑热度。

The hotspot analysis page uses a hotspot timeline, heatmaps, bubble charts, and time slices to observe short-term strength diffusion across markets, sectors, styles, defensive assets, and holdings. Page cache refresh is hourly, with an optional hourly page refresh; actual data freshness depends on provider permission and latency. Hotspot heat is research observation only.

热点分析现在默认使用 `快速预览` 工作台模式，限制对象数和时间切片数，并在生成前显示 `热点快速预检`：它会提前说明当前请求是否命中缓存、预计请求多少对象、是否可能较慢，以及下一步建议。需要报告前复盘时可切换到 `标准分析` 或 `完整复盘`；缓存清理等低频动作放在高级区。页面也提供可选的 `52ETF 公开参考`，只读取 `https://52etf.site/` 公开页面的板块和交互提示，用于对照市场云图表达，不作为行情、回测或交易证据。

Market hotspots now default to `快速预览`, limiting object count and time slices. Before generation, `热点快速预检` shows cache hit/miss, expected provider requests, possible slow-run warnings, and the recommended next action. Switch to `标准分析` or `完整复盘` for deeper review; cache cleanup stays in the advanced area. The optional `52ETF 公开参考` reads only the public `https://52etf.site/` page for market-cloud reference and is not used as market data, backtest evidence, or trading input.

盘感训练页面用 MA20/MA60、支撑压力、RSI、MACD、Bollinger、ATR、波动、回撤和成交量拆解技术结构。它支持三档训练：入门判断方向，中等判断方向和收益区间，专家判断方向、区间和更精确涨跌幅。开始作答后页面会实时自动倒计时，系统会隐藏未来答案区间，先锁定事前技术分析，再揭示实际走势和多维复盘。它只用于读图训练和研究观察，不输出实盘买卖指令。

The market-feel training page explains technical structure with MA20/MA60, support/resistance, RSI, MACD, Bollinger, ATR, volatility, drawdown, and volume. It supports three levels: beginner direction judgement, intermediate direction plus return range, and expert direction plus precise return estimate. After a challenge starts, the page shows a live countdown. PFIOS hides the future answer window, locks the pre-result technical analysis first, then reveals the actual path and multi-dimensional review. It never outputs live trading instructions.

## Docs

日常使用主入口：`docs/QuickStart.md`。

完整文档索引：`docs/Index.md`。

## Quick Start

最快启动方式：双击 Desktop、Downloads 或 Applications 里的 `PFI_OS.app`。

Fastest start: double-click `PFI_OS.app` in Desktop, Downloads, or Applications.

```text
~/Desktop/PFI_OS.app
~/Downloads/PFI_OS.app
/Applications/PFI_OS.app
```

日常快速检查，不打开浏览器。

Daily quick check without opening a browser.

```bash
$PFI_OS_HOME/scripts/dailyCheck.sh
```

生成日常就绪检查正式产物。

Generate formal Daily Readiness artifacts.

```bash
$PFI_OS_HOME/scripts/dailyCheck.sh --output-dir data/systemAudit
```

输出文件包括 `PFIOSDailyReadiness_DDMMYYYY.json`、`PFIOSDailyReadiness_DDMMYYYY.md` 和 `PFIOSDailyReadiness_DDMMYYYY.pdf`。

The outputs include `PFIOSDailyReadiness_DDMMYYYY.json`, `PFIOSDailyReadiness_DDMMYYYY.md`, and `PFIOSDailyReadiness_DDMMYYYY.pdf`.

日常检查并运行联网验证。

Daily check with network validation.

```bash
$PFI_OS_HOME/scripts/dailyCheck.sh --network
```



联网日常检查会展示单个数据源失败，但会继续执行后续诊断。

The network daily check shows individual provider failures but continues the remaining diagnostics.

同步 PFIOS、行研系统、持仓和独立验证状态，不打开浏览器。

Sync PFIOS, AI research, holdings, and independent validation state without opening a browser.

```bash
$PFI_OS_HOME/scripts/syncResearchBus.sh --json
```

独立验证十亿行 dry-run 分片测试。

Independent validation billion-row dry-run sharding test.

```bash
$PFI_OS_HOME/scripts/runIndependentValidation.sh run --synthetic-rows 1000000000 --rows-per-shard 100000000 --json
```

独立验证 checksum 实际分片校验。实际文件建议先用 `create-manifest` 生成 manifest；合成规模测试不会逐行展开。

Independent validation checksum execution. For real files, create a manifest first; synthetic scale tests do not expand rows one by one.

```bash
$PFI_OS_HOME/scripts/runIndependentValidation.sh run --synthetic-rows 1000000000 --rows-per-shard 100000000 --mode checksum --json
```

通过对话输入写入研究总线。

Submit chat input into the research bus.

```bash
$PFI_OS_HOME/scripts/researchBusApi.sh submit-chat --text "请验证 600000 的 RSI 均线策略是否有效" --source-system ExternalChat --json
```

通过任意对话输入触发千万级 checksum 独立验证。

Trigger ten-million-row checksum independent validation through chat input.

```bash
$PFI_OS_HOME/scripts/researchBusApi.sh submit-chat --text "请运行千万行独立验证 checksum 校验，每片100万行" --source-system ExternalChat --json
$PFI_OS_HOME/scripts/researchBusApi.sh process --system-name ResearchBus --limit 100 --json
```

行研系统聊天入口也会写入同一张共享请求表。

The AI-Research-System chat entry writes into the same shared request table.

```bash
cd $PFI_AI_RESEARCH_ROOT
python3 -m src.cli research-bus-submit --text "run hundred million rows independent validation, rows_per_shard 10 million" --json
```

通过 Webhook 写入研究总线。

Submit through the local webhook.

```bash
$PFI_OS_HOME/scripts/researchBusWebhook.sh --port 8765
curl -X POST http://127.0.0.1:8765/chat -H 'Content-Type: application/json' --data '{"text":"请验证 AAPL 的 RSI 策略"}'
```

准实时处理研究总线请求。

Near-real-time research bus processing.

```bash
RESEARCH_BUS_WATCH_INTERVAL_SECONDS=30 $PFI_OS_HOME/scripts/watchResearchBus.sh
```

串行同步 PFIOS、行研系统、消费行为和投递箱，一次运行后退出。

Run one serial sync across PFIOS, AI research, consumer state, and the chat dropbox.

```bash
$PFI_OS_HOME/scripts/syncResearchSystemsOnce.sh
```

安装 macOS LaunchAgent 后台同步配置。

Install the macOS LaunchAgent background sync configuration.

```bash
$PFI_OS_HOME/scripts/installResearchBusLaunchAgent.sh install
```

如果要尝试后台托管：

To try background hosting:

```bash
$PFI_OS_HOME/scripts/installResearchBusLaunchAgent.sh load
```

当前工程位于 macOS `Documents` 目录；如果 LaunchAgent 日志出现 `Operation not permitted`，需要在系统设置中给后台执行环境授予访问权限，或把工程迁移到不受 TCC 限制的位置。为避免反复失败，可执行：
当前安装器会把 runner 写入 `~/Library/Application Support/PFIOS/researchBusSyncRunner.sh`，但共享库和项目数据仍位于当前工程目录；如果 macOS 后台权限不足，仍可能被 TCC 拦截写入 `Documents`。
runner 已内置单步超时保护，避免后台任务卡死。当前机器验证结果：手动执行 runner 可完整同步；launchd 后台仍需要系统权限允许访问当前 `Documents` 工程目录。

The project is under macOS `Documents`; if LaunchAgent logs show `Operation not permitted`, grant the background process access or keep using the one-shot script.

```bash
$PFI_OS_HOME/scripts/installResearchBusLaunchAgent.sh unload
```

macOS 应用入口会自动打开浏览器。`/Applications/PFI_OS.app` 可以放入 Dock，也会出现在 Launchpad。

The macOS app launcher opens the browser automatically. `/Applications/PFI_OS.app` can be kept in the Dock and appears in Launchpad.

Moomoo 是优先真实数据入口，需要你本机启动 Moomoo OpenD；PFIOS 只使用行情数据，不接实盘交易。

Moomoo is the primary real-data entry and requires local Moomoo OpenD; PFIOS uses quote data only and does not connect to live trading.

如果 PFIOS 已经在运行，双击入口会刷新旧服务后重新打开工作台，避免旧进程保留过期代码状态。

If PFIOS is already running, the launcher refreshes the old service and reopens the workspace to avoid stale code state.

通过 `.app` 新启动时，关闭浏览器页面后后台服务会自动停止并释放内存。

When started from the `.app` launcher, closing the browser page automatically stops the service and releases memory.

`.app` 启动不会弹出 Terminal 窗口。启动日志保存在 `data/cache/pfi_os_macos_app.log`。

The `.app` launcher does not open a Terminal window. Launch logs are saved to `data/cache/pfi_os_macos_app.log`.

如果要重新生成三个 `.app` 或替换图标，先修改 `assets/PFIOSAppIconConfig.json`，再运行安装脚本。

To rebuild the three `.app` launchers or update the icon, edit `assets/PFIOSAppIconConfig.json` first, then run the installer script.

```bash
$PFI_OS_HOME/scripts/installMacAppLaunchers.sh
```

如果 `8501` 端口已经被占用，脚本会自动选择下一个可用端口。

If port `8501` is already in use, the launcher automatically chooses the next available port.

或者在终端运行一条命令。这个脚本不会自动打开浏览器。

Or run one command in Terminal. This script does not open a browser automatically.

```bash
$PFI_OS_HOME/scripts/startPFIOS.sh
```

停止 PFIOS：双击这个文件。

Stop PFIOS: double-click this file.

```text
$PFI_OS_HOME/StopPFIOS.command
```

检查 PFIOS 是否运行，不会打开浏览器。

Check whether PFIOS is running without opening a browser.

```bash
$PFI_OS_HOME/scripts/statusPFIOS.sh
```

日常开发默认先运行统一 macOS 验收入口。它不会触发最终验收、CI smoke、完整测试或策略 smoke gate。

Run the unified macOS acceptance hub first during normal development. It does not trigger release acceptance, CI smoke, the full test suite, or strategy smoke gates.

```bash
$PFI_OS_HOME/scripts/macosAcceptance.sh
```

需要单项检查时显式选择模式，例如 UI 可见性验收会用 headless Chrome 检查工作台页面真实渲染、生命周期面板和运行时证据，不运行完整 smoke。

Choose a mode explicitly for component checks. For example, UI visual acceptance uses headless Chrome to verify rendered workbench visibility, lifecycle panel, and runtime evidence without running full smoke.

```bash
$PFI_OS_HOME/scripts/macosAcceptance.sh --mode ui --summary-json
```

macOS public acceptance summary converts local runtime/UI evidence into GitHub-safe JSON/Markdown without starting services or running smoke.

```bash
$PFI_OS_HOME/scripts/macosAcceptance.sh --mode public-summary --summary-json
```

完整验收 PFIOS，不会打开浏览器。

Run full PFIOS verification without opening a browser.

```bash
$PFI_OS_HOME/scripts/verifyPFIOS.sh
```

最终成品验收会同时检查双击入口、报告目录、核心文档、关键功能源码、完整测试和日常检查，不会联网，也不会打开浏览器。该重门禁默认被保护，只有明确 release gate 时才运行。

Final product acceptance checks launchers, report directory, core docs, key feature source files, full tests, and daily checks. It does not use network access or open a browser. This heavy gate is guarded by default and should run only for deliberate release gates.

```bash
PFI_OS_ALLOW_HEAVY_SMOKE=1 $PFI_OS_HOME/scripts/finalAcceptanceCheck.sh
```

快速生成一份样例 Word 研究报告，不会打开浏览器。

Quickly generate one sample Word research report without opening a browser.

```bash
$PFI_OS_HOME/scripts/createSampleReport.sh
```

该样例报告会同时生成 RunMetadata，并写入 `PFIOSReportEvidenceV1` 报告证据层；如果缺少真实多源交叉校验，报告会诚实降级为 `NeedsMoreEvidence`。

首次配置真实数据 key，可以先创建本地 `.env` 模板。脚本不会覆盖已有 `.env`。

For first-time real-data key setup, create a local `.env` template first. The script does not overwrite an existing `.env`.

```bash
$PFI_OS_HOME/scripts/setupEnv.sh
```

联网验证不需要 key 的真实数据源。

Validate real data providers that do not require keys.

```bash
$PFI_OS_HOME/scripts/validateRealData.sh
```

检查 Moomoo 只读行情环境，不会调用交易接口。

Check the Moomoo quote-only environment without using trading APIs.

```bash
$PFI_OS_HOME/scripts/checkMoomoo.sh
```

配置足够 key 后，运行多源交叉校验。

After enough keys are configured, run cross-source validation.

```bash
$PFI_OS_HOME/scripts/validateCrossSource.sh
```

如果浏览器没有自动打开，请复制启动窗口显示的地址。

If the browser does not open automatically, copy the address shown in the launch window.

```text
http://localhost:8501
```

## Daily Use

第一步，打开 PFIOS。

Step one, open PFIOS.

打开后先查看首页的 `系统自检 System Health`。

After opening it, first review `系统自检 System Health` on the home page.

首页会显示 `工作台状态 Workspace Status` 和 `快速路径 Quick Paths`。

The home page shows `工作台状态 Workspace Status` and `快速路径 Quick Paths`.

首页还会显示 `日常使用 Runbook`，用于确认启动前检查、首次运行、真实数据接入和研究决策规则。

The home page also shows `日常使用 Runbook`, covering pre-start checks, first run, real-data use, and research decision rules.

如果你不知道先做什么，按 `快速路径 Quick Paths` 选择：单标的回测、参数扫描、报告中心或策略库。

If you are not sure where to start, use `快速路径 Quick Paths`: single backtest, parameter scan, report center, or strategy library.

日常使用建议顺序：

Recommended daily order:

1. 先看系统自检，确认没有 `Review`。
2. 先用 `Sample` 数据跑通一份默认报告。
3. 再切换真实数据源，并做多源交叉校验。
4. 最后只把策略已确认、成本后仍有效、回撤可接受的结果作为交易参考。

1. Review system health and confirm there is no `Review`.
2. Generate one default report with `Sample` data first.
3. Switch to real providers and run cross-source validation.
4. Use only approved, cost-adjusted, drawdown-acceptable results as trading references.

第二步，进入 `单标的回测 Single Backtest`。

Step two, go to `单标的回测 Single Backtest`.

单标的页面按四步使用：选择数据、选择策略、运行回测、复核风险。

The single backtest page follows four steps: choose data, choose strategy, run backtest, and review risk.

第一次使用建议保留默认值，直接点击运行。

For first use, keep the defaults and click run directly.

第三步，选择数据源、市场、标的、周期、日期和策略。

Step three, choose provider, market, symbol, interval, dates, and strategy.

周期下拉支持 `1min`、`5min`、`15min`、`30min`、`60min`、`1d`、`1w`、`1m`、`1q` 和 `1y`。

The interval selector supports `1min`, `5min`, `15min`, `30min`, `60min`, `1d`, `1w`, `1m`, `1q`, and `1y`.

如果真实数据源不原生支持周线、月线、季线或年线，系统会先拉取可用的较低周期数据，再在本地汇总，并在数据质量说明中记录来源周期。

If a real data provider does not natively support weekly, monthly, quarterly, or yearly bars, PFIOS fetches an available lower interval first, resamples it locally, and records the source interval in the data quality notes.

第四步，点击运行，查看指标、图表和 Word 报告路径。

Step four, click run, then review metrics, charts, and the Word report path.

运行后先看 `结果判读 Result Interpretation`，再看详细指标和图表。

After running, review `结果判读 Result Interpretation` before detailed metrics and charts.

结果判读会比较策略与买入持有、最大回撤和交易摩擦。

Result interpretation compares the strategy with buy-and-hold, maximum drawdown, and trading friction.

核心指标使用表格展示策略、买入持有和相对差值；相对收益等于策略收益率减去目标走势收益率。

Core metrics are shown as a table comparing strategy, buy-and-hold, and relative difference; relative return equals strategy return minus target price return.

胜率表示已完成买卖回合中盈利回合的占比；买入持有没有同口径回合交易，因此显示为不适用。

Win rate means the percentage of profitable completed round trips; buy-and-hold has no comparable round-trip trading unit, so it is shown as N/A.

第五步，进入 `报告中心 Report Center` 下载或查找历史报告。

Step five, go to `报告中心 Report Center` to download or find historical reports.

报告中心支持按类型、日期和关键词搜索，并可以直接打开报告目录。

The report center supports filtering by type, date, and keyword, and can open the report folder directly.

报告中心会汇总 Word 报告、运行元数据、数据质量文件和参数扫描实验记录。

The report center summarizes Word reports, run metadata, data quality files, and parameter scan experiment records.

报告中心的 `总览 Dashboard` 会显示资产类型、日期活动、运行收益/回撤分布、最近运行趋势、策略表现汇总和实验最佳收益。

The report center `总览 Dashboard` shows asset types, activity by date, run return/drawdown distribution, recent run trend, strategy performance summary, and top experiment returns.

`数据工具 Data Tools` 会显示数据源状态、代码格式示例、A 股代码转换和多源交叉校验。

`数据工具 Data Tools` shows provider status, symbol format examples, A-share symbol conversion, and cross-source validation.

如果数据源状态是 `NeedsConfig`，先配置对应的环境变量，再运行真实数据回测。

If a provider status is `NeedsConfig`, configure the related environment variable before running real-data backtests.

实验记录支持选择单个实验并查看最佳参数、核心风险收益指标和完整明细。

Experiment records support selecting a single experiment and reviewing best parameters, core risk-return metrics, and full run details.

参数扫描会生成参数稳定性分析，用于判断最佳参数附近是否也有较好表现，降低只挑单个最高分导致的过拟合风险。

Parameter scans generate parameter stability analysis to check whether nearby parameters also perform well, reducing overfitting risk from selecting only the single highest score.

参数扫描页会显示总收益、夏普和最大回撤热力图，并用 Top N 参数组合图比较最佳参数组。

The parameter scan page shows total-return, Sharpe, and max-drawdown heatmaps and compares the best parameter sets with a Top N chart.

参数扫描现在支持选择数据源、周期和已确认策略。内置策略可直接扫描常用参数；自定义策略必须先在策略库确认，扫描时可用 `indicator.parameter=值1,值2` 覆盖策略库参数，并用 `weight=0.50,0.75,1.00` 比较仓位权重。页面会先显示 `参数扫描预检`，只解析参数网格和选择项，提前提示组合数、上限占用、网格错误、标的错误或过大扫描；真正运行前不会读取行情或跑回测。页面会限制最大组合数，避免一次扫描过慢或制造低质量数据挖掘。

Parameter scan now supports provider, interval, and approved strategy selection. Built-in strategies expose common parameter grids; custom strategies must be approved in the strategy library first, then can use `indicator.parameter=value1,value2` plus `weight=0.50,0.75,1.00` for controlled scanning. The page shows `参数扫描预检` first, parsing only grid and selection metadata to warn about combination count, usage ratio, grid errors, invalid symbols, or oversized scans before market data or backtests run. The page enforces a max-combination limit to avoid slow runs and low-value data mining.

单标的回测页和 Word 回测报告会显示 Bootstrap 鲁棒性验证，用于查看模拟收益分布、回撤分布、亏损概率和达到目标收益概率。

The single-symbol backtest page and Word backtest reports show Bootstrap robustness validation for simulated return distribution, drawdown distribution, loss probability, and target-return probability.

参数扫描也会生成样本内/样本外验证，用训练期选择最佳参数，再检查同一参数在测试期是否仍有效。

Parameter scans also generate train-test validation, selecting the best parameter in the training period and checking whether the same parameter remains effective in the test period.

参数扫描还会生成 walk-forward 滚动验证，在多个训练/测试窗口中重复检验参数是否能够样本外延续。

Parameter scans also generate walk-forward validation, repeatedly testing whether parameters generalize across multiple rolling train/test windows.

实验详情会显示决策质量门禁和研究风险闸门，把数据质量、多源校验、回撤、交易摩擦、参数稳定性、样本外验证和 walk-forward 结果汇总为研究状态。

Experiment detail shows Decision Quality Score and the research risk gate, combining data quality, cross-source validation, drawdown, trading friction, parameter stability, out-of-sample validation, and walk-forward results into a research status.

实验详情支持一键导出实验 Word 研究报告，报告会汇总最佳参数、Top Runs 对比图、参数稳定性、样本外验证、walk-forward、Decision Quality Score 和研究风险闸门。

Experiment detail supports one-click export of an experiment Word research report, summarizing best parameters, a Top Runs comparison chart, parameter stability, out-of-sample validation, walk-forward validation, Decision Quality Score, and the research risk gate.

`策略库 Strategy Library` 会集中展示每个内置策略的研究假设、收益来源、失效环境、参数设置和确认说明。

`策略库 Strategy Library` centralizes each built-in strategy's research thesis, return sources, failure regimes, parameter settings, and approval notes.

单标的回测新增内置策略 `追跌杀涨 Buy Dips Sell Rallies`。该策略按你的规则研究“尾盘下跌补入、持仓盈利分档卖出”：A 股默认使用 14:30 作为决策点，日线数据没有盘中时间时使用当日收盘价作为近似；一天最多执行一个方向，不支持做空，不接实盘交易。

Single-symbol backtest now includes the built-in `追跌杀涨 Buy Dips Sell Rallies` strategy. It studies your rule of adding on pre-close declines and scaling out profitable holdings: A-shares default to a 14:30 decision point, daily data uses the daily close as a proxy when intraday time is unavailable, at most one direction is executed per day, short selling is disabled, and no live trading is connected.

`追跌杀涨 Buy Dips Sell Rallies` 买入公式：`BuyAmount = floor(abs(CurrentPrice / PreviousSessionClose - 1) * BuyBaseAmount)`。默认 `BuyBaseAmount = 100000`，例如下跌 `-3.54%` 时买入 `3540` 元；现金不足时跳过。

`追跌杀涨 Buy Dips Sell Rallies` buy formula: `BuyAmount = floor(abs(CurrentPrice / PreviousSessionClose - 1) * BuyBaseAmount)`. Default `BuyBaseAmount = 100000`; for example, a `-3.54%` decline buys `3540` yuan, and insufficient cash skips the order.

`追跌杀涨 Buy Dips Sell Rallies` 卖出规则使用最高档：收盘前上涨且持仓收益率约为 `CurrentPrice / WeightedAverageBuyCost - 1`，达到 `10%` 卖 `1/4`，达到 `15%` 卖 `1/2`，达到 `20%` 全卖。

`追跌杀涨 Buy Dips Sell Rallies` sell rule uses the highest reached threshold: on an up day, position return is approximated as `CurrentPrice / WeightedAverageBuyCost - 1`; sell `1/4` at `10%`, sell `1/2` at `15%`, and sell all at `20%`.

单标的回测新增 `追跌杀涨增强 Buy Dips Sell Rallies Enhanced`。增强版保留原低吸规则，并加入 RSI、布林带、均线和 MACD：超卖时提高低吸金额，弱趋势时降低买入金额，强趋势且未超买时小额参与上涨，并延迟卖出以减少上涨阶段明显落后于买入持有。

Single-symbol backtest now includes `追跌杀涨增强 Buy Dips Sell Rallies Enhanced`. The enhanced version keeps the original dip-buying rule and adds RSI, Bollinger Bands, moving averages, and MACD: it increases buys during oversold conditions, discounts buys in weak trends, participates with small buys in strong non-overbought trends, and delays exits to reduce upside lag versus buy-and-hold.

增强版目标不是保证收益更高，而是提供一个可回测的研究方向：下跌时维持较低回撤，上涨时通过趋势参与和延迟卖出提高上限。每次修改参数后都应比较买入持有、最大回撤、成本压力、市场环境分层和策略诊断。

The enhanced goal is not guaranteed outperformance; it is a testable research direction: keep lower drawdown in declines and improve upside through trend participation and delayed selling. After parameter changes, compare buy-and-hold, max drawdown, cost stress, market-regime breakdown, and strategy diagnostics.

新增自定义策略从 `策略库 Strategy Library` 进入：输入中文名，选择策略逻辑、指标组合和参数设置，系统会自动生成英文名、策略编号、类别、收益来源、研究假设、失效环境、no-code 可执行策略代码、策略档案、可运行规格 JSON 和 Pending 确认记录。

Create custom strategies from `策略库 Strategy Library`: enter a Chinese name, choose strategy logic, indicator combination, and parameter settings, then PFIOS automatically generates the English name, strategy id, category, return sources, thesis, failure regime, no-code executable strategy code, profile, runnable spec JSON, and Pending approval record.

策略库会显示自定义策略候选档案，但 Candidate 不等于 Approved，未确认策略仍不能运行正式回测。

The strategy library shows custom strategy candidate profiles, but Candidate does not mean Approved, and unapproved strategies still cannot run formal backtests.

候选档案会显示 `ReadyForReview` 或 `Incomplete`，用于提示研究假设、收益来源、失效环境和参数设置是否完整。

Candidate profiles show `ReadyForReview` or `Incomplete`, indicating whether research thesis, return source, failure regime, and parameter settings are complete.

内置策略档案可以在策略库编辑，修改会永久保存到 `data/strategyLibrary/StrategyProfileOverrides.json`，不会覆盖内置源码。

Built-in strategy profiles can be edited in the strategy library. Edits persist in `data/strategyLibrary/StrategyProfileOverrides.json` and do not overwrite built-in source code.

自定义策略规格永久保存到 `data/strategyLibrary/CustomStrategySpecs.json`。确认后，自定义策略会出现在单标的回测的策略下拉框；未确认时会显示 Pending Approval 并阻止回测。

Custom strategy specs persist in `data/strategyLibrary/CustomStrategySpecs.json`. After approval, custom strategies appear in the single-symbol backtest strategy selector; before approval, they show Pending Approval and backtesting is blocked.

编辑自定义策略规格会自动升级版本号、写入 `data/strategyLibrary/CustomStrategySpecHistory.json`，并创建新的 Pending 确认记录；策略库可以直接确认当前版本确认。

Editing a custom strategy spec automatically bumps the version, writes `data/strategyLibrary/CustomStrategySpecHistory.json`, and creates a new Pending approval record; the strategy library can approve the current version directly.

编辑后系统会同步更新 `src/pfi_os/strategies/custom/*.py` 中对应策略代码文件，避免 JSON 规格和代码版本不一致。

After editing, PFIOS synchronizes the matching strategy code file under `src/pfi_os/strategies/custom/*.py`, preventing spec and code version drift.

Word 回测报告会读取自定义策略规格，使用自定义策略的收益来源、研究假设、失效环境和参数设置生成策略审查内容。

Word backtest reports read custom strategy specs and use the custom return sources, thesis, failure regime, and parameter settings in the strategy review section.

候选策略代码会显示 `CodeDraft` 或 `CodeReadyForReview`，用于提示代码是否仍是模板草稿或缺少基本结构。

Candidate strategy code shows `CodeDraft` or `CodeReadyForReview`, indicating whether the code is still a template draft or missing basic structure.

候选策略会汇总为 `NotReady`、`ReadyForReview` 或 `ApprovedForResearch`，把档案质量、代码质量、smoke test 和确认状态合成一个研究前门禁。

Candidate strategies are summarized as `NotReady`, `ReadyForReview`, or `ApprovedForResearch`, combining profile quality, code quality, smoke test, and change confirmation status into one pre-research gate.

候选策略还会运行 Sample 数据 smoke test，只检查代码能否产出合法信号和 `[-1.00, 1.00]` 范围内的目标权重，不评价收益。

Candidate strategies also run a Sample data smoke test, checking only whether code can produce valid signals and target weights within `[-1.00, 1.00]`; it does not evaluate returns.

安全清理只删除 `.DS_Store` 和旧 HTML 文件，不会删除 Word、JSON 或 CSV 研究产物。

Safe cleanup only removes `.DS_Store` and legacy HTML files. It does not delete Word, JSON, or CSV research artifacts.

## Maintenance Commands

进入项目目录。

Enter the project directory.

```bash
cd $PFI_OS_HOME
```

按锁文件创建本地环境。安装必须显式执行；启动和测试命令不会自动安装依赖。

Create the local environment from the lock file. Installation is explicit;
startup and test commands never install dependencies automatically.

```bash
scripts/installLockedEnv.sh
```

运行测试。

Run tests.

```bash
scripts/runTests.sh
```

运行 PFI gate。

Run PFI gates.

```bash
scripts/pfiGate.sh fast
scripts/pfiGate.sh target
```

运行示例回测。

Run the sample backtest.

```bash
PYTHONPATH=src .venv/bin/python -m pfi_os.examples.run_sample_backtest
```

运行参数扫描示例。

Run the parameter scan example.

```bash
PYTHONPATH=src .venv/bin/python -m pfi_os.examples.run_parameter_scan
```

清理缓存。

Clean caches.

```bash
scripts/cleanCache.sh
```

清理报告目录杂项文件。

Clean report directory junk files.

```bash
scripts/cleanReportJunk.sh
```

打开报告目录。

Open the report directory.

```bash
scripts/openReports.sh
```

## Output Directories

代码保存在以下目录。

Code is stored in the following directory.

```text
$PFI_OS_HOME
```

报告默认按日期保存到以下目录。

Reports are saved by date in the following directory.

```text
~/Downloads/量化回测分析/YYYY-MM-DD/
```

## Documentation

功能说明书和增删修补功能账本。

Feature specification and change ledger.

- [FeatureSpecification](docs/FeatureSpecification.md)

使用手册。

User handbook.

- [Handbook](docs/Handbook.md)

开发与协作准则。

Development and collaboration guideline.

- [Guideline](docs/Guideline.md)

落地化工作流。

Implementation workflow.

- [Workflow](docs/Workflow.md)

数据源说明。

Data source guide.

- [DataSources](docs/DataSources.md)

测试说明。

Testing guide.

- [Testing](docs/Testing.md)

风险和限制。

Risks and limits.

- [RiskAndLimits](docs/RiskAndLimits.md)

报告说明。

Report guide.

- [ReportGuide](docs/ReportGuide.md)

报告补证据任务。

Report evidence gap tasks.

- [ReportEvidenceGapTasks](docs/ReportEvidenceGapTasks.md)

验证任务优先级计划。

Validation task priority plan.

- [ValidationPriorityPlan](docs/ValidationPriorityPlan.md)

验证任务执行记录。

Validation task execution.

- [ValidationTaskExecution](docs/ValidationTaskExecution.md)
