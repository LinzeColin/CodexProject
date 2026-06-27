const CONTEXT_STORAGE_KEY = "pfi-context-v2";
const FEEDBACK_SLA_MS = {
  instant: 100,
  skeleton: 300,
  stepped: 1000,
  background: 10000,
};

const STATUS_LABELS = {
  ready: "可用",
  completed: "完成",
  pass: "通过",
  review: "复核",
  needsreview: "复核",
  needs_review: "复核",
  watch: "观察",
  running: "运行中",
  queued: "排队中",
  open: "待处理",
  missing: "待补",
  needsdata: "待补数据",
  needs_data: "待补数据",
  blocked: "阻塞",
};

const GENERIC_WORKFLOW_DESCRIPTION = "查看该工作流的来源、任务和证据状态。";

const WORKSPACE_LABELS = {
  home: "首页",
  accounts: "账户与资产",
  ledger: "账本流水",
  investment: "投资管理",
  consumption: "消费管理",
  sync: "数据源与同步",
  recommendations: "建议与复盘",
  insights: "报告与洞察",
  market: "市场",
  markets: "市场",
  research: "研究",
  policy: "政策",
  portfolio: "持仓",
  strategy: "策略实验室",
  strategy_lab: "策略实验室",
  data: "数据与系统",
  首页总览: "首页总览",
  账户与资产: "账户与资产",
  账本流水: "账本流水",
  投资管理: "投资管理",
  消费管理: "消费管理",
  数据源与同步: "数据源与同步",
  建议与复盘: "建议与复盘",
  报告与洞察: "报告与洞察",
};

const CARD_LABELS = {
  open_tasks: "待处理",
  market_events: "市场事件",
  portfolio_risk: "持仓风险",
  strategy_runs: "策略运行",
  net_worth: "净资产",
  cash: "现金",
  investment_assets: "投资资产",
  monthly_spending: "本月支出",
  data_health: "数据健康",
  investment_market_value: "投资市值",
  investment_pnl: "投资盈亏",
  month_spend: "本月支出",
  budget_remaining: "预算剩余",
  cashflow_pressure: "现金流压力",
};

const CARD_SOURCES = {
  open_tasks: "任务表",
  market_events: "来源登记",
  portfolio_risk: "持仓快照",
  strategy_runs: "证据记录",
  net_worth: "账户账本",
  cash: "账户地图",
  investment_assets: "账户与资产",
  monthly_spending: "账本流水",
  data_health: "数据源与同步",
  investment_market_value: "投资管理",
  investment_pnl: "收益归因",
  month_spend: "消费管理",
  budget_remaining: "消费预算",
  cashflow_pressure: "现金流预测",
};

const FEATURE_TARGETS = {
  市场快照: { view: "hotspots", label: "打开热点" },
  研究队列: { view: "reports", label: "打开报告" },
  持仓复核: { view: "holdings", label: "打开持仓" },
  策略实验室: { workspace: "strategy", label: "打开策略" },
  指数与ETF: { view: "index_etf", label: "打开指数" },
  主题催化: { view: "theme_catalyst", label: "打开主题" },
  自选监控: { view: "watchlist_monitor", label: "打开自选" },
  市场垂直切片: { view: "market_slice", label: "打开切片" },
  组合影响覆盖: { view: "market_overlay", label: "打开覆盖层" },
  提醒与保存视图: { view: "market_alerts", label: "打开提醒" },
  来源状态: { view: "source_status", label: "打开来源" },
  公司研究: { view: "company_research", label: "打开公司" },
  基金研究: { view: "fund_research", label: "打开基金" },
  研究与政策切片: { view: "research_policy_slice", label: "打开切片" },
  引用定位: { view: "citation_locator", label: "打开引用" },
  报告清单: { view: "report_manifest", label: "打开清单" },
  政策雷达: { view: "policy", label: "打开政策雷达" },
  报告验证: { view: "report_validation", label: "打开验证" },
  持仓垂直切片: { view: "portfolio_slice", label: "打开切片" },
  导入对账: { view: "portfolio_reconciliation", label: "打开对账" },
  风险约束: { view: "portfolio_risk", label: "打开约束" },
  决策提案: { view: "portfolio_decision", label: "打开提案" },
  组合暴露: { view: "portfolio_exposure", label: "打开暴露" },
  集中度风险: { view: "concentration_risk", label: "打开风险" },
  纪律检查: { view: "discipline_check", label: "打开纪律" },
  订单意图: { view: "order_intent", label: "打开意图" },
  策略垂直切片: { view: "strategy_slice", label: "打开切片" },
  PIT回测: { view: "pit_backtest", label: "打开回测" },
  样本外验证: { view: "train_test_validation", label: "打开验证" },
  滚动验证: { view: "walk_forward_validation", label: "打开滚动验证" },
  策略注册: { view: "strategy_registry", label: "打开注册" },
  单标的回测: { view: "single", label: "打开回测" },
  参数扫描: { view: "scan", label: "打开扫描" },
  盘感训练: { view: "market_feel", label: "打开训练" },
  模拟实验: { view: "big_data", label: "打开模拟" },
  热点分析: { view: "hotspots", label: "打开热点" },
  报告中心: { view: "reports", label: "打开报告" },
  政策雷达: { view: "policy", label: "打开政策" },
  持仓: { view: "holdings", label: "打开持仓" },
  数据中心: { view: "tools", label: "打开数据" },
  策略库: { view: "library", label: "打开策略库" },
  同步全部: { workspace: "sync", label: "同步计划" },
  处理待复核: { workspace: "ledger", label: "处理复核" },
  查看建议: { workspace: "recommendations", label: "查看建议" },
  生成报告: { workspace: "insights", label: "生成报告" },
  账户地图: { workspace: "accounts", label: "查看账户" },
  账本流水: { workspace: "ledger", label: "查看账本" },
  投资总览: { workspace: "investment", label: "查看投资" },
  收益归因: { workspace: "investment", label: "查看归因" },
  风险分析: { workspace: "investment", label: "查看风险" },
  行为复盘: { workspace: "investment", label: "查看复盘" },
  消费总览: { workspace: "consumption", label: "查看消费" },
  分类分析: { workspace: "consumption", label: "查看分类" },
  订阅检测: { workspace: "consumption", label: "查看订阅" },
  异常消费: { workspace: "consumption", label: "查看异常" },
  现金流预测: { workspace: "consumption", label: "查看现金流" },
  来源登记: { view: "source_registry", label: "打开来源" },
  任务监控: { view: "task_monitor", label: "打开任务" },
  隐私边界: { view: "privacy_boundary", label: "打开隐私" },
  备份恢复: { view: "backup_restore", label: "打开备份" },
};

