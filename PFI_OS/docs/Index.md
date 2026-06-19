# PFI_OS Docs Index

## Start Here

先读 `QuickStart.md`。

它是日常使用主入口，按启动、持仓、回测、报告、跨系统同步和常见问题组织。

主系统架构、子系统边界和共享底座，读 `PFI_OS.md`。

总控驾驶舱、日常状态、行动队列和证据来源，读 `ExecutiveCommandCenter.md`。

报告和验证的默认合并入口，读 `ReportValidationHub.md`。

报告证据是否足够支撑研究决策，读 `ReportDecisionSupport.md`。

报告缺失证据如何自动转为验证任务，读 `ReportEvidenceGapTasks.md`。

验证任务太多时如何决定先做哪一个，读 `ValidationPriorityPlan.md`。

如何执行一个验证任务并留下可追溯结果，读 `ValidationTaskExecution.md`。

需要深入理解策略、指标、报告、风险和公式时，再读 `Handbook.md`。

跨系统同步、任意聊天框输入、持仓候选、行研系统和独立验证互通，读 `ResearchBus.md`。

跨系统开发排期、谁主导、谁暂停、后续合并顺序，读 `SystemCoordinationPlan.md`。

公开信息研究标准、高 ROI 外部方案吸收、子系统升级清单，读 `PublicResearchUpgradePlan.md`。

事件驱动行情层、行情事件日志和后续数据湖/回放入口，读 `MarketEventLayer.md`。

可复现数据湖 manifest、checksum、partition 和 replay cursor，读 `ReproducibleDataLake.md`。

事件回放 batch、cursor 过滤和三模式模拟内核输入，读 `EventReplay.md`。

向量化研究模式、replay 到 OHLCV、快速参数扫描，读 `VectorizedResearchMode.md`。

## Documents

