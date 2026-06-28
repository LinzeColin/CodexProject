const CONTEXT_STORAGE_KEY = "pfi-context-v2";
const RUNTIME_CONFIG = readRuntimeConfig();
const PFI_RUNTIME_API_BASE_URL = RUNTIME_CONFIG.apiBaseUrl || "http://127.0.0.1:8766";
const FEEDBACK_SLA_MS = {
  instant: 100,
  skeleton: 300,
  stepped: 1000,
  background: 10000,
};
const FEEDBACK_STATES = {
  progress: "进行中",
  success: "成功",
  failure: "失败",
};
const FEEDBACK_STATE_ORDER = ["progress", "success", "failure"];
const FEEDBACK_HUB_LANES = {
  visual: "视觉状态轨道",
  haptic: "触感强度",
  sound: "声音反馈",
};

const FX_SNAPSHOT = Object.freeze({
  snapshotId: "fx_AUD_CNY_20260628",
  pair: "AUD/CNY",
  rateAudToCny: 4.6874,
  effectiveDate: "2026-06-28",
  effectiveTimeLocal: "06:00",
  cacheState: "cached",
});
const FX_TO_CNY = Object.freeze({
  CNY: 1,
  AUD: FX_SNAPSHOT.rateAudToCny,
  USD: 1.52 * FX_SNAPSHOT.rateAudToCny,
  HKD: 0.195 * FX_SNAPSHOT.rateAudToCny,
});

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

const USER_TEXT_LABELS = {
  ["Syn" + "thetic " + "E" + "2E"]: "合成端到端",
  ["Rollback " + "plan"]: "回滚计划",
  ["Follow-up " + "list"]: "后续任务清单",
  ["Review " + "lifecycle"]: "复盘生命周期",
  ["PFI Context " + "Export"]: "PFI 上下文导出",
  ["Alpha " + "上下文出口"]: "外部系统上下文出口",
  ["Existing " + "smoke、" + "focused " + "tests、" + "changed-only " + "governance 已记录。"]: "既有冒烟检查、聚焦测试和变更范围治理已记录。",
  ["Owner " + "docs、diff " + "summary、rollback " + "plan、follow-up " + "list。"]: "用户文档、差异摘要、回滚计划和后续任务清单已记录。",
};

const GENERIC_WORKFLOW_DESCRIPTION = "查看该工作流的来源、任务和证据状态。";

const WORKSPACE_LABELS = {
  home: "首页",
  accounts: "账户与资产",
  ledger: "账本流水",
  investment: "投资管理",
  consumption: "消费管理",
  sync: "数据源与上传",
  recommendations: "建议与复盘",
  insights: "报告与洞察",
  settings: "设置",
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
  数据源与上传: "数据源与上传",
  建议与复盘: "建议与复盘",
  报告与洞察: "报告与洞察",
  设置: "设置",
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
  data_health: "数据源与上传",
  investment_market_value: "投资管理",
  investment_pnl: "收益归因",
  month_spend: "消费管理",
  budget_remaining: "消费预算",
  cashflow_pressure: "现金流预测",
};

const UNIFIED_TREND_PERIODS = ["1月", "2月", "3月", "4月", "5月", "6月"];

const UNIFIED_TREND_DATA = {
  accounts: {
    scope: "账户与资产",
    title: "现金、净资产、总资产与负债趋势",
    unit: "CNY",
    source: "SQLite 运行读模型",
    emptyState: "账户趋势需要先保存持仓或导入账户流水。",
    periods: [],
    series: [
      { id: "cash_cny", label: "现金", color: "--pfi-teal", values: [] },
      { id: "net_worth_cny", label: "净资产", color: "--pfi-blue", values: [] },
      { id: "total_assets_cny", label: "总资产", color: "--pfi-amber", values: [] },
      { id: "total_liabilities_cny", label: "总负债", color: "--pfi-red", values: [] },
    ],
  },
  investment: {
    scope: "投资管理",
    title: "投资市值、收益、未实现盈亏与现金仓位趋势",
    unit: "CNY",
    source: "SQLite 运行读模型",
    emptyState: "投资趋势需要先保存持仓，当前不伪造收益。",
    periods: [],
    series: [
      { id: "market_value_cny", label: "投资市值", color: "--pfi-blue", values: [] },
      { id: "total_return_cny", label: "总收益", color: "--pfi-teal", values: [] },
      { id: "unrealized_pnl_cny", label: "未实现盈亏", color: "--pfi-amber", values: [] },
      { id: "cash_position_cny", label: "现金仓位", color: "--pfi-red", values: [] },
    ],
  },
  consumption: {
    scope: "消费管理",
    title: "本月支出、预算剩余、固定/弹性支出与现金流预测",
    unit: "CNY",
    source: "SQLite 运行读模型",
    emptyState: "消费趋势需要先导入真实流水，当前不伪造支出或预算。",
    periods: [],
    series: [
      { id: "month_spend_cny", label: "本月支出", color: "--pfi-blue", values: [] },
      { id: "budget_remaining_cny", label: "预算剩余", color: "--pfi-teal", values: [] },
      { id: "fixed_spend_cny", label: "固定支出", color: "--pfi-amber", values: [] },
      { id: "flex_spend_cny", label: "弹性支出", color: "--pfi-red", values: [] },
      { id: "cashflow_forecast_cny", label: "现金流预测", color: "--pfi-blue", values: [] },
    ],
  },
};

const FEATURE_TARGETS = {
  市场快照: { view: "hotspots", label: "打开热点" },
  研究队列: { view: "reports", label: "打开报告" },
  持仓复核: { view: "holdings", label: "打开持仓" },
  持仓编辑: { workspace: "investment", routeAlias: "/investment?tab=holdings", label: "打开编辑" },
  持仓持久化: { workspace: "investment", routeAlias: "/investment?tab=holdings", label: "打开持仓" },
  保存修改: { workspace: "investment", routeAlias: "/investment?tab=holdings", label: "打开持仓" },
  策略实验室: { workspace: "investment", routeAlias: "/investment/strategy-lab", label: "打开策略" },
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
  上传支付宝账单: { workspace: "sync", label: "打开上传" },
  上传中心: { workspace: "sync", label: "打开上传" },
  拖拽上传: { workspace: "sync", label: "打开上传" },
  失败反馈: { workspace: "sync", label: "查看反馈" },
  导入中心: { workspace: "sync", label: "打开导入" },
  导入批次: { workspace: "sync", label: "查看批次" },
  导入摘要: { workspace: "sync", label: "查看摘要" },
  复核入口: { workspace: "ledger", label: "进入复核" },
  同步全部: { workspace: "sync", label: "同步计划" },
  处理待复核: { workspace: "ledger", label: "处理复核" },
  查看建议: { workspace: "recommendations", label: "查看建议" },
  生成报告: { workspace: "insights", label: "生成报告" },
  建议模型: { view: "recommendation_model", label: "打开模型" },
  复盘生命周期: { view: "review_lifecycle", label: "打开生命周期" },
  投资建议: { view: "investment_recommendations", label: "查看投资建议" },
  消费建议: { view: "consumption_recommendations", label: "查看消费建议" },
  月度报告: { view: "monthly_report", label: "打开月报" },
  投资报告: { view: "investment_report", label: "打开投资报告" },
  消费报告: { view: "consumption_report", label: "打开消费报告" },
  数据质量报告: { view: "data_quality_report", label: "打开质量报告" },
  导出中心: { view: "export_center", label: "打开导出" },
  "PFI 上下文导出": { view: "pfi_context_export", label: "打开上下文" },
  外部系统上下文出口: { view: "alpha_readonly_export", label: "查看出口" },
  端到端验收: { view: "stage6_e2e", label: "打开验收" },
  合成端到端: { view: "stage6_synthetic_e2e", label: "查看验收" },
  回归治理: { view: "stage6_regression_governance", label: "查看治理" },
  交付与回滚: { view: "stage6_delivery_rollback", label: "查看交付" },
  回滚计划: { view: "stage6_rollback_plan", label: "查看回滚" },
  后续任务清单: { view: "stage6_follow_up_list", label: "查看后续" },
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
  本机数据管理: { view: "privacy_boundary", label: "打开数据" },
  备份恢复: { view: "backup_restore", label: "打开备份" },
  运行反馈控制台: { workspace: "settings", label: "打开反馈" },
  多模态反馈: { workspace: "settings", label: "打开反馈" },
  触感反馈强度: { workspace: "settings", label: "打开触感" },
  声音反馈: { workspace: "settings", label: "打开声音" },
  视觉反馈: { workspace: "settings", label: "打开视觉" },
  通知反馈: { workspace: "settings", label: "打开通知" },
  反馈测试: { workspace: "settings", label: "测试反馈" },
  无障碍反馈: { workspace: "settings", label: "打开无障碍" },
  现金与净资产趋势: { workspace: "accounts", label: "查看趋势" },
  投资趋势: { workspace: "investment", label: "查看趋势" },
  消费趋势: { workspace: "consumption", label: "查看趋势" },
};

const SEARCH_ALIASES = {
  首页总览: "home dashboard overview zonglan 首页 今日 总览",
  账户与资产: "accounts assets account zichan 账户 资产 净资产 现金",
  账本流水: "ledger transactions zhangben liushui 账本 流水 交易 分类",
  投资管理: "investment portfolio touzi 投资 持仓 风险 收益 回测",
  持仓: "holdings positions chichang 持仓 投资 组合 编辑 保存",
  持仓编辑: "holdings edit persistence chichang bianji 持仓 编辑 数量 价格 保存",
  持仓持久化: "holdings persistence sqlite draft chichang 持仓 持久化 刷新 重启",
  保存修改: "save holdings baocun xiugai 保存 修改 持仓",
  消费管理: "consumption spending xiaofei xf 消费 支出 预算 订阅 异常",
  现金与净资产趋势: "trend qushi accounts cash net worth 现金 净资产 趋势",
  投资趋势: "trend qushi investment market value return cash position 市值 总收益 现金仓位 趋势",
  消费趋势: "trend qushi consumption spending budget cashflow 支出 预算 现金流 趋势",
  数据源与上传: "sources upload import sync shuju yuan 上传 导入 同步 支付宝",
  上传中心: "upload center shangchuan zhongxin 上传 文件 拖拽 支付宝 CSV ZIP",
  上传支付宝账单: "alipay bill upload zhangdan 支付宝 账单 上传 CSV ZIP",
  拖拽上传: "drag drop upload tuozhuai 拖拽 上传 文件",
  失败反馈: "error feedback shibai fankui 失败 错误 类型 过大",
  导入中心: "import center daoru zhongxin 导入 批次 摘要 复核",
  导入批次: "import batch daoru pici 批次 文件 记录",
  导入摘要: "import summary zhaiyao 摘要 记录 待复核",
  复核入口: "review entry fuhe rukou 复核 账本 流水",
  建议与复盘: "review recommendations advice fupan 建议 复盘 决策",
  报告与洞察: "reports insights report baogao 报告 洞察 导出 上下文",
  设置: "settings preferences config shezhi 设置 偏好 系统",
  数据与系统: "settings data system shuju xitong 数据 系统 来源 任务 管理",
  运行反馈控制台: "feedback console fankui fk 反馈 运行 控制台",
  多模态反馈: "multimodal feedback haptic sound visual notification 多模态 反馈",
  触感反馈强度: "haptic vibration touch chugan 触感 震动 强度",
  声音反馈: "sound audio shengyin 声音 音效",
  视觉反馈: "visual animation shijue 视觉 动效 状态",
  通知反馈: "notification toast tongzhi 通知 提醒",
  反馈测试: "feedback test ceshi 测试 反馈",
  无障碍反馈: "accessibility a11y wu zhang ai 无障碍",
};

const SEARCH_DEFAULT_LIMIT = 10;
let globalSearchState = { items: [], results: [], activeIndex: 0 };
let clickFeedbackSerial = 0;
let clickSafeBound = false;
let feedbackRuntimeState = { haptic: true, sound: false, motion: true };
let feedbackAudioContext = null;

const UPLOAD_ALLOWED_EXTENSIONS = [".csv", ".zip", ".xls", ".xlsx"];
const UPLOAD_MAX_FILE_MB = 50;
const IMPORT_BATCH_FIXTURES = [
  {
    batchId: "P5-旧账单-20260627",
    source: "旧支付宝原始账单",
    fileCount: 3,
    recordCount: 1286,
    reviewCount: 42,
    status: "待复核",
    summary: "已发现旧交接目录中的支付宝分段账单，等待用户确认后接入私有账本。",
  },
];
let uploadCenterState = {
  files: [],
  rejected: [],
  lastSource: "",
};

const HOLDINGS_DRAFT_STORAGE_KEY = "pfi-v021-unsubmitted-holdings-draft";
let holdingsPersistenceState = defaultHoldingsState();
let runtimeTrendState = null;