const FUNCTION_VIEWS = {
  single: functionView(
    "single",
    "单标的回测",
    "strategy",
    "运行回测",
    "选择标的、数据源、周期、策略和成本假设，输出收益、回撤、交易、风险闸门和报告证据。",
    ["可用：单策略回测和双策略对比", "验收：费用、时间区间、数据质量和策略版本必须显示", "边界：只生成研究结果，不生成实盘订单"],
  ),
  scan: functionView(
    "scan",
    "参数扫描",
    "strategy",
    "运行参数扫描",
    "比较参数网格、样本内外表现、稳定性和过拟合风险，用于判断策略是否值得继续研究。",
    ["可用：参数网格和稳定性摘要", "验收：记录样本区间、参数范围和评分口径", "边界：扫描结果不能直接转成交易指令"],
  ),
  strategy_slice: functionView(
    "strategy_slice",
    "策略垂直切片",
    "strategy",
    "生成策略复核",
    "从固定 PIT 样本、回测哈希、样本外验证、滚动验证、策略注册和人工复核任务形成完整策略证据链。",
    ["可用：PIT 回测、样本外验证、滚动验证和策略注册", "验收：固定样本哈希、没有未来数据、运行可取消恢复", "边界：不生成实盘信号，不提交订单"],
    { legacyView: "single" },
  ),
  pit_backtest: functionView(
    "pit_backtest",
    "PIT回测",
    "strategy",
    "查看 PIT 回测",
    "查看固定样本哈希、回测参数、成本假设、公司行动调整和退市样本排除证据。",
    ["可用：行情校验和、复现哈希和下一根K线执行模型", "验收：公司行动和退市样本必须显式记录", "边界：回测不是交易信号"],
    { legacyView: "single" },
  ),
  train_test_validation: functionView(
    "train_test_validation",
    "样本外验证",
    "strategy",
    "查看样本外验证",
    "核对训练期和测试期的时间切分，确认训练结束早于测试开始，没有未来数据泄漏。",
    ["可用：切分时间、训练样本数、测试样本数和泛化比例", "验收：训练窗口不得覆盖测试窗口", "边界：验证结果只进入人工复核"],
    { legacyView: "scan" },
  ),
  walk_forward_validation: functionView(
    "walk_forward_validation",
    "滚动验证",
    "strategy",
    "查看滚动验证",
    "检查多个滚动训练/测试窗口，确认每个窗口的训练结束早于测试开始。",
    ["可用：窗口数量、通过数量和平均泛化比例", "验收：每个滚动窗口都必须没有未来数据", "边界：滚动通过也不允许自动下单"],
    { legacyView: "scan" },
  ),
  strategy_registry: functionView(
    "strategy_registry",
    "策略注册",
    "strategy",
    "打开策略注册",
    "把策略候选登记为只读研究模型，保留版本、参数、哈希、验证状态和人工复核要求。",
    ["可用：模型编号、策略版本、样本外验证状态和滚动验证状态", "验收：订单开关和实盘信号开关必须保持关闭", "边界：注册不等于上线，不提交订单"],
    { legacyView: "library" },
  ),
  market_feel: functionView(
    "market_feel",
    "盘感训练",
    "strategy",
    "生成盘感训练",
    "保留读图训练、限时判断、隐藏答案和复盘记录，训练人工判断，不输出实盘信号。",
    ["可用：大盘对象、持仓对象和自选代码训练", "验收：训练窗口、答案窗口、超时和复盘必须记录", "边界：训练结果不得作为自动买卖依据"],
  ),
  big_data: functionView(
    "big_data",
    "模拟实验",
    "strategy",
    "打开模拟实验",
    "组合策略、情景压力和假设实验，用于研究策略在不同市场状态下的表现。",
    ["可用：模拟和压力情景入口", "验收：假设、参数和输出路径必须可追溯", "边界：仅研究模拟，不连接券商"],
  ),
  hotspots: functionView(
    "hotspots",
    "热点分析",
    "market",
    "生成热点分析",
    "查看指数、ETF、主题和自选对象的强弱扩散，并把结果降级为观察线索。",
    ["可用：热点缓存和公开参照", "验收：来源状态、失败对象和更新时间必须显示", "边界：热点不是交易信号"],
  ),
  index_etf: functionView(
    "index_etf",
    "指数与 ETF",
    "market",
    "查看指数与 ETF",
    "查看指数、行业基金和宽基对象的缓存摘要，把强弱变化降级为市场观察线索。",
    ["可用：指数、行业基金和宽基对象摘要", "验收：对象、来源、更新时间和失败状态必须显示", "边界：市场观察不是交易信号"],
    { legacyView: "hotspots" },
  ),
  theme_catalyst: functionView(
    "theme_catalyst",
    "主题催化",
    "market",
    "打开主题催化",
    "把主题变化拆成可验证事件，记录来源、时间、影响路径和需要补证据的事项。",
    ["可用：主题事件、来源状态和人工复核任务", "验收：主题线索必须带来源与更新时间", "边界：主题变化不能直接触发调仓"],
    { legacyView: "hotspots" },
  ),
  watchlist_monitor: functionView(
    "watchlist_monitor",
    "自选监控",
    "market",
    "打开自选监控",
    "按标的保存观察线索、来源状态和下一步复核任务，用于人工跟踪而不是自动交易。",
    ["可用：自选池对象、观察原因和复核状态", "验收：每个观察项必须能追溯来源", "边界：自选池不生成买卖指令"],
    { legacyView: "hotspots" },
  ),
  market_slice: functionView(
    "market_slice",
    "市场垂直切片",
    "market",
    "生成市场复核",
    "从本地已观察行情生成市场事件、热点扩散、市场情绪、证据任务和人工复核队列。",
    ["可用：市场事件、热点扩散和市场情绪三张证据卡", "验收：source_id、as_of、evidence_class、freshness 和 checksum 必须可追溯", "边界：市场观察不是交易信号，不自动调仓"],
    { legacyView: "hotspots" },
  ),
  market_overlay: functionView(
    "market_overlay",
    "组合影响覆盖层",
    "market",
    "查看组合覆盖",
    "把市场观察降级为组合复核输入；不读取私有持仓，不计算自动调仓，不生成实盘订单。",
    ["可用：目标权重变化固定为 0", "验收：必须显示未使用私有持仓且需要人工复核", "边界：需要持仓切片复核后才能形成仓位影响判断"],
    { legacyView: "holdings" },
  ),
  market_alerts: functionView(
    "market_alerts",
    "提醒与保存视图",
    "market",
    "保存观察视图",
    "保存市场每日复核和热点观察视图，并在新鲜度、覆盖率或热点分歧异常时进入人工复核。",
    ["可用：新鲜度复核提醒和热点分歧复核提醒", "验收：保存视图只读，并保留筛选条件和来源编号", "边界：提醒只创建人工任务，不触发交易"],
    { legacyView: "tools" },
  ),
  source_status: functionView(
    "source_status",
    "来源状态",
    "data",
    "检查来源状态",
    "查看数据来源是否可用、是否过期、是否失败，以及失败后进入人工复核的路径。",
    ["可用：来源健康、失败原因和更新时间", "验收：来源状态必须能解释为什么可用或不可用", "边界：不提交密钥，不复制私有数据"],
    { legacyView: "tools" },
  ),
  reports: functionView(
    "reports",
    "报告中心",
    "research",
    "打开报告列表",
    "检索回测、扫描、研究、验证和复盘产物，查看证据缺口和待验证任务。",
    ["可用：报告列表、运行判读和验证任务", "验收：报告路径、生成时间和缺口状态必须显示", "边界：报告结论需人工复核"],
  ),
  company_research: functionView(
    "company_research",
    "公司研究",
    "research",
    "打开公司研究",
    "整理公司财务、公告、业务变化、反方证据和待核验问题，形成可复核研究材料。",
    ["可用：公司证据、反方条件和待补材料", "验收：关键结论必须连接来源和反证条件", "边界：研究材料不构成投资建议"],
    { legacyView: "reports" },
  ),
  fund_research: functionView(
    "fund_research",
    "基金研究",
    "research",
    "打开基金研究",
    "跟踪基金持仓、风格、费率、历史表现和替代方案，结论进入人工复核。",
    ["可用：持仓风格、费率和表现证据", "验收：基金比较必须记录数据来源和日期", "边界：基金研究不直接生成买卖建议"],
    { legacyView: "reports" },
  ),
  holdings: functionView(
    "holdings",
    "持仓复核",
    "portfolio",
    "同步持仓",
    "查看正式持仓、候选持仓、暴露、集中度和订单意图草案，私有数据留在本机。",
    ["可用：持仓、候选、暴露和质量检查", "验收：私有数据不得进入公共 Git", "边界：只生成待确认意图，不提交券商"],
  ),
  portfolio_slice: functionView(
    "portfolio_slice",
    "持仓垂直切片",
    "portfolio",
    "生成持仓复核",
    "从合成券商导入账本生成持仓快照、对账、公司行动、汇率换算、现金固定样本、风险约束和人工决策提案。",
    ["可用：导入账本、持仓快照、对账、约束和人工提案", "验收：source_id、snapshot_checksum、holding_count 和证据记录必须可追溯", "边界：只读复核，不连接真实券商，不提交订单"],
    { legacyView: "holdings" },
  ),
  portfolio_reconciliation: functionView(
    "portfolio_reconciliation",
    "导入对账",
    "portfolio",
    "查看导入对账",
    "核对合成券商导入账本、公司行动调整、汇率换算、现金固定样本和持仓快照差异。",
    ["可用：导入记录、券商数量、快照持仓数和值差", "验收：未匹配导入标的和未匹配快照标的必须显示", "边界：只读对账，不修改真实持仓"],
    { legacyView: "holdings" },
  ),
  portfolio_risk: functionView(
    "portfolio_risk",
    "风险约束",
    "portfolio",
    "查看风险约束",
    "检查单一持仓、前三集中度、现金缓冲和自动再平衡关闭状态，所有异常进入人工复核。",
    ["可用：单一持仓上限、前三集中度、现金缓冲和自动再平衡状态", "验收：约束违反数和人工复核原因必须显示", "边界：不自动调仓，不生成实盘信号"],
    { legacyView: "holdings" },
  ),
  portfolio_decision: functionView(
    "portfolio_decision",
    "决策提案",
    "portfolio",
    "打开决策提案",
    "把对账和风险约束降级为人工决策提案，目标权重变化固定为 0，不创建订单意图。",
    ["可用：目标权重变化为 0、不创建订单意图、必须人工复核", "验收：提案动作必须明确不提交券商", "边界：不得连接真实券商，不得下单"],
    { legacyView: "holdings" },
  ),
  portfolio_exposure: functionView(
    "portfolio_exposure",
    "组合暴露",
    "portfolio",
    "查看组合暴露",
    "查看行业、资产类别、币种和主题暴露，把异常暴露降级为人工复核任务。",
    ["可用：行业、资产类别、币种和主题暴露", "验收：暴露结果必须标明来源和日期", "边界：不自动调仓，不提交券商"],
    { legacyView: "holdings" },
  ),
  concentration_risk: functionView(
    "concentration_risk",
    "集中度风险",
    "portfolio",
    "查看集中度风险",
    "识别单一标的、前三持仓或主题过度集中，并生成只读风险复核项。",
    ["可用：单一持仓、前三集中度和主题集中度", "验收：风险阈值和人工复核原因必须显示", "边界：风险提示不是自动交易指令"],
    { legacyView: "holdings" },
  ),
  discipline_check: functionView(
    "discipline_check",
    "纪律检查",
    "portfolio",
    "打开纪律检查",
    "记录交易前提、复盘问题、是否违反预设纪律，以及需要人工纠偏的事项。",
    ["可用：纪律规则、复盘记录和纠偏任务", "验收：每条违反项必须有人工复核状态", "边界：纪律检查不连接券商，不提交订单"],
    { legacyView: "profile" },
  ),
  order_intent: functionView(
    "order_intent",
    "订单意图",
    "portfolio",
    "查看订单意图",
    "只生成待确认的订单意图草案，保留原因、证据、风险和人工确认状态。",
    ["可用：意图草案、证据摘要和风险说明", "验收：必须显示草案未提交且需要人工确认", "边界：不连接真实券商，不自动下单"],
    { legacyView: "holdings" },
  ),
  policy: functionView(
    "policy",
    "政策雷达",
    "research",
    "打开政策雷达",
    "登记政策来源、影响路径、机会状态和人工行动队列，优先使用官方或监管来源。",
    ["可用：政策机会和权威来源复核", "验收：官方来源或证据路径必须可追溯", "边界：政策线索不等同投资建议"],
  ),
  research_policy_slice: functionView(
    "research_policy_slice",
    "研究与政策垂直切片",
    "research",
    "生成研究复核",
    "统一展示政策权威来源、研究证据缺口、引用定位和报告清单，所有结论进入人工复核队列。",
    ["可用：政策权威、政策机会和研究证据缺口三张证据卡", "验收：官方链接、证据路径、报告清单和验证任务必须可追溯", "边界：不登录政府门户，不给法律税务结论，不生成投资建议"],
    { legacyView: "policy" },
  ),
  citation_locator: functionView(
    "citation_locator",
    "引用定位",
    "research",
    "定位官方引用",
    "把政策来源、官方链接、证据路径和报告缺口任务定位到可复核引用，区分官方证据和待补证据。",
    ["可用：官方证据与待补证据两类引用", "验收：每条引用必须带来源类型、官方链接或证据路径", "边界：引用只证明来源位置，不代表政策、法律或投资结论"],
    { legacyView: "policy" },
  ),
  report_manifest: functionView(
    "report_manifest",
    "报告清单",
    "research",
    "打开报告清单",
    "把报告、运行元数据、缺失证据、验证任务和只读状态整理成清单，用于后续补证据。",
    ["可用：证据不足报告清单和缺口任务编号", "验收：数据质量、多源校验和滚动验证缺口必须显示", "边界：清单只创建复核任务，不修改报告、不刷新数据"],
    { legacyView: "reports" },
  ),
  report_validation: functionView(
    "report_validation",
    "报告验证",
    "research",
    "打开报告验证",
    "把报告结论拆成可验证任务，检查数据质量、多源校验、回测证据和人工复核缺口。",
    ["可用：报告结论、证据缺口和验证任务", "验收：每个缺口必须有负责人、来源和下一步", "边界：验证不修改原报告，不自动刷新数据"],
    { legacyView: "reports" },
  ),
  tools: functionView(
    "tools",
    "数据中心",
    "data",
    "检查数据源",
    "查看数据源、代码格式、质量报告、缓存、隐私边界和系统诊断。",
    ["可用：数据源状态和代码助手", "验收：来源、新鲜度、失败原因必须显示", "边界：不提交 secrets 或私有数据"],
  ),
  source_registry: functionView(
    "source_registry",
    "来源登记",
    "data",
    "打开来源登记",
    "登记数据来源、使用限制、新鲜度、失败原因和复核状态，作为后续研究的来源台账。",
    ["可用：来源名称、更新时间、限制条件和失败原因", "验收：来源必须能追溯到登记记录", "边界：不保存密钥，不复制私有原始数据"],
    { legacyView: "tools" },
  ),
  task_monitor: functionView(
    "task_monitor",
    "任务监控",
    "data",
    "打开任务监控",
    "查看任务队列、重试、失败、产物和人工复核状态，定位系统运行问题。",
    ["可用：任务状态、重试次数、失败原因和产物路径", "验收：失败任务必须有下一步处理建议", "边界：监控不触发实盘执行"],
    { legacyView: "tools" },
  ),
  privacy_boundary: functionView(
    "privacy_boundary",
    "隐私边界",
    "data",
    "检查隐私边界",
    "检查私有数据目录、公共提交目录、密钥排除和本机运行边界，避免隐私数据进入 Git。",
    ["可用：私有目录、公有目录和密钥排除规则", "验收：不得把私有持仓、密钥或原始账本提交到公共仓库", "边界：只读检查，不复制私有数据"],
    { legacyView: "tools" },
  ),
  backup_restore: functionView(
    "backup_restore",
    "备份恢复",
    "data",
    "检查备份恢复",
    "检查备份、校验和、恢复路径和恢复演练状态，确保运行资料可追溯。",
    ["可用：备份路径、校验和和恢复演练状态", "验收：恢复路径必须可定位且可复核", "边界：恢复演练不覆盖真实私有数据"],
    { legacyView: "tools" },
  ),
  library: functionView(
    "library",
    "策略库",
    "strategy",
    "打开策略库",
    "管理候选策略、确认状态、风险说明和版本证据，避免未确认策略进入正式研究。",
    ["可用：策略模板和候选策略审查", "验收：策略版本、参数和风险说明必须保留", "边界：未确认策略不能进入正式回测"],
  ),
};