| 文档 Document | 用途 Purpose |
| --- | --- |
| `QuickStart.md` | 快速使用说明：启动、持仓、回测、报告、跨系统同步和常见问题。 |
| `PFI_OS.md` | PFI_OS 主系统架构、子系统边界、共享底座和入口说明。 |
| `MarketEventLayer.md` | 事件驱动行情层：把 OHLCV bar 转成可排序、可去重、可落盘的 `BarClosed` 事件。 |
| `ReproducibleDataLake.md` | 可复现数据湖：登记本地不可变数据资产、checksum、partition 和 replay cursor。 |
| `EventReplay.md` | 事件回放：按 replay cursor 读取不可变 market event JSONL，生成确定性 replay batch。 |
| `VectorizedResearchMode.md` | 向量化研究模式：把 EventReplay 转成稳定 OHLCV 输入并运行快速参数扫描。 |
| `CompanyCashFlowCommand.md` | 公司经营现金流：余额、收入、支出、应收、应付、Runway 和证据化行动队列。 |
| `PolicyIntelligenceRadar.md` | 政策机会情报：来源权威、行业映射、影响评分、行动队列和证据门。 |
| `ConsumptionGuard.md` | 消费守卫：消费事件、冲动风险、固定成本、可投资现金流压力和证据门。 |
| `ReportValidationHub.md` | 报告验证工作台：默认只读合并报告证据、补证据候选和验证优先级，减少重复入口和 token 压力。 |
| `ReportDecisionSupport.md` | 报告决策支持索引：判断每份报告是否可继续研究、只能观察、需要更多证据或不要使用。 |
| `ReportEvidenceGapTasks.md` | 报告补证据任务：把 `NeedsMoreEvidence` / `DoNotUse` 报告的缺口追加到验证任务队列。 |
| `ValidationPriorityPlan.md` | 验证任务优先级计划：按证据价值、阻塞项和可执行性排序待验证任务。 |
| `ValidationTaskExecution.md` | 验证任务执行记录：运行一个只读验证任务并输出 Pass/Review/Blocked/Error 证据。 |
| `FeatureSpecification.md` / `FeatureSpecification.pdf` | 功能说明书和增删修补功能账本。Feature specification and change ledger. |
| `Handbook.md` | 深入使用手册、公式、策略解释和专业术语。 |
| `ReportGuide.md` | Word 报告、报告中心和运行判读说明。Word report, report center, and run interpretation guide. |
| `ResearchBus.md` | PFIOS、行研系统、持仓和独立验证系统互通说明。Shared research bus and independent validation interop guide. |
| `DataTrust.md` | 只读证据审计：项目控制文件、数据源、策略库、持仓、ResearchBus、实验和报告可追溯性。Read-only evidence audit for project controls, data providers, strategy library, holdings, ResearchBus, experiments, and reports. |
| `DailyReadiness.md` | 日常开机前就绪检查：核心门禁、数据源状态、最新报告和行动项。Daily pre-use readiness gate for core evidence, providers, latest report, and actions. |
| `MacOSAppAcceptanceLite.md` | macOS app 入口轻量验收：检查 Desktop、Downloads、Applications 的 `PFI_OS.app`，不运行完整 smoke。 |
| `MacOSAcceptanceHub.md` | macOS 统一验收入口：默认 daily 模式合并轻量检查和公开摘要，减少脚本选择成本。 |
| `MacOSLifecycleReadiness.md` | macOS 生命周期只读验收：检查启动、停止、自动关闭、缓存清理保护和 UI allowlist，不运行完整 smoke。 |
| `MacOSRuntimeAcceptance.md` | macOS 受控运行验收：真实启动、health、缓存保护、停止和停止后 dry-run，不运行完整 smoke。 |
| `MacOSUIVisualAcceptance.md` | macOS UI 可见性验收：用 headless Chrome 检查工作台页面、生命周期面板和运行时证据，不运行完整 smoke。 |
| `MacOSPublicAcceptanceSummary.md` | macOS 公开验收摘要：把本机 runtime/UI evidence 转成 GitHub-safe JSON/Markdown。 |
| `SystemCoordinationPlan.md` | 总系统协调计划：母子系统职责、暂停项、优先级、合并顺序和时间线。Master coordination plan for subsystem ownership, freeze list, priorities, integration order, and timeline. |
| `PublicResearchUpgradePlan.md` | 公开信息研究标准、成熟开源/竞品机制吸收和高 ROI 子系统升级清单。Public-source research standard and high-ROI subsystem upgrade plan. |
| `ResearchBusSchema.json` | 统一研究数据总线 SQLite/JSON schema 合约。Shared ResearchBus SQLite/JSON schema contract. |
| `DataSources.md` | 数据源、API Key、真实数据限制说明。Data providers, API keys, and real-data limitations. |
| `Workflow.md` | 落地化工作流和实现顺序。Implementation workflow and delivery sequence. |
| `RiskAndLimits.md` | 风险、限制、禁止实盘交易规则。Risks, limits, and no-live-trading rules. |
| `Testing.md` | 自动测试和手动验证命令。Automated tests and manual verification commands. |
| `Guideline.md` | 修改、验证、风险和回滚原则。Change, verification, risk, and rollback principles. |
| `AcceptanceChecklist.md` | 成品验收清单和当前限制。Product acceptance checklist and current limitations. |
| `ReleaseNotes.md` | 当前版本能力和限制。Current build capabilities and limitations. |
| `MaturityRoadmap.md` | 当前成熟度和后续产品路线。Current maturity and product roadmap. |
| `OpenSourceReference.md` | 开源量化平台参考和后续吸收路线。Open-source quant platform references and adoption roadmap. |

## Fast Path

第一次使用：双击 `~/Desktop/PFI_OS.app`、`~/Downloads/PFI_OS.app` 或 `/Applications/PFI_OS.app`。

停止使用：双击 `$PFI_OS_HOME/StopPFIOS.command`。

报告目录：`~/Downloads/量化回测分析`。

快速生成样例报告：`$PFI_OS_HOME/scripts/createSampleReport.sh`。

