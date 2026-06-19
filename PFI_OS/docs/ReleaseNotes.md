# PFIOS Release Notes

## 2026-06-17 macOS App Runtime Acceptance Hardening

- `PFIOSMacOSRuntimeAcceptanceV1` now uses wider bounded timeouts for support scripts during real `.app` open acceptance, reducing false failures from slow `statusPFIOS.sh` or `cleanCache.sh --dry-run --json` on a busy Mac.
- Runtime acceptance retries transient App Lite precheck failures once, uses a longer launcher dry-run window, and returns compact failed-check details when App Lite still blocks.
- Final-code real app-open acceptance passed for `~/Desktop/PFI_OS.app`, `~/Downloads/PFI_OS.app`, and `/Applications/PFI_OS.app`: each returned `status=Pass pass=10 fail=0 launch_method=app`.

## 2026-06-17 Command Center Action Router

- `总控驾驶舱` 新增 `PFIOSCommandCenterActionRouterV1`，把行动队列、热点快速预检、参数扫描预检、报告验证和 macOS 日常验收聚合为 `统一下一步`。
- 页面展示推荐入口、P0/P1 数量、路由数量和直达链接，减少用户在多个页面之间查找功能。
- 路由器只读取总控 compact payload 和静态路由元数据，不扫描报告、不读取行情、不运行回测、不执行 macOS 脚本、不清理缓存。

## 2026-06-17 Hotspot Quick Preflight

- 热点分析新增 `PFIOSHotspotQuickPreflightV1` 预检层，生成前先展示缓存状态、对象数、切片上限、预计 provider 请求数和下一步建议。
- `CacheHit` 会提示点击生成优先复用本地派生缓存；`LargeRun` 会建议先切回 `快速预览`，把完整复盘保留给报告前使用。
- 缓存清理入口移动到 `高级缓存与清理` 折叠区，默认页面先给用户判断和建议，减少控件噪音。
- 预检只读 UI selection 和 cache metadata，不读取行情、不生成热点、不连接券商、不创建订单、不修改持仓。

## 2026-06-17 Parameter Scan Preflight

- 参数扫描新增 `PFIOSParameterScanPreflightV1` 预检层，运行前先展示组合数、最大组合数、上限占用、策略类型和下一步建议。
- `TooMany` 会阻止超过上限的扫描；`InvalidGrid` 和 `Blocked` 分别提示网格错误和标的错误；`LargeRun` 会建议先缩小网格。
- 页面复用同一份网格解析结果进入实际扫描，减少重复解析和用户困惑。
- 预检只解析参数网格和选择项，不读取行情、不运行回测、不生成报告、不连接券商、不创建订单、不修改持仓。

## 2026-06-17 Report Validation Hub

- 新增 `PFIOSReportValidationHubV1` 和 `scripts/reportValidation.sh`，把报告证据索引、补证据候选和验证优先级计划合并成默认只读入口。
- 无参数运行等价于 `--mode daily --summary-json`，只输出 compact 摘要，降低 agent 接手、UI 查看和日常检查的 token 压力。
- Streamlit 报告中心新增 `报告验证工作台` 摘要；原本会写文件、入队或执行验证的按钮收进高级动作。
- 高级命令 `reportDecisionSupport.sh`、`reportGapTasks.sh`、`validationPriorityPlan.sh` 和 `runValidationTask.sh` 保留，用于明确需要产物、入队或执行验证的场景。
- 默认入口不写文件、不追加验证队列、不执行验证任务、不刷新行情、不连接券商、不创建订单、不修改持仓。

## 2026-06-16 macOS Runtime Acceptance

- Hotspot page now exposes current-request persisted cache status, directory cache metrics, and a button that clears only the current request-key cache; `scripts/hotspotRuntimeSummary.sh` also supports `--cache-status` and `--invalidate-cache`.
- Hotspot generation now records `PFIOSHotspotRequestTraceV1` compact per-symbol timing and error diagnostics so slow providers/symbols can be identified before recomputing.
- 新增 `PFIOSMacOSRuntimeAcceptanceV1` 和 `scripts/macosRuntimeAcceptance.sh`，用于受控真实启动本地服务、检查 health、验证运行中缓存清理拒绝、停止服务并复核停止状态。
- `scripts/macosRuntimeAcceptance.sh --launch-method app --app-path ~/Downloads/PFI_OS.app --summary-json` 可通过真实 `.app` 打开路径做启动、health、缓存保护和停止闭环验收。
- Native launcher 现在通过 `posix_spawn("/bin/zsh", "-f", StartPFIOS.command)` 启动本地脚本，不再通过 `open -a Terminal` 兜转启动。
- `scripts/installPFIOSEntryApps.sh` 先在临时目录清理元数据、构建并 ad-hoc 签名 app bundle，再用 `ditto --norsrc --noextattr --noacl` 安装到 Desktop、Downloads 和 Applications，避免目标目录的 Finder/resource metadata 导致 codesign 失败。
- Runtime Acceptance 默认发现已有服务时 fail-closed，避免误停用户当前打开的工作台。
- App Runtime Acceptance 未显式指定 `--start-timeout` 时默认等待 300 秒；脚本超时会返回结构化 Fail check，不再抛出 `UnexpectedException`。
- `StartPFIOS.command` 的启动锁等待默认降为 30 秒，减少 `.app` 重复唤起或 stale lock 时的等待时间。
- Native launcher 的本地 health 端口探测使用短连接超时，减少无服务时点击 `.app` 和 dry-run 的等待。
- Runtime Acceptance 的 app 模式会先尝试 macOS `open -n`；若短窗口内没有日志或 health，会 fallback 到同一 app bundle 的 `Contents/MacOS/PFI_OS`，并在停止阶段清理本项目残留 launcher 进程。
- `macOS 生命周期` 面板新增 `运行时验收` Terminal 命令展示，但不加入 Streamlit allowlist，避免从页面内停止当前会话。
- `scripts/cleanCache.sh` 改为端口 + 进程 cwd 的 scoped detection，可识别 `startPFIOS.sh` 的相对路径 Streamlit 启动，避免服务运行时误进入 delete mode。
- App Lite launcher dry-run timeout 现在返回结构化 Fail check，不再让上层验收 traceback。
- 该入口不运行 `scripts/finalAcceptanceCheck.sh`、`scripts/ciSmoke.sh`、full pytest、浏览器自动化、行情刷新、回测、券商连接、订单、付款或持仓写入。

## 2026-06-16 macOS Lifecycle Readiness