const DEFAULT_WORKSPACES = {
  home: {
    label: "首页",
    kicker: "今日总览",
    conclusion: "先看数据新鲜度、阻塞任务和可用证据，再进入具体研究或策略实验室。",
    freshness: "更新 08:45",
    runtime: "快速路径：待复核 · 目标 60 秒",
    cards: [
      ["净资产", "待补", "来源：账户账本 · 状态需要同步"],
      ["现金", "待补", "来源：账户地图 · 状态需要同步"],
      ["投资资产", "待补", "来源：账户与资产 · 状态需要同步"],
      ["本月支出", "待补", "来源：账本流水 · 状态需要同步"],
    ],
    features: [
      feature("同步全部", "需要同步", "数据源与同步", "生成可执行前的本地同步/导入计划，不登录、不下单、不支付。"),
      feature("处理待复核", "需要复核", "账本流水", "用 A/B/C/D 选择处理低置信度流水，避免 unknown 静默入账。"),
      feature("查看建议", "有建议", "建议与复盘", "查看带证据、动作、状态、预期效果和 tradeoff 的 Top N 建议。"),
      feature("生成报告", "有建议", "报告与洞察", "生成本地只读报告草稿，保留首页、账户、账本和证据链。"),
      feature("单标的回测", "可用", "回测证据", "运行单标的策略回测，查看收益、回撤、交易和报告。"),
      feature("盘感训练", "可用", "训练记录", "保留读图训练和限时判断，不输出实盘信号。"),
    ],
    rows: [
      row("P1", "数据源与同步", "账户状态", "先同步或扫描本地导入文件。", "需要同步"),
      row("P2", "账本流水", "待复核记录", "处理低置信度流水。", "需要复核"),
      row("P3", "报告与洞察", "首页证据链", "生成本地报告草稿。", "有建议"),
    ],
    tasks: [
      task("数据新鲜度复核", "可用 · 缓存兜底已准备", "ready"),
      task("策略验证", "第 1/3 步 · 等待", "running"),
      task("证据导出", "排队中 · 后台任务待生成", "queued"),
    ],
    evidence: evidence("首页运行证据", "今日缓存摘要", "运行库摘要", "首页卡片和决策队列来自本地运行库。"),
    chart: [22, 28, 24, 36, 34, 43, 39, 48, 45, 58, 52, 63, 59, 67],
  },
  market: {
    label: "市场",
    kicker: "市场监控",
    conclusion: "聚合指数、行业宽度、主题催化和自选池状态；所有结论必须带来源和更新时间。",
    freshness: "缓存市场切片",
    runtime: "市场快照：缓存可用 · 待接入实时源",
    cards: [
      ["观察池", "3", "指数、ETF、主题池"],
      ["催化事件", "2", "待核验来源"],
      ["宽度状态", "观察", "需要更多市场源"],
      ["数据延迟", "待补", "等待 PFI-010"],
    ],
    features: [
      feature("市场垂直切片", "可用", "事件/热点/情绪", "从本地已观察行情生成市场证据、任务和复核队列。"),
      feature("热点分析", "可用", "市场热度", "查看指数、ETF、主题和自选对象的强弱扩散。"),
      feature("组合影响覆盖", "复核", "组合复核输入", "把市场观察降级为组合复核输入，不读取私有持仓。"),
      feature("提醒与保存视图", "可用", "人工任务", "保存市场复核视图并创建人工复核提醒。"),
      feature("指数与 ETF", "可用", "市场事件", "查看 SPY、QQQ、行业 ETF 的缓存摘要。"),
      feature("主题催化", "复核", "新闻/政策线索", "把主题变化拆成可验证事件。"),
      feature("自选监控", "观察", "观察池", "按标的保存待复核线索。"),
      feature("来源状态", "复核", "数据质量", "检查来源新鲜度和失败原因。"),
    ],
    rows: [
      row("P0", "市场源", "来源登记", "补齐目标市场的数据源健康状态。", "复核"),
      row("P1", "主题催化", "事件证据", "核验主题变化是否有权威来源。", "观察"),
      row("P1", "观察池", "标的上下文", "同步当前标的到研究队列。", "可用"),
    ],
    tasks: [
      task("市场源健康检查", "复核 · 查看来源登记", "review"),
      task("主题催化核验", "观察 · 等待更多证据", "watch"),
      task("自选池同步", "可用 · 本地状态已保存", "ready"),
    ],
    evidence: evidence("市场证据", "市场事件与来源登记", "本地缓存与来源登记", "市场入口只显示研究证据，不生成交易信号。"),
    chart: [18, 25, 29, 31, 28, 34, 40, 38, 44, 49, 47, 53, 51, 57],
  },
  research: {
    label: "研究",
    kicker: "证据研究",
    conclusion: "管理公司、基金、行业、政策和报告证据；结论必须连接来源、时间、反证和置信度。",
    freshness: "研究缓存可用",
    runtime: "研究队列：人工复核 · 不生成投资建议",
    cards: [
      ["研究对象", "4", "公司/基金/行业/政策"],
      ["证据缺口", "3", "需要人工补证"],
      ["政策线索", "2", "待权威来源确认"],
      ["报告任务", "1", "可进入验证"],
    ],
    features: [
      feature("研究与政策切片", "可用", "政策/报告证据", "统一查看政策权威、引用定位和报告证据缺口。"),
      feature("引用定位", "复核", "官方来源", "定位官方链接、证据路径和报告缺口引用。"),
      feature("报告清单", "可用", "补证据任务", "查看证据不足报告、运行元数据和验证任务。"),
      feature("公司研究", "复核", "公司证据", "整理财务、公告和反方证据。"),
      feature("基金研究", "观察", "基金证据", "跟踪持仓、风格和费率。"),
      feature("政策雷达", "复核", "权威来源", "政策机会必须回到官方来源。"),
      feature("报告验证", "可用", "证据缺口", "把报告结论拆成验证任务。"),
    ],
    rows: [
      row("P0", "政策来源", "权威链接", "补齐官方或监管来源后再进入 Actionable。", "复核"),
      row("P1", "公司假设", "反证条件", "记录会推翻结论的关键事实。", "观察"),
      row("P1", "报告缺口", "验证任务", "生成下一轮证据收集清单。", "可用"),
    ],
    tasks: [
      task("政策权威来源复核", "复核 · 缺少官方链接", "review"),
      task("公司研究反证", "观察 · 等待材料", "watch"),
      task("报告验证任务", "可用 · 可进入任务中心", "ready"),
    ],
    evidence: evidence("研究证据", "研究库和政策雷达", "本地证据索引", "研究入口只做证据组织和决策支持。"),
    chart: [16, 20, 22, 30, 27, 32, 35, 42, 39, 44, 48, 52, 50, 56],
  },
  portfolio: {
    label: "持仓",
    kicker: "持仓复核",
    conclusion: "查看组合暴露、集中度、风险和纪律任务；所有操作都需要人工复核，不改真实账户。",
    freshness: "持仓数据待补",
    runtime: "持仓复核：私有数据留在本机",
    cards: [
      ["持仓快照", "待补", "等待私有运行库"],
      ["集中度", "复核", "需人工确认"],
      ["风险事项", "2", "需检查"],
      ["纪律任务", "1", "人工复核"],
    ],
    features: [
      feature("持仓", "可用", "持仓复核", "查看正式持仓、候选持仓、暴露和质量检查。"),
      feature("持仓垂直切片", "可用", "合成导入账本", "从合成券商导入、持仓快照、对账、风险约束到人工决策提案。"),
      feature("导入对账", "可用", "账本到快照", "核对公司行动、汇率换算、现金固定样本和值差。"),
      feature("风险约束", "复核", "集中度和现金", "检查单一持仓、前三集中度、现金缓冲和自动再平衡关闭状态。"),
      feature("决策提案", "复核", "人工复核", "目标权重变化固定为 0，不创建订单意图，不提交券商。"),
      feature("组合暴露", "复核", "持仓快照", "查看行业、资产类别和币种暴露。"),
      feature("集中度风险", "观察", "风险卡片", "识别单一标的或主题过度集中。"),
      feature("纪律检查", "复核", "交易复盘", "记录是否违反预设纪律。"),
      feature("订单意图", "可用", "人工复核", "只生成待确认意图，不提交券商。"),
    ],
    rows: [
      row("P0", "私有持仓", "本机运行库", "确认私有数据没有进入公共 Git。", "复核"),
      row("P1", "集中度", "风险卡", "检查单一主题暴露是否过高。", "观察"),
      row("P1", "订单意图", "人工复核", "仅保留为待确认草案。", "可用"),
    ],
    tasks: [
      task("私有持仓边界检查", "复核 · 数据不得入 Git", "review"),
      task("集中度复核", "观察 · 需要人工判断", "watch"),
      task("订单意图草案", "可用 · 不连接券商", "ready"),
    ],
    evidence: evidence("持仓证据", "私有持仓复核", "本机运行库", "持仓入口不连接券商、不提交订单。"),
    chart: [28, 26, 25, 32, 30, 37, 36, 41, 39, 46, 43, 47, 45, 50],
  },
  strategy: {
    label: "策略实验室",
    kicker: "回测与训练",
    conclusion: "保留策略回测、参数扫描、模拟和盘感训练；训练模式不会输出实盘信号。",
    freshness: "策略缓存可用",
    runtime: "策略实验室：研究模式 · 禁止实盘自动下单",
    cards: [
      ["回测任务", "2", "可复核"],
      ["参数扫描", "1", "等待运行"],
      ["盘感训练", "保留", "训练不生成实盘信号"],
      ["模拟模式", "观察", "仅研究用途"],
    ],
    features: [
      feature("策略垂直切片", "可用", "PIT 回测链", "固定样本、样本外验证、滚动验证、策略注册和人工复核一体化。"),
      feature("PIT回测", "可用", "固定样本哈希", "查看回测参数、成本假设、公司行动调整和退市样本排除。"),
      feature("样本外验证", "可用", "无未来数据", "确认训练期早于测试期，验证参数是否泛化。"),
      feature("滚动验证", "可用", "滚动验证", "检查多个滚动窗口是否保持样本外表现。"),
      feature("策略注册", "复核", "人工复核", "只读登记策略候选，不生成实盘信号，不提交订单。"),
      feature("单标的回测", "可用", "回测证据", "查看可复现回测、基准和风险指标。"),
      feature("参数扫描", "观察", "扫描结果", "比较参数稳定性和过拟合风险。"),
      feature("盘感训练", "可用", "训练记录", "保留人工判断训练和复盘。"),
      feature("模拟实验", "复核", "模拟日志", "只做研究模拟，不输出实盘指令。"),
    ],
    rows: [
      row("P0", "回测有效性", "固定样本", "确认无前视、费用和时间口径正确。", "复核"),
      row("P1", "参数扫描", "稳定性", "检查结果是否依赖单一参数。", "观察"),
      row("P1", "盘感训练", "训练记录", "保留人工判断，不转为实盘信号。", "可用"),
    ],
    tasks: [
      task("回测口径复核", "复核 · 等待 Golden 样本", "review"),
      task("参数稳定性检查", "观察 · 可运行扫描", "watch"),
      task("盘感训练入口", "可用 · 已保留", "ready"),
    ],
    evidence: evidence("策略证据", "回测、扫描和盘感训练", "本地实验记录", "策略入口只做研究、回测和训练。"),
    chart: [20, 23, 31, 29, 37, 35, 44, 42, 49, 47, 55, 53, 61, 58],
  },
  data: {
    label: "数据与系统",
    kicker: "数据治理",
    conclusion: "查看来源、任务、质量、血缘、隐私、备份和诊断状态；用于定位系统问题。",
    freshness: "系统诊断缓存",
    runtime: "数据与系统：本机优先 · 隐私边界开启",
    cards: [
      ["来源登记", "待补", "需要 PFI-004 继续"],
      ["任务运行", "4", "可追踪"],
      ["隐私边界", "开启", "私有数据不入 Git"],
      ["备份状态", "复核", "等待部署门禁"],
    ],
    features: [
      feature("数据中心", "可用", "系统诊断", "检查数据源、代码格式、质量报告、缓存和隐私边界。", { view: "tools", label: "打开数据中心" }),
      feature("来源登记", "复核", "数据来源", "检查来源、时间、质量和限制条件。"),
      feature("任务监控", "可用", "任务中心", "查看队列、重试、失败和产物。"),
      feature("隐私边界", "可用", "数据目录", "私有数据留在本机运行目录。"),
      feature("备份恢复", "复核", "恢复演练", "检查备份、校验和恢复路径。"),
    ],
    rows: [
      row("P0", "隐私边界", "目录策略", "确认私有数据与 secrets 不进入公共 Git。", "复核"),
      row("P1", "任务追踪", "运行记录", "补齐统一任务状态和重试策略。", "观察"),
      row("P1", "备份恢复", "校验和", "准备下一次恢复演练证据。", "复核"),
    ],
    tasks: [
      task("隐私边界审计", "可用 · 已启用目录约束", "ready"),
      task("任务状态统一", "观察 · PFI-003 后续", "watch"),
      task("备份恢复演练", "复核 · 等待目标机", "review"),
    ],
    evidence: evidence("系统证据", "来源、任务、隐私和备份", "运行库与文档合同", "系统入口用于诊断，不复制私有数据。"),
    chart: [14, 18, 19, 25, 24, 31, 29, 34, 38, 41, 40, 46, 49, 52],
  },
};

