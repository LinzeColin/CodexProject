# EVA_OS Docs Index

## Start Here

先读 `QuickStart.md`。

它是日常使用主入口，按启动、持仓、回测、报告、跨系统同步和常见问题组织。

主系统架构、子系统边界和共享底座，读 `EVA_OS.md`。

总控驾驶舱、日常状态、行动队列和证据来源，读 `ExecutiveCommandCenter.md`。

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

## Documents

| 文档 Document | 用途 Purpose |
| --- | --- |
| `QuickStart.md` | 快速使用说明：启动、持仓、回测、报告、跨系统同步和常见问题。 |
| `EVA_OS.md` | EVA_OS 主系统架构、子系统边界、共享底座和入口说明。 |
| `ExecutiveCommandCenter.md` | 总控驾驶舱：聚合就绪检查、总集成审计、Token ROI、最新报告和行动队列。 |
| `MarketEventLayer.md` | 事件驱动行情层：把 OHLCV bar 转成可排序、可去重、可落盘的 `BarClosed` 事件。 |
| `ReproducibleDataLake.md` | 可复现数据湖：登记本地不可变数据资产、checksum、partition 和 replay cursor。 |
| `EventReplay.md` | 事件回放：按 replay cursor 读取不可变 market event JSONL，生成确定性 replay batch。 |
| `CompanyCashFlowCommand.md` | 公司经营现金流：余额、收入、支出、应收、应付、Runway 和证据化行动队列。 |
| `PolicyIntelligenceRadar.md` | 政策机会情报：来源权威、行业映射、影响评分、行动队列和证据门。 |
| `ConsumptionGuard.md` | 消费守卫：消费事件、冲动风险、固定成本、可投资现金流压力和证据门。 |
| `ReportDecisionSupport.md` | 报告决策支持索引：判断每份报告是否可继续研究、只能观察、需要更多证据或不要使用。 |
| `ReportEvidenceGapTasks.md` | 报告补证据任务：把 `NeedsMoreEvidence` / `DoNotUse` 报告的缺口追加到验证任务队列。 |
| `ValidationPriorityPlan.md` | 验证任务优先级计划：按证据价值、阻塞项和可执行性排序待验证任务。 |
| `ValidationTaskExecution.md` | 验证任务执行记录：运行一个只读验证任务并输出 Pass/Review/Blocked/Error 证据。 |
| `TokenROI.md` | Token ROI Ledger：登记审计、报告和元数据产物，形成 Value Layer 台账。 |
| `FeatureSpecification.md` / `FeatureSpecification.pdf` | 功能说明书和增删修补功能账本。Feature specification and change ledger. |
| `Handbook.md` | 深入使用手册、公式、策略解释和专业术语。 |
| `ReportGuide.md` | Word 报告、报告中心和运行判读说明。Word report, report center, and run interpretation guide. |
| `ResearchBus.md` | QuantLab、行研系统、持仓和独立验证系统互通说明。Shared research bus and independent validation interop guide. |
| `DataTrust.md` | 只读证据审计：项目控制文件、数据源、策略库、持仓、ResearchBus、实验和报告可追溯性。Read-only evidence audit for project controls, data providers, strategy library, holdings, ResearchBus, experiments, and reports. |
| `DailyReadiness.md` | 日常开机前就绪检查：核心门禁、数据源状态、最新报告和行动项。Daily pre-use readiness gate for core evidence, providers, latest report, and actions. |
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

第一次使用：双击 `/Users/linzezhang/Desktop/EVA_OS.app`、`/Users/linzezhang/Downloads/EVA_OS.app` 或 `/Applications/EVA_OS.app`。

停止使用：双击 `/Users/linzezhang/Documents/Codex/2026-06-04/files-mentioned-by-the-user-quantlab/outputs/CodexFinance/StopQuantLab.command`。

报告目录：`/Users/linzezhang/Downloads/量化回测分析`。

快速生成样例报告：`/Users/linzezhang/Documents/Codex/2026-06-13/files-mentioned-by-the-user-eva/outputs/CodexFinance/scripts/createSampleReport.sh`。

日常检查：`/Users/linzezhang/Documents/Codex/2026-06-13/files-mentioned-by-the-user-eva/outputs/CodexFinance/scripts/dailyCheck.sh`。

日常就绪正式产物：`/Users/linzezhang/Documents/Codex/2026-06-13/files-mentioned-by-the-user-eva/outputs/CodexFinance/scripts/dailyCheck.sh --output-dir data/systemAudit`。