- 新增 `PFIOSMacOSLifecycleReadinessV1` 和 `scripts/macosLifecycleReadiness.sh`，用于只读检查启动、停止、heartbeat 自动关闭、缓存清理保护、UI allowlist 和 App 轻量验收。
- Streamlit `macOS 生命周期` 面板新增 `生命周期验收` 按钮，并通过 allowlist 运行该只读脚本。
- 该 readiness 会汇总状态脚本、cache dry-run compact summary 和 `macosAppAcceptanceLite` compact summary，不启动服务、不停止服务、不删除缓存。
- 该入口不运行 `scripts/finalAcceptanceCheck.sh`、`scripts/ciSmoke.sh`、full pytest、浏览器自动化、行情刷新、回测、券商连接、订单、付款或持仓写入。

## 2026-06-16 macOS App Acceptance Lite

- 新增 `PFIOSMacOSAppAcceptanceLiteV1` 和 `scripts/macosAppAcceptanceLite.sh`，用于日常轻量检查 Desktop、Downloads、Applications 三个 `PFI_OS.app` 入口。
- 轻量验收检查 app bundle、native launcher、Info.plist、`PFI_OS_PROJECT_ROOT` binding、GitHub fallback 缺失、codesign、launcher dry-run、状态脚本和本地 `_stcore/health`。
- Streamlit `macOS 生命周期` 面板新增 `轻量验收` 按钮，并通过 allowlist 运行该只读脚本。
- 该入口不运行 `scripts/finalAcceptanceCheck.sh`、`scripts/ciSmoke.sh`、full pytest、浏览器自动化、行情刷新、回测、券商连接、订单、付款或持仓写入，用于减少重复 SmokeTest 噪音。

## 2026-06-16 52ETF Public Snapshot Artifact

- 新增 `PFIOS52ETFPublicSnapshotV1`，把 `https://52etf.site/` 公开大盘云图页面契约固化为低 token latest snapshot。
- 新增 `scripts/site52etfSnapshot.sh` 和 `src/pfi_os/examples/site52etf_snapshot.py`，可输出 `Site52ETFPublicSnapshot_DDMMYYYY.json` 和 `Site52ETFPublicSnapshot_latest.json`。
- 热点页面勾选 `显示 52ETF 公开参考` 后会优先读取 `data/integrations/site52etf/Site52ETFPublicSnapshot_latest.json`；缺失时才使用 Streamlit cache 在线读取公开页面。
- 当 Python `urllib` 在本机遇到证书链问题时，读取器会降级使用系统 `/usr/bin/curl` 读取同一个公开页面；curl 失败仍返回 `Unavailable/NeedsReview`。
- 52ETF snapshot 只保存板块、指标、操作提示、刷新节奏、证据闸门和只读边界，不保存 raw HTML、cookies、登录态、行情明细、回测输入、订单或持仓修改。
- `data/integrations/site52etf/*.json` 默认 gitignored，只保留 `.gitkeep`，避免本地页面刷新产物污染 Git。


- 安全边界不变：只读取本地 reviewed JSON，不伪造收入、节省成本、避免损失或资产复用价值，不交易、不下单、不付款、不转账。

## 2026-06-16 Consumption Guard Reviewed Input Refresh

- 新增 `scripts/consumptionReviewedInputRefresh.sh` 和 `src/pfi_os/consumption/reviewed_input.py`，把 Consumption Guard 推进到 real-input refresh MVP。
- 默认真实输入路径为 `data/private/consumption/ConsumptionGuardReviewedInput.json`，该路径被 Git 忽略；缺少输入时返回 `PFIOSConsumptionGuardReviewedInputRefreshV1 status=Blocked` 且不写入输出。
- 新增 public-safe 模板 `data/consumption/ConsumptionGuardReviewedInput.example.json` 和 schema `shared/schema/consumption_guard_reviewed_input.schema.json`。
- `scripts/refreshRuntimeSummaries.sh` 新增 `--consumption-event-path`，可以在刷新四个 compact summaries 时复用同一 reviewed consumption input。
- 安全边界不变：只读取本地 reviewed JSON，不连接支付宝、银行、工资、税务、支付、券商或交易系统，不执行付款、转账、退款、冻结账户或投资动作。

## 2026-06-16 macOS PFI_OS App Launch Hardening

- Replaced the shell-script app executable with a native Mach-O launcher built from `macos/PFI_OS_launcher.c`.
- `PFI_OS.app` now reads `Contents/Resources/PFI_OS_PROJECT_ROOT`, opens the local `StartPFIOS.command`, and never falls back to GitHub when the local project path is missing.
- `scripts/installPFIOSEntryApps.sh` compiles the native launcher with `clang`, writes the current local project root into Desktop, Downloads, and Applications app bundles, clears xattrs, and ad-hoc signs each app.
- `StartPFIOS.command` now records launch-lock pid metadata and immediately removes stale locks without pid metadata; `scripts/stopPFIOS.sh` removes the launch lock during stop.
- Verified `open -n ~/Downloads/PFI_OS.app` starts local PFI_OS and `/_stcore/health` returns `ok`.

## 2026-06-16 Policy Intelligence Reviewed Input Refresh

- 新增 `scripts/policyReviewedInputRefresh.sh` 和 `src/pfi_os/policy/reviewed_input.py`，把 Policy Intelligence 推进到 real-input refresh MVP。
- 默认真实输入路径为 `data/private/policy/PolicyReviewedInput.json`，该路径被 Git 忽略；缺少输入时返回 `PFIOSPolicyReviewedInputRefreshV1 status=Blocked` 且不写入输出。
- 新增 public-safe 模板 `data/policy/PolicyReviewedInput.example.json` 和 schema `shared/schema/policy_reviewed_input.schema.json`。
- `scripts/refreshRuntimeSummaries.sh` 新增 `--policy-entry-path`，可以在刷新四个 compact summaries 时复用同一 reviewed policy input。
- 安全边界不变：只读取本地 reviewed JSON，不抓取实时政策、不登录政府平台、不提交申请、不付款、不生成法律/税务/合规/投资结论、不交易。

## 2026-06-16 Company CashFlow Reviewed Input Refresh

- 新增 `scripts/cashFlowReviewedInputRefresh.sh` 和 `src/pfi_os/business/cashflow_reviewed_input.py`，把 Company CashFlow 推进到 real-input refresh MVP。
- 默认真实输入路径为 `data/private/cashflow/CompanyCashFlowReviewedInput.json`，该路径被 Git 忽略；缺少输入时返回 `PFIOSCompanyCashFlowReviewedInputRefreshV1 status=Blocked` 且不写入输出。
- 新增 public-safe 模板 `data/cashflow/CompanyCashFlowReviewedInput.example.json` 和 schema `shared/schema/company_cashflow_reviewed_input.schema.json`。
- `scripts/refreshRuntimeSummaries.sh` 新增 `--cashflow-entry-path`，可以在刷新四个 compact summaries 时复用同一 reviewed cashflow input。
- 安全边界不变：只读取本地 reviewed JSON，不连接银行、支付、工资、税务、会计、券商或交易系统，不执行付款、转账或账户动作。