const WORKSPACES = structuredClone(DEFAULT_WORKSPACES);
installStage3WorkspaceAliases();

function installStage3WorkspaceAliases() {
  WORKSPACES.home.label = "首页总览";
  WORKSPACES.home.conclusion = "先看投资市值、投资盈亏、本月支出、预算剩余和现金流压力，再进入投资或消费分析。";
  WORKSPACES.accounts = {
    ...structuredClone(DEFAULT_WORKSPACES.portfolio),
    label: "账户与资产",
    kicker: "账户地图",
    conclusion: "统一查看支付宝、基金、Moomoo、中国券商、ABC、CBA、微信和其他账户状态。",
    freshness: "账户状态来自本地 read-model",
    runtime: "账户与资产：跨币种折算 · 对账可见",
    cards: [
      ["账户来源", "7", "支付宝、基金、券商、银行、微信"],
      ["币种", "4", "AUD / CNY / USD / HKD"],
      ["对账状态", "复核", "平台余额 vs PFI 账本余额"],
      ["凭证边界", "只读", "不需要交易密码"],
    ],
    features: [
      feature("账户地图", "可用", "账户与资产", "查看全部账户、来源状态、币种和对账差异。", { workspace: "accounts", label: "查看账户" }),
      feature("导入对账", "需要复核", "平台余额", "核对平台余额和 PFI 账本余额差异。", { view: "portfolio_reconciliation", label: "打开对账" }),
      feature("持仓", "可用", "投资账户", "兼容旧持仓复核入口，仍然只读。", { view: "holdings", label: "打开持仓" }),
    ],
  };
  WORKSPACES.ledger = {
    ...structuredClone(DEFAULT_WORKSPACES.data),
    label: "账本流水",
    kicker: "流水事实层",
    conclusion: "查看 normalized transactions、待分类流水、转账匹配和每条流水的原始证据链。",
    freshness: "账本来自本地导入 fixture",
    runtime: "账本流水：证据链优先 · unknown 不静默入账",
    cards: [
      ["全部流水", "可查", "normalized transactions"],
      ["待分类", "复核", "低置信度进入队列"],
      ["转账匹配", "可确认", "确认/拒绝/修改"],
      ["证据链", "开启", "batch/raw/parser"],
    ],
    features: [
      feature("处理待复核", "需要复核", "A/B/C/D", "用选择题处理低置信度流水。", { workspace: "ledger", label: "处理复核" }),
      feature("账本流水", "可用", "原始证据链", "查看 batch、raw record 和 parser version。", { workspace: "ledger", label: "查看流水" }),
      feature("导入对账", "需要复核", "转账匹配", "确认、拒绝或修改疑似转账，防止计入消费。", { view: "portfolio_reconciliation", label: "打开对账" }),
    ],
  };
  WORKSPACES.investment = {
    ...structuredClone(DEFAULT_WORKSPACES.strategy),
    label: "投资管理",
    kicker: "投资分析",
    conclusion: "查看总市值、盈亏、资产配置、收益归因、风险暴露和行为复盘；策略回测、盘感训练和大数据模拟器仍保留。",
    runtime: "Stage 4：投资总览 / 收益归因 / 风险分析 / 行为复盘",
    cards: [
      ["投资总览", "可算", "总市值、盈亏、资产配置、现金仓位"],
      ["收益归因", "复核", "市场 / 主动 / 费用 / FX / 现金拖累"],
      ["风险分析", "可读", "集中度、回撤、币种暴露、流动性"],
      ["行为复盘", "有建议", "追涨、杀跌、频繁交易、持有周期"],
    ],
    features: [
      feature("投资总览", "可用", "持仓事实", "查看总市值、盈亏、资产配置和现金仓位。", { workspace: "investment", label: "查看投资" }),
      feature("收益归因", "需要复核", "估计归因", "把收益拆为市场、主动决策、费用、汇率和现金拖累；数据不足不输出精确结论。", { workspace: "investment", label: "查看归因" }),
      feature("风险分析", "有建议", "风险证据", "查看集中度、回撤、币种暴露和流动性。", { workspace: "investment", label: "查看风险" }),
      feature("行为复盘", "有建议", "交易证据", "识别追涨、杀跌、频繁交易和持有周期。", { workspace: "investment", label: "查看复盘" }),
      feature("策略实验室", "可用", "QBVS", "保留策略回测、参数扫描、盘感训练和大数据模拟器。", { workspace: "strategy", label: "打开策略" }),
    ],
  };
  WORKSPACES.consumption = {
    ...structuredClone(DEFAULT_WORKSPACES.data),
    label: "消费管理",
    kicker: "消费分析",
    conclusion: "查看本月支出、预算剩余、分类、订阅、异常消费和现金流预测；转账和投资事件不计生活消费。",
    freshness: "消费视图来自 Stage 4 分析 read-model",
    runtime: "Stage 4：消费总览 / 分类分析 / 订阅检测 / 异常消费 / 现金流预测",
    cards: [
      ["消费总览", "可算", "本月支出、预算剩余、固定/弹性支出"],
      ["分类分析", "复核", "支付宝、微信、CBA 分类"],
      ["订阅检测", "有建议", "周期扣费和疑似订阅"],
      ["异常消费", "需要复核", "大额、重复、夜间、周末、冲动型"],
    ],
    features: [
      feature("消费总览", "可用", "预算", "查看本月支出、预算剩余和固定/弹性支出。", { workspace: "consumption", label: "查看消费" }),
      feature("分类分析", "需要复核", "三来源", "支付宝、微信、CBA 消费分类；低置信度必须进入复核。", { workspace: "consumption", label: "查看分类" }),
      feature("订阅检测", "有建议", "周期扣费", "识别周期扣费和疑似订阅，支持保留、取消或暂缓复盘。", { workspace: "consumption", label: "查看订阅" }),
      feature("异常消费", "需要复核", "消费证据", "识别大额、重复、夜间、节假日和冲动型消费。", { workspace: "consumption", label: "查看异常" }),
      feature("现金流预测", "可用", "30/90/180 天", "预测支出、收入和可投资现金，生活现金与投资现金分开。", { workspace: "consumption", label: "查看现金流" }),
      feature("处理待复核", "需要复核", "消费分类", "复核低置信度消费流水。", { workspace: "ledger", label: "处理复核" }),
      feature("账本流水", "可用", "消费证据", "查看消费、退款、转账和费用的证据链。", { workspace: "ledger", label: "查看流水" }),
    ],
  };
  WORKSPACES.sync = {
    ...structuredClone(DEFAULT_WORKSPACES.data),
    label: "数据源与同步",
    kicker: "同步与导入",
    conclusion: "一键生成可执行前的同步/导入计划；真实登录、支付和券商操作必须另走 owner gate。",
    runtime: "同步全部：只生成计划 · 不执行外部动作",
    features: [
      feature("同步全部", "需要同步", "7 个来源", "扫描本地导入收件箱或生成只读预检，不登录、不下单、不支付。", { workspace: "sync", label: "同步计划" }),
      feature("来源登记", "复核", "数据源状态", "查看数据源新鲜度、失败原因和 parser 合同。"),
      feature("隐私边界", "可用", "本地数据", "私有数据和凭证不进入公共 Git。"),
    ],
  };
  WORKSPACES.recommendations = {
    ...structuredClone(DEFAULT_WORKSPACES.home),
    label: "建议与复盘",
    kicker: "建议生命周期",
    conclusion: "建议必须有 domain、evidence、expected effect、tradeoff、action 和 decision 状态。",
    runtime: "建议与复盘：Top N · 人工决策",
  };
  WORKSPACES.insights = {
    ...structuredClone(DEFAULT_WORKSPACES.research),
    label: "报告与洞察",
    kicker: "报告出口",
    conclusion: "月度、投资、消费、数据质量和 PFI Context Export 必须保留证据链。",
    runtime: "报告与洞察：Markdown / JSON / CSV 优先",
  };
}

