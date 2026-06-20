const CONTEXT_STORAGE_KEY = "pfi-context-v1";
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
  来源状态: { workspace: "data", label: "打开来源" },
  公司研究: { workspace: "research", label: "打开研究" },
  基金研究: { workspace: "research", label: "打开研究" },
  政策雷达: { view: "policy", label: "打开政策雷达" },
  报告验证: { view: "reports", label: "打开报告中心" },
  组合暴露: { view: "holdings", label: "打开持仓" },
  集中度风险: { view: "holdings", label: "打开持仓" },
  纪律检查: { view: "profile", label: "打开画像" },
  订单意图: { view: "holdings", label: "打开持仓" },
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
  writeContext({ ...currentContext(), workspace: workspaceId });

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
    const link = document.createElement("a");
    link.className = "workflow-open";
    link.href = legacyViewUrl(target.view);
    link.target = "_top";
    link.dataset.featureView = target.view;
    link.textContent = target.label || "打开功能";
    return link;
  }
  const button = document.createElement("button");
  button.type = "button";
  button.className = "workflow-open";
  button.dataset.featureWorkspace = target.workspace || "home";
  button.textContent = target.label || "打开入口";
  button.addEventListener("click", () => setActiveWorkspace(target.workspace || "home"));
  return button;
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
  const requestedWorkspace = readContext().workspace || "home";
  renderWorkspace(WORKSPACES[requestedWorkspace] ? requestedWorkspace : "home", { silent: true, preserveFocus: true });
});