## 2026-06-16 Runtime Summary Latest Artifact Refresh

- 新命令输出 `PFIOSRuntimeSummaryRefreshV1`，只写 runtime summary JSON，不重写完整 records、entries、opportunities、events、CSV、Markdown 或 PDF，降低交接和总控聚合的 token 压力。
- 生成的 runtime summary `outputs` 使用 repo-relative 路径，避免把本机绝对路径固化进 public GitHub。
- Final acceptance 现在检查四个 runtime latest artifacts 存在且 schema 正确，防止总控长期 fallback 到 full snapshot。
- 安全边界不变：不读取私密导入、不连接银行/支付/政府平台/支付宝/税务/工资/券商、不执行付款、下单或真实账户动作。

## 2026-06-16 Executive Command Center Runtime Summary Aggregation

- 总控输出新增 `runtime_summary_sources`，明确每个 value/business 子系统当前使用 `runtime_summary`、`full_snapshot` 还是 fallback build。
- 缺少 compact summary 时仍 fallback 到 full latest 或本地 fail-closed 构建，保持旧产物兼容和安全降级。
- 安全边界不变：总控仍不刷新行情、不连接银行/支付/政府平台/支付宝/税务/工资/券商、不执行付款、下单或真实账户动作。

## 2026-06-16 Consumption Guard Runtime Summary

- Consumption Guard 新增 `PFIOSConsumptionGuardRuntimeSummaryV1` compact 运行摘要，包含守卫状态、计入记录、缺证据、待复核、冲动风险、固定成本、可投资现金流压力和 evidence gate。
- `scripts/consumptionGuard.sh --summary-json` 可以只输出低 token 摘要，后续 agent 或总控不需要读取完整 events 才能判断消费守卫状态。
- `--output-dir` 生成正式快照时会同时写入 `ConsumptionGuardRuntimeSummary_DDMMYYYY.json` 和 `ConsumptionGuardRuntimeSummary_latest.json`。
- Streamlit `消费守卫` 页面新增 `运行摘要与证据闸门`，优先展示消费证据、人工复核、冲动风险、预算压力和 no-external-execution 边界。
- 安全边界不变：不连接支付宝、银行、工资、税务、券商或支付系统，不执行付款、转账、退款、冻结账户或投资动作。

## 2026-06-16 Policy Intelligence Runtime Summary

- Policy Intelligence Radar 新增 `PFIOSPolicyIntelligenceRuntimeSummaryV1` compact 运行摘要，包含政策状态、机会数量、Actionable、来源权威、待溯源、待复核、缺证据和 evidence gate。
- `scripts/policyRadar.sh --summary-json` 可以只输出低 token 摘要，后续 agent 或总控不需要读取完整 opportunities 才能判断政策证据状态。
- `--output-dir` 生成正式快照时会同时写入 `PolicyIntelligenceRuntimeSummary_DDMMYYYY.json` 和 `PolicyIntelligenceRuntimeSummary_latest.json`。
- Streamlit `政策雷达` 页面新增 `运行摘要与证据闸门`，优先展示来源权威、缺证据、人工复核和 no-external-execution 边界。
- 安全边界不变：不抓取实时政策、不登录政府平台、不提交申请、不付款、不生成法律/税务/合规/投资结论、不交易。

## 2026-06-16 Company CashFlow Runtime Summary

- Company CashFlow Command 新增 `PFIOSCompanyCashFlowRuntimeSummaryV1` compact 运行摘要，包含现金流状态、余额日期、计入记录、待复核、缺证据、净现金流、Runway、应收应付和 evidence gate。
- `scripts/cashFlowCommand.sh --summary-json` 可以只输出低 token 摘要，后续 agent 或总控不需要读取完整 entries 才能判断现金流状态。
- `--output-dir` 生成正式快照时会同时写入 `CompanyCashFlowRuntimeSummary_DDMMYYYY.json` 和 `CompanyCashFlowRuntimeSummary_latest.json`。
- Streamlit `现金流` 页面新增 `运行摘要与证据闸门`；脚本支持 `PFI_PYTHON -> .venv -> python3` fallback，提高本地瘦身后的可运行性。
- 安全边界不变：不连接银行、支付、工资、税务、会计、券商或交易系统，不执行付款、转账或账户动作。



## 2026-06-16 Research Chart UX Controls

- 热点时间轴、热点热力图、热点气泡图和向量化研究图表接入统一 Plotly 研究图表交互配置，支持滚轮缩放、拖拽平移或缩放、悬停辅助线、响应式渲染和 PNG 导出。
- 热点时间轴新增范围滑块和快捷区间按钮，方便按近 6 期、近 24 期、近 7 天或全部范围复核热点扩散。
- 图表交互只改变前端视图，不触发新的行情请求、参数扫描、回测、券商连接、下单或持仓修改。

## 2026-06-16 Hotspot Runtime Summary MVP

- 热点分析新增 `PFIOSHotspotRuntimeSummaryV1` compact 运行摘要：生成后显示请求指纹、对象覆盖、切片数量、缓存 TTL 和证据状态，帮助判断本次点击是否复用同一计算口径，降低重复解释和排查成本。
- 新增 `scripts/hotspotRuntimeSummary.sh` Sample-only smoke 入口，可在不打开 Streamlit、不联网、不连接券商的情况下验证热点 summary 和证据闸门。
- 热点分析新增 `PFIOSHotspotPersistedCacheV1` 本地派生缓存，写入被 Git 忽略的 `data/cache/hotspots/`；同一请求指纹在 TTL 内可跨工作台重启复用已计算热点结果。
- 52ETF 公开参考升级为 `PFIOS52ETFHotspotComparisonV1` 只读对照摘要，展示公开 A 股云图板块与 PFI_OS 当前热点对象池的映射、口径差异和安全边界。
- 安全边界不变：热点分析仍只作研究观察，不创建订单、不修改持仓、不连接实盘交易。

## 2026-06-13 Event Replay MVP

- 新增事件回放层：`src/pfi_os/data/replay.py`。
- 新增 CLI：`scripts/eventReplay.sh --output-dir data/replay`。
- 支持读取 `DataLakeManifest_latest.json`、`DataLakeManifest_latest_replay_cursors.json` 和本地不可变 `MarketEventLog_*.jsonl`。
- 支持按 cursor id、dataset、market、symbol、interval、source、start/end window 和 limit 生成确定性 replay batch。
- 输出 `EventReplay_<cursor>_DDMMYYYY.json/csv/md` 和 latest 指针；记录 manifest、cursor、asset、过滤条件、next_after 和 missing data log。
- 当前只回放本地 market event JSONL；不模拟订单、不连接 Moomoo、不接 Kafka/QuestDB/ClickHouse、不连接实盘。