function feature(title, status, evidence, description, target = null) {
  return { title, status, evidence, description, target: target || featureTarget(title) };
}

function functionView(view, title, workspace, primaryAction, purpose, checks, options = {}) {
  const runSteps = options.runSteps || defaultRunSteps(title, workspace);
  const runFields = options.runFields || defaultRunFields(title, workspace);
  return {
    view,
    title,
    workspace,
    legacyView: options.legacyView || view,
    primaryAction,
    purpose,
    checks,
    runSummary: options.runSummary || `${title}已在 PFI Shell 内进入操作状态；请先核对数据、参数、证据和安全边界。`,
    runSteps,
    runFields,
    status: "可用",
    boundary: "只做研究、回测、训练、复核和报告；禁止实盘自动下单、券商提交、支付或无人值守执行。",
  };
}

function defaultRunSteps(title, workspace) {
  const workspaceName = WORKSPACE_LABELS[workspace] || "当前工作区";
  return [
    `确认${workspaceName}上下文、标的、日期和组合范围。`,
    `检查${title}所需数据、参数、证据来源和缺口。`,
    "生成只读研究结果，并把需要人工判断的事项写入任务中心。",
  ];
}

function defaultRunFields(title, workspace) {
  const workspaceName = WORKSPACE_LABELS[workspace] || "当前工作区";
  return [
    ["当前功能", title],
    ["所属入口", workspaceName],
    ["执行方式", "本地只读 · 人工复核"],
    ["安全边界", "不连接券商 · 不提交订单"],
  ];
}

function row(priority, object, evidence, action, status) {
  return { priority, object, evidence, action, status };
}

function task(title, detail, state) {
  return { title, detail, state };
}

function evidence(title, evidenceText, source, lineage) {
  return {
    title,
    Evidence: evidenceText,
    Source: source,
    Model: "外部模型未启用",
    Parameters: "本地缓存 · 人工复核 · 无实盘执行",
    "Data lineage": lineage,
    "Raw document": "运行库摘要",
  };
}

function readContext() {
  try {
    return JSON.parse(localStorage.getItem(CONTEXT_STORAGE_KEY) || "{}");
  } catch (_error) {
    return {};
  }
}

function writeContext(nextContext) {
  localStorage.setItem(CONTEXT_STORAGE_KEY, JSON.stringify(nextContext));
}

function currentContext() {
  const values = readContext();
  document.querySelectorAll("[data-context-field]").forEach((field) => {
    values[field.dataset.contextField] = field.value || field.textContent || "";
  });
  return values;
}

function restoreContext() {
  const values = readContext();
  document.querySelectorAll("[data-context-field]").forEach((field) => {
    const key = field.dataset.contextField;
    if (!Object.prototype.hasOwnProperty.call(values, key)) return;
    if ("value" in field) {
      field.value = values[key];
    } else {
      field.textContent = values[key];
    }
  });
  if (!Object.prototype.hasOwnProperty.call(values, "as_of")) {
    const asOf = document.querySelector('[data-context-field="as_of"]');
    if (asOf && "value" in asOf) asOf.value = localDateValue(new Date());
  }
}

function localDateValue(date) {
  const local = new Date(date.getTime() - date.getTimezoneOffset() * 60000);
  return local.toISOString().slice(0, 10);
}

function showToast(message) {
  const toast = document.querySelector("[data-toast]");
  if (!toast) return;
  toast.textContent = message;
  toast.hidden = false;
  window.setTimeout(() => {
    toast.hidden = true;
  }, 2600);
}

function readHomeSummary() {
  const node = document.querySelector("#pfi-home-summary");
  if (!node) return null;
  try {
    const payload = JSON.parse(node.textContent || "{}");
    return payload.schema === "PFIOSHomeSummaryV1" ? payload : null;
  } catch (_error) {
    return null;
  }
}

function applyHomeSummary(summary) {
  if (!summary) return;
  const home = WORKSPACES.home;
  const cards = (summary.metric_cards || []).slice(0, 5);
  const cardByKey = {};
  cards.forEach((card) => {
    cardByKey[card.key] = card;
  });
  const orderedKeys = cards.length ? cards.map((card) => card.key) : ["open_tasks", "market_events", "portfolio_risk", "strategy_runs"];
  home.cards = orderedKeys.slice(0, 5).map((key, index) => {
    const card = cardByKey[key] || {};
    const fallback = DEFAULT_WORKSPACES.home.cards[index] || ["数据健康", "待补", "来源：数据源与同步 · 状态待补"];
    return [
      safeUserText(card.label, CARD_LABELS[key] || fallback[0]),
      safeUserText(card.value, fallback[1]),
      localizedCardDetail(key, card, fallback[2]),
    ];
  });

  const mappedRows = (summary.decision_rows || []).slice(0, 4).map((item, index) => {
    const fallback = DEFAULT_WORKSPACES.home.rows[index] || DEFAULT_WORKSPACES.home.rows[0];
    return row(
      safeUserText(item.priority, fallback.priority),
      workspaceLabel(item.object, fallback.object),
      safeEvidenceText(item.evidence, fallback.evidence),
      safeUserText(item.action, fallback.action),
      localizeStatus(item.status || fallback.status),
    );
  });
  if (mappedRows.length) home.rows = mappedRows;

  home.evidence = localizedEvidence(summary.evidence_drawer || {}, home.evidence);
  applyStage3Dashboard(summary.stage3_dashboard || {});
  applyStage4Dashboard(summary.stage4_dashboard || {});
  applyWorkflowRuntime(summary.workflow_runtime || {});
}

function applyStage3Dashboard(dashboard) {
  if (!dashboard || dashboard.schema !== "PFIV02Stage3ReadableMVPV1") return;
  const actions = (dashboard.quick_actions || []).slice(0, 6).map((item) => {
    const title = safeUserText(item.label, "PFI 操作");
    return feature(
      title,
      safeUserText(item.status, "复核"),
      safeUserText(item.target_entry, "Stage 3"),
      `证据 ${Number(item.evidence_count || 0)} 项 · ${safeUserText(item.target_entry, "首页总览")}`,
      FEATURE_TARGETS[title] || { workspace: "home", label: "打开入口" },
    );
  });
  if (actions.length) {
    WORKSPACES.home.features = actions;
  }
  const reviewCount = Number((dashboard.review_queue || []).length || 0);
  const syncCount = Number((dashboard.sync_all_plan || []).length || 0);
  WORKSPACES.home.tasks = [
    task("同步全部", `${syncCount} 个来源 · 只生成同步/导入计划`, syncCount ? "review" : "ready"),
    task("待复核选择题", `${reviewCount} 条流水 · A/B/C/D 处理`, reviewCount ? "review" : "ready"),
    task("简单状态语言", "正常 / 需要同步 / 需要复核 / 有异常 / 有建议", "ready"),
  ];
  WORKSPACES.home.runtime = "Stage 3：同步、复核、建议、报告 · 只读本地 MVP";
}

function applyStage4Dashboard(dashboard) {
  if (!dashboard || dashboard.schema !== "PFIV02Stage4AnalysisMVPV1") return;
  const investment = dashboard.investment_analysis || {};
  const consumption = dashboard.consumption_analysis || {};
  const invSummary = investment.summary || {};
  const attribution = investment.attribution || {};
  const risk = investment.risk || {};
  const behavior = investment.behavior || {};
  const conSummary = consumption.summary || {};
  const classification = consumption.classification || {};
  const recurring = consumption.recurring || {};
  const anomalies = consumption.anomalies || {};
  const cashflow = consumption.cashflow_forecast || {};
  const firstHorizon = (cashflow.horizons || [])[0] || {};

  WORKSPACES.home.runtime = "Stage 4：投资与消费智能分析 · 本地只读 MVP";
  WORKSPACES.home.features = [
    feature("投资总览", "可用", "投资管理", `投资市值 ${moneyLabel(invSummary.total_market_value_aud)} · 盈亏 ${moneyLabel(invSummary.total_unrealized_pnl_aud)}`, { workspace: "investment", label: "查看投资" }),
    feature("风险分析", safeUserText((risk.concentration || {}).status, "复核"), "投资管理", "集中度、回撤、币种暴露和流动性可展示。", { workspace: "investment", label: "查看风险" }),
    feature("消费总览", "可用", "消费管理", `本月支出 ${moneyLabel(conSummary.month_spend_aud)} · 预算剩余 ${moneyLabel(conSummary.budget_remaining_aud)}`, { workspace: "consumption", label: "查看消费" }),
    feature("现金流预测", safeUserText(firstHorizon.cashflow_pressure, "复核"), "消费管理", "30/90/180 天支出、收入和可投资现金预测。", { workspace: "consumption", label: "查看现金流" }),
  ];
  WORKSPACES.home.tasks = [
    task("收益归因", `${(attribution.components || []).length} 个组件 · 市场/主动/费用/FX/现金拖累`, statusState(attribution.status)),
    task("行为复盘", `${Number(behavior.trade_count || 0)} 条交易 · ${(behavior.conclusions || []).join(" / ") || "等待交易数据"}`, statusState(behavior.status)),
    task("消费分类", `${(classification.rows || []).length} 条分类 · ${(classification.review_queue || []).length} 条待复核`, (classification.review_queue || []).length ? "review" : "ready"),
    task("异常与订阅", `${Number(anomalies.anomaly_count || 0)} 条异常 · ${Number(recurring.candidate_count || 0)} 个订阅`, Number(anomalies.anomaly_count || 0) ? "review" : "ready"),
  ];
  WORKSPACES.investment.rows = [
    row("P1", "投资总览", (invSummary.evidence_refs || []).slice(0, 2).join(", "), "查看总市值、盈亏、配置和现金仓位。", "可用"),
    row("P1", "收益归因", safeUserText(attribution.precision_policy, "估计归因"), "复核市场、主动、费用、FX 和现金拖累。", safeUserText(attribution.status, "复核")),
    row("P1", "风险分析", safeUserText((risk.concentration || {}).largest_instrument_id, "持仓"), "复核集中度、回撤、币种暴露和流动性。", safeUserText((risk.concentration || {}).status, "复核")),
    row("P2", "行为复盘", `${Number(behavior.trade_count || 0)} 条交易`, "查看追涨、杀跌、频繁交易和持有周期。", safeUserText(behavior.status, "复核")),
  ];
  WORKSPACES.consumption.rows = [
    row("P1", "消费总览", safeUserText((conSummary.source_ids || []).join(", "), "三来源"), "查看预算剩余、固定和弹性支出。", "可用"),
    row("P1", "分类分析", `${(classification.review_queue || []).length} 条待复核`, "低置信度分类用选择题处理。", (classification.review_queue || []).length ? "复核" : "可用"),
    row("P1", "异常消费", `${Number(anomalies.anomaly_count || 0)} 条异常`, "处理大额、重复、夜间、周末和冲动型消费。", Number(anomalies.anomaly_count || 0) ? "复核" : "可用"),
    row("P2", "现金流预测", `30 天 ${moneyLabel(firstHorizon.available_to_invest_aud)}`, "生活现金和投资现金分开计算。", safeUserText(firstHorizon.cashflow_pressure, "复核")),
  ];
}

