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
  market: "市场",
  markets: "市场",
  research: "研究",
  policy: "政策",
  portfolio: "持仓",
  strategy: "策略实验室",
  strategy_lab: "策略实验室",
  data: "数据与系统",
};

const CARD_LABELS = {
  open_tasks: "待处理",
  market_events: "市场事件",
  portfolio_risk: "持仓风险",
  strategy_runs: "策略运行",
};

const CARD_SOURCES = {
  open_tasks: "任务表",
  market_events: "来源登记",
  portfolio_risk: "持仓快照",
  strategy_runs: "证据记录",
};

const FEATURE_TARGETS = {
  市场快照: { view: "hotspots", label: "打开热点" },
  研究队列: { view: "reports", label: "打开报告" },
  持仓复核: { view: "holdings", label: "打开持仓" },
  策略实验室: { workspace: "strategy", label: "打开策略" },
  指数与ETF: { workspace: "market", label: "打开市场" },
  主题催化: { workspace: "market", label: "打开市场" },
  自选监控: { workspace: "market", label: "打开市场" },
  市场垂直切片: { view: "market_slice", label: "打开切片" },
  组合影响覆盖: { view: "market_overlay", label: "打开覆盖层" },
  提醒与保存视图: { view: "market_alerts", label: "打开提醒" },
  来源状态: { workspace: "data", label: "打开来源" },
  公司研究: { workspace: "research", label: "打开研究" },
  基金研究: { workspace: "research", label: "打开研究" },
  研究与政策切片: { view: "research_policy_slice", label: "打开切片" },
  引用定位: { view: "citation_locator", label: "打开引用" },
  报告清单: { view: "report_manifest", label: "打开清单" },
  政策雷达: { view: "policy", label: "打开政策雷达" },
  报告验证: { view: "reports", label: "打开报告中心" },
  持仓垂直切片: { view: "portfolio_slice", label: "打开切片" },
  导入对账: { view: "portfolio_reconciliation", label: "打开对账" },
  风险约束: { view: "portfolio_risk", label: "打开约束" },
  决策提案: { view: "portfolio_decision", label: "打开提案" },
  组合暴露: { view: "portfolio_slice", label: "打开切片" },
  集中度风险: { view: "portfolio_risk", label: "打开约束" },
  纪律检查: { view: "profile", label: "打开画像" },
  订单意图: { view: "portfolio_decision", label: "打开提案" },
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
  来源登记: { workspace: "data", label: "打开数据" },
  任务监控: { workspace: "data", label: "打开任务" },
  隐私边界: { workspace: "data", label: "打开系统" },
  备份恢复: { workspace: "data", label: "打开系统" },
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
    ["可用：目标权重变化固定为 0", "验收：必须显示 no_private_holdings_used 和 human_review_required", "边界：需要持仓切片复核后才能形成仓位影响判断"],
    { legacyView: "holdings" },
  ),
  market_alerts: functionView(
    "market_alerts",
    "提醒与保存视图",
    "market",
    "保存观察视图",
    "保存市场每日复核和热点观察视图，并在新鲜度、覆盖率或热点分歧异常时进入人工复核。",
    ["可用：新鲜度复核提醒和热点分歧复核提醒", "验收：保存视图只读、带 filters 和 source_ids", "边界：提醒只创建人工任务，不触发交易"],
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
    ["可用：max_single、top3、cash_buffer 和自动再平衡状态", "验收：约束违反数和人工复核原因必须显示", "边界：不自动调仓，不生成实盘信号"],
    { legacyView: "holdings" },
  ),
  portfolio_decision: functionView(
    "portfolio_decision",
    "决策提案",
    "portfolio",
    "打开决策提案",
    "把对账和风险约束降级为人工决策提案，目标权重变化固定为 0，不创建订单意图。",
    ["可用：target_weight_change=0、order_intent_created=false、human_review_required=true", "验收：提案动作必须明确不提交券商", "边界：不得连接真实券商，不得下单"],
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
    ["可用：政策权威、政策机会和研究证据缺口三张证据卡", "验收：source_url、evidence_path、report manifest 和 validation task 必须可追溯", "边界：不登录政府门户，不给法律税务结论，不生成投资建议"],
    { legacyView: "policy" },
  ),
  citation_locator: functionView(
    "citation_locator",
    "引用定位",
    "research",
    "定位官方引用",
    "把政策来源、官方链接、证据路径和报告缺口任务定位到可复核引用，区分官方证据和待补证据。",
    ["可用：OfficialEvidence 与 EvidenceRepairRequired 两类引用", "验收：每条引用必须带 source_type、source_url 或 evidence_path", "边界：引用只证明来源位置，不代表政策、法律或投资结论"],
    { legacyView: "policy" },
  ),
  report_manifest: functionView(
    "report_manifest",
    "报告清单",
    "research",
    "打开报告清单",
    "把报告、RunMetadata、缺失证据、验证任务和只读状态整理成 manifest，用于后续补证据。",
    ["可用：NeedsMoreEvidence 报告清单和 gap task id", "验收：数据质量、多源校验和 walk-forward 缺口必须显示", "边界：清单只创建复核任务，不修改报告、不刷新数据"],
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
      ["待处理", "0", "来源：任务表 · 状态待补"],
      ["市场事件", "0", "来源：来源登记 · 状态待补"],
      ["持仓风险", "待补", "来源：持仓快照 · 需要人工数据"],
      ["策略运行", "0", "来源：证据记录 · 状态待补"],
    ],
    features: [
      feature("单标的回测", "可用", "回测证据", "运行单标的策略回测，查看收益、回撤、交易和报告。"),
      feature("参数扫描", "可用", "参数稳定性", "比较参数网格、Train-Test 和 Walk-Forward 结果。"),
      feature("盘感训练", "可用", "训练记录", "保留读图训练和限时判断，不输出实盘信号。"),
      feature("热点分析", "可用", "市场热度", "查看指数、ETF、主题和自选对象的强弱扩散。"),
      feature("报告中心", "可用", "研究档案", "查看、筛选、下载和复核研究产物。"),
      feature("持仓", "复核", "持仓边界", "查看正式持仓、候选持仓、暴露和质量检查。"),
      feature("政策雷达", "复核", "权威来源", "登记政策来源、影响路径和人工行动队列。"),
      feature("数据中心", "复核", "系统诊断", "检查来源、任务、隐私边界和备份状态。"),
    ],
    rows: [
      row("P0", "数据新鲜度", "来源时间", "复核缓存兜底是否仍可用。", "复核"),
      row("P1", "市场简报", "事件摘要", "查看今日可用市场证据。", "可用"),
      row("P1", "策略运行", "回测元数据", "确认策略结果是否可复现。", "观察"),
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
      feature("引用定位", "复核", "官方来源", "定位 source_url、evidence_path 和报告缺口引用。"),
      feature("报告清单", "可用", "补证据任务", "查看 NeedsMoreEvidence 报告、RunMetadata 和验证任务。"),
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

function feature(title, status, evidence, description, target = null) {
  return { title, status, evidence, description, target: target || featureTarget(title) };
}

function functionView(view, title, workspace, primaryAction, purpose, checks, options = {}) {
  return {
    view,
    title,
    workspace,
    legacyView: options.legacyView || view,
    primaryAction,
    purpose,
    checks,
    status: "可用",
    boundary: "只做研究、回测、训练、复核和报告；禁止实盘自动下单、券商提交、支付或无人值守执行。",
  };
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
  const cardByKey = {};
  (summary.metric_cards || []).forEach((card) => {
    cardByKey[card.key] = card;
  });
  home.cards = ["open_tasks", "market_events", "portfolio_risk", "strategy_runs"].map((key, index) => {
    const card = cardByKey[key] || {};
    const fallback = DEFAULT_WORKSPACES.home.cards[index];
    return [
      CARD_LABELS[key] || fallback[0],
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
  applyWorkflowRuntime(summary.workflow_runtime || {});
}

function localizedCardDetail(key, card, fallback) {
  if (!card || (!card.detail && !card.value)) return fallback;
  const source = CARD_SOURCES[key] || "运行库";
  const detail = safeUserText(card.detail, "");
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
  if (runtime.supervisor_runtime) {
    applySupervisorRuntime(runtime.supervisor_runtime);
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
  cards.slice(0, 8).forEach((card, index) => {
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
    actionButton.href = legacyViewUrl(detail.legacyView || detail.view);
    actionButton.target = "_blank";
    actionButton.rel = "noreferrer";
  }
  if (legacyLink) {
    legacyLink.href = legacyViewUrl(detail.legacyView || detail.view);
    legacyLink.target = "_blank";
    legacyLink.rel = "noreferrer";
    legacyLink.textContent = `进入${detail.title}功能页`;
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
  panel.scrollIntoView({ block: "nearest" });
}

function hideFunctionDetail() {
  const panel = document.querySelector("[data-function-detail]");
  if (panel) panel.hidden = true;
}

function runFunctionAction(view, trigger = null) {
  const detail = FUNCTION_VIEWS[view] || FUNCTION_VIEWS.single;
  const taskPhase = document.querySelector("#task-phase");
  const jobLabel = document.querySelector("#background-job-label");
  if (taskPhase) taskPhase.textContent = `${detail.title} · 已准备`;
  if (jobLabel) jobLabel.textContent = `${detail.primaryAction} · 正在进入功能页`;
  showToast(`正在进入${detail.title}功能页`);
  if (!trigger || !trigger.href) navigateToFunctionPage(detail.legacyView || detail.view);
}

function navigateToFunctionPage(view) {
  const anchor = document.createElement("a");
  anchor.href = legacyViewUrl(view);
  anchor.target = "_blank";
  anchor.rel = "noreferrer";
  anchor.hidden = true;
  document.body.appendChild(anchor);
  anchor.click();
  anchor.remove();
}

function legacyViewUrl(view) {
  let search = window.location.search || "";
  let pathname = window.location.pathname || "/";
  try {
    if (window.parent && window.parent !== window) {
      search = window.parent.location.search || search;
      pathname = window.parent.location.pathname || pathname;
    }
  } catch (_error) {
    search = window.location.search || "";
    pathname = window.location.pathname || "/";
  }
  const params = new URLSearchParams(search);
  params.set("pfi_shell", "0");
  params.set("view", view);
  return `${pathname}?${params.toString()}`;
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
  const params = new URLSearchParams(window.location.search || "");
  const requestedFeature = params.get("view") || readContext().feature_view || "";
  if (Object.prototype.hasOwnProperty.call(FUNCTION_VIEWS, requestedFeature)) {
    openFunctionView(requestedFeature, { silent: true });
    return;
  }
  const requestedWorkspace = readContext().workspace || "home";
  renderWorkspace(WORKSPACES[requestedWorkspace] ? requestedWorkspace : "home", { silent: true, preserveFocus: true });
});