## 2026-06-13 Reproducible Data Lake MVP

- 新增可复现数据湖 manifest 层：`src/pfi_os/data/lake.py`。
- 新增 CLI：`scripts/dataLakeManifest.sh --output-dir data/dataLake`。
- 支持索引不可变 `data/marketEvents/MarketEventLog_*.jsonl` 和结构化 `data/cache/<MARKET>/<interval>/<symbol>.csv/parquet` bar cache。
- 输出 asset manifest、asset CSV、replay cursor JSON/CSV、Markdown 和 latest 指针。
- 每个 asset 记录 schema、partition、row count、quality status、SHA-256 checksum、first/last event time 和 replay cursor id。
- `*latest*` 文件只登记为 mutable alias，不计入不可变资产，避免可变指针污染可复现实验。
- 当前不复制数据、不接 Kafka、不写 QuestDB/ClickHouse、不连接 Moomoo 或券商；Arrow/Parquet 优化和外部存储适配后续分轮推进。

## 2026-06-13 Market Event Layer MVP

- 新增本地事件驱动行情层：`src/pfi_os/data/market_events.py`。
- 新增 CLI：`scripts/marketEventLayer.sh --output-dir data/marketEvents`。
- 支持把 deterministic sample 或本地 CSV 的 OHLCV bar 转成 `PFIOSMarketEventV1` / `BarClosed` 事件。
- 输出 `MarketEventLog_DDMMYYYY.json/jsonl/csv/md` 和 latest 指针文件，事件按 `event_time` 排序，并使用稳定 `event_id` 支持去重写入。
- 复用现有 `assess_bars` 数据质量报告，记录 source、symbol、market、interval、checksum、缺失值和重复时间戳。
- 当前只落地本地事件契约；Kafka、QuestDB、ClickHouse、Moomoo 实时订阅、Arrow 数据湖和三模式模拟内核仍按后续独立 Run Contract 推进。

## 2026-06-13 Executive Command Center Business Subsystem Aggregation

- `总控驾驶舱` 现在聚合 `Company CashFlow Command`、`Policy Intelligence Radar` 和 `Consumption Guard` 的 latest 快照。
- 总控 JSON/Markdown/PDF 增加 `business_system_summary`、`cashflow_summary`、`policy_summary` 和 `consumption_summary`。
- 行动队列会纳入现金流证据缺口、政策机会和消费止血事项；`Critical` 与 `StopBleeding` 会使总控进入 `Blocked`。
- 页面新增 `业务子系统` 表和 `子系统复核` 指标，减少在多个页面之间切换的总控 token/操作压力。
- 聚合层只读本地 evidence/latest，不连接银行、支付、政府平台、支付宝、税务、工资、券商或实盘系统。

## 2026-06-13 Consumption Guard Productization

- 新增 `Consumption Guard` 后端模块：`src/pfi_os/consumption/guard.py`。
- 新增 Streamlit `消费守卫` 工作台入口，支持录入消费事件、分类、金额、商户、支付方式、计划性、周期性、必要性、冲动分、后悔分、证据和复核状态。
- 新增 CLI：`scripts/consumptionGuard.sh --output-dir data/consumption`。
- 新增正式输出：`ConsumptionGuard_DDMMYYYY.json/csv/md/pdf` 和 latest 指针文件。
- 消费指标 fail-closed：只有 `Reviewed` 且有 `evidence_link` 或 `evidence_path` 的记录才会进入支出、冲动风险、固定成本和可投资现金流压力汇总。
- 本子系统不连接支付宝、银行、工资、税务、券商或支付系统，不执行付款、转账、退款、冻结账户或投资操作。

## 2026-06-13 Policy Intelligence Radar Productization

- 新增 `Policy Intelligence Radar` 后端模块：`src/pfi_os/policy/radar.py`。
- 新增 Streamlit `政策雷达` 工作台入口，支持录入政策来源、来源类型、URL、本地证据、地区、政策层级、机会类型、影响行业、影响对象、影响摘要、下一步行动和评分。
- 新增 CLI：`scripts/policyRadar.sh --output-dir data/policy`。
- 新增正式输出：`PolicyIntelligenceRadar_DDMMYYYY.json/csv/md/pdf` 和 latest 指针文件。
- 政策机会 fail-closed：只有 `Reviewed`、权威来源类型、source evidence 和足够影响评分的记录才会进入 `Actionable`。
- `Research`、`News` 和 `Manual` 来源必须回溯官方、监管、政府或交易所来源后才能升级。
- 本子系统不自动抓取实时政策，不登录政府平台，不提交申请，不生成法律、税务、合规或投资结论。

## 2026-06-13 Company CashFlow Command Productization

- 新增 `Company CashFlow Command` 后端模块：`src/pfi_os/business/cashflow.py`。
- 新增 Streamlit `现金流` 工作台入口，支持录入余额快照、收入、支出、应收、应付、分类、证据、复核状态和备注。
- 新增 CLI：`scripts/cashFlowCommand.sh --output-dir data/cashflow`。
- 新增正式输出：`CompanyCashFlowCommand_DDMMYYYY.json/csv/md/pdf` 和 latest 指针文件。
- 现金流汇总 fail-closed：只有 `Reviewed` 且有 `evidence_link` 或 `evidence_path` 的记录才会计入余额、收入、支出、应收、应付和 Runway。
- 本子系统不连接银行、支付、税务、工资或会计系统，不执行付款、转账或账户动作。


- 支持录入任务目标、证据链接、Token 估算、AI 成本、人工时间成本、新增收入、节省成本、避免损失、资产复用价值、节省时间、复用次数和复核备注。

## 2026-06-07 Report Decision Support Index

- 新增报告决策支持索引：`src/pfi_os/reports/decision_support.py`。
- 新增命令：`scripts/reportDecisionSupport.sh --output-dir data/reportDecision`。
- 报告中心新增 `证据索引` 页签，用于按 RunMetadata 和 Word 报告判断报告是否可继续研究、只能观察、需要更多证据或不要使用。
- 该索引只读，不修改原报告、不刷新行情、不连接实盘。

## 2026-06-07 Executive Command Center MVP

- 新增 PFI_OS 第一入口 `总控驾驶舱`，默认打开后先看系统是否可继续研究。
- 新增 `src/pfi_os/executive/command_center.py` 和 `scripts/commandCenter.sh --output-dir data/commandCenter`。
- 总控只读聚合证据，不刷新行情、不启动 OpenD、不修改持仓、不连接实盘。