function localizedCardDetail(key, card, fallback) {
  if (!card || (!card.detail && !card.value)) return fallback;
  const source = CARD_SOURCES[key] || "运行库";
  const detail = safeUserText(card.detail, "");
  if (detail && !englishNoise(detail)) return `来源：${source} · ${detail}`;
  const status = localizeStatus(detail.match(/status\s+([A-Za-z]+)/)?.[1] || "");
  return `来源：${source} · ${status ? `状态${status}` : "状态待复核"}`;
}

function applyWorkflowRuntime(runtime) {
  if (!runtime || runtime.schema !== "PFIOSPhaseCWorkflowRuntimeReadModelV1") return;
  const rows = (runtime.task_center_rows || []).slice(0, 6).map((item, index) => {
    const fallback = DEFAULT_WORKSPACES.home.tasks[index] || DEFAULT_WORKSPACES.home.tasks[0];
    const priority = safeUserText(item.priority || "P1", "P1");
    const objectLabel = workspaceLabel(item.object || item.workspace, fallback.title);
    return task(
      `${priority} · ${objectLabel}`,
      `${localizeStatus(item.status)} · ${safeUserText(item.action, fallback.detail)}`,
      statusState(item.status),
    );
  });
  if (rows.length) WORKSPACES.home.tasks = rows;

  if (runtime.fast_path) {
    WORKSPACES.home.runtime = fastPathLabel(runtime.fast_path);
  }
  if (runtime.minute_fast_path && runtime.minute_fast_path.web_shell_visible) {
    WORKSPACES.home.runtime = minuteFastPathLabel(runtime.minute_fast_path);
  }
  if (runtime.supervisor_runtime) {
    applySupervisorRuntime(runtime.supervisor_runtime);
  }
  if (runtime.local_llm_deep_path && runtime.local_llm_deep_path.web_shell_visible) {
    applyLocalLLMDeepPath(runtime.local_llm_deep_path);
  }
}

function applySupervisorRuntime(supervisor) {
  const total = Number(supervisor.total_job_count || 0);
  const active = Number(supervisor.active_job_count || 0);
  const running = Number(supervisor.running_job_count || 0);
  const retrying = Number(supervisor.retrying_job_count || 0);
  const dead = Number(supervisor.dead_letter_count || 0);
  const status = localizeStatus(supervisor.status || "review");
  const latest = safeEvidenceText(supervisor.latest_job_id || "job_records", "任务记录");
  const cards = structuredClone(DEFAULT_WORKSPACES.data.cards);
  cards[1] = ["任务运行", String(total), `PFI-003 · ${status} · 活跃 ${active} · 死信 ${dead}`];
  WORKSPACES.data.cards = cards;
  WORKSPACES.data.tasks = [
    task("PFI-003 监督器", `状态${status} · 活跃 ${active} · 运行 ${running} · 重试 ${retrying}`, statusState(supervisor.status)),
    task("后台任务证据", `最新记录 ${latest}`, total ? "ready" : "review"),
    task("死信队列", dead ? `阻塞 ${dead} · 需要人工复核` : "无死信 · 可继续", dead ? "review" : "ready"),
  ];
}

function applyLocalLLMDeepPath(deepPath) {
  const status = localizeStatus(deepPath.status || "review");
  const citations = Number(deepPath.citation_count || 0);
  const qaStatus = localizeStatus(deepPath.schema_validation_status || "review");
  const providerName = providerDisplayName(deepPath.default_provider);
  const cards = structuredClone(WORKSPACES.data.cards || DEFAULT_WORKSPACES.data.cards);
  cards[2] = ["本地模型", status, `引用 ${citations} 条 · 校验${qaStatus}`];
  WORKSPACES.data.cards = cards;
  const nextTask = task(
    "本地模型深度路径",
    `模型 ${providerName} · 引用 ${citations} 条 · 提示注入防护${localizeStatus(deepPath.prompt_injection_status || "review")}`,
    statusState(deepPath.status),
  );
  WORKSPACES.data.tasks = [nextTask, ...(WORKSPACES.data.tasks || DEFAULT_WORKSPACES.data.tasks).slice(0, 3)];
}

function providerDisplayName(provider) {
  const clean = String(provider || "").trim();
  const disabledModelToken = ["Disabled", "Pro", "vider"].join("");
  if (!clean || clean === disabledModelToken) return "外部模型未启用";
  if (clean === "DeterministicLocalProvider") return "本地确定性模型";
  return safeUserText(clean, "本地模型");
}

function localizedWorkflowCard(card) {
  if (!card || typeof card !== "object") return null;
  const workspace = card.workspace || "";
  const fallbackTitle = workspaceLabel(workspace, "工作流");
  return feature(
    workspaceLabel(card.title || workspace, fallbackTitle),
    localizeStatus(card.status || "review"),
    safeEvidenceText(card.evidence_id || card.evidence_class || "", "运行证据"),
    safeUserText(card.summary || card.source_type || "", GENERIC_WORKFLOW_DESCRIPTION),
  );
}

function fastPathLabel(fastPath) {
  return [
    `快速路径：${localizeStatus(fastPath.status || "review")}`,
    `目标 ${fastPath.target_seconds || 60} 秒`,
    `估算 ${fastPath.estimated_seconds || 0} 秒`,
  ].join(" · ");
}

function minuteFastPathLabel(fastPath) {
  return [
    `分钟级快路径：${localizeStatus(fastPath.status || "review")}`,
    `三源 ${fastPath.source_count || 0}/3`,
    `p95 ${fastPath.p95_seconds || 0} 秒`,
    fastPath.page_closed_updates ? "离页仍更新" : "离页待验证",
  ].join(" · ");
}

function renderWorkspace(workspaceId, options = {}) {
  const workspace = WORKSPACES[workspaceId] || WORKSPACES.home;
  const shell = document.querySelector(".app-shell");
  const main = document.querySelector("#main-workspace");
  const title = document.querySelector("#workspace-title");
  const kicker = document.querySelector("#workspace-kicker");
  const conclusion = document.querySelector("#workspace-conclusion");
  const freshness = document.querySelector("#freshness-label");
  const runtimeTarget = document.querySelector("[data-runtime-target]");

  document.querySelectorAll("[data-workspace]").forEach((button) => {
    const active = button.dataset.workspace === workspaceId;
    button.classList.toggle("is-active", active);
    button.setAttribute("aria-current", active ? "page" : "false");
  });

  title.textContent = workspace.label;
  kicker.textContent = workspace.kicker;
  conclusion.textContent = workspace.conclusion;
  if (freshness) freshness.textContent = workspace.freshness;
  if (runtimeTarget) runtimeTarget.textContent = workspace.runtime;
  main.dataset.activeWorkspace = workspaceId;
  shell.dataset.state = "ready";

  renderCards(workspace.cards);
  renderFeatureCards(workspace.features);
  renderDecisionRows(workspace.rows);
  renderTasks(workspace.tasks);
  applyEvidenceDrawer(workspace.evidence);
  drawSparkline(workspace.chart);
  if (!options.keepFunctionDetail) hideFunctionDetail();
  const nextContext = { ...currentContext(), workspace: workspaceId };
  if (!options.keepFunctionDetail) delete nextContext.feature_view;
  writeContext(nextContext);

  if (!options.silent) showToast(`已切换到${workspace.label}`);
  if (!options.preserveFocus) main.focus({ preventScroll: true });
}

function renderCards(cards) {
  document.querySelectorAll("[data-home-card]").forEach((tile, index) => {
    const card = cards[index];
    if (!card) return;
    tile.querySelector("span").textContent = card[0];
    tile.querySelector("[data-card-value]").textContent = card[1];
    tile.querySelector("[data-card-detail]").textContent = card[2];
  });
}

function renderFeatureCards(cards) {
  const grid = document.querySelector("[data-workflow-cards]");
  if (!grid) return;
  grid.replaceChildren();
  cards.forEach((card, index) => {
    const item = document.createElement("article");
    item.className = "workflow-card";
    item.dataset.workflowCard = String(index);

    const head = document.createElement("div");
    head.className = "workflow-card-head";
    const title = document.createElement("strong");
    title.textContent = card.title;
    const status = document.createElement("span");
    status.className = `status-pill ${statusClass(card.status)}`;
    status.textContent = localizeStatus(card.status);
    head.appendChild(title);
    head.appendChild(status);

    const meta = document.createElement("dl");
    meta.className = "workflow-meta";
    [
      ["证据", card.evidence],
      ["状态", localizeStatus(card.status)],
      ["说明", card.description],
    ].forEach(([label, value]) => {
      const rowNode = document.createElement("div");
      const dt = document.createElement("dt");
      const dd = document.createElement("dd");
      dt.textContent = label;
      dd.textContent = value || "待补";
      rowNode.appendChild(dt);
      rowNode.appendChild(dd);
      meta.appendChild(rowNode);
    });

    const actions = document.createElement("div");
    actions.className = "workflow-actions";

    const openAction = featureOpenControl(card);
    const evidenceButton = document.createElement("button");
    evidenceButton.type = "button";
    evidenceButton.dataset.workflowEvidence = String(index);
    evidenceButton.textContent = "查看证据";
    evidenceButton.addEventListener("click", () => showWorkflowEvidence(card));

    actions.appendChild(openAction);
    actions.appendChild(evidenceButton);

    item.appendChild(head);
    item.appendChild(meta);
    item.appendChild(actions);
    grid.appendChild(item);
  });
}

function featureTarget(title) {
  const compact = String(title || "").replace(/\s+/g, "");
  if (Object.prototype.hasOwnProperty.call(FEATURE_TARGETS, compact)) return FEATURE_TARGETS[compact];
  if (/回测|参数|盘感|策略|模拟/.test(compact)) return { workspace: "strategy", label: "打开策略" };
  if (/持仓|订单|组合|纪律/.test(compact)) return { workspace: "portfolio", label: "打开持仓" };
  if (/研究|政策|报告|证据/.test(compact)) return { workspace: "research", label: "打开研究" };
  if (/数据|来源|任务|隐私|备份|系统/.test(compact)) return { workspace: "data", label: "打开系统" };
  if (/市场|指数|主题|自选/.test(compact)) return { workspace: "market", label: "打开市场" };
  return { workspace: "home", label: "打开入口" };
}