Token ROI 台账：`/Users/linzezhang/Documents/Codex/2026-06-13/files-mentioned-by-the-user-eva/outputs/CodexFinance/scripts/tokenRoiLedger.sh --output-dir data/value`。

公司现金流快照：`/Users/linzezhang/Documents/Codex/2026-06-13/files-mentioned-by-the-user-eva/outputs/CodexFinance/scripts/cashFlowCommand.sh --output-dir data/cashflow`。

政策雷达快照：`/Users/linzezhang/Documents/Codex/2026-06-13/files-mentioned-by-the-user-eva/outputs/CodexFinance/scripts/policyRadar.sh --output-dir data/policy`。

消费守卫快照：`/Users/linzezhang/Documents/Codex/2026-06-13/files-mentioned-by-the-user-eva/outputs/CodexFinance/scripts/consumptionGuard.sh --output-dir data/consumption`。

总控报告：`/Users/linzezhang/Documents/Codex/2026-06-13/files-mentioned-by-the-user-eva/outputs/CodexFinance/scripts/commandCenter.sh --output-dir data/commandCenter`。

行情事件日志：`/Users/linzezhang/Documents/Codex/2026-06-13/files-mentioned-by-the-user-eva/outputs/CodexFinance/scripts/marketEventLayer.sh --output-dir data/marketEvents`。

数据湖 Manifest：`/Users/linzezhang/Documents/Codex/2026-06-13/files-mentioned-by-the-user-eva/outputs/CodexFinance/scripts/dataLakeManifest.sh --output-dir data/dataLake`。

事件回放：`scripts/eventReplay.sh --output-dir data/replay`。

报告证据索引：`/Users/linzezhang/Documents/Codex/2026-06-13/files-mentioned-by-the-user-eva/outputs/CodexFinance/scripts/reportDecisionSupport.sh --output-dir data/reportDecision`。

报告补证据任务预览：`/Users/linzezhang/Documents/Codex/2026-06-13/files-mentioned-by-the-user-eva/outputs/CodexFinance/scripts/reportGapTasks.sh --dry-run --output-dir data/reportDecision`。

报告补证据任务入队：`/Users/linzezhang/Documents/Codex/2026-06-13/files-mentioned-by-the-user-eva/outputs/CodexFinance/scripts/reportGapTasks.sh --output-dir data/reportDecision`。

验证任务优先级计划：`/Users/linzezhang/Documents/Codex/2026-06-13/files-mentioned-by-the-user-eva/outputs/CodexFinance/scripts/validationPriorityPlan.sh --output-dir data/validationQueue`。

执行最高优先级验证任务：`/Users/linzezhang/Documents/Codex/2026-06-13/files-mentioned-by-the-user-eva/outputs/CodexFinance/scripts/runValidationTask.sh --output-dir data/validationQueue`。

最终成品验收：`/Users/linzezhang/Documents/Codex/2026-06-13/files-mentioned-by-the-user-eva/outputs/CodexFinance/scripts/finalAcceptanceCheck.sh`。

只读证据审计：`PYTHONPATH=src .venv/bin/python -m quantlab.examples.data_trust_audit --output-dir /private/tmp/quantlab-data-trust`。

联网验证：`/Users/linzezhang/Documents/Codex/2026-06-13/files-mentioned-by-the-user-eva/outputs/CodexFinance/scripts/dailyCheck.sh --network`。

Moomoo 只读行情诊断：`/Users/linzezhang/Documents/Codex/2026-06-13/files-mentioned-by-the-user-eva/outputs/CodexFinance/scripts/checkMoomoo.sh`。

持仓簿：`/Users/linzezhang/Documents/Codex/2026-06-04/files-mentioned-by-the-user-quantlab/outputs/CodexFinance/data/holdings/HoldingsBook.json`。

持仓导入目录：`/Users/linzezhang/Documents/Codex/2026-06-04/files-mentioned-by-the-user-quantlab/outputs/CodexFinance/data/holdings/imports`。

统一研究数据总线：`/Users/linzezhang/Documents/Codex/2026-06-13/files-mentioned-by-the-user-eva/outputs/CodexFinance/scripts/syncResearchBus.sh --json`。

独立验证系统：`/Users/linzezhang/Documents/Codex/2026-06-13/files-mentioned-by-the-user-eva/outputs/CodexFinance/scripts/runIndependentValidation.sh run --synthetic-rows 1000000000 --rows-per-shard 100000000 --json`。