- 台账会登记 `data/systemAudit` 和报告目录中的审计、报告、RunMetadata、数据质量、交叉校验和实验产物。
- 金额字段默认保持 `0.00`，`roi_score=null`，`value_status=Unquantified`；没有真实金额输入时不伪造收益。
- 输出 JSON、CSV、Markdown、PDF 和 `latest` 指针文件。

## 2026-06-07 PFI_OS 主入口

- 主系统入口更名为 `PFI_OS.app`，应用显示名为 `PFI_OS`。
- PFIOS 保留为 PFI_OS 内的量化研究与回测主入口。
- 健康检查和最终验收脚本同步检查新入口，并要求旧 `量化回测系统.app` 已移除，避免重复入口。

## Current Build

当前版本定位为个人日常研究工作台。

The current build is positioned as a personal daily research workspace.

## Ready For Daily Use

启动、停止、状态检查和验收脚本已经具备。

Start, stop, status check, and verification scripts are available.

日常就绪检查现在可以输出 JSON、Markdown 和 PDF，汇总核心审计门禁、数据源状态、最新报告和行动项。

Daily Readiness can now output JSON, Markdown, and PDF, summarizing core audit gates, provider status, latest report, and action items.

样例 Word 研究报告脚本已经具备，便于快速确认报告链路。

Sample Word research report generation is available for quickly verifying the report pipeline.

`.env` 模板创建脚本已经具备，便于配置真实数据源 key。

The `.env` template setup script is available for configuring real-data provider keys.

真实数据联网验证脚本已经具备，当前覆盖 Yahoo Finance 和 AKShare。

The real-data network validation script is available and currently covers Yahoo Finance and AKShare.

AKShare 验证已加入重试和备用标的，降低第三方接口临时断开的影响。

AKShare validation now includes retries and backup symbols to reduce the impact of temporary third-party disconnects.

多源交叉校验结果现在会保存为 JSON，并进入报告中心资产统计。

Cross-source validation results are now saved as JSON and included in report center artifact counts.

策略库新增布林带均值回归策略。

The strategy library now includes a Bollinger Reversion strategy.

单标的回测新增内置策略 `追跌杀涨 Buy Dips Sell Rallies`，覆盖 14:30 决策点、下跌整数金额补入、上涨按持仓收益率最高档卖出、现金不足跳过、一天最多一个方向和禁止做空。

Single-symbol backtest now includes the built-in `追跌杀涨 Buy Dips Sell Rallies` strategy, covering the 14:30 decision point, integer-yuan add-on buys on declines, highest-threshold scale-out on profitable up days, insufficient-cash skips, at most one direction per day, and no short selling.

单标的回测新增内置策略 `追跌杀涨增强 Buy Dips Sell Rallies Enhanced`，在原追跌杀涨规则上加入 RSI、布林带、均线和 MACD，用于研究下跌少亏、上涨少踏空的增强方向。

Single-symbol backtest now includes the built-in `追跌杀涨增强 Buy Dips Sell Rallies Enhanced` strategy, adding RSI, Bollinger Bands, moving averages, and MACD to the original buy-dips-sell-rallies rule to study lower downside loss and lower upside lag.

单标的结果页将核心指标卡片改为策略、买入持有和相对差值的对比表，避免标题截断，并新增胜率口径说明。

The single-symbol result page now replaces key metric cards with a strategy, buy-and-hold, and relative-difference comparison table to avoid truncated labels, and adds a win-rate definition.

收益图新增相对收益线，权益与交易摩擦图新增持仓金额线和策略收益率线；K 线改为红涨绿跌，买卖点使用轻量圆点标记。

The return chart now includes relative return, and the equity/friction chart includes position value and strategy-return lines; candlesticks use red-up and green-down colors, while buy/sell markers use lightweight circle markers.

Word 回测报告新增策略、目标与相对收益曲线、月度收益热力图、滚动夏普与波动率图，参考 QuantStats/pyfolio 类 tear sheet 的核心分析视角。

Word backtest reports now include strategy, target, and relative return curves, monthly return heatmaps, and rolling Sharpe/volatility charts, inspired by QuantStats/pyfolio-style tear sheet analysis.

报告中心新增总览 Dashboard，展示研究资产类型、日期活动、运行收益/回撤分布、最近运行趋势、策略表现汇总和实验最佳收益。

Report Center now includes a dashboard showing asset types, activity by date, run return/drawdown distribution, recent run trend, strategy performance summary, and top experiment returns.

参数扫描页新增总收益、夏普和最大回撤热力图，并增加 Top N 参数组合对比图。

Parameter Scan now includes total-return, Sharpe, and max-drawdown heatmaps plus a Top N parameter-combination comparison chart.

实验 Word 报告同步新增总收益、夏普和最大回撤参数热力图，便于检查最佳参数是否只是孤立点。

Experiment Word reports now include total-return, Sharpe, and max-drawdown parameter heatmaps to check whether the best parameter is an isolated point.

单标的回测和 Word 回测报告新增 Bootstrap 鲁棒性验证，展示模拟总收益分布、最大回撤分布、样本路径、亏损概率和达到目标收益概率。

Single-symbol backtests and Word backtest reports now include Bootstrap robustness validation with simulated total-return distribution, max-drawdown distribution, sample paths, loss probability, and target-return probability.

单标的回测和 Word 回测报告新增策略诊断，覆盖交易质量、成本压力、市场环境分层和失效检查。

Single-symbol backtests and Word backtest reports now include strategy diagnostics covering trade quality, cost stress, market-regime breakdown, and failure checks.

组合回测新增组合归因，展示单标的权重、期末持仓、价格收益、交易次数和执行成本。

Portfolio backtests now include attribution showing symbol weights, ending position value, price return, trade count, and execution cost.

新增日常检查脚本，可快速汇总系统状态、数据源配置和报告资产数量，并可选择联网验证。

The daily check script now summarizes system status, data provider configuration, and report asset counts, with optional network validation.

双击启动入口现在会在浏览器页面关闭后自动停止新启动的服务。

The double-click launcher now stops newly started services automatically after the browser page is closed.

页面关闭联动改为浏览器心跳监控，页面关闭后会停止 Streamlit；macOS `.app` 启动入口不会弹出 Terminal 窗口。

Page-close linkage now uses a browser heartbeat monitor; after the page closes, it stops Streamlit, and the macOS `.app` launcher does not open a Terminal window.

启动稳定性已增强：`.app` 入口使用启动锁防止重复启动抢端口，Streamlit 只绑定本机地址，关闭源码文件监听，页面心跳默认容错 120 秒，避免短暂卡顿导致 connection lost。

Startup stability has been improved: the `.app` launcher now uses a launch lock to prevent duplicate port races, binds Streamlit to localhost, disables source file watching, and uses a 120-second browser heartbeat tolerance to reduce connection lost events during short freezes.

首页移除了安全边界卡片，并把工作台状态移动到页面底部。