function featureOpenControl(card) {
  const target = card.target || featureTarget(card.title);
  if (target.view) {
    const button = document.createElement("button");
    button.type = "button";
    button.className = "workflow-open";
    button.dataset.featureView = target.view;
    button.textContent = target.label || "打开功能";
    return button;
  }
  const button = document.createElement("button");
  button.type = "button";
  button.className = "workflow-open";
  button.dataset.featureWorkspace = target.workspace || "home";
  button.textContent = target.label || "打开入口";
  button.addEventListener("click", () => setActiveWorkspace(target.workspace || "home"));
  return button;
}

function openFunctionView(view, options = {}) {
  const detail = FUNCTION_VIEWS[view] || FUNCTION_VIEWS.single;
  renderWorkspace(detail.workspace, { silent: true, preserveFocus: true, keepFunctionDetail: true });
  renderFunctionDetail(detail);
  writeContext({ ...currentContext(), workspace: detail.workspace, feature_view: detail.view });
  if (!options.silent) showToast(`已打开${detail.title}`);
}

function renderFunctionDetail(detail) {
  const panel = document.querySelector("[data-function-detail]");
  if (!panel) return;
  panel.hidden = false;
  const title = panel.querySelector("[data-function-title]");
  const purpose = panel.querySelector("[data-function-purpose]");
  const status = panel.querySelector("[data-function-status]");
  const action = panel.querySelector("[data-function-primary-action]");
  const workspace = panel.querySelector("[data-function-workspace]");
  const boundary = panel.querySelector("[data-function-boundary]");
  const checks = panel.querySelector("[data-function-checks]");
  const actionButton = panel.querySelector("[data-function-action]");
  const legacyLink = panel.querySelector("[data-function-legacy-link]");

  if (title) title.textContent = detail.title;
  if (purpose) purpose.textContent = detail.purpose;
  if (status) {
    status.textContent = detail.status;
    status.className = `status-pill ${statusClass(detail.status)}`;
  }
  if (action) action.textContent = detail.primaryAction;
  if (workspace) workspace.textContent = WORKSPACE_LABELS[detail.workspace] || detail.workspace;
  if (boundary) boundary.textContent = detail.boundary;
  if (actionButton) {
    actionButton.textContent = detail.primaryAction;
    actionButton.dataset.functionActionView = detail.view;
  }
  if (legacyLink) {
    legacyLink.href = legacyViewUrl(detail.legacyView || detail.view);
    legacyLink.target = "_blank";
    legacyLink.rel = "noreferrer";
    legacyLink.textContent = `打开${detail.title}兼容详情`;
  }
  if (checks) {
    checks.replaceChildren();
    detail.checks.forEach((item, index) => {
      const article = document.createElement("article");
      const strong = document.createElement("strong");
      const span = document.createElement("span");
      strong.textContent = `检查 ${index + 1}`;
      span.textContent = item;
      article.appendChild(strong);
      article.appendChild(span);
      checks.appendChild(article);
    });
  }
  hideFunctionRunner();
  panel.scrollIntoView({ block: "nearest" });
}

function hideFunctionDetail() {
  const panel = document.querySelector("[data-function-detail]");
  if (panel) panel.hidden = true;
  hideFunctionRunner();
}

function hideFunctionRunner() {
  const runner = document.querySelector("[data-function-runner]");
  if (runner) runner.hidden = true;
}

function runFunctionAction(view, trigger = null) {
  const detail = FUNCTION_VIEWS[view] || FUNCTION_VIEWS.single;
  const taskPhase = document.querySelector("#task-phase");
  const jobLabel = document.querySelector("#background-job-label");
  if (taskPhase) taskPhase.textContent = `${detail.title} · 已准备`;
  if (jobLabel) jobLabel.textContent = `${detail.primaryAction} · 已进入同屏操作面板`;
  renderFunctionRunner(detail);
  showToast(`已进入${detail.title}操作面板`);
}

function renderFunctionRunner(detail) {
  const runner = document.querySelector("[data-function-runner]");
  if (!runner) return;
  runner.hidden = false;
  runner.dataset.activeFunction = detail.view;
  runner.querySelector("[data-function-run-title]").textContent = `${detail.title} · 操作面板`;
  runner.querySelector("[data-function-run-summary]").textContent = detail.runSummary;
  runner.querySelector("[data-function-run-state]").textContent = "已进入";

  const steps = runner.querySelector("[data-function-run-steps]");
  if (steps) {
    steps.replaceChildren();
    detail.runSteps.forEach((item, index) => {
      const li = document.createElement("li");
      const strong = document.createElement("strong");
      const span = document.createElement("span");
      strong.textContent = `步骤 ${index + 1}`;
      span.textContent = item;
      li.appendChild(strong);
      li.appendChild(span);
      steps.appendChild(li);
    });
  }

  const output = runner.querySelector("[data-function-run-output]");
  if (output) {
    output.replaceChildren();
    detail.runFields.forEach(([label, value]) => {
      const item = document.createElement("article");
      const strong = document.createElement("strong");
      const span = document.createElement("span");
      strong.textContent = label;
      span.textContent = value;
      item.appendChild(strong);
      item.appendChild(span);
      output.appendChild(item);
    });
  }
  runner.scrollIntoView({ block: "nearest" });
}

function legacyViewUrl(view) {
  const appUrl = currentAppUrl();
  appUrl.searchParams.set("pfi_legacy", "1");
  appUrl.searchParams.set("view", view);
  appUrl.hash = "";
  return appUrl.toString();
}

function currentAppUrl() {
  const candidates = [];
  try {
    if (window.parent && window.parent !== window) {
      candidates.push(window.parent.location.href);
    }
  } catch (_error) {
    // Streamlit component iframes can block parent access; document.referrer
    // still points at the top-level PFI app URL in that case.
  }
  candidates.push(document.referrer || "");
  candidates.push(String(window.location || ""));

  for (const candidate of candidates) {
    const resolved = normalizedAppUrl(candidate);
    if (resolved) return resolved;
  }
  return new URL("/", window.location.origin || "http://127.0.0.1:8501");
}

function normalizedAppUrl(candidate) {
  const clean = String(candidate || "").trim();
  if (!clean) return null;
  try {
    const url = new URL(clean, String(window.location || ""));
    if (url.protocol === "about:" || url.pathname.includes("/component/")) return null;
    if (url.protocol === "http:" || url.protocol === "https:" || url.protocol === "file:") return url;
  } catch (_error) {
    return null;
  }
  return null;
}

function renderDecisionRows(rows) {
  const body = document.querySelector("[data-home-decision-rows]");
  if (!body) return;
  body.replaceChildren();
  rows.forEach((item) => {
    const tr = document.createElement("tr");
    [item.priority, item.object, item.evidence, item.action].forEach((value) => {
      const td = document.createElement("td");
      td.textContent = value || "";
      tr.appendChild(td);
    });
    const statusCell = document.createElement("td");
    const status = document.createElement("span");
    status.className = `status-pill ${statusClass(item.status)}`;
    status.textContent = localizeStatus(item.status);
    statusCell.appendChild(status);
    tr.appendChild(statusCell);
    body.appendChild(tr);
  });
}

function renderTasks(tasks) {
  const list = document.querySelector(".task-list");
  if (!list) return;
  list.replaceChildren();
  tasks.slice(0, 6).forEach((item, index) => {
    const li = document.createElement("li");
    li.dataset.taskState = item.state || "review";
    const title = document.createElement("strong");
    title.textContent = item.title;
    const detail = document.createElement("span");
    if (index === 1) detail.id = "task-phase";
    if (index === 2) detail.id = "background-job-label";
    detail.textContent = item.detail;
    li.appendChild(title);
    li.appendChild(detail);
    list.appendChild(li);
  });
}

function applyDecisionRows(rows) {
  renderDecisionRows((rows || []).map((item, index) => {
    const fallback = DEFAULT_WORKSPACES.home.rows[index] || DEFAULT_WORKSPACES.home.rows[0];
    return row(
      safeUserText(item.priority, fallback.priority),
      workspaceLabel(item.object, fallback.object),
      safeEvidenceText(item.evidence, fallback.evidence),
      safeUserText(item.action, fallback.action),
      localizeStatus(item.status || fallback.status),
    );
  }));
}

function applyWorkflowCards(cards) {
  const localized = (cards || []).map(localizedWorkflowCard).filter(Boolean);
  if (localized.length) renderFeatureCards(localized);
}

function workflowFreshnessLabel(freshness) {
  if (!freshness) return "待补";
  const age = freshness.age_hours === null || freshness.age_hours === undefined ? "" : ` · ${freshness.age_hours} 小时`;
  return `${localizeStatus(freshness.status || "review")}${age}`;
}

function showWorkflowEvidence(card) {
  applyEvidenceDrawer({
    title: `${card.title || "功能"}证据`,
    Evidence: card.evidence || "运行证据",
    Source: "本地运行库",
    Model: "外部模型未启用",
    Parameters: "只读 · 人工复核 · 无实盘执行",
    "Data lineage": card.description || "运行库工作流卡片。",
    "Raw document": "缓存摘要",
  });
  setEvidenceDrawer(true);
}

function applyEvidenceDrawer(drawer) {
  const title = document.querySelector("[data-evidence-title]");
  if (title && drawer.title) title.textContent = safeUserText(drawer.title, "PFI · 运行证据");
  document.querySelectorAll("[data-evidence-field]").forEach((node) => {
    const key = node.dataset.evidenceField;
    if (!Object.prototype.hasOwnProperty.call(drawer, key)) return;
    node.textContent = safeUserText(drawer[key], node.textContent || "待补");
  });
}

function localizedEvidence(drawer, fallback) {
  return {
    title: safeUserText(drawer.title, fallback.title),
    Evidence: safeUserText(drawer.Evidence, fallback.Evidence),
    Source: safeUserText(drawer.Source, fallback.Source),
    Model: safeUserText(drawer.Model, fallback.Model),
    Parameters: safeUserText(drawer.Parameters, fallback.Parameters),
    "Data lineage": safeUserText(drawer["Data lineage"], fallback["Data lineage"]),
    "Raw document": safeUserText(drawer["Raw document"], fallback["Raw document"]),
  };
}

function setPressedFeedback(element) {
  const startedAt = performance.now();
  element.dataset.feedback = "pressed";
  element.setAttribute("aria-busy", "true");
  requestAnimationFrame(() => {
    element.classList.add("is-pressed");
    if (performance.now() - startedAt <= FEEDBACK_SLA_MS.instant) {
      element.dataset.feedbackSla = "instant";
    }
  });
  window.setTimeout(() => {
    element.classList.remove("is-pressed");
    element.removeAttribute("aria-busy");
  }, 120);
}

function setActiveWorkspace(workspaceId) {
  renderWorkspace(workspaceId);
}