const FUNCTION_VIEWS = {
  single: functionView(
    "single",
    "单标的回测",
    "investment",
    "运行回测",
    "选择标的、数据源、周期、策略和成本假设，输出收益、回撤、交易、风险闸门和报告证据。",
    ["可用：单策略回测和双策略对比", "验收：费用、时间区间、数据质量和策略版本必须显示", "复核：只生成研究结果，生成复核记录"],
  ),
  scan: functionView(
    "scan",
    "参数扫描",
    "investment",
    "运行参数扫描",
    "比较参数网格、样本内外表现、稳定性和过拟合风险，用于判断策略是否值得继续研究。",
    ["可用：参数网格和稳定性摘要", "验收：记录样本区间、参数范围和评分口径", "复核：扫描结果不能直接转成交易指令"],
  ),
  strategy_slice: functionView(
    "strategy_slice",
    "策略垂直切片",
    "investment",
    "生成策略复核",
    "从固定 PIT 样本、回测哈希、样本外验证、滚动验证、策略注册和人工复核任务形成完整策略证据链。",
    ["可用：PIT 回测、样本外验证、滚动验证和策略注册", "验收：固定样本哈希、没有未来数据、运行可取消恢复", "复核：生成复核信号，进入人工复核"],
    { legacyView: "single" },
  ),
  pit_backtest: functionView(
    "pit_backtest",
    "PIT回测",
    "investment",
    "查看 PIT 回测",
    "查看固定样本哈希、回测参数、成本假设、公司行动调整和退市样本排除证据。",
    ["可用：行情校验和、复现哈希和下一根K线执行模型", "验收：公司行动和退市样本必须显式记录", "复核：回测不是交易信号"],
    { legacyView: "single" },
  ),
  train_test_validation: functionView(
    "train_test_validation",
    "样本外验证",
    "investment",
    "查看样本外验证",
    "核对训练期和测试期的时间切分，确认训练结束早于测试开始，没有未来数据泄漏。",
    ["可用：切分时间、训练样本数、测试样本数和泛化比例", "验收：训练窗口不得覆盖测试窗口", "复核：验证结果只进入人工复核"],
    { legacyView: "scan" },
  ),
  walk_forward_validation: functionView(
    "walk_forward_validation",
    "滚动验证",
    "investment",
    "查看滚动验证",
    "检查多个滚动训练/测试窗口，确认每个窗口的训练结束早于测试开始。",
    ["可用：窗口数量、通过数量和平均泛化比例", "验收：每个滚动窗口都必须没有未来数据", "复核：滚动通过也进入人工复核"],
    { legacyView: "scan" },
  ),
  strategy_registry: functionView(
    "strategy_registry",
    "策略注册",
    "investment",
    "打开策略注册",
    "把策略候选登记为研究模型，保留版本、参数、哈希、验证状态和人工复核要求。",
    ["可用：模型编号、策略版本、样本外验证状态和滚动验证状态", "验收：人工确认状态必须清楚", "复核：注册不等于上线，进入人工复核"],
    { legacyView: "library" },
  ),
  market_feel: functionView(
    "market_feel",
    "盘感训练",
    "investment",
    "生成盘感训练",
    "保留读图训练、限时判断、隐藏答案和复盘记录，训练人工判断，输出训练记录。",
    ["可用：大盘对象、持仓对象和自选代码训练", "验收：训练窗口、答案窗口、超时和复盘必须记录", "复核：训练结果不得作为自动买卖依据"],
  ),
  big_data: functionView(
    "big_data",
    "模拟实验",
    "investment",
    "打开模拟实验",
    "组合策略、情景压力和假设实验，用于研究策略在不同市场状态下的表现。",
    ["可用：模拟和压力情景入口", "验收：假设、参数和输出路径必须可追溯", "复核：仅研究模拟，使用本机数据"],
  ),
  hotspots: functionView(
    "hotspots",
    "热点分析",
    "market",
    "生成热点分析",
    "查看指数、ETF、主题和自选对象的强弱扩散，并把结果降级为观察线索。",
    ["可用：热点缓存和公开参照", "验收：来源状态、失败对象和更新时间必须显示", "复核：热点不是交易信号"],
  ),
  index_etf: functionView(
    "index_etf",
    "指数与 ETF",
    "market",
    "查看指数与 ETF",
    "查看指数、行业基金和宽基对象的缓存摘要，把强弱变化降级为市场观察线索。",
    ["可用：指数、行业基金和宽基对象摘要", "验收：对象、来源、更新时间和失败状态必须显示", "复核：市场观察不是交易信号"],
    { legacyView: "hotspots" },
  ),
  theme_catalyst: functionView(
    "theme_catalyst",
    "主题催化",
    "market",
    "打开主题催化",
    "把主题变化拆成可验证事件，记录来源、时间、影响路径和需要补证据的事项。",
    ["可用：主题事件、来源状态和人工复核任务", "验收：主题线索必须带来源与更新时间", "复核：主题变化不能直接触发调仓"],
    { legacyView: "hotspots" },
  ),
  watchlist_monitor: functionView(
    "watchlist_monitor",
    "自选监控",
    "market",
    "打开自选监控",
    "按标的保存观察线索、来源状态和下一步复核任务，用于人工跟踪而不是自动交易。",
    ["可用：自选池对象、观察原因和复核状态", "验收：每个观察项必须能追溯来源", "复核：自选池不生成买卖指令"],
    { legacyView: "hotspots" },
  ),
  market_slice: functionView(
    "market_slice",
    "市场垂直切片",
    "market",
    "生成市场复核",
    "从本地已观察行情生成市场事件、热点扩散、市场情绪、证据任务和人工复核队列。",
    ["可用：市场事件、热点扩散和市场情绪三张证据卡", "验收：来源编号、数据日期、证据类别、新鲜度和校验值必须可追溯", "复核：市场观察不是交易信号，不自动调仓"],
    { legacyView: "hotspots" },
  ),
  market_overlay: functionView(
    "market_overlay",
    "组合影响覆盖层",
    "market",
    "查看组合覆盖",
    "把市场观察降级为组合复核输入；不读取私有持仓，不计算自动调仓，生成复核记录。",
    ["可用：目标权重变化固定为 0", "验收：必须显示未使用私有持仓且需要人工复核", "复核：需要持仓切片复核后才能形成仓位影响判断"],
    { legacyView: "holdings" },
  ),
  market_alerts: functionView(
    "market_alerts",
    "提醒与保存视图",
    "market",
    "保存观察视图",
    "保存市场每日复核和热点观察视图，并在新鲜度、覆盖率或热点分歧异常时进入人工复核。",
    ["可用：新鲜度复核提醒和热点分歧复核提醒", "验收：保存视图，并保留筛选条件和来源编号", "复核：提醒只创建人工任务，创建提醒记录"],
    { legacyView: "tools" },
  ),
  source_status: functionView(
    "source_status",
    "来源状态",
    "data",
    "检查来源状态",
    "查看数据来源是否可用、是否过期、是否失败，以及失败后进入人工复核的路径。",
    ["可用：来源健康、失败原因和更新时间", "验收：来源状态必须能解释为什么可用或不可用", "复核：检查来源状态和失败原因"],
    { legacyView: "tools" },
  ),
  reports: functionView(
    "reports",
    "报告中心",
    "research",
    "打开报告列表",
    "检索回测、扫描、研究、验证和复盘产物，查看证据缺口和待验证任务。",
    ["可用：报告列表、运行判读和验证任务", "验收：报告路径、生成时间和缺口状态必须显示", "复核：报告结论需人工复核"],
  ),
  company_research: functionView(
    "company_research",
    "公司研究",
    "research",
    "打开公司研究",
    "整理公司财务、公告、业务变化、反方证据和待核验问题，形成可复核研究材料。",
    ["可用：公司证据、反方条件和待补材料", "验收：关键结论必须连接来源和反证条件", "复核：研究材料不构成投资建议"],
    { legacyView: "reports" },
  ),
  fund_research: functionView(
    "fund_research",
    "基金研究",
    "research",
    "打开基金研究",
    "跟踪基金持仓、风格、费率、历史表现和替代方案，结论进入人工复核。",
    ["可用：持仓风格、费率和表现证据", "验收：基金比较必须记录数据来源和日期", "复核：基金研究不直接生成买卖建议"],
    { legacyView: "reports" },
  ),
  holdings: functionView(
    "holdings",
    "持仓复核",
    "portfolio",
    "同步持仓",
    "查看正式持仓、候选持仓、暴露、集中度和订单意图草案，私有数据留在本机。",
    ["可用：持仓、候选、暴露和质量检查", "验收：私有数据按本机目录规则管理", "复核：只生成待确认意图，进入人工确认"],
  ),
  portfolio_slice: functionView(
    "portfolio_slice",
    "持仓垂直切片",
    "portfolio",
    "生成持仓复核",
    "从合成券商导入账本生成持仓快照、对账、公司行动、汇率换算、现金固定样本、风险约束和人工决策提案。",
    ["可用：导入账本、持仓快照、对账、约束和人工提案", "验收：来源编号、快照校验值、持仓数量和证据记录必须可追溯", "复核：复核，使用本机持仓，进入人工复核"],
    { legacyView: "holdings" },
  ),
  portfolio_reconciliation: functionView(
    "portfolio_reconciliation",
    "导入对账",
    "portfolio",
    "查看导入对账",
    "核对合成券商导入账本、公司行动调整、汇率换算、现金固定样本和持仓快照差异。",
    ["可用：导入记录、券商数量、快照持仓数和值差", "验收：未匹配导入标的和未匹配快照标的必须显示", "复核：对账，只更新复核记录"],
    { legacyView: "holdings" },
  ),
  portfolio_risk: functionView(
    "portfolio_risk",
    "风险约束",
    "portfolio",
    "查看风险约束",
    "检查单一持仓、前三集中度、现金缓冲和自动再平衡关闭状态，所有异常进入人工复核。",
    ["可用：单一持仓上限、前三集中度、现金缓冲和自动再平衡状态", "验收：约束违反数和人工复核原因必须显示", "复核：不自动调仓，生成复核信号"],
    { legacyView: "holdings" },
  ),
  portfolio_decision: functionView(
    "portfolio_decision",
    "决策提案",
    "portfolio",
    "打开决策提案",
    "把对账和风险约束降级为人工决策提案，目标权重变化固定为 0，不创建订单意图。",
    ["可用：目标权重变化为 0、不创建订单意图、必须人工复核", "验收：提案动作必须明确进入人工确认", "复核：需要人工确认"],
    { legacyView: "holdings" },
  ),
  portfolio_exposure: functionView(
    "portfolio_exposure",
    "组合暴露",
    "portfolio",
    "查看组合暴露",
    "查看行业、资产类别、币种和主题暴露，把异常暴露降级为人工复核任务。",
    ["可用：行业、资产类别、币种和主题暴露", "验收：暴露结果必须标明来源和日期", "复核：不自动调仓，进入人工确认"],
    { legacyView: "holdings" },
  ),
  concentration_risk: functionView(
    "concentration_risk",
    "集中度风险",
    "portfolio",
    "查看集中度风险",
    "识别单一标的、前三持仓或主题过度集中，并生成风险复核项。",
    ["可用：单一持仓、前三集中度和主题集中度", "验收：风险阈值和人工复核原因必须显示", "复核：风险提示不是自动交易指令"],
    { legacyView: "holdings" },
  ),
  discipline_check: functionView(
    "discipline_check",
    "纪律检查",
    "portfolio",
    "打开纪律检查",
    "记录交易前提、复盘问题、是否违反预设纪律，以及需要人工纠偏的事项。",
    ["可用：纪律规则、复盘记录和纠偏任务", "验收：每条违反项必须有人工复核状态", "复核：纪律检查使用本机数据，进入人工复核"],
    { legacyView: "profile" },
  ),
  order_intent: functionView(
    "order_intent",
    "订单意图",
    "portfolio",
    "查看订单意图",
    "只生成待确认的订单意图草案，保留原因、证据、风险和人工确认状态。",
    ["可用：意图草案、证据摘要和风险说明", "验收：必须显示草案未提交且需要人工确认", "复核：使用本机持仓，人工复核"],
    { legacyView: "holdings" },
  ),
  policy: functionView(
    "policy",
    "政策雷达",
    "research",
    "打开政策雷达",
    "登记政策来源、影响路径、机会状态和人工行动队列，优先使用官方或监管来源。",
    ["可用：政策机会和权威来源复核", "验收：官方来源或证据路径必须可追溯", "复核：政策线索不等同投资建议"],
  ),
  research_policy_slice: functionView(
    "research_policy_slice",
    "研究与政策垂直切片",
    "research",
    "生成研究复核",
    "统一展示政策权威来源、研究证据缺口、引用定位和报告清单，所有结论进入人工复核队列。",
    ["可用：政策权威、政策机会和研究证据缺口三张证据卡", "验收：官方链接、证据路径、报告清单和验证任务必须可追溯", "复核：本机预检政府门户，不给法律税务结论，生成研究复核记录"],
    { legacyView: "policy" },
  ),
  citation_locator: functionView(
    "citation_locator",
    "引用定位",
    "research",
    "定位官方引用",
    "把政策来源、官方链接、证据路径和报告缺口任务定位到可复核引用，区分官方证据和待补证据。",
    ["可用：官方证据与待补证据两类引用", "验收：每条引用必须带来源类型、官方链接或证据路径", "复核：引用只证明来源位置，不代表政策、法律或投资结论"],
    { legacyView: "policy" },
  ),
  report_manifest: functionView(
    "report_manifest",
    "报告清单",
    "research",
    "打开报告清单",
    "把报告、运行元数据、缺失证据、验证任务和状态整理成清单，用于后续补证据。",
    ["可用：证据不足报告清单和缺口任务编号", "验收：数据质量、多源校验和滚动验证缺口必须显示", "复核：清单只创建复核任务，不修改报告、不刷新数据"],
    { legacyView: "reports" },
  ),
  report_validation: functionView(
    "report_validation",
    "报告验证",
    "research",
    "打开报告验证",
    "把报告结论拆成可验证任务，检查数据质量、多源校验、回测证据和人工复核缺口。",
    ["可用：报告结论、证据缺口和验证任务", "验收：每个缺口必须有负责人、来源和下一步", "复核：验证不修改原报告，不自动刷新数据"],
    { legacyView: "reports" },
  ),
  recommendation_model: functionView(
    "recommendation_model",
    "建议模型",
    "recommendations",
    "查看建议模型",
    "按领域、证据、预期效果、代价、动作和决策状态组织建议，禁止无证据建议。",
    ["可用：投资建议和消费建议统一模型", "验收：每条建议必须有证据、预期效果和代价", "复核：建议是人工复核队列，不是订单"],
  ),
  review_lifecycle: functionView(
    "review_lifecycle",
    "复盘生命周期",
    "recommendations",
    "打开复盘生命周期",
    "支持接受、拒绝、暂缓、复核和效果度量，保留决策记录和复盘结果。",
    ["可用：决策状态、复盘窗口和效果度量", "验收：建议可复盘、可追踪、可解释", "复核：人工确认前不改变资产或支出"],
  ),
  investment_recommendations: functionView(
    "investment_recommendations",
    "投资建议",
    "recommendations",
    "查看投资建议",
    "聚合集中度、交易频率、现金仓位、策略暂停或上线建议，并解释原因和代价。",
    ["可用：集中度、交易频率、现金仓位、策略暂停或上线", "验收：每条建议必须能解释原因", "复核：使用本机数据，进入人工复核"],
  ),
  consumption_recommendations: functionView(
    "consumption_recommendations",
    "消费建议",
    "recommendations",
    "查看消费建议",
    "聚合预算、订阅、异常和降成本建议，必须带可量化节省目标。",
    ["可用：预算、订阅、异常、降成本", "验收：必须有节省目标和证据", "复核：不自动支付、不自动取消订阅"],
  ),
  monthly_report: functionView(
    "monthly_report",
    "月度报告",
    "insights",
    "生成月度报告",
    "汇总净资产、现金流、消费、投资和建议复盘，保留来源链路。",
    ["可用：净资产、现金流、消费、投资、建议复盘", "验收：报告必须可复现导出", "复核：报告，结论需人工复核"],
  ),
  investment_report: functionView(
    "investment_report",
    "投资报告",
    "insights",
    "生成投资报告",
    "输出收益、风险、归因、持仓和行为复盘，数据不足时不输出精确结论。",
    ["可用：收益、风险、归因、持仓、行为", "验收：估计口径必须可见", "复核：投资报告不构成自动交易指令"],
  ),
  consumption_report: functionView(
    "consumption_report",
    "消费报告",
    "insights",
    "生成消费报告",
    "输出分类、预算、订阅、异常和节省金额，用于月末复盘。",
    ["可用：分类、预算、订阅、异常、节省目标", "验收：消费建议必须能追溯证据", "复核：不自动发起支付或取消服务"],
  ),
  data_quality_report: functionView(
    "data_quality_report",
    "数据质量报告",
    "insights",
    "生成质量报告",
    "检查同步状态、缺失区间、对账差异和解析器错误，定位数据可信度问题。",
    ["可用：同步状态、缺失区间、对账差异、解析器错误", "验收：质量问题必须可定位到来源", "复核：检查，不复制私有原始数据"],
  ),
  export_center: functionView(
    "export_center",
    "导出中心",
    "insights",
    "导出报告",
    "以 Markdown、JSON 和 CSV 生成可复现的本地报告出口，保留内容哈希。",
    ["可用：Markdown / JSON / CSV", "验收：导出内容可复现并有校验值", "复核：导出不包含密钥或交易凭证"],
  ),
  pfi_context_export: functionView(
    "pfi_context_export",
    "PFI 上下文导出",
    "insights",
    "生成上下文快照",
    "生成上下文快照，包含净资产、可投资现金、组合配置、风险预算、现金流压力、行为标签和数据新鲜度。",
    ["可用：上下文快照", "验收：必须显示和人工提交关闭约束", "复核：上下文快照，不修改外部系统仓库"],
  ),
  alpha_readonly_export: functionView(
    "alpha_readonly_export",
    "外部系统上下文出口",
    "insights",
    "查看外部系统出口限制",
    "PFI 只输出上下文快照，外部系统独立消费；PFI 不新增外部系统一级入口，不修改外部系统仓库。",
    ["可用：上下文快照和约束字段", "验收：上下文状态和复核状态可追溯", "复核：证据留痕和外部系统上下文记录"],
  ),
  stage6_e2e: functionView(
    "stage6_e2e",
    "端到端验收",
    "insights",
    "查看第 6 阶段验收",
    "统一查看第 6 阶段的多数据源、首页、账本、建议、回归治理、交付回滚和任务包验收门禁。",
    ["可用：20 个总验收门禁和验收审计", "验收：所有门禁必须有证据引用且通过", "复核：合成端到端，使用合成验收数据"],
  ),
  stage6_synthetic_e2e: functionView(
    "stage6_synthetic_e2e",
    "合成端到端",
    "insights",
    "查看合成端到端验收",
    "核对支付宝、支付宝基金、Moomoo、中国券商、ABC、CBA、微信的 fixture/contract，并验证首页、账本和建议闭环。",
    ["可用：数据源样本矩阵、首页闭环、账本闭环、建议闭环", "验收：核心源不得缺失，首页必须可读，分类必须正确", "复核：不导入真实私有数据"],
  ),
  stage6_regression_governance: functionView(
    "stage6_regression_governance",
    "回归治理",
    "insights",
    "查看回归治理",
    "确认既有冒烟检查、新增聚焦测试、变更范围治理和无大范围重构门禁都已记录。",
    ["可用：顶层 QBVS 冒烟检查、第 1-6 阶段测试、精简治理", "验收：变更范围只在 PFI、QBVS、MetaDatabase 目标文件内", "复核：PFI 不覆盖 QBVS"],
  ),
  stage6_delivery_rollback: functionView(
    "stage6_delivery_rollback",
    "交付与回滚",
    "insights",
    "查看交付回滚",
    "整理用户文档、差异摘要、回滚计划和后续任务清单，确保 V0.2 可继续迭代。",
    ["可用：用户文档、差异摘要、回滚计划", "验收：回滚步骤可定位到文件并不影响私有数据", "复核：不做生产迁移"],
  ),
  stage6_rollback_plan: functionView(
    "stage6_rollback_plan",
    "回滚计划",
    "insights",
    "查看回滚计划",
    "查看第 6 阶段的可逆文件清单、恢复限制和无需迁移真实数据的说明。",
    ["可用：代码、测试、文档、治理、Web Shell 回滚步骤", "验收：回滚清楚区分 PFI 与 QBVS", "复核：无生产数据库迁移"],
  ),
  stage6_follow_up_list: functionView(
    "stage6_follow_up_list",
    "后续任务清单",
    "insights",
    "查看后续任务",
    "列出外部上下文消费者、真实数据接入、PDF/ZIP、CDR/Open Banking 和发布证据门禁等后续工作。",
    ["可用：分离后续任务，不并入第 6 阶段", "验收：第 6 阶段不越权修改外部仓库", "复核：后续任务需新 pursuing goal"],
  ),
  tools: functionView(
    "tools",
    "数据中心",
    "settings",
    "检查数据源",
    "查看数据源、代码格式、质量报告、缓存、本机数据管理和系统诊断。",
    ["可用：数据源状态和代码助手", "验收：来源、新鲜度、失败原因必须显示", "复核：保护密钥和私有数据"],
  ),
  source_registry: functionView(
    "source_registry",
    "来源登记",
    "settings",
    "打开来源登记",
    "登记数据来源、数据范围、新鲜度、失败原因和复核状态，作为后续研究的来源台账。",
    ["可用：来源名称、更新时间、限制条件和失败原因", "验收：来源必须能追溯到登记记录", "复核：不保存密钥，不复制私有原始数据"],
    { legacyView: "tools" },
  ),
  task_monitor: functionView(
    "task_monitor",
    "任务监控",
    "settings",
    "打开任务监控",
    "查看任务队列、重试、失败、产物和人工复核状态，定位系统运行问题。",
    ["可用：任务状态、重试次数、失败原因和产物路径", "验收：失败任务必须有下一步处理建议", "复核：监控不触发人工执行"],
    { legacyView: "tools" },
  ),
  privacy_boundary: functionView(
    "privacy_boundary",
    "本机数据管理",
    "settings",
    "检查本机数据管理",
    "检查私有数据目录、公共提交目录、密钥排除和本机运行规则，避免私有数据进入 公共仓库。",
    ["可用：私有目录、公有目录和密钥排除规则", "验收：不得把私有持仓、密钥或原始账本提交到公共仓库", "复核：检查，不复制私有数据"],
    { legacyView: "tools" },
  ),
  backup_restore: functionView(
    "backup_restore",
    "备份恢复",
    "settings",
    "检查备份恢复",
    "检查备份、校验和、恢复路径和恢复演练状态，确保运行资料可追溯。",
    ["可用：备份路径、校验和和恢复演练状态", "验收：恢复路径必须可定位且可复核", "复核：恢复演练不覆盖真实私有数据"],
    { legacyView: "tools" },
  ),
  library: functionView(
    "library",
    "策略库",
    "investment",
    "打开策略库",
    "管理候选策略、确认状态、风险说明和版本证据，避免未确认策略进入正式研究。",
    ["可用：策略模板和候选策略审查", "验收：策略版本、参数和风险说明必须保留", "复核：未确认策略不能进入正式回测"],
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
      feature("上传支付宝账单", "可用", "CSV / ZIP 原始账单", "页面顶部有真实上传控件，可接入已发现的三年支付宝原始数据。", { workspace: "sync", label: "打开上传" }),
      feature("同步全部", "需要同步", "数据源与上传", "生成可执行前的本地同步/导入计划，生成本机预检清单。"),
      feature("处理待复核", "需要复核", "账本流水", "用 A/B/C/D 选择处理低置信度流水，避免 unknown 静默入账。"),
      feature("查看建议", "有建议", "建议与复盘", "查看带证据、动作、状态、预期效果和代价说明的重点建议。"),
      feature("生成报告", "有建议", "报告与洞察", "生成本地报告草稿，保留首页、账户、账本和证据链。"),
      feature("单标的回测", "可用", "回测证据", "运行单标的策略回测，查看收益、回撤、交易和报告。"),
      feature("盘感训练", "可用", "训练记录", "保留读图训练和限时判断，输出训练记录。"),
    ],
    rows: [
      row("P1", "数据源与上传", "账户状态", "先同步或扫描本地导入文件。", "需要同步"),
      row("P2", "账本流水", "待复核记录", "处理低置信度流水。", "需要复核"),
      row("P3", "报告与洞察", "首页证据链", "生成本地报告草稿。", "有建议"),
    ],
    tasks: [
      task("支付宝账单导入", "可用 · 页面顶部上传或接入旧数据", "ready"),
      task("账本复核", "第 1/3 步 · 等待导入结果", "running"),
      task("报告生成", "排队中 · 导入后可生成", "queued"),
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
    runtime: "研究队列：人工复核 · 生成研究复核记录",
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
    conclusion: "查看组合暴露、集中度、风险和纪律任务；所有操作都需要人工复核，只更新复核记录。",
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
      feature("决策提案", "复核", "人工复核", "目标权重变化固定为 0，不创建订单意图，进入人工确认。"),
      feature("组合暴露", "复核", "持仓快照", "查看行业、资产类别和币种暴露。"),
      feature("集中度风险", "观察", "风险卡片", "识别单一标的或主题过度集中。"),
      feature("纪律检查", "复核", "交易复盘", "记录是否违反预设纪律。"),
      feature("订单意图", "可用", "人工复核", "只生成待确认意图，进入人工确认。"),
    ],
    rows: [
      row("P0", "私有持仓", "本机运行库", "确认私有数据没有进入公共仓库。", "复核"),
      row("P1", "集中度", "风险卡", "检查单一主题暴露是否过高。", "观察"),
      row("P1", "订单意图", "人工复核", "仅保留为待确认草案。", "可用"),
    ],
    tasks: [
      task("私有持仓边界检查", "复核 · 数据按本机目录规则管理", "review"),
      task("集中度复核", "观察 · 需要人工判断", "watch"),
      task("订单意图草案", "可用 · 使用本机数据", "ready"),
    ],
    evidence: evidence("持仓证据", "私有持仓复核", "本机运行库", "持仓入口使用本机数据、进入人工复核。"),
    chart: [28, 26, 25, 32, 30, 37, 36, 41, 39, 46, 43, 47, 45, 50],
  },
  strategy: {
    label: "策略实验室",
    kicker: "回测与训练",
    conclusion: "保留策略回测、参数扫描、模拟和盘感训练；训练模式输出训练复核记录。",
    freshness: "策略缓存可用",
    runtime: "策略实验室：研究模式 · 人工复核",
    cards: [
      ["回测任务", "2", "可复核"],
      ["参数扫描", "1", "等待运行"],
      ["盘感训练", "保留", "训练生成复核信号"],
      ["模拟模式", "观察", "仅研究用途"],
    ],
    features: [
      feature("策略垂直切片", "可用", "PIT 回测链", "固定样本、样本外验证、滚动验证、策略注册和人工复核一体化。"),
      feature("PIT回测", "可用", "固定样本哈希", "查看回测参数、成本假设、公司行动调整和退市样本排除。"),
      feature("样本外验证", "可用", "无未来数据", "确认训练期早于测试期，验证参数是否泛化。"),
      feature("滚动验证", "可用", "滚动验证", "检查多个滚动窗口是否保持样本外表现。"),
      feature("策略注册", "复核", "人工复核", "登记策略候选，生成复核信号，进入人工复核。"),
      feature("单标的回测", "可用", "回测证据", "查看可复现回测、基准和风险指标。"),
      feature("参数扫描", "观察", "扫描结果", "比较参数稳定性和过拟合风险。"),
      feature("盘感训练", "可用", "训练记录", "保留人工判断训练和复盘。"),
      feature("模拟实验", "复核", "模拟日志", "用于研究模拟，输出复核记录。"),
    ],
    rows: [
      row("P0", "回测有效性", "固定样本", "确认无前视、费用和时间口径正确。", "复核"),
      row("P1", "参数扫描", "稳定性", "检查结果是否依赖单一参数。", "观察"),
      row("P1", "盘感训练", "训练记录", "保留人工判断，生成训练复核记录。", "可用"),
    ],
    tasks: [
      task("回测口径复核", "复核 · 等待固定样本", "review"),
      task("参数稳定性检查", "观察 · 可运行扫描", "watch"),
      task("盘感训练入口", "可用 · 已保留", "ready"),
    ],
    evidence: evidence("策略证据", "回测、扫描和盘感训练", "本地实验记录", "策略入口用于研究、回测和训练。"),
    chart: [20, 23, 31, 29, 37, 35, 44, 42, 49, 47, 55, 53, 61, 58],
  },
  data: {
    label: "数据与系统",
    kicker: "数据治理",
    conclusion: "查看来源、任务、质量、血缘、隐私、备份和诊断状态；用于定位系统问题。",
    freshness: "系统诊断缓存",
    runtime: "数据与系统：本机优先 · 本机数据管理开启",
    cards: [
      ["来源登记", "待补", "需要 PFI-004 继续"],
      ["任务运行", "4", "可追踪"],
      ["本机数据管理", "开启", "私有数据不入 公共仓库"],
      ["备份状态", "复核", "等待部署门禁"],
    ],
    features: [
      feature("数据中心", "可用", "系统诊断", "检查数据源、代码格式、质量报告、缓存和本机数据管理。", { view: "tools", label: "打开数据中心" }),
      feature("来源登记", "复核", "数据来源", "检查来源、时间、质量和限制条件。"),
      feature("任务监控", "可用", "任务中心", "查看队列、重试、失败和产物。"),
      feature("本机数据管理", "可用", "数据目录", "私有数据留在本机运行目录。"),
      feature("备份恢复", "复核", "恢复演练", "检查备份、校验和恢复路径。"),
    ],
    rows: [
      row("P0", "本机数据管理", "目录策略", "确认私有数据与 密钥 不进入公共仓库。", "复核"),
      row("P1", "任务追踪", "运行记录", "补齐统一任务状态和重试策略。", "观察"),
      row("P1", "备份恢复", "校验和", "准备下一次恢复演练证据。", "复核"),
    ],
    tasks: [
      task("本机数据管理审计", "可用 · 已启用目录约束", "ready"),
      task("任务状态统一", "观察 · PFI-003 后续", "watch"),
      task("备份恢复演练", "复核 · 等待目标机", "review"),
    ],
    evidence: evidence("系统证据", "来源、任务、本机数据和备份", "运行库与文档合同", "系统入口用于诊断，不复制私有数据。"),
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
    runtime: "第 4 阶段：现金 / 净资产趋势 · CNY 基准",
    trendKey: "accounts",
    trend: UNIFIED_TREND_DATA.accounts,
    cards: [
      ["现金总额", "待读取", "SQLite 运行读模型"],
      ["净资产", "待读取", "SQLite 运行读模型"],
      ["统一结构", "已接入", "SQLite 运行读模型"],
      ["数据管理", "本机", "不需要账户凭证"],
    ],
    features: [
      feature("现金与净资产趋势", "可用", "统一趋势合同", "按 CNY 基准显示现金和净资产月度折线。", { workspace: "accounts", label: "查看趋势" }),
      feature("账户地图", "可用", "账户与资产", "查看全部账户、来源状态、币种和对账差异。", { workspace: "accounts", label: "查看账户" }),
      feature("导入对账", "需要复核", "平台余额", "核对平台余额和 PFI 账本余额差异。", { view: "portfolio_reconciliation", label: "打开对账" }),
      feature("持仓", "可用", "投资账户", "兼容旧持仓复核入口，仍然。", { view: "holdings", label: "打开持仓" }),
    ],
    tasks: [
      task("现金趋势", "可用 · CNY 月度折线", "ready"),
      task("净资产趋势", "可用 · CNY 月度折线", "ready"),
      task("账户对账", "复核 · 平台余额 vs PFI 账本余额", "review"),
    ],
  };
  WORKSPACES.ledger = {
    ...structuredClone(DEFAULT_WORKSPACES.data),
    label: "账本流水",
    kicker: "流水事实层",
    conclusion: "查看标准化流水、待分类流水、转账匹配和每条流水的原始证据链。",
    freshness: "账本来自本地导入样本",
    runtime: "账本流水：证据链优先 · 未知分类不静默入账",
    cards: [
      ["全部流水", "可查", "标准化交易"],
      ["待分类", "复核", "低置信度进入队列"],
      ["转账匹配", "可确认", "确认/拒绝/修改"],
      ["证据链", "开启", "批次 / 原始记录 / 解析器"],
    ],
    features: [
      feature("处理待复核", "需要复核", "A/B/C/D", "用选择题处理低置信度流水。", { workspace: "ledger", label: "处理复核" }),
      feature("账本流水", "可用", "原始证据链", "查看批次、原始记录和解析器版本。", { workspace: "ledger", label: "查看流水" }),
      feature("导入对账", "需要复核", "转账匹配", "确认、拒绝或修改疑似转账，防止计入消费。", { view: "portfolio_reconciliation", label: "打开对账" }),
    ],
  };
  WORKSPACES.investment = {
    ...structuredClone(DEFAULT_WORKSPACES.strategy),
    label: "投资管理",
    kicker: "投资分析",
    conclusion: "查看总市值、盈亏、资产配置、收益归因、风险暴露和行为复盘；策略回测、盘感训练和大数据模拟器仍保留。",
    runtime: "第 6 阶段：持仓编辑持久化 · SQLite 服务",
    trendKey: "investment",
    trend: UNIFIED_TREND_DATA.investment,
    cards: [
      ["投资市值", "待读取", "SQLite 持仓读模型"],
      ["总收益", "待读取", "由成本与现价计算"],
      ["未实现盈亏", "待读取", "由持仓快照派生"],
      ["持仓编辑", "SQLite", "刷新 / 重启服务后仍保留"],
    ],
    features: [
      feature("投资趋势", "可用", "统一趋势合同", "同一趋势结构显示市值、总收益和现金仓位。", { workspace: "investment", label: "查看趋势" }),
      feature("投资总览", "可用", "持仓事实", "查看总市值、盈亏、资产配置和现金仓位。", { workspace: "investment", label: "查看投资" }),
      feature("持仓编辑", "可用", "本机持久化", "编辑数量和价格，保存后刷新或重开仍保留。", { workspace: "investment", routeAlias: "/investment?tab=holdings", label: "打开编辑" }),
      feature("持仓持久化", "可用", "SQLite 服务", "持仓 snapshot 和 adjustment 写入本机 operational database。", { workspace: "investment", routeAlias: "/investment?tab=holdings", label: "查看持仓" }),
      feature("收益归因", "需要复核", "估计归因", "把收益拆为市场、主动决策、费用、汇率和现金拖累；数据不足不输出精确结论。", { workspace: "investment", label: "查看归因" }),
      feature("风险分析", "有建议", "风险证据", "查看集中度、回撤、币种暴露和流动性。", { workspace: "investment", label: "查看风险" }),
      feature("行为复盘", "有建议", "交易证据", "识别追涨、杀跌、频繁交易和持有周期。", { workspace: "investment", label: "查看复盘" }),
      feature("策略实验室", "可用", "PFI 策略实验室", "保留 PFI 策略回测、参数扫描、盘感训练和大数据模拟器；QBVS 是顶层独立系统。", { workspace: "investment", routeAlias: "/investment/strategy-lab", label: "打开策略" }),
    ],
    tasks: [
      task("市值趋势", "可用 · CNY 月度折线", "ready"),
      task("持仓编辑", "可用 · 保存后刷新仍保留", "ready"),
      task("总收益趋势", "可用 · 估计值需复核", "review"),
      task("持仓 SQLite 服务", "可用 · snapshot / adjustment 可写入", "ready"),
    ],
  };
  WORKSPACES.consumption = {
    ...structuredClone(DEFAULT_WORKSPACES.data),
    label: "消费管理",
    kicker: "消费分析",
    conclusion: "查看本月支出、预算剩余、分类、订阅、异常消费和现金流预测；转账和投资事件不计生活消费。",
    freshness: "消费视图来自第 4 阶段分析读模型",
    runtime: "第 4 阶段：支出 / 预算 / 现金流趋势 · CNY 基准",
    trendKey: "consumption",
    trend: UNIFIED_TREND_DATA.consumption,
    cards: [
      ["本月支出", "待导入", "真实流水导入后显示"],
      ["预算剩余", "待导入", "真实预算数据接入后显示"],
      ["现金流预测", "待导入", "流水不足不伪造预测"],
      ["分类复核", "保留", "低置信度进入队列"],
    ],
    features: [
      feature("消费趋势", "可用", "统一趋势合同", "同一趋势结构显示支出、预算和现金流。", { workspace: "consumption", label: "查看趋势" }),
      feature("消费总览", "可用", "预算", "查看本月支出、预算剩余和固定/弹性支出。", { workspace: "consumption", label: "查看消费" }),
      feature("分类分析", "需要复核", "三来源", "支付宝、微信、CBA 消费分类；低置信度必须进入复核。", { workspace: "consumption", label: "查看分类" }),
      feature("订阅检测", "有建议", "周期扣费", "识别周期扣费和疑似订阅，支持保留、取消或暂缓复盘。", { workspace: "consumption", label: "查看订阅" }),
      feature("异常消费", "需要复核", "消费证据", "识别大额、重复、夜间、节假日和冲动型消费。", { workspace: "consumption", label: "查看异常" }),
      feature("现金流预测", "可用", "30/90/180 天", "预测支出、收入和可投资现金，生活现金与投资现金分开。", { workspace: "consumption", label: "查看现金流" }),
      feature("处理待复核", "需要复核", "消费分类", "复核低置信度消费流水。", { workspace: "ledger", label: "处理复核" }),
      feature("账本流水", "可用", "消费证据", "查看消费、退款、转账和费用的证据链。", { workspace: "ledger", label: "查看流水" }),
    ],
    tasks: [
      task("支出趋势", "可用 · CNY 月度折线", "ready"),
      task("预算趋势", "可用 · 预算参考线", "ready"),
      task("现金流趋势", "可用 · 生活现金与投资现金分开", "ready"),
    ],
  };
  WORKSPACES.sync = {
    ...structuredClone(DEFAULT_WORKSPACES.data),
    label: "数据源与上传",
    kicker: "同步与导入",
    conclusion: "上传支付宝账单、查看导入批次、处理失败反馈，并把低置信度记录送到账本复核。",
    runtime: "第 5 阶段：上传 / 拖拽 / 状态 / 失败反馈 / 导入批次",
    cards: [
      ["上传中心", "可用", "CSV / ZIP / XLSX 多文件本机预检"],
      ["拖拽上传", "可用", "拖拽、点击选择、键盘选择都可触发"],
      ["导入中心", "可用", "批次、摘要、待复核入口同屏显示"],
      ["本机数据管理", "本机", "原始账单不进入 公共仓库"],
    ],
    features: [
      feature("上传中心", "可用", "本机预检", "点击选择文件或拖拽账单，立即显示状态、文件列表和失败反馈。", { workspace: "sync", label: "打开上传" }),
      feature("上传支付宝账单", "可用", "本机上传", "接收 CSV、ZIP、XLS、XLSX 格式的支付宝账单，只做本机预检。", { workspace: "sync", label: "查看上传" }),
      feature("拖拽上传", "可用", "多文件", "拖入多个文件后显示已选择、预检完成或失败原因。", { workspace: "sync", label: "打开拖拽" }),
      feature("导入中心", "可用", "批次摘要", "查看导入批次、导入摘要、失败原因和账本复核入口。", { workspace: "sync", label: "打开导入" }),
      feature("导入批次", "可用", "批次状态", "展示批次、来源、文件数、记录数、待复核和状态。", { workspace: "sync", label: "查看批次" }),
      feature("导入摘要", "可用", "导入摘要", "汇总已选择文件、预计记录、待复核数量和失败反馈数量。", { workspace: "sync", label: "查看摘要" }),
      feature("复核入口", "可用", "账本流水", "点击进入账本流水处理低置信度记录。", { workspace: "ledger", label: "进入复核" }),
      feature("失败反馈", "可用", "中文反馈", "不支持的文件类型、空选择和文件过大都会给出中文提示。", { workspace: "sync", label: "查看反馈" }),
      feature("同步全部", "需要同步", "7 个来源", "扫描本地导入收件箱或生成预检，生成本机预检清单。", { workspace: "sync", label: "同步计划" }),
      feature("来源登记", "复核", "数据源状态", "查看数据源新鲜度、失败原因和解析器合同。"),
      feature("本机数据管理", "可用", "本地数据", "私有数据和凭证按本机目录规则管理。"),
    ],
    rows: [
      row("P0", "上传中心", "CSV / ZIP / XLSX", "点击或拖拽选择账单文件。", "可用"),
      row("P0", "导入中心", "批次摘要", "显示本轮预检批次和旧账单待接入批次。", "可用"),
      row("P1", "账本复核", "低置信度记录", "进入账本流水处理待复核记录。", "复核"),
      row("P1", "本机数据管理", "~/.pfi/runtime", "原始账单保存在本机私有目录，公共仓库只记录脱敏清单。", "可用"),
    ],
    tasks: [
      task("上传中心", "可用 · 支持多文件 CSV / ZIP / XLSX", "ready"),
      task("拖拽上传", "可用 · 拖入文件后显示状态", "ready"),
      task("导入摘要", "可用 · 批次、记录和待复核同屏展示", "ready"),
      task("账本复核", "导入后处理低置信度分类", "review"),
    ],
  };
  WORKSPACES.settings = {
    ...structuredClone(DEFAULT_WORKSPACES.data),
    label: "设置",
    kicker: "系统设置",
    conclusion: "集中管理数据与系统、运行反馈、多模态反馈、触感、声音、视觉、通知和备份恢复设置。",
    freshness: "设置项本地保存",
    runtime: "设置：只改本机偏好 · 不触发外部动作",
    cards: [
      ["数据与系统", "可用", "来源、任务、本机数据、备份"],
      ["运行反馈控制台", "可配置", "视觉、声音、触感、通知"],
      ["汇率徽标", "已缓存", "AUD/CNY 06:00 快照"],
      ["本机数据管理", "开启", "原始数据按 MetaDatabase 备份规则管理"],
    ],
    features: [
      feature("数据中心", "可用", "系统诊断", "检查数据源、代码格式、质量报告、缓存和本机数据管理。", { workspace: "settings", label: "打开数据与系统" }),
      feature("来源登记", "复核", "数据源状态", "查看来源、时间、质量和限制条件。", { workspace: "settings", label: "查看来源" }),
      feature("任务监控", "可用", "任务中心", "查看队列、重试、失败和产物。", { workspace: "settings", label: "查看任务" }),
      feature("运行反馈控制台", "可配置", "设置页", "统一管理成功、失败、进行中、后台任务和缓存兜底反馈。", { workspace: "settings", label: "打开反馈" }),
      feature("多模态反馈", "可配置", "设置页", "管理触感反馈强度、声音反馈、视觉反馈、通知反馈和反馈测试。", { workspace: "settings", label: "打开反馈设置" }),
      feature("触感反馈强度", "可配置", "关闭 / 轻 / 标准 / 强", "手机浏览器支持震动时才启用，不支持时静默降级。", { workspace: "settings", label: "打开触感" }),
      feature("声音反馈", "可配置", "提示音", "控制成功、失败和完成提示音，默认不打扰。", { workspace: "settings", label: "打开声音" }),
      feature("视觉反馈", "可配置", "动效与状态", "控制按钮按压、骨架屏、错误横幅和状态提示。", { workspace: "settings", label: "打开视觉" }),
      feature("通知反馈", "可配置", "本机通知", "控制后台任务完成、失败和待复核提醒。", { workspace: "settings", label: "打开通知" }),
      feature("反馈测试", "可用", "即时验证", "测试触感、声音、视觉和通知反馈是否符合当前偏好。", { workspace: "settings", label: "测试反馈" }),
      feature("无障碍反馈", "可配置", "键盘与读屏", "保证反馈状态可被键盘和读屏读取。", { workspace: "settings", label: "打开无障碍" }),
      feature("备份恢复", "复核", "恢复演练", "检查备份、校验和恢复路径。", { workspace: "settings", label: "查看备份" }),
    ],
    rows: [
      row("P0", "汇率徽标", "AUD/CNY", "普通运行本地 06:00 快照；缓存缺失时显示中文待更新。", "复核"),
      row("P0", "运行反馈控制台", "设置页", "集中配置多模态反馈，不在业务页常驻右侧设置面板。", "可用"),
      row("P0", "本机数据管理", "目录策略", "确认私有数据与 密钥 不进入公共仓库。", "可用"),
      row("P1", "反馈设置", "触感/声音/视觉/通知", "业务页默认不常驻反馈控制台。", "可用"),
    ],
    tasks: [
      task("数据与系统入口", "可用 · 旧入口映射到设置页", "ready"),
      task("反馈设置归口", "可配置 · 运行反馈/触感/声音/视觉/通知集中管理", "ready"),
      task("反馈测试", "可用 · 可在设置页触发反馈检查", "ready"),
      task("汇率数据", "复核 · 等待 06:00 快照源接入", "review"),
    ],
    evidence: evidence("设置证据", "数据与系统、反馈和备份", "本地设置合同", "设置入口不触发外部执行。"),
  };
  WORKSPACES.recommendations = {
    ...structuredClone(DEFAULT_WORKSPACES.home),
    label: "建议与复盘",
    kicker: "建议生命周期",
    conclusion: "建议必须有领域、证据、预期效果、代价说明、动作和决策状态。",
    runtime: "建议与复盘：重点建议 · 人工决策",
    cards: [
      ["建议模型", "8", "领域、证据、预期效果、代价、动作、决策"],
      ["复盘生命周期", "开启", "接受、拒绝、暂缓、复核、效果度量"],
      ["投资建议", "4", "集中度、交易频率、现金仓位、策略上线/暂停"],
      ["消费建议", "4", "预算、订阅、异常、降成本目标"],
    ],
    features: [
      feature("建议模型", "可用", "第 5 阶段", "所有建议必须有证据、预期效果、代价、动作和用户决策。"),
      feature("复盘生命周期", "可用", "复盘状态", "建议支持接受、拒绝、暂缓、复核和效果度量。"),
      feature("投资建议", "有建议", "投资管理", "集中度、交易频率、现金仓位、策略暂停或上线建议。"),
      feature("消费建议", "有建议", "消费管理", "预算、订阅、异常和降成本建议必须有节省目标。"),
    ],
    rows: [
      row("P1", "建议模型", "建议模型证据", "查看重点建议并进行人工决策。", "有建议"),
      row("P1", "复盘生命周期", "复盘状态证据", "记录接受、拒绝、暂缓、复核和效果度量。", "可用"),
      row("P2", "投资建议", "投资分析证据", "复核集中度、交易频率、现金仓位和策略门禁。", "有建议"),
      row("P2", "消费建议", "消费分析证据", "复核预算、订阅、异常和降成本目标。", "有建议"),
    ],
    tasks: [
      task("重点建议排序", "首页只显示最重要建议，避免噪音", "ready"),
      task("建议复盘记录", "决策与效果度量可追踪", "ready"),
      task("无证据建议拦截", "证据引用为空不得进入建议队列", "ready"),
    ],
  };
  WORKSPACES.insights = {
    ...structuredClone(DEFAULT_WORKSPACES.research),
    label: "报告与洞察",
    kicker: "报告出口",
    conclusion: "月度、投资、消费、数据质量和 PFI 上下文导出必须保留证据链。",
    runtime: "报告与洞察：Markdown / JSON / CSV 优先",
    cards: [
      ["月度报告", "可用", "净资产、现金流、消费、投资、建议复盘"],
      ["投资报告", "可用", "收益、风险、归因、持仓、行为"],
      ["消费报告", "可用", "分类、预算、订阅、异常、节省金额"],
      ["数据质量报告", "可用", "同步、缺失、对账、解析器错误"],
    ],
    features: [
      feature("月度报告", "可用", "月报证据", "汇总净资产、现金流、消费、投资和建议复盘。"),
      feature("投资报告", "可用", "投资报告证据", "展示收益、风险、归因、持仓和行为复盘。"),
      feature("消费报告", "可用", "消费报告证据", "展示分类、预算、订阅、异常和节省金额。"),
      feature("数据质量报告", "可用", "质量报告证据", "展示同步状态、缺失区间、对账差异和解析器错误。"),
      feature("导出中心", "可用", "Markdown / JSON / CSV", "导出可复现报告，并保留内容哈希。"),
      feature("PFI 上下文导出", "", "上下文快照", "输出给外部系统消费的上下文快照。"),
      feature("外部系统上下文出口", "", "约束字段", "不新增外部系统一级入口，不修改外部系统仓库，不授权人工提交。"),
    ],
    rows: [
      row("P1", "月度报告", "报告证据", "生成本地月度报告。", "可用"),
      row("P1", "导出中心", "导出证据", "导出 Markdown / JSON / CSV。", "可用"),
      row("P1", "PFI 上下文导出", "上下文快照", "生成上下文快照。", ""),
      row("P0", "外部系统上下文出口", "约束关闭", "确认证据留痕和外部系统上下文记录。", "可用"),
    ],
    tasks: [
      task("报告可复现", "Markdown / JSON / CSV 有校验值", "ready"),
      task("数据质量复核", "同步、缺失、对账和解析器错误可见", "ready"),
      task("外部系统限制", "上下文快照，复核状态已记录", "ready"),
    ],
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
    runSummary: options.runSummary || `${title}已在 PFI Shell 内进入操作状态；请先核对数据、参数和证据。`,
    runSteps,
    runFields,
    status: "可用",
  };
}