The home page removed the safety boundary card and moved workspace status to the bottom.

单标的回测和数据工具新增联网模糊搜索标的。

Single backtest and data tools now include online fuzzy symbol search.

首页已经加入日常使用 Runbook。

The home page now includes a daily-use Runbook.

单标的回测、组合轮动、参数扫描、数据工具、报告中心、策略库和策略确认机制已经集成到 Streamlit 工作台。

Single backtest, portfolio rotation, parameter scan, data tools, report center, strategy library, and strategy approval are integrated in the Streamlit workbench.

Word 报告包含执行摘要、结果判读、买入持有对比、策略说明、风险闸门、数据质量、多源交叉校验、图表和运行追溯。

Word reports include executive summary, result interpretation, buy-and-hold comparison, strategy description, risk gate, data quality, cross-source validation, charts, and run traceability.

报告中心支持报告列表、运行判读、实验记录和安全清理。

The report center supports report lists, run interpretation, experiment records, and safe cleanup.

## Commands

启动：

Start:

```bash
~/Desktop/PFI_OS.app
~/Downloads/PFI_OS.app
/Applications/PFI_OS.app
```

三个启动入口已经统一为标准 macOS `.app` 包，支持 Dock 和 Launchpad。图标配置保存在 `assets/PFIOSAppIconConfig.json`，重新生成入口使用 `scripts/installMacAppLaunchers.sh`。

The three launchers are now standard macOS `.app` bundles with Dock and Launchpad support. Icon configuration is saved in `assets/PFIOSAppIconConfig.json`, and launchers can be rebuilt with `scripts/installMacAppLaunchers.sh`.

命令行静默启动，不自动打开浏览器：

Quiet terminal start without opening a browser:

```bash
$PFI_OS_HOME/scripts/startPFIOS.sh
```

停止：

Stop:

```bash
$PFI_OS_HOME/StopPFIOS.command
```

状态检查，不打开浏览器：

Status check without opening a browser:

```bash
$PFI_OS_HOME/scripts/statusPFIOS.sh
```

完整验收，不打开浏览器：

Full verification without opening a browser:

```bash
$PFI_OS_HOME/scripts/verifyPFIOS.sh
```

快速样例报告，不打开浏览器：

Quick sample report without opening a browser:

```bash
$PFI_OS_HOME/scripts/createSampleReport.sh
```

## Current Limitations

真实数据源受 API Key、网络、第三方接口额度和数据覆盖范围影响。

Real data providers depend on API keys, network access, third-party quotas, and data coverage.

Polygon 已接入聚合行情拉取，但需要 `POLYGON_API_KEY`。

Polygon aggregate market data fetching is implemented, but it requires `POLYGON_API_KEY`.

Moomoo 行情入口已接入，需要本机 Moomoo OpenD 和 `futu-api`。

Moomoo quote data is implemented and requires local Moomoo OpenD plus `futu-api`.

权益与交易摩擦占比图已改为累计交易摩擦成本占当前 Equity 的百分比。

The equity and trading friction chart now uses cumulative trading friction cost as a percentage of current equity.

结束日期控件新增 `今天 Today` 按钮。

End-date controls now include a `今天 Today` button.

结果判读中的回撤改为策略最大回撤相对买入持有最大回撤的比较，下方核心指标显示为策略最大回撤。

The drawdown interpretation now compares strategy max drawdown with buy-and-hold max drawdown, while the lower key metric is labeled strategy max drawdown.

策略库新增自定义策略快速新增和候选策略档案编辑功能。

The strategy library now includes quick custom strategy creation and candidate profile editing.

买入持有最大回撤现在会按行情时间顺序重新排序后计算，降低数据源乱序造成的回撤低估风险。

Buy-and-hold max drawdown is now calculated after sorting market data by time, reducing the risk of understated drawdown from out-of-order provider data.

结果判读中的回撤文案改为“策略最大回撤相比买入持有最大回撤为 xxx%”，并说明正数表示策略回撤更小。

The drawdown interpretation now states "strategy max drawdown versus buy-and-hold max drawdown is xxx%" and explains that positive values mean smaller strategy drawdown.

新增自定义策略改为从策略库统一进入，系统根据策略逻辑、指标组合和参数设置自动生成英文名、策略编号、类别、收益来源、研究假设和失效环境。

Custom strategy creation is now centralized in the strategy library. PFIOS infers English name, strategy id, category, return sources, thesis, and failure regime from strategy logic, indicator combination, and parameter settings.

内置策略档案支持编辑修改，修改永久保存到 `data/strategyLibrary/StrategyProfileOverrides.json`，不会覆盖内置源码。

Built-in strategy profiles can now be edited. Edits persist in `data/strategyLibrary/StrategyProfileOverrides.json` without overwriting built-in source code.

内置策略默认参数支持在策略库中编辑修改，修改永久保存到 `data/strategyLibrary/BuiltInStrategyParameters.json`，并同步到单标的回测默认参数；保存和恢复默认参数都会记录策略变更确认。

Built-in strategy default parameters can now be edited in the strategy library. Edits persist in `data/strategyLibrary/BuiltInStrategyParameters.json`, synchronize to single-symbol backtest defaults, and create strategy-change confirmation records when saved or reset.

自定义策略新增 no-code 可执行规格。策略库创建策略时会保存到 `data/strategyLibrary/CustomStrategySpecs.json`，生成可执行信号逻辑，并在确认后接入单标的回测策略选择。

Custom strategies now support no-code executable specs. The strategy library saves specs to `data/strategyLibrary/CustomStrategySpecs.json`, generates executable signal logic, and connects confirmed custom strategies to the single-symbol backtest strategy selector.

自定义策略规格支持策略库内编辑、自动版本升级、修改历史保存和当前版本一键确认。修改历史保存到 `data/strategyLibrary/CustomStrategySpecHistory.json`。

Custom strategy specs now support in-library editing, automatic version bumping, change-history persistence, and one-click current-version confirmation. Change history is saved to `data/strategyLibrary/CustomStrategySpecHistory.json`.

编辑自定义策略规格后，系统会自动同步对应 `src/pfi_os/strategies/custom/*.py` 策略代码文件，避免规格和代码版本不一致。

After editing a custom strategy spec, PFIOS automatically synchronizes the matching `src/pfi_os/strategies/custom/*.py` strategy code file to prevent spec and code version drift.

Word 回测报告现在会读取自定义策略规格，用自定义策略的收益来源、研究假设、失效环境和参数设置生成策略审查内容。

Word backtest reports now read custom strategy specs and use custom return sources, thesis, failure regime, and parameter settings in strategy review content.

单标的回测周期选择已扩展到 `1min`、`5min`、`15min`、`30min`、`60min`、`1d`、`1w`、`1m`、`1q` 和 `1y`。