日常检查：`$PFI_OS_HOME/scripts/dailyCheck.sh`。

macOS 统一验收入口：`$PFI_OS_HOME/scripts/macosAcceptance.sh`。

日常开发轻量检查：`$PFI_OS_HOME/scripts/devReadyCheck.sh --summary-json`。

macOS app 入口轻量验收：`$PFI_OS_HOME/scripts/macosAppAcceptanceLite.sh --summary-json`。

macOS 生命周期只读验收：`$PFI_OS_HOME/scripts/macosLifecycleReadiness.sh --summary-json`。

macOS 受控运行验收：`$PFI_OS_HOME/scripts/macosRuntimeAcceptance.sh --summary-json`。

macOS UI 可见性验收：`$PFI_OS_HOME/scripts/uiVisualAcceptance.sh --summary-json`。

macOS 公开验收摘要：`$PFI_OS_HOME/scripts/macosPublicAcceptanceSummary.sh`。

日常就绪正式产物：`$PFI_OS_HOME/scripts/dailyCheck.sh --output-dir data/systemAudit`。


公司现金流快照：`$PFI_OS_HOME/scripts/cashFlowCommand.sh --output-dir data/cashflow`。

政策雷达快照：`$PFI_OS_HOME/scripts/policyRadar.sh --output-dir data/policy`。

消费守卫快照：`$PFI_OS_HOME/scripts/consumptionGuard.sh --output-dir data/consumption`。

总控报告：`$PFI_OS_HOME/scripts/commandCenter.sh --output-dir data/commandCenter`。

行情事件日志：`$PFI_OS_HOME/scripts/marketEventLayer.sh --output-dir data/marketEvents`。

数据湖 Manifest：`$PFI_OS_HOME/scripts/dataLakeManifest.sh --output-dir data/dataLake`。

事件回放：`scripts/eventReplay.sh --output-dir data/replay`。

向量化研究扫描：`scripts/vectorizedResearch.sh --symbol SPY --market US --interval 1d --param short_window=2,3 --param long_window=4,5`。

报告验证工作台：`$PFI_OS_HOME/scripts/reportValidation.sh`。

报告证据索引高级产物：`$PFI_OS_HOME/scripts/reportDecisionSupport.sh --output-dir data/reportDecision`。

报告补证据任务预览：`$PFI_OS_HOME/scripts/reportGapTasks.sh --dry-run --output-dir data/reportDecision`。

报告补证据任务入队：`$PFI_OS_HOME/scripts/reportGapTasks.sh --output-dir data/reportDecision`。

验证任务优先级计划：`$PFI_OS_HOME/scripts/validationPriorityPlan.sh --output-dir data/validationQueue`。

执行最高优先级验证任务：`$PFI_OS_HOME/scripts/runValidationTask.sh --output-dir data/validationQueue`。

最终成品验收：`PFI_OS_ALLOW_HEAVY_SMOKE=1 $PFI_OS_HOME/scripts/finalAcceptanceCheck.sh`。仅在明确发布闸门或完整验收时运行；日常 agent 工作不要运行。

只读证据审计：`PYTHONPATH=src .venv/bin/python -m pfi_os.examples.data_trust_audit --output-dir /private/tmp/pfi_os-data-trust`。

联网验证：`$PFI_OS_HOME/scripts/dailyCheck.sh --network`。

Moomoo 只读行情诊断：`$PFI_OS_HOME/scripts/checkMoomoo.sh`。

持仓簿：`$PFI_OS_HOME/data/holdings/HoldingsBook.json`。

持仓导入目录：`$PFI_OS_HOME/data/holdings/imports`。

统一研究数据总线：`$PFI_OS_HOME/scripts/syncResearchBus.sh --json`。

独立验证系统：`$PFI_OS_HOME/scripts/runIndependentValidation.sh run --synthetic-rows 1000000000 --rows-per-shard 100000000 --json`。