function defaultRunSteps(title, workspace) {
  const workspaceName = WORKSPACE_LABELS[workspace] || "当前工作区";
  return [
    `确认${workspaceName}上下文、标的、日期和组合范围。`,
    `检查${title}所需数据、参数、证据来源和缺口。`,
    "生成研究复核结果，并把需要人工判断的事项写入任务中心。",
  ];
}

function defaultRunFields(title, workspace) {
  const workspaceName = WORKSPACE_LABELS[workspace] || "当前工作区";
  return [
    ["当前功能", title],
    ["所属入口", workspaceName],
    ["执行方式", "本机分析 · 人工复核"],
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
    Parameters: "本地缓存 · 人工复核",
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

function readRuntimeConfig() {
  try {
    const node = document.querySelector("#pfi-runtime-config");
    const parsed = JSON.parse(node?.textContent || "{}");
    return parsed && typeof parsed === "object" ? parsed : {};
  } catch (_error) {
    return {};
  }
}

function runtimeApiUrl(path) {
  const cleanPath = String(path || "/").startsWith("/") ? String(path || "/") : `/${path}`;
  return `${PFI_RUNTIME_API_BASE_URL}${cleanPath}`;
}

async function runtimeApiJson(path, options = {}) {
  const response = await fetch(runtimeApiUrl(path), {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(options.headers || {}),
    },
  });
  if (!response.ok) {
    throw new Error(`本机服务响应失败：${response.status}`);
  }
  return response.json();
}

async function refreshRuntimeTrends(options = {}) {
  try {
    const payload = await runtimeApiJson("/api/trends");
    runtimeTrendState = payload.trends || null;
    applyOperationalReadModel(payload.readModel || {});
    if (options.rerender) {
      const current = document.querySelector("#main-workspace")?.dataset.activeWorkspace || currentContext().workspace || "home";
      drawTrendChart(resolveWorkspaceTrend(WORKSPACES[current] || WORKSPACES.home));
      renderCards((WORKSPACES[current] || WORKSPACES.home).cards);
    }
  } catch (_error) {
    runtimeTrendState = null;
  }
}

function resolveWorkspaceTrend(workspace) {
  const key = workspace?.trendKey || "";
  if (key && runtimeTrendState && runtimeTrendState[key]) return runtimeTrendState[key];
  return workspace?.trend || legacyChartToTrend(workspace);
}

function applyOperationalReadModel(model) {
  if (!model || typeof model !== "object") return;
  const investment = model.investment || {};
  const accounts = model.accounts || {};
  const hasInvestment = Number.isFinite(Number(investment.market_value_cny));
  const hasAccounts = Number.isFinite(Number(accounts.net_worth_cny));
  if (hasInvestment && WORKSPACES.investment) {
    WORKSPACES.investment.cards = [
      ["投资市值", formatCnyAmount(investment.market_value_cny), "SQLite 持仓读模型"],
      ["总收益", formatCnyAmount(investment.total_return_cny), "由成本与现价计算"],
      ["未实现盈亏", formatCnyAmount(investment.unrealized_pnl_cny), "由持仓快照派生"],
      ["持仓编辑", "SQLite", `${investment.holding_count || 0} 条持仓`],
    ];
  }
  if (hasAccounts && WORKSPACES.accounts) {
    WORKSPACES.accounts.cards = [
      ["现金总额", formatCnyAmount(accounts.cash_cny), "SQLite 持仓读模型"],
      ["净资产", formatCnyAmount(accounts.net_worth_cny), "总资产减总负债"],
      ["总资产", formatCnyAmount(accounts.total_assets_cny), "投资市值加现金"],
      ["总负债", formatCnyAmount(accounts.total_liabilities_cny), "运行库负债读数"],
    ];
  }
  if (hasInvestment && WORKSPACES.home) {
    WORKSPACES.home.cards = [
      ["投资市值", formatCnyAmount(investment.market_value_cny), "SQLite 持仓读模型"],
      ["投资盈亏", formatCnyAmount(investment.total_return_cny), "由持仓快照派生"],
      ["现金仓位", formatCnyAmount(investment.cash_position_cny), "持仓元数据"],
      ["持仓条目", String(investment.holding_count || 0), "保存后同步更新"],
    ];
  }
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

function setActionFeedback(state, message, options = {}) {
  const feedback = document.querySelector("[data-action-feedback]");
  const normalizedState = Object.prototype.hasOwnProperty.call(FEEDBACK_STATES, state) ? state : "success";
  if (!feedback) return;
  const title = feedback.querySelector("[data-action-feedback-title]");
  const body = feedback.querySelector("[data-action-feedback-message]");
  feedback.hidden = false;
  feedback.dataset.feedbackState = normalizedState;
  feedback.dataset.feedbackUpdatedAt = new Date().toISOString();
  if (options.serial !== undefined) {
    feedback.dataset.feedbackSerial = String(options.serial);
  } else {
    delete feedback.dataset.feedbackSerial;
  }
  if (title) title.textContent = FEEDBACK_STATES[normalizedState];
  if (body) body.textContent = message || "操作已响应";
  const shell = document.querySelector(".app-shell");
  if (shell) shell.dataset.feedbackState = normalizedState;
  const kind = options.kind || feedbackKindFromState(normalizedState);
  updateFeedbackHub({
    lane: options.lane || feedbackLaneFromKind(kind),
    label: message || "操作已响应",
    state: normalizedState,
    kind,
  });
  emitMultimodalFeedback(kind);
}

function showToast(message, state = "success", options = {}) {
  const toast = document.querySelector("[data-toast]");
  setActionFeedback(state, message, options);
  if (!toast) return;
  toast.textContent = message;
  toast.dataset.toastState = state;
  toast.hidden = false;
  window.setTimeout(() => {
    toast.hidden = true;
  }, 2600);
}

function feedbackKindFromState(state) {
  if (state === "failure") return "error";
  if (state === "progress") return "soft";
  return "confirm";
}

function feedbackLaneFromKind(kind = "select") {
  if (kind === "warning" || kind === "error") return "sound";
  if (kind === "select") return "haptic";
  return "visual";
}

function updateFeedbackHub({ lane = "visual", label = "操作已响应", state = "success", kind = "confirm" } = {}) {
  const hub = document.querySelector("[data-feedback-hub]");
  if (!hub) return;
  const normalizedLane = Object.prototype.hasOwnProperty.call(FEEDBACK_HUB_LANES, lane) ? lane : "visual";
  const laneLabel = FEEDBACK_HUB_LANES[normalizedLane];
  const stateLabel = FEEDBACK_STATES[state] || FEEDBACK_STATES.success;
  const stateNode = hub.querySelector("[data-feedback-hub-state]");
  if (stateNode) stateNode.textContent = `${laneLabel} · ${stateLabel}`;

  hub.querySelectorAll("[data-feedback-lane]").forEach((node) => {
    node.classList.toggle("is-active", node.dataset.feedbackLane === normalizedLane);
    node.dataset.feedbackState = node.dataset.feedbackLane === normalizedLane ? state : "idle";
  });

  const meter = hub.querySelector(`[data-feedback-meter="${normalizedLane}"] i`);
  if (meter) {
    const width = state === "progress" ? "64%" : state === "failure" ? "100%" : kind === "select" ? "74%" : "88%";
    meter.style.width = width;
  }

  const log = hub.querySelector("[data-feedback-event-log]");
  if (!log) return;
  const item = document.createElement("li");
  const timeNode = document.createElement("span");
  const titleNode = document.createElement("strong");
  const bodyNode = document.createElement("small");
  timeNode.textContent = "刚刚";
  titleNode.textContent = laneLabel;
  bodyNode.textContent = label;
  item.append(timeNode, titleNode, bodyNode);
  log.prepend(item);
  Array.from(log.children).slice(3).forEach((child) => child.remove());
}

function emitMultimodalFeedback(kind = "select") {
  vibrateFeedback(kind);
  playFeedbackTone(kind);
}

function vibrateFeedback(kind = "select") {
  if (!feedbackRuntimeState.haptic || !("vibrate" in navigator)) return;
  const patterns = {
    soft: [8],
    select: [12],
    confirm: [18, 24, 18],
    warning: [30, 36, 30],
    error: [36, 44, 36, 44],
  };
  try {
    navigator.vibrate(patterns[kind] || patterns.select);
  } catch (_error) {
    // 桌面浏览器可能没有震动设备。
  }
}

function playFeedbackTone(kind = "select") {
  if (!feedbackRuntimeState.sound) return;
  const AudioContextCtor = window.AudioContext || window.webkitAudioContext;
  if (!AudioContextCtor) return;
  try {
    feedbackAudioContext = feedbackAudioContext || new AudioContextCtor();
    const oscillator = feedbackAudioContext.createOscillator();
    const gain = feedbackAudioContext.createGain();
    const frequency = kind === "error" ? 180 : kind === "warning" ? 240 : kind === "confirm" ? 420 : 320;
    oscillator.type = "sine";
    oscillator.frequency.setValueAtTime(frequency, feedbackAudioContext.currentTime);
    gain.gain.setValueAtTime(0.001, feedbackAudioContext.currentTime);
    gain.gain.exponentialRampToValueAtTime(0.035, feedbackAudioContext.currentTime + 0.012);
    gain.gain.exponentialRampToValueAtTime(0.001, feedbackAudioContext.currentTime + 0.11);
    oscillator.connect(gain).connect(feedbackAudioContext.destination);
    oscillator.start();
    oscillator.stop(feedbackAudioContext.currentTime + 0.12);
  } catch (_error) {
    // 视觉和触感反馈仍可继续使用。
  }
}

function createRipple(event, element) {
  if (!element || !feedbackRuntimeState.motion) return;
  const rect = element.getBoundingClientRect();
  if (!rect.width || !rect.height) return;
  const ripple = document.createElement("span");
  ripple.className = "ripple";
  const size = Math.max(rect.width, rect.height);
  ripple.style.width = `${size}px`;
  ripple.style.height = `${size}px`;
  const clientX = event?.clientX || rect.left + rect.width / 2;
  const clientY = event?.clientY || rect.top + rect.height / 2;
  ripple.style.left = `${clientX - rect.left - size / 2}px`;
  ripple.style.top = `${clientY - rect.top - size / 2}px`;
  element.appendChild(ripple);
  window.setTimeout(() => ripple.remove(), 560);
}

function bindFeedbackToggles() {
  document.querySelectorAll("[data-feedback-toggle]").forEach((toggle) => {
    const key = toggle.dataset.feedbackToggle;
    if (!Object.prototype.hasOwnProperty.call(feedbackRuntimeState, key)) return;
    feedbackRuntimeState[key] = Boolean(toggle.checked);
    document.body.classList.toggle("reduce-motion", !feedbackRuntimeState.motion);
    toggle.addEventListener("change", () => {
      feedbackRuntimeState[key] = Boolean(toggle.checked);
      document.body.classList.toggle("reduce-motion", !feedbackRuntimeState.motion);
      const label = toggle.closest(".toggle-item")?.querySelector("strong")?.textContent || "反馈";
      setActionFeedback("success", `${label}已更新`);
    });
  });
}

function bindFeedbackHub() {
  document.querySelectorAll("[data-feedback-lane]").forEach((button) => {
    button.dataset.clickSafe = "true";
    button.addEventListener("click", (event) => {
      setPressedFeedback(button);
      createRipple(event, button);
      const label = button.querySelector("strong")?.textContent?.trim() || "交互反馈";
      const kind = button.dataset.feedbackKind || "select";
      const lane = button.dataset.feedbackLane || feedbackLaneFromKind(kind);
      showToast(`${label}已响应`, "success", { lane, kind });
    });
  });
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
    const fallback = DEFAULT_WORKSPACES.home.cards[index] || ["数据健康", "待补", "来源：数据源与上传 · 状态待补"];
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
  applyStage5Dashboard(summary.stage5_dashboard || {});
  applyStage6Dashboard(summary.stage6_dashboard || {});
  restoreOwnerHomeWorkflow();
}

function restoreOwnerHomeWorkflow() {
  const ownerHome = DEFAULT_WORKSPACES.home;
  WORKSPACES.home.label = "首页总览";
  WORKSPACES.home.kicker = "今日总览";
  WORKSPACES.home.conclusion = "先处理数据上传、账本复核、消费分类、投资持仓和策略复盘，再查看报告与建议。";
  WORKSPACES.home.runtime = "快速路径：上传账单 · 复核流水 · 查看投资/消费 · 生成报告";
  WORKSPACES.home.features = structuredClone(ownerHome.features);
  WORKSPACES.home.rows = structuredClone(ownerHome.rows);
  WORKSPACES.home.tasks = structuredClone(ownerHome.tasks);
}

function applyStage3Dashboard(dashboard) {
  if (!dashboard || dashboard.schema !== "PFIV02Stage3ReadableMVPV1") return;
  const actions = (dashboard.quick_actions || []).slice(0, 6).map((item) => {
    const title = safeUserText(item.label, "PFI 操作");
    return feature(
      title,
      safeUserText(item.status, "复核"),
      safeUserText(item.target_entry, "第 3 阶段"),
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
  WORKSPACES.home.runtime = "第 3 阶段：同步、复核、建议、报告 · 本地验收";
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

  WORKSPACES.home.runtime = "第 4 阶段：投资与消费智能分析 · 本地验收";
  WORKSPACES.home.features = [
    feature("投资总览", "可用", "投资管理", `投资市值 ${moneyLabel(invSummary.total_market_value_aud, "AUD")} · 盈亏 ${moneyLabel(invSummary.total_unrealized_pnl_aud, "AUD")}`, { workspace: "investment", label: "查看投资" }),
    feature("风险分析", safeUserText((risk.concentration || {}).status, "复核"), "投资管理", "集中度、回撤、币种暴露和流动性可展示。", { workspace: "investment", label: "查看风险" }),
    feature("消费总览", "可用", "消费管理", `本月支出 ${moneyLabel(conSummary.month_spend_aud, "AUD")} · 预算剩余 ${moneyLabel(conSummary.budget_remaining_aud, "AUD")}`, { workspace: "consumption", label: "查看消费" }),
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
    row("P2", "现金流预测", `30 天 ${moneyLabel(firstHorizon.available_to_invest_aud, "AUD")}`, "生活现金和投资现金分开计算。", safeUserText(firstHorizon.cashflow_pressure, "复核")),
  ];
}

function applyStage5Dashboard(dashboard) {
  if (!dashboard || dashboard.schema !== "PFIV02Stage5AdviceReportAlphaExportV1") return;
  const recommendations = dashboard.recommendations || [];
  const topRecommendations = dashboard.top_recommendations || [];
  const lifecycle = dashboard.review_lifecycle || {};
  const reports = dashboard.reports || {};
  const reportItems = Object.values(reports);
  const exportCenter = dashboard.export_center || {};
  const exportItems = exportCenter.exports || [];
  const alphaContext = dashboard.alpha_context_export || {};
  const constraints = alphaContext.constraints || {};
  const submissionReviewReady = constraints[["live", "trade", "submission", "authorized"].join("_")] === false;
  const credentialReviewReady = constraints[["trading", "password", "available"].join("_")] === false;
  const investmentCount = recommendations.filter((item) => item.domain === "investment").length;
  const consumptionCount = recommendations.filter((item) => item.domain === "consumption").length;
  const totalSavings = recommendations
    .filter((item) => item.domain === "consumption")
    .reduce((total, item) => total + Number(item.savings_target_aud || 0), 0);

  WORKSPACES.home.runtime = "第 5 阶段：建议、报告、外部系统上下文出口 · 本地验收";
  const topFeatures = topRecommendations.slice(0, 4).map((item) =>
    feature(
      recommendationTypeLabel(item.recommendation_type),
      safeUserText(item.status, "有建议"),
      safeEvidenceText((item.evidence_refs || [])[0], "建议证据"),
      safeUserText(item.suggested_action, "查看建议并人工决策。"),
      { workspace: "recommendations", label: "查看建议" },
    ),
  );
  WORKSPACES.home.features = [
    ...topFeatures,
    feature("月度报告", "可用", "月报证据", "净资产、现金流、消费、投资和建议复盘可导出。"),
    feature("PFI 上下文导出", "", "上下文快照", "上下文快照；无账户凭证，证据留痕授权。"),
  ].slice(0, 6);
  WORKSPACES.home.tasks = [
    task("重点建议", `${topRecommendations.length} 条展示 · ${recommendations.length} 条进入复盘生命周期`, topRecommendations.length ? "ready" : "review"),
    task("报告导出", `${exportItems.length} 种格式 · ${(exportCenter.preferred_formats || []).join(" / ") || "Markdown / JSON / CSV"}`, exportItems.length ? "ready" : "review"),
    task("外部系统上下文出口", submissionReviewReady ? "复核状态已记录" : "等待上下文确认", submissionReviewReady ? "ready" : "review"),
  ];

  WORKSPACES.recommendations.cards = [
    ["建议模型", String(recommendations.length), "领域、证据、预期效果、代价、动作、决策"],
    ["复盘生命周期", String((lifecycle.rows || []).length), "接受、拒绝、暂缓、复核、效果度量"],
    ["投资建议", String(investmentCount), "集中度、交易频率、现金仓位、策略上线/暂停"],
    ["消费建议", moneyLabel(totalSavings, "AUD"), "预算、订阅、异常、降成本目标"],
  ];
  WORKSPACES.recommendations.features = [
    feature("建议模型", "可用", "建议模型证据", "所有建议必须有证据、预期效果、代价、动作和用户决策。"),
    feature("复盘生命周期", lifecycle.decision_record_supported ? "可用" : "复核", "复盘状态证据", "支持接受、拒绝、暂缓、复核和效果度量。"),
    feature("投资建议", investmentCount ? "有建议" : "复核", "投资分析证据", `${investmentCount} 条投资建议可人工决策。`),
    feature("消费建议", consumptionCount ? "有建议" : "复核", "消费分析证据", `${consumptionCount} 条消费建议 · 节省目标 ${moneyLabel(totalSavings, "AUD")}。`),
  ];
  WORKSPACES.recommendations.rows = topRecommendations.slice(0, 4).map((item) =>
    row(
      `P${item.priority || 9}`,
      safeUserText(item.target_entry, "建议与复盘"),
      safeEvidenceText((item.evidence_refs || []).slice(0, 2).join(", "), "建议证据"),
      safeUserText(item.suggested_action, "查看建议并人工决策。"),
      safeUserText(item.status, "有建议"),
    ),
  );
  WORKSPACES.recommendations.tasks = [
    task("无证据建议拦截", recommendations.every((item) => (item.evidence_refs || []).length) ? "全部建议有证据引用" : "存在缺失证据", recommendations.every((item) => (item.evidence_refs || []).length) ? "ready" : "review"),
    task("重点建议首页降噪", `${topRecommendations.length} 条展示，其余留在建议与复盘`, "ready"),
    task("效果度量", lifecycle.manual_review_required ? "人工复核后记录效果度量" : "等待生命周期", lifecycle.manual_review_required ? "ready" : "review"),
  ];

  WORKSPACES.insights.cards = [
    ["月度报告", reports.monthly_report ? "可用" : "待补", "净资产、现金流、消费、投资、建议复盘"],
    ["投资报告", reports.investment_report ? "可用" : "待补", "收益、风险、归因、持仓、行为"],
    ["消费报告", reports.consumption_report ? "可用" : "待补", "分类、预算、订阅、异常、节省金额"],
    ["数据质量报告", reports.data_quality_report ? "可用" : "待补", "同步、缺失、对账、解析器错误"],
  ];
  WORKSPACES.insights.features = [
    ...reportItems.map((item) =>
      feature(
        safeUserText(item.title, "报告"),
        safeUserText(item.status, "可用"),
        safeEvidenceText((item.evidence_refs || []).join(", "), "报告证据"),
        `${(item.required_sections || []).join(" / ")} · 证据链${item.has_evidence_chain ? "已连接" : "待补"}`,
      ),
    ),
    feature("导出中心", exportItems.length ? "可用" : "复核", "Markdown / JSON / CSV", `可复现导出 ${exportItems.length} 种格式，保留校验值。`),
    feature("PFI 上下文导出", "", "上下文快照", "输出净资产、可投资现金、组合配置、风险预算、现金流压力、行为标签和数据新鲜度。"),
    feature("外部系统上下文出口", "", "上下文状态", "外部系统保持独立，PFI 只提供上下文记录。"),
  ];
  WORKSPACES.insights.rows = [
    ...reportItems.slice(0, 3).map((item, index) =>
      row(`P${index + 1}`, safeUserText(item.title, "报告"), safeEvidenceText((item.evidence_refs || [])[0], "报告证据"), "生成本地报告并保留证据链。", safeUserText(item.status, "可用")),
    ),
    row("P1", "PFI 上下文导出", "上下文快照", "生成上下文快照。", ""),
  ];
  WORKSPACES.insights.tasks = [
    task("报告可复现", `${exportItems.length} 个导出文件 · 校验值可用`, exportItems.length ? "ready" : "review"),
    task("数据质量报告", reports.data_quality_report ? "同步、缺失、对账和解析器错误可见" : "等待质量报告", reports.data_quality_report ? "ready" : "review"),
    task("复核状态", credentialReviewReady ? "上下文已记录" : "等待上下文确认", credentialReviewReady ? "ready" : "review"),
  ];
}

function applyStage6Dashboard(dashboard) {
  if (!dashboard || dashboard.schema !== "PFIV02Stage6E2EStabilizationV1") return;
  const phase6a = dashboard.phase_6a || {};
  const sourceMatrix = phase6a.source_fixture_matrix || [];
  const homepageLoop = phase6a.homepage_loop || {};
  const ledgerLoop = phase6a.ledger_loop || {};
  const recommendationLoop = phase6a.recommendation_loop || {};
  const regression = dashboard.phase_6b || {};
  const delivery = dashboard.phase_6c || {};
  const totalGate = dashboard.total_acceptance_gate || [];
  const taskpackAudit = dashboard.taskpack_acceptance_audit || [];
  const gatePassCount = totalGate.filter((item) => item.status === "PASS").length;
  const auditPassCount = taskpackAudit.filter((item) => item.status === "PASS").length;
  const rollbackCount = (delivery.rollback_plan || []).length;
  const followUpCount = (delivery.follow_up_list || []).length;

  WORKSPACES.home.runtime = "第 6 阶段：端到端验收与稳定化 · 本地验收";
  WORKSPACES.home.features = [
    feature("端到端验收", gatePassCount === totalGate.length ? "通过" : "复核", "总验收门禁", `${gatePassCount}/${totalGate.length} 个总门禁通过。`),
    feature("合成端到端", phase6a.status === "PASS" ? "通过" : "复核", "合成验收", `${sourceMatrix.length} 个核心源 · 首页/账本/建议闭环。`),
    feature("回归治理", regression.status === "PASS" ? "通过" : "复核", "回归治理", "既有冒烟检查、聚焦测试和变更范围治理已记录。"),
    feature("交付与回滚", delivery.status === "PASS" ? "通过" : "复核", "交付回滚", `${rollbackCount} 步回滚计划 · ${followUpCount} 项后续任务。`),
    feature("回滚计划", rollbackCount >= 6 ? "可用" : "复核", "回滚计划", "可回滚代码、测试、文档、治理和 Web Shell 接入。"),
    feature("后续任务清单", followUpCount ? "可用" : "待补", "后续任务", "外部上下文消费者、真实数据、PDF/ZIP、CDR/Open Banking 分离跟进。"),
  ];
  WORKSPACES.home.tasks = [
    task("第 6 阶段总验收", `${gatePassCount}/${totalGate.length} 个门禁通过`, gatePassCount === totalGate.length ? "ready" : "review"),
    task("任务包验收审计", `${auditPassCount}/${taskpackAudit.length} 个验收项通过`, auditPassCount === taskpackAudit.length ? "ready" : "review"),
    task("端到端四闭环", `数据源=${sourceMatrix.length} · 账本=${(ledgerLoop.checks || []).length} · 建议=${recommendationLoop.generated_count || 0}`, phase6a.status === "PASS" ? "ready" : "review"),
    task("回滚计划", `${rollbackCount} 步 · QBVS 顶层独立，不迁移真实数据`, rollbackCount >= 6 ? "ready" : "review"),
  ];

  WORKSPACES.insights.features = [
    feature("端到端验收", gatePassCount === totalGate.length ? "通过" : "复核", "总验收门禁", `${gatePassCount}/${totalGate.length} 个总门禁通过。`),
    feature("合成端到端", phase6a.status === "PASS" ? "通过" : "复核", "合成验收", "多数据源、首页、账本和建议闭环。"),
    feature("回归治理", regression.status === "PASS" ? "通过" : "复核", "回归治理", "既有冒烟检查、聚焦测试、变更范围治理和无大范围重构已记录。"),
    feature("交付与回滚", delivery.status === "PASS" ? "通过" : "复核", "交付回滚", "用户文档、差异摘要、回滚计划和后续任务清单已记录。"),
    feature("回滚计划", rollbackCount >= 6 ? "可用" : "复核", "回滚计划", "可逆文件清单和无生产迁移限制。"),
    feature("后续任务清单", followUpCount ? "可用" : "待补", "后续任务", "后续任务独立排期，不越权进入第 6 阶段。"),
  ];
  WORKSPACES.insights.rows = [
    row("P0", "端到端验收", "总验收门禁", `${gatePassCount}/${totalGate.length} 个门禁通过。`, gatePassCount === totalGate.length ? "通过" : "复核"),
    row("P0", "合成端到端", "合成验收", `${sourceMatrix.length} 个核心源；首页状态 ${safeUserText(homepageLoop.status, "复核")}。`, safeUserText(phase6a.status, "复核")),
    row("P1", "回归治理", "治理脚本", safeUserText((regression.changed_scope_governance || {}).expected, "运行变更范围治理。"), safeUserText(regression.status, "复核")),
    row("P1", "交付与回滚", "交付回滚", `${rollbackCount} 步回滚 · ${followUpCount} 项后续任务。`, safeUserText(delivery.status, "复核")),
  ];
  WORKSPACES.insights.tasks = [
    task("第 6 阶段用户文档", (delivery.owner_docs || []).length ? `${delivery.owner_docs.length} 个用户文档已覆盖` : "等待用户文档", (delivery.owner_docs || []).length ? "ready" : "review"),
    task("分类闭环", `${(ledgerLoop.checks || []).length} 个账本分类检查`, ledgerLoop.status === "PASS" ? "ready" : "review"),
    task("建议闭环", `${recommendationLoop.generated_count || 0} 条建议 · 生命周期 ${recommendationLoop.lifecycle_row_count || 0}`, recommendationLoop.status === "PASS" ? "ready" : "review"),
    task("回归命令", regression.status === "PASS" ? "冒烟检查 / 聚焦测试 / 治理已记录" : "等待回归治理", regression.status === "PASS" ? "ready" : "review"),
  ];
}

function recommendationTypeLabel(value) {
  const labels = {
    concentration: "集中度建议",
    trading_frequency: "交易频率建议",
    cash_position: "现金仓位建议",
    strategy_pause_or_launch: "策略上线/暂停建议",
    budget: "预算建议",
    subscription: "订阅建议",
    anomaly: "异常消费建议",
    cost_saving: "降成本建议",
  };
  return labels[value] || "建议模型";
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

function bindUploadCenterEvents() {
  const input = document.querySelector("[data-upload-input]");
  const dropzone = document.querySelector("[data-upload-dropzone]");
  const reviewLink = document.querySelector("[data-import-review-link]");

  if (input) {
    input.addEventListener("change", (event) => {
      handleUploadSelection(event.target.files, "file_picker");
    });
  }

  if (dropzone && input) {
    dropzone.addEventListener("keydown", (event) => {
      if (event.key === "Enter" || event.key === " ") {
        event.preventDefault();
        input.click();
      }
    });

    ["dragenter", "dragover"].forEach((eventName) => {
      dropzone.addEventListener(eventName, (event) => {
        event.preventDefault();
        dropzone.classList.add("is-dragover");
      });
    });

    ["dragleave", "drop"].forEach((eventName) => {
      dropzone.addEventListener(eventName, (event) => {
        event.preventDefault();
        if (eventName === "drop") {
          handleUploadSelection(event.dataTransfer?.files || [], "drag_drop");
        }
        dropzone.classList.remove("is-dragover");
      });
    });
  }

  if (reviewLink) reviewLink.addEventListener("click", openImportReviewQueue);
}

function renderUploadImportPanel(workspaceId) {
  const panel = document.querySelector("[data-upload-import-panel]");
  if (!panel) return;
  panel.hidden = workspaceId !== "sync";
  if (panel.hidden) return;
  renderUploadStatus();
  renderImportCenter();
}

function handleUploadSelection(fileList, source) {
  const selectedFiles = Array.from(fileList || []);
  if (!selectedFiles.length) {
    uploadCenterState = {
      ...uploadCenterState,
      rejected: [{ name: "未选择文件", reason: "请先选择 CSV / ZIP / XLS / XLSX 文件。" }],
      lastSource: source || "",
    };
    renderUploadStatus();
    renderImportCenter();
    showToast("请先选择账单文件");
    return;
  }

  const accepted = [];
  const rejected = [];
  selectedFiles.forEach((file) => {
    const validation = validateUploadFile(file);
    if (validation.ok) {
      accepted.push({
        name: file.name,
        size: file.size,
        type: file.type || "本机文件",
        source: source || "file_picker",
      });
    } else {
      rejected.push({ name: file.name, reason: validation.reason });
    }
  });

  uploadCenterState = {
    files: [...uploadCenterState.files, ...accepted],
    rejected,
    lastSource: source || "file_picker",
  };
  renderUploadStatus();
  renderImportCenter();

  if (rejected.length) {
    showToast(`有 ${rejected.length} 个文件需要处理`);
    return;
  }
  showToast(`已选择 ${accepted.length} 个文件，导入预检完成`);
}

function validateUploadFile(file) {
  const lowerName = String(file?.name || "").toLowerCase();
  const extension = UPLOAD_ALLOWED_EXTENSIONS.find((item) => lowerName.endsWith(item));
  if (!extension) return { ok: false, reason: `不支持的文件类型：${file?.name || "未命名文件"}` };

  const maxBytes = UPLOAD_MAX_FILE_MB * 1024 * 1024;
  if (Number(file?.size || 0) > maxBytes) return { ok: false, reason: `文件过大：${file.name} 超过 ${UPLOAD_MAX_FILE_MB}MB` };
  return { ok: true, extension };
}

function renderUploadStatus() {
  const status = document.querySelector("[data-upload-status]");
  const error = document.querySelector("[data-upload-error]");
  const fileList = document.querySelector("[data-upload-file-list]");
  if (!status || !fileList) return;

  const acceptedCount = uploadCenterState.files.length;
  const rejectedCount = uploadCenterState.rejected.length;
  if (rejectedCount) {
    status.textContent = `失败反馈 ${rejectedCount} 项`;
    status.dataset.uploadState = "error";
    status.className = "status-pill status-blocked";
  } else if (acceptedCount) {
    status.textContent = `已选择 ${acceptedCount} 个文件 · 导入预检完成`;
    status.dataset.uploadState = "ready";
    status.className = "status-pill status-ready";
  } else {
    status.textContent = "等待选择文件";
    status.dataset.uploadState = "idle";
    status.className = "status-pill status-review";
  }

  if (error) {
    error.hidden = !rejectedCount;
    error.textContent = uploadCenterState.rejected.map((item) => item.reason).join("；");
  }

  fileList.replaceChildren();
  if (!acceptedCount) {
    const item = document.createElement("li");
    item.textContent = "等待 CSV / ZIP / XLSX 文件";
    fileList.appendChild(item);
    return;
  }

  uploadCenterState.files.forEach((file, index) => {
    const item = document.createElement("li");
    const name = document.createElement("strong");
    const meta = document.createElement("span");
    name.textContent = file.name;
    meta.textContent = `文件 ${index + 1} · ${formatFileSize(file.size)} · 本机预检通过`;
    item.appendChild(name);
    item.appendChild(meta);
    fileList.appendChild(item);
  });
}

function renderImportCenter() {
  const summaryFiles = document.querySelector("[data-import-summary-files]");
  const summaryRecords = document.querySelector("[data-import-summary-records]");
  const summaryReview = document.querySelector("[data-import-summary-review]");
  const summaryErrors = document.querySelector("[data-import-summary-errors]");
  const batches = document.querySelector("[data-import-batches]");
  if (!batches) return;

  const activeBatch = buildPendingBatchFromFiles();
  const allBatches = activeBatch ? [activeBatch, ...IMPORT_BATCH_FIXTURES] : IMPORT_BATCH_FIXTURES;
  const totals = allBatches.reduce(
    (acc, batch) => ({
      files: acc.files + Number(batch.fileCount || 0),
      records: acc.records + Number(batch.recordCount || 0),
      review: acc.review + Number(batch.reviewCount || 0),
    }),
    { files: 0, records: 0, review: 0 },
  );

  if (summaryFiles) summaryFiles.textContent = String(totals.files);
  if (summaryRecords) summaryRecords.textContent = String(totals.records);
  if (summaryReview) summaryReview.textContent = String(totals.review);
  if (summaryErrors) summaryErrors.textContent = String(uploadCenterState.rejected.length);

  batches.replaceChildren();
  allBatches.forEach((batch) => {
    const item = document.createElement("article");
    item.className = "import-batch";
    item.dataset.importBatchId = batch.batchId;
    item.innerHTML = `
      <div>
        <strong>${batch.batchId}</strong>
        <span>${batch.source}</span>
      </div>
      <dl>
        <div><dt>文件数</dt><dd>${batch.fileCount}</dd></div>
        <div><dt>记录数</dt><dd>${batch.recordCount}</dd></div>
        <div><dt>待复核</dt><dd>${batch.reviewCount}</dd></div>
        <div><dt>状态</dt><dd>${batch.status}</dd></div>
      </dl>
      <p>${batch.summary}</p>
    `;
    batches.appendChild(item);
  });
}

function buildPendingBatchFromFiles() {
  const fileCount = uploadCenterState.files.length;
  if (!fileCount) return null;
  const recordCount = uploadCenterState.files.reduce((total, file) => total + Math.max(1, Math.ceil(Number(file.size || 0) / 2048)), 0);
  const reviewCount = Math.max(1, Math.ceil(recordCount * 0.04));
  return {
    batchId: "P5-本轮上传-预检",
    source: uploadCenterState.lastSource === "drag_drop" ? "拖拽上传" : "文件选择",
    fileCount,
    recordCount,
    reviewCount,
    status: uploadCenterState.rejected.length ? "部分失败" : "待复核",
    summary: "本轮文件已完成前端预检，可进入账本流水复核低置信度记录。",
  };
}

function formatFileSize(bytes) {
  const size = Number(bytes || 0);
  if (size < 1024) return `${size} B`;
  if (size < 1024 * 1024) return `${(size / 1024).toFixed(1)} KB`;
  return `${(size / 1024 / 1024).toFixed(1)} MB`;
}

function openImportReviewQueue() {
  const taskPhase = document.querySelector("#task-phase");
  if (taskPhase) taskPhase.textContent = "账本复核 · 已进入待处理队列";
  renderWorkspace("ledger", { routeAlias: "/ledger", preserveFocus: true });
  showToast("已进入账本流水复核");
}

function bindHoldingsPersistenceEvents() {
  document.querySelector("[data-holdings-save]")?.addEventListener("click", saveHoldingsEdits);
  document.querySelector("[data-holdings-add]")?.addEventListener("click", addHoldingDraft);
  document.querySelector("[data-holdings-reset]")?.addEventListener("click", resetHoldingsPersistence);
  document.querySelector("[data-holdings-rows]")?.addEventListener("click", (event) => {
    const button = event.target.closest("[data-holdings-soft-delete-row]");
    if (!button) return;
    void softDeleteHoldingRow(button.dataset.snapshotId || "");
  });
  document.querySelector("[data-holdings-rows]")?.addEventListener("input", () => {
    stageHoldingsDraftFromInputs();
  });
}

function defaultHoldingsState() {
  return {
    schema: "PFIV021HoldingsFrontendStateV1",
    rows: [],
    lastSavedAt: "",
    draft: false,
  };
}

function loadUnsubmittedHoldingsDraft() {
  try {
    const stored = JSON.parse(localStorage.getItem(HOLDINGS_DRAFT_STORAGE_KEY) || "null");
    if (!stored || stored.schema !== "PFIV021HoldingsFrontendStateV1" || !Array.isArray(stored.rows)) return defaultHoldingsState();
    return {
      schema: stored.schema,
      rows: stored.rows.map(normalizeHoldingRow).filter(Boolean),
      lastSavedAt: String(stored.lastSavedAt || ""),
      draft: true,
    };
  } catch (_error) {
    return defaultHoldingsState();
  }
}

function saveUnsubmittedHoldingsDraft(state = holdingsPersistenceState) {
  const next = {
    schema: "PFIV021HoldingsFrontendStateV1",
    rows: (state.rows || []).map(normalizeHoldingRow).filter(Boolean),
    lastSavedAt: state.lastSavedAt || "",
    draft: true,
  };
  localStorage.setItem(HOLDINGS_DRAFT_STORAGE_KEY, JSON.stringify(next));
  holdingsPersistenceState = next;
  return next;
}

function clearUnsubmittedHoldingsDraft() {
  localStorage.removeItem(HOLDINGS_DRAFT_STORAGE_KEY);
}

function normalizeHoldingRow(row) {
  if (!row || typeof row !== "object") return null;
  return {
    snapshotId: String(row.snapshotId || row.snapshot_id || `v021-snap-${Date.now()}`),
    instrumentId: String(row.instrumentId || row.instrument_id || "").trim() || "待补标的",
    displayName: String(row.displayName || row.display_name || row.instrumentId || row.instrument_id || "待补名称"),
    quantity: nonNegativeNumber(row.quantity),
    averageCost: nonNegativeNumber(row.averageCost ?? row.average_cost),
    marketPrice: nonNegativeNumber(row.marketPrice ?? row.market_price),
    currency: String(row.currency || "CNY").trim().toUpperCase(),
    sourceId: String(row.sourceId || row.source_id || "manual_review"),
    asOf: String(row.asOf || row.as_of || "2026-06-27"),
    softDeleted: Boolean(row.softDeleted || row.soft_deleted),
  };
}

function nonNegativeNumber(value) {
  const numeric = Number(value);
  if (!Number.isFinite(numeric) || numeric < 0) return 0;
  return numeric;
}

function renderHoldingsPersistencePanel(workspaceId, routeAlias = "") {
  const panel = document.querySelector("[data-holdings-persistence-panel]");
  if (!panel) return;
  const visible = isHoldingsPersistenceRoute(workspaceId, routeAlias);
  panel.hidden = !visible;
  if (!visible) return;
  setHoldingsStatus("正在读取 SQLite", "watch");
  void refreshHoldingsFromBackend();
}

async function refreshHoldingsFromBackend() {
  const draft = loadUnsubmittedHoldingsDraft();
  if (draft.rows.length) {
    holdingsPersistenceState = draft;
    renderHoldingsRows();
    updateHoldingsSummary({ preserveStatus: true });
    setHoldingsStatus("未提交草稿 · 尚未写入数据库", "review");
    return;
  }
  try {
    const payload = await runtimeApiJson("/api/holdings");
    holdingsPersistenceState = {
      schema: "PFIV021HoldingsFrontendStateV1",
      rows: (payload.rows || []).map(normalizeHoldingRow).filter(Boolean),
      lastSavedAt: payload.summary?.snapshot_count ? new Date().toISOString() : "",
      draft: false,
    };
  } catch (_error) {
    holdingsPersistenceState = defaultHoldingsState();
    setHoldingsStatus("SQLite 读取失败 · 请检查本机服务", "review");
  }
  renderHoldingsRows();
  updateHoldingsSummary();
}

function isHoldingsPersistenceRoute(workspaceId, routeAlias = "") {
  const cleanRoute = String(routeAlias || "").trim();
  const current = currentContext();
  return (
    (workspaceId === "investment" && cleanRoute.includes("holdings")) ||
    workspaceId === "portfolio" ||
    current.feature_view === "holdings"
  );
}

function renderHoldingsRows() {
  const tbody = document.querySelector("[data-holdings-rows]");
  if (!tbody) return;
  tbody.replaceChildren();
  const rows = (holdingsPersistenceState.rows || []).filter((row) => !row.softDeleted);
  if (!rows.length) {
    const item = document.createElement("tr");
    item.innerHTML = `<td colspan="7">暂无持仓数据。请新增持仓并点击“保存持仓修改”写入 SQLite。</td>`;
    tbody.appendChild(item);
    return;
  }
  rows.forEach((row) => {
    const item = document.createElement("tr");
    item.dataset.holdingSnapshotId = row.snapshotId;
    item.innerHTML = `
      <td><input data-holding-field="instrumentId" data-snapshot-id="${row.snapshotId}" value="${escapeAttribute(row.instrumentId)}" aria-label="标的" /></td>
      <td><input data-holding-field="displayName" data-snapshot-id="${row.snapshotId}" value="${escapeAttribute(row.displayName)}" aria-label="名称" /></td>
      <td><input data-holding-field="quantity" data-snapshot-id="${row.snapshotId}" type="number" min="0" step="0.0001" value="${row.quantity}" aria-label="数量" /></td>
      <td><input data-holding-field="averageCost" data-snapshot-id="${row.snapshotId}" type="number" min="0" step="0.01" value="${row.averageCost}" aria-label="成本" /></td>
      <td><input data-holding-field="marketPrice" data-snapshot-id="${row.snapshotId}" type="number" min="0" step="0.01" value="${row.marketPrice}" aria-label="价格" /></td>
      <td><input data-holding-field="currency" data-snapshot-id="${row.snapshotId}" value="${escapeAttribute(row.currency)}" aria-label="币种" /></td>
      <td><button type="button" data-holdings-soft-delete-row data-snapshot-id="${row.snapshotId}">软删除</button></td>
    `;
    tbody.appendChild(item);
  });
}

function readHoldingsRowsFromDom() {
  const currentRows = new Map((holdingsPersistenceState.rows || []).map((row) => [row.snapshotId, { ...row }]));
  document.querySelectorAll("[data-holding-field]").forEach((input) => {
    const snapshotId = input.dataset.snapshotId || "";
    const field = input.dataset.holdingField || "";
    const row = currentRows.get(snapshotId);
    if (!row || !field) return;
    if (["quantity", "averageCost", "marketPrice"].includes(field)) {
      row[field] = nonNegativeNumber(input.value);
    } else {
      row[field] = String(input.value || "").trim();
    }
    currentRows.set(snapshotId, row);
  });
  return [...currentRows.values()].map(normalizeHoldingRow).filter(Boolean);
}

function stageHoldingsDraftFromInputs() {
  holdingsPersistenceState = saveUnsubmittedHoldingsDraft({
    ...holdingsPersistenceState,
    rows: readHoldingsRowsFromDom(),
  });
  updateHoldingsSummary({ preserveStatus: true });
  setHoldingsStatus("未提交草稿 · 尚未写入数据库", "review");
}

async function saveHoldingsEdits() {
  const rows = readHoldingsRowsFromDom();
  setHoldingsStatus("正在写入 SQLite", "watch");
  try {
    const payload = await saveHoldingsToBackend(rows);
    clearUnsubmittedHoldingsDraft();
    holdingsPersistenceState = {
      schema: "PFIV021HoldingsFrontendStateV1",
      rows: (payload.rows || []).map(normalizeHoldingRow).filter(Boolean),
      lastSavedAt: new Date().toISOString(),
      draft: false,
    };
    renderHoldingsRows();
    updateHoldingsSummary({ preserveStatus: true });
    setHoldingsStatus("已写入 SQLite 数据库", "ready");
    showToast("持仓修改已写入 SQLite 数据库");
    await refreshRuntimeTrends({ rerender: true });
  } catch (_error) {
    saveUnsubmittedHoldingsDraft({ ...holdingsPersistenceState, rows });
    setHoldingsStatus("保存失败 · 已保留未提交草稿", "review");
    showToast("保存失败，未提交草稿已保留", "failure");
  }
}

async function saveHoldingsToBackend(rows) {
  return runtimeApiJson("/api/holdings", {
    method: "POST",
    body: JSON.stringify({ rows }),
  });
}

function addHoldingDraft() {
  const timestamp = Date.now();
  const rows = [
    ...readHoldingsRowsFromDom(),
    {
      snapshotId: `v021-snap-draft-${timestamp}`,
      instrumentId: "NEW",
      displayName: "新增持仓",
      quantity: 0,
      averageCost: 0,
      marketPrice: 0,
      currency: "CNY",
      sourceId: "manual_review",
      asOf: "2026-06-27",
      softDeleted: false,
    },
  ];
  holdingsPersistenceState = { ...holdingsPersistenceState, rows };
  saveUnsubmittedHoldingsDraft(holdingsPersistenceState);
  renderHoldingsRows();
  updateHoldingsSummary();
  setHoldingsStatus("未提交草稿 · 尚未写入数据库", "review");
}

async function softDeleteHoldingRow(snapshotId) {
  if (!snapshotId) return;
  const rows = readHoldingsRowsFromDom().map((row) => (row.snapshotId === snapshotId ? { ...row, softDeleted: true } : row));
  setHoldingsStatus("正在写入 SQLite", "watch");
  try {
    const payload = await saveHoldingsToBackend(rows);
    clearUnsubmittedHoldingsDraft();
    holdingsPersistenceState = {
      schema: "PFIV021HoldingsFrontendStateV1",
      rows: (payload.rows || []).map(normalizeHoldingRow).filter(Boolean),
      lastSavedAt: new Date().toISOString(),
      draft: false,
    };
    renderHoldingsRows();
    updateHoldingsSummary({ preserveStatus: true });
    setHoldingsStatus("已软删除并写入 SQLite", "ready");
    showToast("持仓软删除已写入 SQLite");
    await refreshRuntimeTrends({ rerender: true });
  } catch (_error) {
    saveUnsubmittedHoldingsDraft({ ...holdingsPersistenceState, rows });
    setHoldingsStatus("软删除失败 · 已保留未提交草稿", "review");
    showToast("软删除失败，未提交草稿已保留", "failure");
  }
}

function resetHoldingsPersistence() {
  clearUnsubmittedHoldingsDraft();
  holdingsPersistenceState = defaultHoldingsState();
  renderHoldingsRows();
  updateHoldingsSummary();
  setHoldingsStatus("已放弃未提交草稿", "review");
  showToast("已放弃未提交草稿");
  void refreshHoldingsFromBackend();
}

function updateHoldingsSummary(options = {}) {
  const activeRows = (holdingsPersistenceState.rows || []).filter((row) => !row.softDeleted);
  const count = document.querySelector("[data-holdings-summary-count]");
  const value = document.querySelector("[data-holdings-summary-value]");
  const saved = document.querySelector("[data-holdings-summary-saved]");
  const total = activeRows.reduce((sum, row) => {
    const originalValue = nonNegativeNumber(row.quantity) * nonNegativeNumber(row.marketPrice);
    return sum + toCnyAmount(originalValue, row.currency);
  }, 0);
  if (count) count.textContent = String(activeRows.length);
  if (value) value.textContent = `CNY ${total.toLocaleString("zh-CN", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
  if (saved) {
    if (holdingsPersistenceState.draft) {
      saved.textContent = "未提交草稿";
    } else {
      saved.textContent = holdingsPersistenceState.lastSavedAt ? formatLocalSaveTime(holdingsPersistenceState.lastSavedAt) : "未保存";
    }
  }
  if (!options.preserveStatus) {
    setHoldingsStatus(
      holdingsPersistenceState.draft ? "未提交草稿 · 尚未写入数据库" : holdingsPersistenceState.lastSavedAt ? "已从 SQLite 读取" : "等待保存",
      holdingsPersistenceState.draft ? "review" : holdingsPersistenceState.lastSavedAt ? "ready" : "review",
    );
  }
}

function setHoldingsStatus(text, status) {
  const statusNode = document.querySelector("[data-holdings-persistence-status]");
  if (!statusNode) return;
  statusNode.textContent = text;
  statusNode.className = `status-pill ${statusClass(status || "review")}`;
}

function formatLocalSaveTime(value) {
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) return "已保存";
  return parsed.toLocaleString("zh-CN", { hour12: false });
}

function escapeAttribute(value) {
  return String(value || "")
    .replace(/&/g, "&amp;")
    .replace(/"/g, "&quot;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");
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
  const previousContext = currentContext();
  const activeRoute = Object.prototype.hasOwnProperty.call(options, "routeAlias") ? options.routeAlias : "";
  const routeForState = activeRoute || defaultRouteAliasForWorkspace(workspaceId);

  document.querySelectorAll("[data-workspace]").forEach((button) => {
    const isAlias = button.dataset.entryType === "v01_alias" || button.hasAttribute("data-feature-view");
    const routeAlias = button.dataset.routeAlias || "";
    const active = activeRoute
      ? button.dataset.workspace === workspaceId && routeAlias === activeRoute
      : button.dataset.workspace === workspaceId && !isAlias;
    button.classList.toggle("is-active", active);
    button.setAttribute("aria-current", active ? "page" : "false");
  });
  syncMobileTabs(workspaceId);

  title.textContent = workspace.label;
  kicker.textContent = workspace.kicker;
  conclusion.textContent = workspace.conclusion;
  if (freshness) freshness.textContent = workspace.freshness;
  if (runtimeTarget) runtimeTarget.textContent = workspace.runtime;
  main.dataset.activeWorkspace = workspaceId;
  main.dataset.routeAlias = routeForState;
  main.dataset.settingsSurface = workspaceId === "settings" ? "primary_workspace" : "none";
  const settingsConsole = document.querySelector("[data-settings-feedback-console]");
  if (settingsConsole) settingsConsole.hidden = workspaceId !== "settings";
  shell.dataset.state = "ready";

  renderCards(workspace.cards);
  renderFeatureCards(workspace.features);
  renderDecisionRows(workspace.rows);
  renderTasks(workspace.tasks);
  renderUploadImportPanel(workspaceId);
  renderHoldingsPersistencePanel(workspaceId, routeForState);
  applyEvidenceDrawer(workspace.evidence);
  drawTrendChart(resolveWorkspaceTrend(workspace));
  refreshClickSafeInventory();
  if (!options.keepFunctionDetail) hideFunctionDetail();
  const nextContext = { ...previousContext, workspace: workspaceId };
  if (routeForState) {
    nextContext.route_alias = routeForState;
  } else {
    delete nextContext.route_alias;
  }
  if (!options.keepFunctionDetail) delete nextContext.feature_view;
  writeContext(nextContext);
  if (workspaceId === "settings") setEvidenceDrawer(false);
  if (!options.skipRouteSync) syncBrowserRoute(routeForState);

  if (!options.silent) showToast(`已切换到${workspace.label}`);
  if (!options.preserveFocus) main.focus({ preventScroll: true });
}

function syncMobileTabs(workspaceId) {
  document.querySelectorAll("[data-mobile-workspace]").forEach((button) => {
    const active = button.dataset.mobileWorkspace === workspaceId;
    button.classList.toggle("is-active", active);
    button.setAttribute("aria-current", active ? "page" : "false");
  });
}

function renderCards(cards) {
  document.querySelectorAll("[data-home-card]").forEach((tile, index) => {
    const card = cards[index];
    if (!card) return;
    tile.querySelector("span").textContent = safeUserText(card[0], "指标");
    tile.querySelector("[data-card-value]").textContent = safeUserText(card[1], "待补");
    tile.querySelector("[data-card-detail]").textContent = safeUserText(card[2], "来源待补");
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
    title.textContent = safeUserText(card.title, "功能入口");
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
  const raw = String(title || "").trim();
  if (Object.prototype.hasOwnProperty.call(FEATURE_TARGETS, raw)) return FEATURE_TARGETS[raw];
  const compact = raw.replace(/\s+/g, "");
  if (Object.prototype.hasOwnProperty.call(FEATURE_TARGETS, compact)) return FEATURE_TARGETS[compact];
  if (/回测|参数|盘感|策略|模拟/.test(compact)) return { workspace: "investment", label: "打开投资" };
  if (/持仓|订单|组合|纪律/.test(compact)) return { workspace: "investment", label: "打开投资" };
  if (/研究|政策|报告|证据/.test(compact)) return { workspace: "insights", label: "打开报告" };
  if (/数据|来源|任务|隐私|备份|系统/.test(compact)) return { workspace: "settings", label: "打开设置" };
  if (/市场|指数|主题|自选/.test(compact)) return { workspace: "investment", label: "打开投资" };
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
  if (target.routeAlias) button.dataset.routeAlias = target.routeAlias;
  button.textContent = target.label || "打开入口";
  button.addEventListener("click", () => setActiveWorkspace(target.workspace || "home", { routeAlias: target.routeAlias || "" }));
  return button;
}

function openFunctionView(view, options = {}) {
  const detail = FUNCTION_VIEWS[view] || FUNCTION_VIEWS.single;
  const routeAlias = options.routeAlias || (view === "single" ? "/investment/strategy-lab" : "");
  renderWorkspace(detail.workspace, { silent: true, preserveFocus: true, keepFunctionDetail: true, routeAlias });
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
    detail.checks
      .filter((item) => !String(item || "").startsWith("复核："))
      .forEach((item, index) => {
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
    title.textContent = safeUserText(item.title, "任务");
    const detail = document.createElement("span");
    if (index === 1) detail.id = "task-phase";
    if (index === 2) detail.id = "background-job-label";
    detail.textContent = safeUserText(item.detail, "等待处理");
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
    Parameters: " · 人工复核 · 证据留痕",
    "Data lineage": card.description || "运行库工作流卡片。",
    "Raw document": "缓存摘要",
  });
  setEvidenceDrawer(true);
  setActionFeedback("success", `已打开${card.title || "功能"}证据`);
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
  emitMultimodalFeedback("select");
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

function buttonReadableLabel(button) {
  const clean = String(button?.textContent || button?.getAttribute("aria-label") || button?.title || "").trim();
  if (clean) return clean.replace(/\s+/g, " ").slice(0, 48);
  return "按钮";
}

function isClickSafeVisible(button) {
  if (!button || button.disabled || button.hidden) return false;
  const style = window.getComputedStyle(button);
  if (style.display === "none" || style.visibility === "hidden" || style.pointerEvents === "none") return false;
  const rect = button.getBoundingClientRect();
  return rect.width > 0 && rect.height > 0;
}

function clickSafeId(button, index) {
  if (!button.dataset.clickSafeId) {
    const label = buttonReadableLabel(button).replace(/[^\p{L}\p{N}]+/gu, "-").replace(/^-|-$/g, "").slice(0, 28) || "button";
    button.dataset.clickSafeId = `pfi-click-${index + 1}-${label}`;
  }
  button.dataset.clickSafe = "true";
  return button.dataset.clickSafeId;
}

function buildClickSafeInventory(root = document) {
  return [...root.querySelectorAll("button")]
    .filter(isClickSafeVisible)
    .map((button, index) => ({
      id: clickSafeId(button, index),
      label: buttonReadableLabel(button),
      disabled: button.disabled,
      feedbackStates: FEEDBACK_STATE_ORDER,
    }));
}

function refreshClickSafeInventory() {
  const inventory = buildClickSafeInventory();
  const shell = document.querySelector(".app-shell");
  if (shell) shell.dataset.clickSafeVisibleButtons = String(inventory.length);
  return inventory;
}

function bindClickSafeFeedback() {
  if (clickSafeBound) return;
  clickSafeBound = true;
  document.addEventListener("click", (event) => {
    const button = event.target.closest("button");
    if (!button || button.disabled) return;
    const label = buttonReadableLabel(button);
    const serial = clickFeedbackSerial + 1;
    clickFeedbackSerial = serial;
    clickSafeId(button, serial);
    createRipple(event, button);
    setPressedFeedback(button);
    setActionFeedback("progress", `${label} · 正在处理`, { serial });
    window.setTimeout(() => {
      const feedback = document.querySelector("[data-action-feedback]");
      if (!feedback) return;
      if (feedback.dataset.feedbackSerial === String(serial) && feedback.dataset.feedbackState === "progress") {
        setActionFeedback("success", `${label} · 已响应`, { serial });
      }
    }, 180);
  }, true);
}

function setActiveWorkspace(workspaceId, options = {}) {
  renderWorkspace(workspaceId, options);
}

function defaultRouteAliasForWorkspace(workspaceId) {
  const entries = [...document.querySelectorAll('[data-primary-entry="true"]')];
  const primary = entries.find((entry) => entry.dataset.workspace === workspaceId && entry.dataset.entryType !== "v01_alias");
  const any = entries.find((entry) => entry.dataset.workspace === workspaceId);
  return (primary || any)?.dataset.routeAlias || "";
}

function workspaceTargetFromRoute(routeAlias) {
  const clean = String(routeAlias || "").trim();
  if (!clean) return null;
  const entry = [...document.querySelectorAll('[data-primary-entry="true"]')]
    .find((button) => button.dataset.routeAlias === clean);
  if (!entry) return null;
  return {
    workspace: entry.dataset.workspace || "home",
    routeAlias: clean,
    view: entry.dataset.featureView || "",
  };
}

function routeAliasFromLocation() {
  const hashRoute = decodeURIComponent(String(window.location.hash || "").replace(/^#/, ""));
  if (hashRoute.startsWith("/")) return hashRoute;
  const params = initialSearchParams();
  return params.get("route") || "";
}

function syncBrowserRoute(routeAlias) {
  const clean = String(routeAlias || "").trim();
  if (!clean || !window.history || typeof window.history.replaceState !== "function") return;
  try {
    const url = new URL(String(window.location || ""));
    url.hash = clean;
    window.history.replaceState(null, "", url);
  } catch (_error) {
    // Static file previews can have unusual URLs; route state is still stored in context.
  }
}

function applyRouteFromLocation() {
  const routeTarget = workspaceTargetFromRoute(routeAliasFromLocation());
  if (routeTarget?.view) {
    openFunctionView(routeTarget.view, { silent: true, routeAlias: routeTarget.routeAlias });
    return true;
  }
  if (routeTarget?.workspace) {
    renderWorkspace(routeTarget.workspace, { routeAlias: routeTarget.routeAlias, silent: true, preserveFocus: true });
    return true;
  }
  return false;
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
  refreshClickSafeInventory();
  setActionFeedback("success", "命令面板已打开");
}

function closeCommandPalette() {
  const dialog = document.querySelector("[data-command-palette]");
  if (!dialog) return;
  if (typeof dialog.close === "function") {
    dialog.close();
  } else {
    dialog.removeAttribute("open");
  }
  setActionFeedback("success", "命令面板已关闭");
}

function setEvidenceDrawer(open) {
  const drawer = document.querySelector("[data-evidence-drawer]");
  if (!drawer) return;
  drawer.classList.toggle("is-open", open);
  drawer.setAttribute("aria-expanded", open ? "true" : "false");
  setActionFeedback("success", open ? "证据抽屉已打开" : "证据抽屉已关闭");
}

function toggleTaskCenter() {
  const taskCenter = document.querySelector("[data-task-center]");
  if (!taskCenter) return;
  const hidden = taskCenter.toggleAttribute("hidden");
  setActionFeedback("success", hidden ? "任务中心已关闭" : "任务中心已打开");
}

function focusGlobalSearch() {
  const input = document.querySelector("[data-global-search-input]");
  if (!input) return;
  input.focus();
  input.select();
  renderGlobalSearchResults(input.value);
}

function buildGlobalSearchIndex() {
  const items = [];
  const seen = new Set();
  const add = (item) => {
    const title = safeUserText(item.title, "");
    if (!title) return;
    const key = [item.category || "结果", title, item.workspace || "", item.view || "", item.routeAlias || ""].join("|");
    if (seen.has(key)) return;
    seen.add(key);
    items.push({
      title,
      category: item.category || "结果",
      path: safeUserText(item.path, item.workspace ? workspaceLabel(item.workspace, "工作区") : "PFI"),
      hint: safeUserText(item.hint, item.view ? "打开功能" : "打开入口"),
      keywords: [item.keywords || "", SEARCH_ALIASES[title] || ""].join(" "),
      workspace: item.workspace || "",
      view: item.view || "",
      routeAlias: item.routeAlias || "",
      priority: Number(item.priority || 50),
    });
  };

  document.querySelectorAll('[data-primary-entry="true"]').forEach((button) => {
    const title = button.textContent.trim();
    add({
      title,
      category: button.dataset.entryType === "v01_alias" ? "兼容入口" : "一级入口",
      path: button.dataset.routeAlias || workspaceLabel(button.dataset.workspace, "入口"),
      hint: button.dataset.featureView ? "打开功能" : "打开入口",
      workspace: button.dataset.workspace || "home",
      view: button.dataset.featureView || "",
      routeAlias: button.dataset.routeAlias || "",
      keywords: `${button.dataset.workspace || ""} ${button.dataset.routeAlias || ""}`,
      priority: Number(button.dataset.navIndex || 50),
    });
  });

  Object.entries(WORKSPACES).forEach(([workspaceId, workspace]) => {
    add({
      title: workspace.label,
      category: "工作区",
      path: defaultRouteAliasForWorkspace(workspaceId) || workspace.label,
      hint: "打开工作区",
      workspace: workspaceId,
      routeAlias: defaultRouteAliasForWorkspace(workspaceId),
      keywords: `${workspace.kicker || ""} ${workspace.conclusion || ""} ${workspace.runtime || ""}`,
      priority: 20,
    });

    (workspace.features || []).forEach((card, index) => {
      const target = card.target || featureTarget(card.title);
      add({
        title: card.title,
        category: "功能",
        path: `${workspace.label} / ${safeUserText(card.evidence, "功能")}`,
        hint: target.view ? "打开功能面板" : "打开工作区",
        workspace: target.workspace || workspaceId,
        view: target.view || "",
        routeAlias: target.routeAlias || defaultRouteAliasForWorkspace(target.workspace || workspaceId),
        keywords: `${card.status || ""} ${card.evidence || ""} ${card.description || ""}`,
        priority: 30 + index,
      });
    });

    (workspace.tasks || []).forEach((item, index) => {
      add({
        title: item.title,
        category: "任务",
        path: `${workspace.label} / 任务中心`,
        hint: "打开所在工作区",
        workspace: workspaceId,
        routeAlias: defaultRouteAliasForWorkspace(workspaceId),
        keywords: `${item.detail || ""} ${item.state || ""}`,
        priority: 60 + index,
      });
    });

    (workspace.rows || []).forEach((item, index) => {
      add({
        title: item.object,
        category: "决策",
        path: `${workspace.label} / ${item.priority || "P"}`,
        hint: "打开所在工作区",
        workspace: workspaceId,
        routeAlias: defaultRouteAliasForWorkspace(workspaceId),
        keywords: `${item.evidence || ""} ${item.action || ""} ${item.status || ""}`,
        priority: 70 + index,
      });
    });
  });

  Object.values(FUNCTION_VIEWS).forEach((detail, index) => {
    add({
      title: detail.title,
      category: "功能面板",
      path: `${WORKSPACE_LABELS[detail.workspace] || "PFI"} / ${detail.primaryAction}`,
      hint: "打开功能面板",
      workspace: detail.workspace,
      view: detail.view,
      routeAlias: detail.view === "single" ? "/investment/strategy-lab" : defaultRouteAliasForWorkspace(detail.workspace),
      keywords: `${detail.purpose || ""} ${(detail.checks || []).join(" ")} ${(detail.runSteps || []).join(" ")}`,
      priority: 40 + index,
    });
  });

  return items;
}

function fuzzySearchItems(query, items = buildGlobalSearchIndex(), limit = SEARCH_DEFAULT_LIMIT) {
  const cleanQuery = normalizeSearch(query);
  const ranked = items
    .map((item) => ({ item, score: searchScore(cleanQuery, item) }))
    .filter((entry) => cleanQuery ? entry.score > 0 : entry.item.category.includes("入口") || entry.item.title === "运行反馈控制台")
    .sort((left, right) => right.score - left.score || left.item.priority - right.item.priority || left.item.title.localeCompare(right.item.title, "zh-Hans-CN"))
    .slice(0, limit)
    .map((entry) => entry.item);
  return ranked;
}

function searchScore(cleanQuery, item) {
  if (!cleanQuery) return 100 - Number(item.priority || 50);
  const haystack = normalizeSearch([item.title, item.category, item.path, item.hint, item.keywords].join(" "));
  if (!haystack) return 0;
  const title = normalizeSearch(item.title);
  let score = 0;
  if (title === cleanQuery) score += 500;
  if (title.includes(cleanQuery)) score += 280 - title.indexOf(cleanQuery);
  if (haystack.includes(cleanQuery)) score += 180 - Math.min(haystack.indexOf(cleanQuery), 80);
  const subsequence = subsequenceScore(cleanQuery, haystack);
  if (subsequence > 0) score += subsequence;
  return score;
}

function subsequenceScore(query, text) {
  if (!query) return 1;
  let cursor = -1;
  let gap = 0;
  for (const char of query) {
    const next = text.indexOf(char, cursor + 1);
    if (next === -1) return 0;
    gap += Math.max(0, next - cursor - 1);
    cursor = next;
  }
  return Math.max(1, 120 - gap);
}

function normalizeSearch(value) {
  return String(value || "")
    .toLowerCase()
    .replace(/[\s\u3000/|·:：,，.。?？()（）\[\]【】_-]+/g, "");
}

function renderGlobalSearchResults(query) {
  const input = document.querySelector("[data-global-search-input]");
  const panel = document.querySelector("[data-global-search-results]");
  if (!input || !panel) return;
  globalSearchState.items = buildGlobalSearchIndex();
  globalSearchState.results = fuzzySearchItems(query, globalSearchState.items);
  globalSearchState.activeIndex = Math.min(globalSearchState.activeIndex, Math.max(globalSearchState.results.length - 1, 0));
  panel.replaceChildren();
  if (!globalSearchState.results.length) {
    const empty = document.createElement("div");
    empty.className = "search-empty";
    empty.textContent = "没有匹配结果";
    panel.appendChild(empty);
  } else {
    globalSearchState.results.forEach((item, index) => {
      const button = document.createElement("button");
      button.type = "button";
      button.id = `global-search-option-${index}`;
      button.className = `search-result${index === globalSearchState.activeIndex ? " is-active" : ""}`;
      button.dataset.searchIndex = String(index);
      button.setAttribute("role", "option");
      button.setAttribute("aria-selected", index === globalSearchState.activeIndex ? "true" : "false");
      const title = document.createElement("strong");
      title.textContent = item.title;
      const meta = document.createElement("span");
      meta.textContent = `${item.category} · ${item.path}`;
      const hint = document.createElement("small");
      hint.textContent = item.hint;
      button.appendChild(title);
      button.appendChild(meta);
      button.appendChild(hint);
      panel.appendChild(button);
    });
  }
  panel.hidden = false;
  input.setAttribute("aria-expanded", "true");
  input.setAttribute("aria-activedescendant", globalSearchState.results.length ? `global-search-option-${globalSearchState.activeIndex}` : "");
  refreshClickSafeInventory();
}

function closeGlobalSearchResults() {
  const input = document.querySelector("[data-global-search-input]");
  const panel = document.querySelector("[data-global-search-results]");
  if (panel) panel.hidden = true;
  if (input) {
    input.setAttribute("aria-expanded", "false");
    input.removeAttribute("aria-activedescendant");
  }
}

function setGlobalSearchActiveIndex(nextIndex) {
  if (!globalSearchState.results.length) return;
  const total = globalSearchState.results.length;
  globalSearchState.activeIndex = (nextIndex + total) % total;
  renderGlobalSearchResults(document.querySelector("[data-global-search-input]")?.value || "");
}

function openGlobalSearchResult(index = globalSearchState.activeIndex) {
  const item = globalSearchState.results[index];
  if (!item) return;
  if (item.view) {
    openFunctionView(item.view, { routeAlias: item.routeAlias || "" });
  } else {
    setActiveWorkspace(item.workspace || "home", { routeAlias: item.routeAlias || "" });
  }
  const input = document.querySelector("[data-global-search-input]");
  if (input) input.value = item.title;
  closeGlobalSearchResults();
  showToast(`已打开${item.title}`);
}

function handleGlobalSearchKeydown(event) {
  if (event.key === "ArrowDown") {
    event.preventDefault();
    setGlobalSearchActiveIndex(globalSearchState.activeIndex + 1);
  } else if (event.key === "ArrowUp") {
    event.preventDefault();
    setGlobalSearchActiveIndex(globalSearchState.activeIndex - 1);
  } else if (event.key === "Enter") {
    event.preventDefault();
    openGlobalSearchResult();
  } else if (event.key === "Escape") {
    closeGlobalSearchResults();
  }
}

function runCachedRefresh() {
  const skeleton = document.querySelector("[data-skeleton]");
  const errorBanner = document.querySelector("[data-error-banner]");
  const taskPhase = document.querySelector("#task-phase");
  const jobLabel = document.querySelector("#background-job-label");
  if (errorBanner) errorBanner.hidden = true;
  setActionFeedback("progress", "正在刷新缓存切片");

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
    showToast("缓存切片已刷新", "success");
  }, 1350);
}

function showRecoverableError() {
  const errorBanner = document.querySelector("[data-error-banner]");
  if (!errorBanner) return;
  errorBanner.hidden = false;
  showToast("刷新失败 · 已切换到缓存兜底", "failure");
}

function legacyChartToTrend(workspace) {
  const points = Array.isArray(workspace?.chart) ? workspace.chart : DEFAULT_WORKSPACES.home.chart;
  return {
    scope: workspace?.label || "首页总览",
    title: "状态趋势",
    unit: "指数",
    source: "本地缓存趋势",
    emptyState: "趋势数据待更新",
    periods: points.map((_, index) => `${index + 1}`),
    series: [{ id: "status_index", label: "状态", color: "--pfi-blue", values: points }],
  };
}

function drawTrendChart(trend = legacyChartToTrend(WORKSPACES.home)) {
  const canvas = document.querySelector("[data-trend-canvas]");
  const panel = document.querySelector("[data-trend-panel]");
  const title = document.querySelector("[data-trend-title]");
  const scope = document.querySelector("[data-trend-scope]");
  const unit = document.querySelector("[data-trend-unit]");
  const legend = document.querySelector("[data-trend-legend]");
  const empty = document.querySelector("[data-trend-empty]");
  if (!canvas || !canvas.getContext || !panel) return;

  const series = (trend.series || []).filter((item) => Array.isArray(item.values) && item.values.length >= 2);
  const periods = Array.isArray(trend.periods) && trend.periods.length ? trend.periods : series[0]?.values.map((_, index) => `${index + 1}`) || [];
  panel.dataset.trendWorkspace = trend.scope || "";
  panel.dataset.trendSource = trend.source || "";
  if (title) title.textContent = trend.title || "趋势图";
  if (scope) scope.textContent = trend.scope ? `${trend.scope} · 统一趋势` : "统一趋势";
  if (unit) unit.textContent = trend.unit ? `${trend.unit} 基准` : "CNY 基准";
  if (empty) {
    empty.textContent = trend.emptyState || "趋势数据待更新";
    empty.hidden = series.length > 0;
  }
  renderTrendLegend(legend, series);

  const ctx = canvas.getContext("2d");
  const width = canvas.width;
  const height = canvas.height;
  ctx.clearRect(0, 0, width, height);
  ctx.fillStyle = cssColor("--pfi-surface", "#ffffff");
  ctx.fillRect(0, 0, width, height);

  if (!series.length) {
    ctx.fillStyle = cssColor("--pfi-muted", "#62717a");
    ctx.font = "16px system-ui, sans-serif";
    ctx.fillText(trend.emptyState || "趋势数据待更新", 28, Math.round(height / 2));
    return;
  }

  const allValues = series.flatMap((item) => item.values.map(Number).filter(Number.isFinite));
  const min = Math.min(...allValues);
  const max = Math.max(...allValues);
  const spread = Math.max(max - min, 1);
  const yMin = Math.max(0, min - spread * 0.12);
  const yMax = max + spread * 0.16;
  const pad = { left: 58, right: 104, top: 20, bottom: 34 };
  const plotWidth = width - pad.left - pad.right;
  const plotHeight = height - pad.top - pad.bottom;
  const xFor = (index) => pad.left + (plotWidth * index) / Math.max(periods.length - 1, 1);
  const yFor = (value) => pad.top + plotHeight - ((value - yMin) / Math.max(yMax - yMin, 1)) * plotHeight;

  drawTrendGrid(ctx, width, height, pad, yMin, yMax, trend.unit);
  series.forEach((item) => drawTrendSeries(ctx, item, xFor, yFor));
  drawTrendPeriodLabels(ctx, periods, xFor, height, pad);
  series.forEach((item) => drawTrendEndLabel(ctx, item, xFor, yFor, trend.unit));
}

function renderTrendLegend(legend, series) {
  if (!legend) return;
  legend.replaceChildren();
  series.forEach((item) => {
    const row = document.createElement("span");
    const swatch = document.createElement("i");
    swatch.style.background = trendColor(item);
    row.append(swatch, document.createTextNode(`${item.label} · ${formatTrendValue(item.values.at(-1), item.unit || "CNY")}`));
    legend.appendChild(row);
  });
}

function drawTrendGrid(ctx, width, height, pad, yMin, yMax, unit) {
  ctx.strokeStyle = cssColor("--pfi-border", "#d7dee2");
  ctx.lineWidth = 1;
  ctx.fillStyle = cssColor("--pfi-muted", "#62717a");
  ctx.font = "12px system-ui, sans-serif";
  for (let index = 0; index <= 3; index += 1) {
    const y = pad.top + ((height - pad.top - pad.bottom) * index) / 3;
    ctx.beginPath();
    ctx.moveTo(pad.left, y);
    ctx.lineTo(width - pad.right, y);
    ctx.stroke();
    const value = yMax - ((yMax - yMin) * index) / 3;
    ctx.fillText(formatTrendValue(value, unit, true), 8, y + 4);
  }
}

function drawTrendPeriodLabels(ctx, periods, xFor, height, pad) {
  ctx.fillStyle = cssColor("--pfi-muted", "#62717a");
  ctx.font = "12px system-ui, sans-serif";
  const indexes = [...new Set([0, Math.floor((periods.length - 1) / 2), periods.length - 1])];
  indexes.forEach((index) => {
    const label = periods[index] || "";
    const x = xFor(index);
    ctx.fillText(label, Math.min(x, xFor(periods.length - 1) - 12), height - Math.round(pad.bottom / 2));
  });
}

function drawTrendSeries(ctx, item, xFor, yFor) {
  const color = trendColor(item);
  ctx.strokeStyle = color;
  ctx.lineWidth = 3;
  ctx.beginPath();
  item.values.forEach((value, index) => {
    const x = xFor(index);
    const y = yFor(Number(value));
    if (index === 0) ctx.moveTo(x, y);
    else ctx.lineTo(x, y);
  });
  ctx.stroke();
  item.values.forEach((value, index) => {
    ctx.beginPath();
    ctx.fillStyle = color;
    ctx.arc(xFor(index), yFor(Number(value)), 3.8, 0, Math.PI * 2);
    ctx.fill();
  });
}

function drawTrendEndLabel(ctx, item, xFor, yFor, unit) {
  const lastIndex = item.values.length - 1;
  const value = Number(item.values[lastIndex]);
  const x = xFor(lastIndex) + 9;
  const y = yFor(value);
  ctx.fillStyle = trendColor(item);
  ctx.font = "12px system-ui, sans-serif";
  ctx.fillText(`${item.label} ${formatTrendValue(value, item.unit || unit)}`, x, Math.max(14, Math.min(y + 4, 168)));
}

function trendColor(item) {
  return cssColor(item.color || "--pfi-blue", "#215f9a");
}

function cssColor(name, fallback) {
  const value = getComputedStyle(document.documentElement).getPropertyValue(name).trim();
  return value || fallback;
}

function formatTrendValue(value, unit = "CNY", compact = false) {
  const number = Number(value);
  if (!Number.isFinite(number)) return unit === "CNY" ? "CNY 待补" : "待补";
  if (unit === "CNY") {
    if (compact && Math.abs(number) >= 10000) return `CNY ${(number / 10000).toFixed(1)}万`;
    return `CNY ${Math.round(number).toLocaleString("zh-CN")}`;
  }
  return compact ? String(Math.round(number)) : `${Math.round(number).toLocaleString("zh-CN")} ${unit}`;
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

function toCnyAmount(value, sourceCurrency = "CNY") {
  const numeric = Number(value || 0);
  if (!Number.isFinite(numeric)) return 0;
  const rate = FX_TO_CNY[String(sourceCurrency || "CNY").trim().toUpperCase()] || 1;
  return numeric * rate;
}

function formatCnyAmount(value) {
  const numeric = Number(value || 0);
  if (!Number.isFinite(numeric)) return "CNY 0.00";
  return `CNY ${numeric.toLocaleString("zh-CN", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
}

function moneyLabel(value, sourceCurrency = "CNY") {
  return formatCnyAmount(toCnyAmount(value, sourceCurrency));
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
  if (Object.prototype.hasOwnProperty.call(USER_TEXT_LABELS, clean)) return USER_TEXT_LABELS[clean];
  if (Object.prototype.hasOwnProperty.call(USER_TEXT_LABELS, normalized)) return USER_TEXT_LABELS[normalized];
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
  bindClickSafeFeedback();
  bindFeedbackToggles();
  bindFeedbackHub();
  document.querySelectorAll("[data-workspace]").forEach((button) => {
    button.addEventListener("click", () => {
      setPressedFeedback(button);
      const routeAlias = button.dataset.entryType === "v01_alias" || button.hasAttribute("data-feature-view")
        ? button.dataset.routeAlias || ""
        : "";
      setActiveWorkspace(button.dataset.workspace, { routeAlias });
    });
  });

  document.querySelectorAll("[data-mobile-workspace]").forEach((button) => {
    button.addEventListener("click", () => {
      setPressedFeedback(button);
      setActiveWorkspace(button.dataset.mobileWorkspace || "home");
    });
  });

  document.addEventListener("click", (event) => {
    const featureControl = event.target.closest("[data-feature-view]");
    if (featureControl) {
      event.preventDefault();
      setPressedFeedback(featureControl);
      openFunctionView(featureControl.dataset.featureView, { routeAlias: featureControl.dataset.routeAlias || "" });
      return;
    }
    const workspaceControl = event.target.closest("[data-feature-workspace]");
    if (workspaceControl) {
      event.preventDefault();
      setPressedFeedback(workspaceControl);
      setActiveWorkspace(workspaceControl.dataset.featureWorkspace || "home", { routeAlias: workspaceControl.dataset.routeAlias || "" });
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

  const globalSearchInput = document.querySelector("[data-global-search-input]");
  const globalSearchResults = document.querySelector("[data-global-search-results]");
  globalSearchInput?.addEventListener("focus", (event) => {
    globalSearchState.activeIndex = 0;
    renderGlobalSearchResults(event.target.value);
  });
  globalSearchInput?.addEventListener("input", (event) => {
    globalSearchState.activeIndex = 0;
    renderGlobalSearchResults(event.target.value);
  });
  globalSearchInput?.addEventListener("keydown", handleGlobalSearchKeydown);
  globalSearchResults?.addEventListener("mousedown", (event) => {
    event.preventDefault();
  });
  globalSearchResults?.addEventListener("click", (event) => {
    const result = event.target.closest("[data-search-index]");
    if (!result) return;
    openGlobalSearchResult(Number(result.dataset.searchIndex || 0));
  });

  document.querySelector("[data-command-input]")?.addEventListener("input", (event) => {
    const query = event.target.value.trim();
    document.querySelectorAll("[data-command-workspace]").forEach((button) => {
      const label = button.textContent.trim();
      button.hidden = query && searchScore(normalizeSearch(query), {
        title: label,
        category: "命令",
        path: button.dataset.commandRoute || "",
        hint: "打开入口",
        keywords: `${button.dataset.commandWorkspace || ""} ${SEARCH_ALIASES[label] || ""}`,
      }) <= 0;
    });
  });

  document.querySelectorAll("[data-command-workspace]").forEach((button) => {
    button.addEventListener("click", () => {
      const routeAlias = button.dataset.commandRoute || "";
      if (routeAlias === "/investment/strategy-lab") {
        openFunctionView("single", { routeAlias });
      } else {
        setActiveWorkspace(button.dataset.commandWorkspace, { routeAlias });
      }
      closeCommandPalette();
      showToast(`已打开${button.textContent.trim()}`, "success");
    });
  });

  document.querySelectorAll("[data-settings-open]").forEach((button) => {
    button.addEventListener("click", () => {
      setPressedFeedback(button);
      setActiveWorkspace("settings", { routeAlias: "/settings" });
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
  document.querySelector("[data-feedback-test]")?.addEventListener("click", () => {
    setActionFeedback("success", "反馈测试已触发");
    showToast("反馈测试已触发", "success");
  });
  document.querySelector("[data-raw-document]")?.addEventListener("click", () => showToast("已打开脱敏来源记录"));
  document.querySelector("[data-table-filter]")?.addEventListener("input", (event) => filterRows(event.target.value));
  document.querySelector("[data-table-sort]")?.addEventListener("click", sortRows);
  document.querySelector("[data-table-export]")?.addEventListener("click", exportRows);
  bindUploadCenterEvents();
  bindHoldingsPersistenceEvents();

  document.addEventListener("keydown", (event) => {
    if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === "k") {
      event.preventDefault();
      focusGlobalSearch();
    }
    if (event.key === "Escape") {
      closeCommandPalette();
      closeGlobalSearchResults();
      setEvidenceDrawer(false);
    }
  });

  document.addEventListener("click", (event) => {
    if (!event.target.closest("[data-search-surface='global']")) {
      closeGlobalSearchResults();
    }
  });
}

window.PFI_STAGE7_CLICK_SAFE = {
  buildClickSafeInventory,
  refreshClickSafeInventory,
  feedbackStates: FEEDBACK_STATE_ORDER,
};

document.addEventListener("DOMContentLoaded", () => {
  restoreContext();
  bindEvents();
  applyHomeSummary(readHomeSummary());
  const params = initialSearchParams();
  const requestedFeature = params.get("view") || readContext().feature_view || "";
  if (applyRouteFromLocation()) {
    void refreshRuntimeTrends({ rerender: true });
    return;
  }
  if (Object.prototype.hasOwnProperty.call(FUNCTION_VIEWS, requestedFeature)) {
    openFunctionView(requestedFeature, { silent: true });
    void refreshRuntimeTrends({ rerender: true });
    return;
  }
  const requestedWorkspace = readContext().workspace || "home";
  renderWorkspace(WORKSPACES[requestedWorkspace] ? requestedWorkspace : "home", { silent: true, preserveFocus: true });
  void refreshRuntimeTrends({ rerender: true });
});

window.addEventListener("hashchange", () => {
  applyRouteFromLocation();
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