Single-symbol backtest interval selection now covers `1min`, `5min`, `15min`, `30min`, `60min`, `1d`, `1w`, `1m`, `1q`, and `1y`.

数据层新增非原生周期兜底：当真实数据源不支持周线、月线、季线或年线时，系统会尝试用日线或月线在本地按 OHLCV 规则重采样，并写入数据质量 notes。

The data layer now includes a fallback for non-native intervals: when a real provider does not support weekly, monthly, quarterly, or yearly bars, PFIOS attempts local OHLCV resampling from daily or monthly bars and writes the source interval into data quality notes.

新增 Moomoo 只读行情诊断脚本 `scripts/checkMoomoo.sh`，用于检查 `futu-api`、Moomoo OpenD 端口、历史 K 线行情和数据质量报告。

Added the Moomoo quote-only diagnostic script `scripts/checkMoomoo.sh` to check `futu-api`, the Moomoo OpenD port, historical K-line quote data, and data quality report creation.

`dailyCheck.sh --network` 已接入 Moomoo 诊断，但不会因为本机没有启动 OpenD 而中断其它日常检查。

`dailyCheck.sh --network` now includes the Moomoo diagnostic, but it does not stop other daily checks when OpenD is not running locally.

`dailyCheck.sh --network` 现在会在单个真实数据源临时失败时继续执行后续诊断，避免日常检查被第三方接口短暂故障整体中断。

`dailyCheck.sh --network` now continues later diagnostics when one real-data provider temporarily fails, preventing a short third-party outage from stopping the full daily check.

新增 `热点分析` 功能区：支持大盘热点、持仓和自选对象，输出热点时间轴、时间切片、热力图、气泡图、优先复核对象和热点明细；缓存刷新间隔为 1 小时，并可开启每小时自动刷新当前页。

Added the `热点分析` workspace: it supports market hotspots, holdings, and custom symbols, then outputs a hotspot timeline, time slices, heatmap, bubble chart, priority review objects, and hotspot detail. Cache refresh TTL is one hour, with optional hourly page refresh.

功能导航和 `使用指导` 已迁移到左侧侧栏；主功能区不再显示独立 `策略变更确认` 入口，策略确认保留在 `策略库` 内。

Navigation and `使用指导` have moved to the sidebar. The main workspace no longer shows a standalone `策略变更确认` entry; strategy confirmation remains inside `策略库`.

盘感训练开始作答后会显示实时自动倒计时；情绪分析新增情绪结构分布图，用于先判断偏热、偏冷和中性对象占比。

Market-feel challenges now show a live countdown after starting. Sentiment analysis now includes a distribution chart for hot, cold, and neutral object counts.

情绪分析新增 `情绪证据闸门`，先检查数据源、对象覆盖、失败率、样本长度、数据新鲜度和情绪集中度；旧的独立 `策略变更确认` / `使用指导` 页面函数已清理，策略确认仍保留在策略库内。

Sentiment analysis now includes a sentiment evidence gate for data source, object coverage, failure rate, sample length, data freshness, and sentiment concentration. Old standalone approval / guide page functions were removed while strategy confirmation remains inside the strategy library.

系统只研究不实盘，不连接券商，不提交真实订单。

The system is research-only, does not connect to brokers, and does not submit real orders.

## 2026-06-05 UI 可读性和热点分析补强

盘感训练、情绪分析和热点分析顶部新增可悬停术语提示，减少不理解专业术语和操作逻辑时的中断。

热点分析新增自定义时间查看，可输入完整时间、日期片段或近似时间，系统自动定位到最近可用时间切片。

热点时间轴新增状态解释，用于判断热点扩散、热点降温、强弱分化、横盘轮动或样本不足。

自动刷新组件明确显示 1 小时缓存刷新规则，并使用实时倒计时；真实行情更新仍取决于数据源权限、交易时段和行情延迟。

策略库界面统一使用“变更确认 / 确认状态”口径，独立策略变更确认功能板块继续保持删除状态；底层确认记录保留，用于阻止未确认策略进入正式研究回测。

左侧 `使用指导` 首屏新增最短操作路径和优先检查点，减少在长说明里查找流程的成本。

热点分析新增 `热点证据闸门`，严格检查数据源、覆盖率、失败率、样本长度、时间切片、刷新粒度、数据新鲜度和热度集中度；任一 Review 或 Block 时只允许作为研究观察。

热点时间轴新增快捷缩放，热力图直接显示近 5 期涨跌，气泡图增加象限标签，用于更快判断短期延续、同步偏弱、反弹待确认和回落分歧。

情绪分析和热点分析分离 `指标预热窗口` 与 `展示窗口`：展示开始日期只控制页面显示范围，系统自动向前取预热数据计算指标，避免同一目标日期或时间切片因为开始日期不同而出现不合理跳变。

## 2026-06-06 热点热度稳定性补强

热点分析把原始单切片热度拆分为 `即时热度`、`平滑热度` 和 `热度变化`。页面默认总览、热力图和气泡图使用平滑热度，降低小时级噪声；悬停和明细表保留即时热度，便于追溯异动来源。

同一对象、同一数据源、同一时间切片在不同展示窗口下会使用同一预热上下文，保持即时热度、平滑热度和热度变化一致。

`Sample` 演示数据源改为按代码和时间戳稳定生成行情；同一个代码、同一个日期或小时在不同请求起点下返回相同价格和成交量，避免情绪分或热点热度因为展示开始日期改变而出现不合理跳变。

## 2026-06-07 报告补证据任务

报告中心新增 `Report Evidence Gap Tasks`。系统会读取报告决策支持索引，把 `NeedsMoreEvidence` 或 `DoNotUse` 报告中的缺失证据拆成验证任务，并追加到 `data/validationQueue/ValidationTasks.json`。

新增命令 `scripts/reportGapTasks.sh`，支持 `--dry-run` 预览、正式追加入队和 `--json-only` 候选数量检查。

该功能只生成补证据待办任务，不联网、不刷新行情、不运行验证、不修改旧报告、不修改持仓、不连接实盘。

## 2026-06-07 验证任务优先级计划

报告中心验证任务队列新增 `Validation Priority Plan`。系统会读取 `ValidationTasks.json`，按证据缺口、任务状态、来源报告、代码/市场完整性和阻塞项生成排序计划。

新增命令 `scripts/validationPriorityPlan.sh`，输出 JSON、CSV、Markdown 和 PDF 到 `data/validationQueue`。

该功能只做排序计划，不修改原任务队列、不运行验证、不刷新行情、不连接实盘。

## 2026-06-07 验证任务执行记录

新增 `Validation Task Execution`。系统可以执行最高优先级 `CrossSourceValidation` 任务，生成 JSON、CSV、Markdown 和 PDF 执行记录。