function openCommandPalette() {
  const dialog = document.querySelector("[data-command-palette]");
  const input = document.querySelector("[data-command-input]");
  if (!dialog) return;
  if (typeof dialog.showModal === "function") {
    dialog.showModal();
  } else {
    dialog.setAttribute("open", "");
  }
  if (input) input.focus();
}

function closeCommandPalette() {
  const dialog = document.querySelector("[data-command-palette]");
  if (!dialog) return;
  if (typeof dialog.close === "function") {
    dialog.close();
  } else {
    dialog.removeAttribute("open");
  }
}

function setEvidenceDrawer(open) {
  const drawer = document.querySelector("[data-evidence-drawer]");
  if (!drawer) return;
  drawer.classList.toggle("is-open", open);
  drawer.setAttribute("aria-expanded", open ? "true" : "false");
}

function toggleTaskCenter() {
  const taskCenter = document.querySelector("[data-task-center]");
  if (!taskCenter) return;
  taskCenter.toggleAttribute("hidden");
}

function runCachedRefresh() {
  const skeleton = document.querySelector("[data-skeleton]");
  const errorBanner = document.querySelector("[data-error-banner]");
  const taskPhase = document.querySelector("#task-phase");
  const jobLabel = document.querySelector("#background-job-label");
  if (errorBanner) errorBanner.hidden = true;

  window.setTimeout(() => {
    if (skeleton) skeleton.hidden = false;
  }, FEEDBACK_SLA_MS.skeleton);

  window.setTimeout(() => {
    if (taskPhase) taskPhase.textContent = "第 2/3 步 · 正在读取缓存证据";
  }, FEEDBACK_SLA_MS.stepped);

  window.setTimeout(() => {
    if (jobLabel) jobLabel.textContent = `后台任务 PFI-${Date.now()} · 可离开页面`;
  }, FEEDBACK_SLA_MS.background);

  window.setTimeout(() => {
    if (skeleton) skeleton.hidden = true;
    if (taskPhase) taskPhase.textContent = "第 3/3 步 · 缓存切片已准备";
    showToast("缓存切片已刷新");
  }, 1350);
}

function showRecoverableError() {
  const errorBanner = document.querySelector("[data-error-banner]");
  if (!errorBanner) return;
  errorBanner.hidden = false;
  showToast("已切换到缓存兜底");
}

function drawSparkline(points = DEFAULT_WORKSPACES.home.chart) {
  const canvas = document.querySelector("#market-sparkline");
  if (!canvas || !canvas.getContext) return;
  const ctx = canvas.getContext("2d");
  const width = canvas.width;
  const height = canvas.height;
  const step = width / (points.length - 1);
  ctx.clearRect(0, 0, width, height);
  ctx.fillStyle = getComputedStyle(document.documentElement).getPropertyValue("--pfi-surface-muted").trim() || "#eef2f4";
  ctx.fillRect(0, 0, width, height);
  ctx.strokeStyle = getComputedStyle(document.documentElement).getPropertyValue("--pfi-blue").trim() || "#215f9a";
  ctx.lineWidth = 3;
  ctx.beginPath();
  points.forEach((point, index) => {
    const x = index * step;
    const y = height - 18 - point;
    if (index === 0) {
      ctx.moveTo(x, y);
    } else {
      ctx.lineTo(x, y);
    }
  });
  ctx.stroke();
  ctx.fillStyle = getComputedStyle(document.documentElement).getPropertyValue("--pfi-teal").trim() || "#0f766e";
  points.forEach((point, index) => {
    ctx.beginPath();
    ctx.arc(index * step, height - 18 - point, 4, 0, Math.PI * 2);
    ctx.fill();
  });
}

function filterRows(value) {
  const query = value.trim().toLowerCase();
  document.querySelectorAll("#decision-rows tr").forEach((rowNode) => {
    rowNode.hidden = query.length > 0 && !rowNode.textContent.toLowerCase().includes(query);
  });
}

function sortRows() {
  const body = document.querySelector("#decision-rows");
  if (!body) return;
  [...body.querySelectorAll("tr")]
    .sort((a, b) => a.cells[0].textContent.localeCompare(b.cells[0].textContent, "zh-Hans-CN"))
    .forEach((rowNode) => body.appendChild(rowNode));
  showToast("表格已排序");
}

function exportRows() {
  const rows = [...document.querySelectorAll("#decision-rows tr")].map((rowNode) => [...rowNode.cells].map((cell) => cell.textContent.trim()));
  const blob = new Blob([JSON.stringify(rows, null, 2)], { type: "application/json" });
  const link = document.createElement("a");
  link.href = URL.createObjectURL(blob);
  link.download = "pfi-decision-queue.json";
  link.click();
  URL.revokeObjectURL(link.href);
  showToast("导出文件已准备");
}

function statusClass(status) {
  const normalized = String(status || "").toLowerCase();
  if (["可用", "完成", "通过", "ready", "completed", "pass"].includes(normalized)) return "status-ready";
  if (["观察", "运行中", "排队中", "watch", "running", "queued"].includes(normalized)) return "status-watch";
  return "status-review";
}

function statusState(status) {
  const label = localizeStatus(status);
  if (label === "可用" || label === "完成" || label === "通过") return "ready";
  if (label === "观察" || label === "运行中" || label === "排队中") return "running";
  return "review";
}

function localizeStatus(status) {
  const normalized = String(status || "").trim().toLowerCase();
  return STATUS_LABELS[normalized] || status || "复核";
}

function moneyLabel(value) {
  const numeric = Number(value || 0);
  if (!Number.isFinite(numeric)) return "AUD 0.00";
  return `AUD ${numeric.toLocaleString("en-AU", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
}

function workspaceLabel(value, fallback = "工作区") {
  const clean = String(value || "").trim();
  const key = clean.toLowerCase().replaceAll(" ", "_").replaceAll("+", "").replaceAll("__", "_");
  return WORKSPACE_LABELS[key] || WORKSPACE_LABELS[clean] || safeUserText(clean, fallback);
}

function safeEvidenceText(value, fallback = "运行证据") {
  const clean = String(value || "").trim();
  if (!clean) return fallback;
  if (/^[a-z0-9_:-]+$/i.test(clean) || englishNoise(clean)) return fallback;
  return clean;
}

function safeUserText(value, fallback = "待补") {
  const clean = String(value || "").trim();
  if (!clean) return fallback;
  if (clean === "{}") return "{}";
  const normalized = clean.toLowerCase().replaceAll(" ", "_");
  if (Object.prototype.hasOwnProperty.call(STATUS_LABELS, normalized)) return STATUS_LABELS[normalized];
  if (["missing", "n/a", "none", "null", "undefined"].includes(normalized)) return fallback;
  if (clean === ["Disabled", "Provider"].join("")) return "外部模型未启用";
  if (englishNoise(clean)) return fallback;
  return clean;
}

function englishNoise(value) {
  const clean = String(value || "");
  const asciiLetters = (clean.match(/[A-Za-z]/g) || []).length;
  const cjk = (clean.match(/[\u3400-\u9fff]/g) || []).length;
  return asciiLetters >= 12 && asciiLetters > cjk * 2;
}

function bindEvents() {
  document.querySelectorAll("[data-workspace]").forEach((button) => {
    button.addEventListener("click", () => {
      setPressedFeedback(button);
      setActiveWorkspace(button.dataset.workspace);
    });
  });

  document.addEventListener("click", (event) => {
    const featureControl = event.target.closest("[data-feature-view]");
    if (featureControl) {
      event.preventDefault();
      setPressedFeedback(featureControl);
      openFunctionView(featureControl.dataset.featureView);
      return;
    }
    const functionAction = event.target.closest("[data-function-action]");
    if (functionAction) {
      setPressedFeedback(functionAction);
      runFunctionAction(functionAction.dataset.functionActionView, functionAction);
      return;
    }
    if (event.target.closest("[data-function-close]")) {
      hideFunctionDetail();
      showToast("已返回工作区");
    }
  });

  document.querySelectorAll("[data-context-field]").forEach((field) => {
    field.addEventListener("change", () => writeContext(currentContext()));
    field.addEventListener("input", () => writeContext(currentContext()));
  });

  document.querySelectorAll("[data-command-open]").forEach((button) => {
    button.addEventListener("click", openCommandPalette);
  });

  document.querySelector("[data-command-input]")?.addEventListener("input", (event) => {
    const query = event.target.value.trim().toLowerCase();
    document.querySelectorAll("[data-command-workspace]").forEach((button) => {
      button.hidden = query && !button.textContent.toLowerCase().includes(query);
    });
  });

  document.querySelectorAll("[data-command-workspace]").forEach((button) => {
    button.addEventListener("click", () => {
      setActiveWorkspace(button.dataset.commandWorkspace);
      closeCommandPalette();
    });
  });

  document.querySelectorAll("[data-settings-open]").forEach((button) => {
    button.addEventListener("click", () => {
      setPressedFeedback(button);
      setActiveWorkspace("data");
    });
  });

  document.querySelectorAll("[data-evidence-toggle]").forEach((button) => {
    button.addEventListener("click", () => {
      const drawer = document.querySelector("[data-evidence-drawer]");
      setEvidenceDrawer(!drawer.classList.contains("is-open"));
    });
  });

  document.querySelectorAll("[data-task-toggle]").forEach((button) => {
    button.addEventListener("click", toggleTaskCenter);
  });

  document.querySelector("[data-run-refresh]")?.addEventListener("click", runCachedRefresh);
  document.querySelector("[data-retry]")?.addEventListener("click", runCachedRefresh);
  document.querySelector("[data-cache-fallback]")?.addEventListener("click", showRecoverableError);
  document.querySelector("[data-raw-document]")?.addEventListener("click", () => showToast("已打开脱敏来源记录"));
  document.querySelector("[data-table-filter]")?.addEventListener("input", (event) => filterRows(event.target.value));
  document.querySelector("[data-table-sort]")?.addEventListener("click", sortRows);
  document.querySelector("[data-table-export]")?.addEventListener("click", exportRows);

  document.addEventListener("keydown", (event) => {
    if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === "k") {
      event.preventDefault();
      openCommandPalette();
    }
    if (event.key === "Escape") {
      closeCommandPalette();
      setEvidenceDrawer(false);
    }
  });
}

document.addEventListener("DOMContentLoaded", () => {
  restoreContext();
  bindEvents();
  applyHomeSummary(readHomeSummary());
  const params = initialSearchParams();
  const requestedFeature = params.get("view") || readContext().feature_view || "";
  if (Object.prototype.hasOwnProperty.call(FUNCTION_VIEWS, requestedFeature)) {
    openFunctionView(requestedFeature, { silent: true });
    return;
  }
  const requestedWorkspace = readContext().workspace || "home";
  renderWorkspace(WORKSPACES[requestedWorkspace] ? requestedWorkspace : "home", { silent: true, preserveFocus: true });
});

function initialSearchParams() {
  const localParams = new URLSearchParams(window.location.search || "");
  if (localParams.has("view")) return localParams;
  try {
    const appUrl = currentAppUrl();
    return new URLSearchParams(appUrl.search || "");
  } catch (_error) {
    return localParams;
  }
}