执行结果分为 `Pass`、`Review`、`Blocked` 和 `Error`。如果当前真实数据源不足两个，系统会输出 `Blocked`，不会伪造多源校验通过。


## 2026-06-13 热点工作台快速预览与 52ETF 公开参考

热点分析新增 `工作台模式`：默认 `快速预览` 限制对象数和时间切片数，降低点击生成后的等待时间；`标准分析` 和 `完整复盘` 保留更大范围，用于盘后复核或报告前复盘。

热点页面新增可选 `52ETF 公开参考`。系统只读取 `https://52etf.site/` 公开首页可见的“大盘云图”板块和操作提示，并以 `Review/Pass` 证据状态展示；读取失败时 fail-closed，不阻塞 PFI_OS 本地热点分析。

该接入不作为正式行情源、不进入回测、不触发交易、不绕过数据质量闸门。

## 2026-06-13 参数扫描策略选择与自定义策略支持

参数扫描从固定 `Sample + MA Crossover` 示例升级为工作台：支持选择数据源、市场、标的、周期、已确认策略、参数网格和最大组合数。

内置扫描策略包括 MA、RSI 均值回归、布林带均值回归和突破策略。自定义 no-code 策略必须先在策略库确认，扫描时可使用 `indicator.parameter=...` 覆盖策略库参数，并可扫描 `weight` 仓位权重。

底层 `ExperimentRunner` 现在支持 strategy class 或 strategy factory，因此可以复用同一套 run_grid、Train-Test 和 Walk-Forward 验证流程。

该功能仍只做研究验证，不生成实盘买卖指令；参数组合过多时页面会阻止运行，避免高成本低质量扫描。

## 2026-06-16 日常开发轻量就绪检查

新增 `scripts/devReadyCheck.sh --summary-json` 作为日常开发默认 gate，输出 `PFIOSDevReadyCheckV1`。

该检查只覆盖关键脚本可执行、shell/Python 语法、状态脚本、缓存 dry-run 和 git 状态；工作区未提交只记录为 `Info`，不会触发最终验收、CI smoke、完整测试、浏览器自动化、行情刷新、券商连接、策略 smoke gate、订单、付款或持仓写入。

`README.md`、`docs/Testing.md` 和 `docs/AcceptanceChecklist.md` 已把该命令放在日常默认验证路径，`finalAcceptanceCheck.sh` 继续保留为明确发布闸门。

`scripts/cleanCache.sh` 同步设置 `PYTHONDONTWRITEBYTECODE=1` 和独立 `PYTHONPYCACHEPREFIX`，避免清理 dry-run/delete 自己生成新的仓库内 `__pycache__`。

统一 Workspace 的 `macOS 生命周期` 面板新增 `开发检查` 按钮，直接运行 allowlisted `scripts/devReadyCheck.sh`；dashboard action 表同步新增 `Dev Ready Check`，最终验收仍保持 Terminal-only 发布闸门。

统一 Workspace 的 `macOS 生命周期` 面板新增 `运行时验收证据` 只读卡片，读取 `data/systemAudit/MacOSRuntimeAcceptance_latest.json` 的状态、检查通过数、最近运行时间、启动方式和失败检查摘要；页面不会自动运行 `scripts/macosRuntimeAcceptance.sh`，运行时验收仍保持 Terminal-only。

2026-06-16 本机已完成 Downloads `PFI_OS.app` open-path runtime acceptance：`PFIOSMacOSRuntimeAcceptanceV1 status=Pass pass=10 fail=0 launch_method=app`。原始 evidence 含本机绝对路径，继续只保留在本地 `data/systemAudit/MacOSRuntimeAcceptance*.json`，不提交 GitHub。

## 2026-06-17 macOS UI 可见性验收

新增 `scripts/uiVisualAcceptance.sh --summary-json` 作为轻量 UI visual acceptance 入口，输出 `PFIOSUIVisualAcceptanceV1`。

该脚本会在没有健康本机服务时启动 PFI_OS Streamlit，用 headless Chrome 检查 `PFI_OS`、`工作台状态`、`macOS 生命周期`、`运行时验收证据`、缓存预览和生命周期按钮是否真实可见，并保存本地截图。

该验收不会运行 `scripts/finalAcceptanceCheck.sh`、`scripts/ciSmoke.sh`、full pytest、行情刷新、券商连接、订单、付款或持仓写入；如果脚本自己启动服务，结束时只停止本次启动的服务。

2026-06-17 本机最终验收通过：`PFIOSUIVisualAcceptanceV1 status=Pass pass=16 fail=0 screenshot_bytes=278744`。本地 UI evidence 和截图继续只保留在 `data/systemAudit/UIVisualAcceptance*`，并已通过 `.gitignore` 排除。

## 2026-06-17 macOS 公开验收摘要

新增 `scripts/macosPublicAcceptanceSummary.sh`，输出 `PFIOSMacOSPublicAcceptanceSummaryV1`，默认把本机 `MacOSRuntimeAcceptance_latest.json` 和 `UIVisualAcceptance_latest.json` 转换成 GitHub-safe JSON/Markdown：

- `docs/evidence/MacOSAcceptancePublicSummary_20260617.json`
- `docs/evidence/MacOSAcceptancePublicSummary_latest.json`
- `docs/evidence/MacOSAcceptancePublicSummary_latest.md`

该摘要只保存 schema、状态、计数、gate 名称和 sanitized pass/fail；不包含 `/Users/`、`/Applications/`、浏览器可执行路径、截图路径、PID、raw logs 或私有数据。

2026-06-17 当前公开摘要状态：`Pass`，runtime source `Pass 10/0`，UI source `Pass 16/0`，11 个覆盖 gate 全部 `Pass`。生成器只读取已有本机 evidence，不启动服务、不打开浏览器、不运行完整 SmokeTest。

## 2026-06-17 macOS 验收入口合并

新增 `scripts/macosAcceptance.sh` 作为用户友好的统一入口，输出 `PFIOSMacOSAcceptanceHubV1`。无参数默认运行 `--mode daily --summary-json`，合并轻量开发就绪和 GitHub-safe 公开验收摘要，减少日常需要记住的脚本数量。

显式模式包括 `app-entry`、`lifecycle`、`runtime`、`app-runtime`、`ui` 和 `public-summary`。其中 `runtime`、`app-runtime`、`ui` 可能启动服务或浏览器，必须由用户显式选择；默认 `daily` 不启动服务、不打开浏览器、不运行完整 SmokeTest。

统一 Workspace 的 `macOS 生命周期` 面板新增 `日常验收` 主按钮，原 `开发检查`、`轻量验收`、`生命周期验收` 保留在 `高级单项验收` 中，降低普通使用路径的按钮噪音。
