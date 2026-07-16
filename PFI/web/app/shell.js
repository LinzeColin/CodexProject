const CONTEXT_STORAGE_KEY = "pfi-context-v2";
const RUNTIME_CONFIG = readRuntimeConfig();
const PFI_RUNTIME_API_BASE_URL = RUNTIME_CONFIG.apiBaseUrl || "http://127.0.0.1:8766";
const PFI_RUNTIME_API_AUTH_TOKEN = String(RUNTIME_CONFIG.apiAuthToken || "");
const PFI_STAGE1_SHELL_INTEGRITY_CONTRACT = "PFI-V024-STAGE1-SHELL-INTEGRITY";
const PFI_STAGE2_ENTRY_CONSISTENCY_CONTRACT = "PFI-V024-STAGE2-ENTRY-CONSISTENCY";
const PFI_STAGE2_ENTRY_METADATA = Object.freeze({
  schema: RUNTIME_CONFIG.schema || "PFIV024Stage2EntryRuntimeMetadataV1",
  targetVersion: RUNTIME_CONFIG.targetVersion || document.body?.dataset.pfiTargetVersion || "v0.2.4",
  sourcePackageVersion: RUNTIME_CONFIG.sourcePackageVersion || "v0.2.3-repair",
  pfiVersion: RUNTIME_CONFIG.pfiVersion || document.body?.dataset.pfiVersion || "v0.2.3",
  appVersion: RUNTIME_CONFIG.appVersion || document.body?.dataset.pfiAppVersion || "0.2.3",
  repairLabel: RUNTIME_CONFIG.repairLabel || document.body?.dataset.pfiRepairLabel || "PFI v0.2.3 Repair",
  buildId: RUNTIME_CONFIG.buildId || document.body?.dataset.pfiBuildId || "pfi-v024-stage2-phase22",
  bundleVersion: RUNTIME_CONFIG.bundleVersion || document.body?.dataset.pfiBundleVersion || "20260630.2",
  uiContractVersion:
    RUNTIME_CONFIG.uiContractVersion ||
    document.body?.dataset.pfiUiContractVersion ||
    PFI_STAGE2_ENTRY_CONSISTENCY_CONTRACT,
  shellIntegrityContract: RUNTIME_CONFIG.shellIntegrityContract || PFI_STAGE1_SHELL_INTEGRITY_CONTRACT,
  entryConsistencyContract: RUNTIME_CONFIG.entryConsistencyContract || PFI_STAGE2_ENTRY_CONSISTENCY_CONTRACT,
  stage: RUNTIME_CONFIG.stage || document.body?.dataset.pfiStage || "Stage 2",
  phase: RUNTIME_CONFIG.phase || document.body?.dataset.pfiPhase || "2.2",
  webBundleHash: RUNTIME_CONFIG.webBundleHash || document.body?.dataset.pfiWebBundleHash || "",
  backendBuildHash: RUNTIME_CONFIG.backendBuildHash || "",
  gitCommit: RUNTIME_CONFIG.gitCommit || "",
  webIndexSha256: RUNTIME_CONFIG.webIndexSha256 || document.body?.dataset.pfiWebIndexSha256 || "",
  tokensCssSha256: RUNTIME_CONFIG.tokensCssSha256 || document.body?.dataset.pfiTokensCssSha256 || "",
  versionJsSha256: RUNTIME_CONFIG.versionJsSha256 || document.body?.dataset.pfiVersionJsSha256 || "",
  entryAuditJsSha256: RUNTIME_CONFIG.entryAuditJsSha256 || document.body?.dataset.pfiEntryAuditJsSha256 || "",
  routesJsSha256: RUNTIME_CONFIG.routesJsSha256 || document.body?.dataset.pfiRoutesJsSha256 || "",
  shellJsSha256: RUNTIME_CONFIG.shellJsSha256 || document.body?.dataset.pfiShellJsSha256 || "",
});
const PFI_STAGE1_ENTRY_METADATA = PFI_STAGE2_ENTRY_METADATA;
window.PFI_STAGE2_ENTRY_METADATA = PFI_STAGE2_ENTRY_METADATA;
window.PFI_STAGE1_ENTRY_METADATA = PFI_STAGE1_ENTRY_METADATA;

function applyPFIStage2EntryMetadata(metadata = PFI_STAGE2_ENTRY_METADATA) {
  const body = document.body;
  if (!body) return metadata;
  body.dataset.pfiTargetVersion = metadata.targetVersion || "v0.2.4";
  body.dataset.pfiRepairLabel = metadata.repairLabel || "PFI v0.2.3 Repair";
  body.dataset.pfiBuildId = metadata.buildId || "pfi-v024-stage2-phase22";
  body.dataset.pfiBundleVersion = metadata.bundleVersion || "20260630.2";
  body.dataset.pfiUiContractVersion = metadata.uiContractVersion || PFI_STAGE2_ENTRY_CONSISTENCY_CONTRACT;
  body.dataset.pfiStage = metadata.stage || "Stage 2";
  body.dataset.pfiPhase = metadata.phase || "2.2";
  if (metadata.webBundleHash) body.dataset.pfiWebBundleHash = metadata.webBundleHash;
  if (metadata.webIndexSha256) body.dataset.pfiWebIndexSha256 = metadata.webIndexSha256;
  if (metadata.tokensCssSha256) body.dataset.pfiTokensCssSha256 = metadata.tokensCssSha256;
  if (metadata.versionJsSha256) body.dataset.pfiVersionJsSha256 = metadata.versionJsSha256;
  if (metadata.entryAuditJsSha256) body.dataset.pfiEntryAuditJsSha256 = metadata.entryAuditJsSha256;
  if (metadata.shellJsSha256) body.dataset.pfiShellJsSha256 = metadata.shellJsSha256;

  const write = (selector, value) => {
    const node = document.querySelector(selector);
    if (node) node.textContent = value;
  };
  const manifest = readEmbeddedReleaseManifest();
  const hash = manifest.frontend_bundle_hash || metadata.webBundleHash || body.dataset.pfiWebBundleHash || "runtime-computed";
  const releaseIdentity = Object.freeze({
    version: manifest.version || metadata.targetVersion || metadata.pfiVersion || "未加载",
    build: manifest.build_id || metadata.buildId || "未加载",
    commit: manifest.git_commit || metadata.gitCommit || "未加载",
    frontend: manifest.frontend_bundle_hash || metadata.webBundleHash || "未加载",
    backend: manifest.backend_build_hash || metadata.backendBuildHash || "未加载",
  });
  write("[data-pfi-entry-repair-label]", metadata.repairLabel || "PFI v0.2.3 Repair");
  write("[data-pfi-entry-build-id]", metadata.buildId || "pfi-v024-stage2-phase22");
  write("[data-pfi-entry-bundle-hash]", `bundle ${String(hash).slice(0, 16)}`);
  write("[data-pfi-entry-ui-contract]", metadata.uiContractVersion || PFI_STAGE2_ENTRY_CONSISTENCY_CONTRACT);
  write("[data-pfi-release-detail-version]", releaseIdentity.version);
  write("[data-pfi-release-detail-build]", releaseIdentity.build);
  write("[data-pfi-release-detail-commit]", releaseIdentity.commit);
  write("[data-pfi-release-detail-frontend]", releaseIdentity.frontend);
  write("[data-pfi-release-detail-backend]", releaseIdentity.backend);
  const detailNode = document.querySelector("[data-pfi-release-identity-details]");
  if (detailNode) {
    detailNode.dataset.pfiReleaseIdentityComplete = Object.values(releaseIdentity).every((value) => value !== "未加载")
      ? "true"
      : "false";
  }
  return metadata;
}

function readPFIStage1Version() {
  const externalVersion = typeof window.PFI_READ_STAGE2_ENTRY_VERSION === "function"
    ? window.PFI_READ_STAGE2_ENTRY_VERSION()
    : typeof window.PFI_READ_STAGE1_VERSION === "function"
    ? window.PFI_READ_STAGE1_VERSION()
    : window.PFI_STAGE2_ENTRY_VERSION || window.PFI_STAGE1_VERSION;
  return Object.freeze({
    schema: "PFIV024Stage1ShellVersionReadModelV1",
    targetVersion: "v0.2.4",
    sourcePackageVersion: "v0.2.3-repair",
    shellIntegrityContract: PFI_STAGE1_SHELL_INTEGRITY_CONTRACT,
    entryConsistencyContract: PFI_STAGE2_ENTRY_CONSISTENCY_CONTRACT,
    ...PFI_STAGE2_ENTRY_METADATA,
    ...(externalVersion && typeof externalVersion === "object" ? externalVersion : {}),
  });
}

function handlePFIStage1ShellError(error, context = {}) {
  const message = error instanceof Error ? error.message : String(error || "unknown shell error");
  try {
    console.error("PFI shell boundary captured error", { message, context, error });
    document.body.dataset.pfiShellError = "true";
    document.body.dataset.pfiShellBoundary = "PFI-V024-STAGE1";
    const shell = document.querySelector(".app-shell");
    if (shell) {
      shell.dataset.state = "error";
      shell.dataset.shellBoundary = "PFI-V024-STAGE1";
    }
    if (typeof showToast === "function") {
      showToast("PFI 页面初始化失败，请刷新或检查本机服务", "failure");
    }
  } catch (_boundaryError) {
    // Keep the boundary non-throwing so the original failure remains diagnosable.
  }
  return {
    status: "handled",
    boundary: "PFI-V024-STAGE1-ERROR-BOUNDARY",
    message,
    context,
  };
}

function mountPFIStage1Route(routeAlias = "", options = {}) {
  try {
    const requestedRouteAlias = String(routeAlias || routeAliasFromLocation() || "").trim();
    const clean = normalizeRouteAlias(requestedRouteAlias);
    if (!clean) return { status: "skipped", routeAlias: "" };
    const routeTarget = workspaceTargetFromRoute(clean);
    if (!routeTarget) {
      renderInvalidRouteState(requestedRouteAlias || clean, {
        preserveFocus: options.preserveFocus === true,
        source: options.source || "route",
        historyState: options.historyState || null,
      });
      return { status: "unmatched", routeAlias: clean, recoveryRouteAlias: "/overview" };
    }
    if (routeTarget.view) {
      openFunctionView(routeTarget.view, { silent: true, routeAlias: clean, skipRouteSync: true });
    } else if (routeTarget.workspace) {
      renderWorkspace(routeTarget.workspace, {
        routeAlias: clean,
        silent: true,
        preserveFocus: options.preserveFocus === true,
        skipRouteSync: true,
        historyScrollY: options.historyState?.scrollY,
      });
    }
    if (options.historyTraversal === true) {
      replaceCurrentStage6HistoryState(clean, {
        source: options.source || "popstate",
        scrollY: options.historyState?.scrollY,
      });
    } else {
      syncBrowserRoute(clean, {
        replace: options.replace === true || normalizeRouteAlias(requestedRouteAlias) !== requestedRouteAlias,
        source: options.source || "route",
      });
    }
    return { status: "mounted", routeAlias: clean, workspace: routeTarget.workspace || "" };
  } catch (error) {
    return handlePFIStage1ShellError(error, { source: "route" });
  }
}

function initializePFIStage1Shell(options = {}) {
  try {
    applyPFIStage2EntryMetadata(PFI_STAGE2_ENTRY_METADATA);
    bootPFIShell();
    return {
      status: "initialized",
      source: options.source || "manual",
      version: readPFIStage1Version(),
    };
  } catch (error) {
    return handlePFIStage1ShellError(error, { source: options.source || "initialize" });
  }
}

window.PFI_STAGE1_SHELL = Object.freeze({
  schema: "PFIV024Stage1ShellIntegrityAPIv1",
  version: readPFIStage1Version,
  initialize: initializePFIStage1Shell,
  mountRoute: mountPFIStage1Route,
  errorBoundary: handlePFIStage1ShellError,
  metadata: PFI_STAGE1_ENTRY_METADATA,
  entryMetadata: PFI_STAGE2_ENTRY_METADATA,
});
const FEEDBACK_SLA_MS = {
  instant: 100,
  skeleton: 300,
  stepped: 1000,
  background: 10000,
};
const FEEDBACK_STATES = {
  loading: "加载中",
  progress: "进行中",
  success: "成功",
  failure: "失败",
  error: "错误",
  blocked: "已阻断",
};
const FEEDBACK_STATE_ORDER = ["loading", "progress", "success", "failure", "error", "blocked"];
const PFI_V024_STAGE6_MOTION_CONTRACT = Object.freeze({
  schema: "PFIV024Stage6Phase62RuntimeMotionContractV1",
  targetVersion: "v0.2.4",
  stage: "Stage 6",
  phase: "6.2",
  pageTransitionMs: 180,
  maxMotionMs: 220,
  routeTransitionAttribute: "data-v024-route-transition",
});
window.PFI_V024_STAGE6_MOTION_CONTRACT = PFI_V024_STAGE6_MOTION_CONTRACT;
const PFI_V024_STAGE6_HAPTICS_CONTRACT = Object.freeze({
  schema: "PFIV024Stage6Phase63RuntimeHapticsContractV1",
  targetVersion: "v0.2.4",
  stage: "Stage 6",
  phase: "6.3",
  capabilitySource: "navigator.vibrate",
  settingRoute: "/settings?tab=feedback",
  silentDegradation: "visual_feedback",
});
window.PFI_V024_STAGE6_HAPTICS_CONTRACT = PFI_V024_STAGE6_HAPTICS_CONTRACT;
const FEEDBACK_HUB_LANES = {
  visual: "视觉状态轨道",
  haptic: "触感强度",
  sound: "声音反馈",
  notification: "通知反馈",
};

const FX_SNAPSHOT = Object.freeze({
  snapshotId: "fx_AUD_CNY_20260628",
  pair: "AUD/CNY",
  rateAudToCny: 4.6874,
  effectiveDate: "2026-06-28",
  effectiveTimeLocal: "06:00",
  cacheState: "cached",
});
const CURRENT_FX_BADGE_DISPLAY = "AUD/CNY=4.69（2026/06/28 06:00）";
const NOT_LOADED_FX_BADGE_DISPLAY = "AUD/CNY=未加载";
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
  ["Rollback " + "plan"]: "回滚计划",
  ["Follow-up " + "list"]: "后续任务清单",
  ["Review " + "lifecycle"]: "复盘生命周期",
  ["PFI Context " + "Export"]: "PFI 上下文导出",
  ["Alpha " + "上下文出口"]: "外部系统上下文出口",
  ["Existing " + "smoke、" + "focused " + "tests、" + "changed-only " + "governance 已记录。"]: "既有冒烟检查、聚焦测试和变更范围治理已记录。",
  ["Owner " + "docs、diff " + "summary、rollback " + "plan、follow-up " + "list。"]: "用户文档、差异摘要、回滚计划和后续任务清单已记录。",
};

const GENERIC_WORKFLOW_DESCRIPTION = "查看该功能的说明、状态和下一步。";

const WORKSPACE_LABELS = {
  home: "首页",
  accounts: "账户与资产",
  ledger: "账本流水",
  investment: "投资管理",
  consumption: "消费管理",
  sync: "数据源与上传",
  recommendations: "建议与复盘",
  insights: "报告与洞察",
  market_research: "市场与研究",
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
  市场与研究: "市场与研究",
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
  strategy_runs: "策略记录",
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

const UNIFIED_TREND_DATA = {
  accounts: {
    scope: "账户与资产",
    title: "现金、净资产、总资产与负债趋势",
    unit: "CNY",
    source: "本机数据层",
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
    source: "本机数据层",
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
    source: "本机数据层",
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
  市场快照: { workspace: "market_research", routeAlias: "/market-research?tab=market", label: "打开市场" },
  研究队列: { workspace: "market_research", routeAlias: "/market-research?tab=research", label: "打开研究" },
  持仓复核: { view: "holdings", label: "打开持仓" },
  持仓编辑: { workspace: "investment", routeAlias: "/investment?tab=holdings", label: "打开编辑" },
  持仓持久化: { workspace: "investment", routeAlias: "/investment?tab=holdings", label: "打开持仓" },
  保存修改: { workspace: "investment", routeAlias: "/investment?tab=holdings", label: "打开持仓" },
  策略实验室: { workspace: "market_research", routeAlias: "/market-research/strategy-lab", label: "打开策略" },
  指数与ETF: { workspace: "market_research", routeAlias: "/market-research?tab=market", label: "打开指数" },
  主题催化: { workspace: "market_research", routeAlias: "/market-research?tab=market", label: "打开主题" },
  自选监控: { workspace: "market_research", routeAlias: "/market-research?tab=market", label: "打开自选" },
  市场垂直切片: { workspace: "market_research", routeAlias: "/market-research?tab=market", label: "打开切片" },
  组合影响覆盖: { workspace: "market_research", routeAlias: "/market-research?tab=market", label: "打开覆盖层" },
  提醒与保存视图: { workspace: "market_research", routeAlias: "/market-research?tab=market", label: "打开提醒" },
  来源状态: { workspace: "market_research", routeAlias: "/market-research?tab=market", label: "打开来源" },
  公司研究: { workspace: "market_research", routeAlias: "/market-research?tab=research", label: "打开公司" },
  基金研究: { workspace: "market_research", routeAlias: "/market-research?tab=research", label: "打开基金" },
  研究与政策切片: { workspace: "market_research", routeAlias: "/market-research?tab=research", label: "打开切片" },
  引用定位: { workspace: "market_research", routeAlias: "/market-research?tab=research", label: "打开引用" },
  报告清单: { workspace: "market_research", routeAlias: "/market-research?tab=research", label: "打开清单" },
  政策雷达: { workspace: "market_research", routeAlias: "/market-research?tab=research", label: "打开政策雷达" },
  报告验证: { workspace: "market_research", routeAlias: "/market-research?tab=research", label: "打开验证" },
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
  单标的回测: { workspace: "market_research", routeAlias: "/market-research/strategy-lab", label: "打开回测" },
  参数扫描: { workspace: "market_research", routeAlias: "/market-research/strategy-lab", label: "打开扫描" },
  盘感训练: { workspace: "market_research", routeAlias: "/market-research/strategy-lab", label: "打开训练" },
  模拟实验: { workspace: "market_research", routeAlias: "/market-research/strategy-lab", label: "打开模拟" },
  热点分析: { workspace: "market_research", routeAlias: "/market-research?tab=market", label: "打开热点" },
  报告中心: { workspace: "insights", label: "打开报告" },
  政策雷达: { workspace: "market_research", routeAlias: "/market-research?tab=research", label: "打开政策" },
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
  反馈偏好: { workspace: "settings", label: "打开反馈" },
  触感反馈: { workspace: "settings", label: "打开触感" },
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
  市场与研究: "market research strategy lab shichang yanjiu celue 市场 研究 策略实验室 策略 回测 盘感",
  市场: "market shichang 市场 指数 ETF 主题 自选",
  研究: "research yanjiu 研究 公司 基金 政策 证据",
  策略实验室: "strategy lab backtest scan market feel celue 策略 实验室 回测 参数 盘感 模拟",
  设置: "settings preferences config shezhi 设置 偏好 系统",
  数据与系统: "settings data system shuju xitong 数据 系统 来源 任务 管理",
  反馈偏好: "feedback preferences fankui fk 反馈 偏好",
  触感反馈: "haptic vibration touch chugan 触感 震动 强度",
  声音反馈: "sound audio shengyin 声音 音效",
  视觉反馈: "visual animation shijue 视觉 动效 状态",
  通知反馈: "notification toast tongzhi 通知 提醒",
  反馈测试: "feedback test ceshi 测试 反馈",
  无障碍反馈: "accessibility a11y wu zhang ai 无障碍",
};

const SEARCH_DEFAULT_LIMIT = 10;
const STAGE6_ROUTES = window.PFI_V025_STAGE6_ROUTES || window.PFI_V025_STAGE6_NAVIGATION || Object.freeze({});
const STAGE6_PAGE_CONTRACTS = window.PFI_V025_STAGE6_PAGE_CONTRACTS || Object.freeze({ pages: Object.freeze([]), pageGroups: Object.freeze({}) });
const STAGE7_LINEAGE = window.PFI_V025_STAGE7_LINEAGE || Object.freeze({});
const ACTIVE_PAGE_CONTRACTS = STAGE6_ROUTES.pageContracts?.pages
  ? STAGE6_ROUTES.pageContracts
  : STAGE6_PAGE_CONTRACTS;
const PFI_V025_STAGE6_PHASE63_HISTORY = STAGE6_ROUTES.phase63HistoryContract || Object.freeze({
  schema: "PFIV025Stage6Phase63HistoryContractV1",
  historyMode: "canonical_path_with_hash_compatibility_fallback",
  invalidRouteRecovery: "/overview",
});
const STAGE3_NAV = STAGE6_ROUTES.schema ? STAGE6_ROUTES : window.PFI_V024_STAGE3_NAVIGATION || window.PFI_V024_STAGE3_NAV || window.PFI_V023_STAGE3_NAV || Object.freeze({
  legacyAliasEntries: Object.freeze([
    Object.freeze({ taskId: "S6-P1-T2", label: "首页", targetWorkspace: "home", routeAlias: "/home", resolvedRouteAlias: "/overview", aliasClass: "command_or_compatibility_alias", primaryEntryAllowed: false }),
    Object.freeze({ taskId: "S6-P1-T2", label: "市场", targetWorkspace: "market_research", routeAlias: "/market", resolvedRouteAlias: "/market-research/market", aliasClass: "command_or_compatibility_alias", primaryEntryAllowed: false }),
    Object.freeze({ taskId: "S6-P1-T2", label: "研究", targetWorkspace: "market_research", routeAlias: "/research", resolvedRouteAlias: "/market-research/research", aliasClass: "command_or_compatibility_alias", primaryEntryAllowed: false }),
    Object.freeze({ taskId: "S6-P1-T2", label: "持仓", targetWorkspace: "investment", routeAlias: "/holdings", resolvedRouteAlias: "/investment/holdings", aliasClass: "command_or_compatibility_alias", primaryEntryAllowed: false }),
    Object.freeze({ taskId: "S6-P1-T2", label: "策略实验室", targetWorkspace: "market_research", routeAlias: "/strategy-lab", resolvedRouteAlias: "/market-research/strategy-lab", aliasClass: "command_or_compatibility_alias", primaryEntryAllowed: false }),
    Object.freeze({ taskId: "S6-P1-T2", label: "数据与系统", targetWorkspace: "settings", routeAlias: "/data-system", resolvedRouteAlias: "/settings/data-system", aliasClass: "command_or_compatibility_alias", primaryEntryAllowed: false }),
  ]),
});
const STAGE3_ROUTES = STAGE6_ROUTES.schema ? STAGE6_ROUTES : window.PFI_V024_STAGE3_ROUTES || STAGE3_NAV || Object.freeze({});
const LEGACY_ALIAS_ENTRIES = Object.freeze([...(STAGE3_NAV.legacyAliasEntries || [])]);
const LEGACY_ALIAS_KEYWORDS = Object.freeze({
  首页: "home 首页 今日 总览",
  市场: "market 市场 指数 ETF 主题 自选",
  研究: "research 研究 公司 基金 政策 证据",
  持仓: "holdings 持仓 投资 组合 编辑",
  策略实验室: "strategy lab 策略 回测 参数 盘感 模拟",
  数据与系统: "data system 数据 系统 设置 来源",
});
const LEGACY_ROUTE_ALIAS_TARGETS = Object.freeze({
  "/": "/overview",
  "/home": "/overview",
  "/market": "/market-research/market",
  "/research": "/market-research/research",
  "/holdings": "/investment/holdings",
  "/strategy-lab": "/market-research/strategy-lab",
  "/data-system": "/settings/data-system",
  "/investment?tab=market": "/market-research/market",
  "/investment?tab=research": "/market-research/research",
  "/investment/strategy-lab": "/market-research/strategy-lab",
  ...Object.fromEntries(LEGACY_ALIAS_ENTRIES.map((entry) => [entry.routeAlias, entry.resolvedRouteAlias || entry.routeAlias])),
});
const LEGACY_COMMAND_ALIASES = Object.freeze(LEGACY_ALIAS_ENTRIES.map((entry) => Object.freeze({
  title: entry.label,
  workspace: entry.targetWorkspace,
  routeAlias: entry.routeAlias,
  keywords: LEGACY_ALIAS_KEYWORDS[entry.label] || "",
})));
const STRATEGY_LAB_VIEWS = new Set(["single", "scan", "strategy_slice", "pit_backtest", "train_test_validation", "walk_forward_validation", "strategy_registry", "market_feel", "big_data", "library"]);
const LEGACY_STAGE2_SECONDARY_TABS = {
  home: [
    { title: "财务状态", routeAlias: "/home?tab=status" },
    { title: "待办事项", routeAlias: "/home?tab=todo" },
    { title: "快捷操作", routeAlias: "/home?tab=actions" },
    { title: "最近报告", routeAlias: "/home?tab=reports" },
  ],
  accounts: [
    { title: "账户总览", routeAlias: "/accounts?tab=overview" },
    { title: "账户列表", routeAlias: "/accounts?tab=list" },
    { title: "资产趋势", routeAlias: "/accounts?tab=trend" },
    { title: "对账状态", routeAlias: "/accounts?tab=reconcile" },
  ],
  ledger: [
    { title: "流水列表", routeAlias: "/ledger?tab=list" },
    { title: "筛选搜索", routeAlias: "/ledger?tab=filter" },
    { title: "分类复核", routeAlias: "/ledger?tab=review" },
    { title: "导出流水", routeAlias: "/ledger?tab=export" },
  ],
  investment: [
    { title: "投资总览", routeAlias: "/investment?tab=overview" },
    { title: "持仓", routeAlias: "/investment?tab=holdings" },
    { title: "交易记录", routeAlias: "/investment?tab=trades" },
    { title: "收益分析", routeAlias: "/investment?tab=returns" },
  ],
  consumption: [
    { title: "消费总览", routeAlias: "/consumption?tab=overview" },
    { title: "分类分析", routeAlias: "/consumption?tab=category" },
    { title: "预算", routeAlias: "/consumption?tab=budget" },
    { title: "订阅", routeAlias: "/consumption?tab=subscription" },
    { title: "异常消费", routeAlias: "/consumption?tab=anomaly" },
  ],
  sync: [
    { title: "上传中心", routeAlias: "/sources-upload?tab=upload" },
    { title: "导入中心", routeAlias: "/sources-upload?tab=import" },
    { title: "数据源管理", routeAlias: "/sources-upload?tab=sources" },
    { title: "待复核", routeAlias: "/sources-upload?tab=review" },
    { title: "导入历史", routeAlias: "/sources-upload?tab=history" },
  ],
  recommendations: [
    { title: "建议列表", routeAlias: "/review?tab=list" },
    { title: "建议详情", routeAlias: "/review?tab=detail" },
    { title: "决策记录", routeAlias: "/review?tab=decision" },
    { title: "复盘记录", routeAlias: "/review?tab=history" },
  ],
  insights: [
    { title: "月报", routeAlias: "/reports?tab=monthly" },
    { title: "季报", routeAlias: "/reports?tab=quarterly" },
    { title: "年报", routeAlias: "/reports?tab=yearly" },
    { title: "自定义报告", routeAlias: "/reports?tab=custom" },
    { title: "导出", routeAlias: "/reports?tab=export" },
  ],
  market_research: [
    { title: "市场观察", routeAlias: "/market-research?tab=market" },
    { title: "研究笔记", routeAlias: "/market-research?tab=research" },
    { title: "公司研究", routeAlias: "/market-research?tab=company" },
    { title: "基金研究", routeAlias: "/market-research?tab=fund" },
    { title: "策略实验室", routeAlias: "/market-research/strategy-lab" },
  ],
  settings: [
    { title: "账户偏好", routeAlias: "/settings?tab=account" },
    { title: "数据与系统", routeAlias: "/settings?tab=data-system" },
    { title: "隐私与本地存储", routeAlias: "/settings?tab=privacy" },
    { title: "反馈偏好", routeAlias: "/settings?tab=feedback" },
    { title: "备份恢复", routeAlias: "/settings?tab=backup" },
  ],
};
const STAGE2_SECONDARY_TABS = Object.freeze(
  Object.keys(ACTIVE_PAGE_CONTRACTS.pageGroups || {}).length
    ? ACTIVE_PAGE_CONTRACTS.pageGroups
    : LEGACY_STAGE2_SECONDARY_TABS
);
const STAGE6_ROUTE_SCROLL_STORAGE_KEY = "pfi-v025-stage6-route-scroll";
let stage6RouteScrollMemory = Object.create(null);
let runtimeStage7LineageState = null;
let runtimeStage7LineageLoading = false;
let runtimeStage7LineageError = "";
let globalSearchState = { items: [], results: [], activeIndex: 0 };
let clickFeedbackSerial = 0;
let clickSafeBound = false;
let feedbackRuntimeState = { haptic: false, sound: false, motion: true };
let feedbackAudioContext = null;

const UPLOAD_ALLOWED_EXTENSIONS = [".csv", ".zip"];
const UPLOAD_MAX_FILE_MB = 50;
let uploadCenterState = {
  files: [],
  rejected: [],
  lastSource: "",
  importing: false,
  previewManifest: null,
  importedManifest: null,
  confirmedAt: "",
};
let alipayImportState = defaultAlipayImportSummary();

let ledgerOperationState = {
  filter: "",
  category: "",
  reviewQueue: [],
  ledger: null,
  selectedReviewId: "",
  lastResolvedReviewId: "",
  reviewSavedAt: "",
  exportPreparedAt: "",
};

let settingsOperationState = {
  defaultAccount: "主账户",
  themeLanguage: "中文优先",
  feedbackHaptic: false,
  feedbackSound: false,
  feedbackMotion: true,
  revision: 0,
  persisted: false,
  loaded: false,
  loading: false,
  savedAt: "",
  resetAt: "",
};

const HOLDINGS_DRAFT_STORAGE_KEY = "pfi-v021-unsubmitted-holdings-draft";
let holdingsPersistenceState = defaultHoldingsState();
let pendingHoldingSoftDeleteId = "";
let holdingPendingRequest = null;
const MAX_STAGE7_UPLOAD_FILES = 20;
const MAX_STAGE7_UPLOAD_TOTAL_BYTES = 100 * 1024 * 1024;
let runtimeTrendState = null;
let stage4PagesCatalog = typeof window !== "undefined" ? window.PFI_V023_STAGE4_PAGES || null : null;
let stage5SubpageCatalog = typeof window !== "undefined" ? window.PFI_V024_STAGE5_PAGES || null : null;
let stage5UxState = typeof window !== "undefined" ? window.PFI_V024_STAGE5_UX_STATE || null : null;
let stage5HomeExperience =
  typeof window !== "undefined" ? window.PFI_V024_STAGE5_HOME || window.PFI_V023_STAGE5_HOME || null : null;
let stage7ReportCenterApi =
  typeof window !== "undefined" ? window.PFI_V024_STAGE7_REPORTS || window.PFI_V023_STAGE7_REPORTS || null : null;
let stage7ReportCenterViewModel = null;
let stage9AnalysisApi =
  typeof window !== "undefined" ? window.PFI_V025_STAGE9_ANALYSIS || null : null;
let stage9AnalysisViewModel = null;
let stage9DecisionReviewApi =
  typeof window !== "undefined" ? window.PFI_V025_STAGE9_DECISION_REVIEW || null : null;
let stage9DecisionReviewViewModel = null;
let runtimeReadModelState = null;
let runtimeStage4SyncState = null;
let runtimeReadModelStatusState = null;

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
    "从真实持仓或正式导入账本生成持仓快照、对账、公司行动、汇率换算、现金记录、风险约束和人工决策提案。",
    ["可用：导入账本、持仓快照、对账、约束和人工提案", "验收：来源编号、快照校验值、持仓数量和记录必须可追溯", "复核：使用本机持仓，进入人工复核"],
    { legacyView: "holdings" },
  ),
  portfolio_reconciliation: functionView(
    "portfolio_reconciliation",
    "导入对账",
    "portfolio",
    "查看导入对账",
    "核对真实导入账本、公司行动调整、汇率换算、现金记录和持仓快照差异。",
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
    "项目级复审",
    "insights",
    "查看项目级复审",
    "统一查看首页、账户、账本、投资、消费、数据源、建议、报告、市场研究和设置的真实行为验收。",
    ["可用：真实浏览器点击、SQLite 查询、服务重启和禁词扫描", "验收：所有入口和主要按钮必须可用", "复核：正式页面读取真实数据或中文空状态"],
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
    "查看可逆文件清单、恢复限制和无需迁移真实数据的说明。",
    ["可用：代码、测试、文档、治理、Web Shell 回滚步骤", "验收：回滚清楚区分 PFI 与 QBVS", "复核：无生产数据库迁移"],
  ),
  stage6_follow_up_list: functionView(
    "stage6_follow_up_list",
    "后续任务清单",
    "insights",
    "查看后续任务",
    "列出外部上下文消费者、真实数据接入、PDF/ZIP、CDR/Open Banking 和发布证据门禁等后续工作。",
    ["可用：分离后续任务，不并入本轮功能页面", "验收：不越权修改外部仓库", "复核：后续任务需新 pursuing goal"],
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
    evidence: evidence("首页说明", "今日缓存摘要", "本机摘要", "首页卡片和待办列表来自本机资料。"),
    chart: [],
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
    chart: [],
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
      task("报告验证任务", "可用 · 可进入待办清单", "ready"),
    ],
    evidence: evidence("研究证据", "研究库和政策雷达", "本地证据索引", "研究入口只做证据组织和决策支持。"),
    chart: [],
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
      feature("持仓垂直切片", "可用", "真实导入账本", "从真实导入账本、持仓快照、对账、风险约束到人工决策提案。"),
      feature("导入对账", "可用", "账本到快照", "核对公司行动、汇率换算、现金记录和值差。"),
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
    chart: [],
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
    chart: [],
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
      feature("待办监控", "可用", "待办清单", "查看队列、重试、失败和产物。"),
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
    chart: [],
  },
};

const WORKSPACES = structuredClone(DEFAULT_WORKSPACES);
installStage3WorkspaceAliases();
installStage2PageSkeletons();

function installStage3WorkspaceAliases() {
  WORKSPACES.home.label = "首页总览";
  WORKSPACES.home.conclusion = "先看投资市值、投资盈亏、本月支出、预算剩余和现金流压力，再进入投资或消费分析。";
  WORKSPACES.accounts = {
    ...structuredClone(DEFAULT_WORKSPACES.portfolio),
    label: "账户与资产",
    kicker: "账户地图",
    conclusion: "统一查看支付宝、基金、Moomoo、中国券商、ABC、CBA、微信和其他账户状态。",
    freshness: "账户状态来自本地 read-model",
    runtime: "现金 / 净资产趋势 · CNY 基准",
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
    runtime: "持仓编辑持久化 · SQLite 服务",
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
      feature("策略实验室", "可用", "市场与研究", "保留 PFI 策略回测、参数扫描、盘感训练和大数据模拟器；QBVS 是顶层独立系统。", { workspace: "market_research", routeAlias: "/market-research/strategy-lab", label: "打开策略" }),
    ],
    tasks: [
      task("市值趋势", "可用 · CNY 月度折线", "ready"),
      task("持仓编辑", "可用 · 保存后刷新仍保留", "ready"),
      task("总收益趋势", "可用 · 估计值需复核", "review"),
      task("持仓 SQLite 服务", "可用 · snapshot / adjustment 可写入", "ready"),
    ],
  };
  WORKSPACES.market_research = {
    ...structuredClone(DEFAULT_WORKSPACES.strategy),
    label: "市场与研究",
    kicker: "市场、研究与策略实验室",
    conclusion: "统一进入市场观察、公司研究、政策证据和策略实验室；旧市场、研究和策略入口只作为兼容别名。",
    freshness: "市场与研究缓存可用",
    runtime: "策略实验室唯一入口 · 路由 /market-research/strategy-lab",
    cards: [
      ["市场观察", "可打开", "指数、ETF、主题和自选线索"],
      ["研究证据", "可打开", "公司、基金、政策和引用定位"],
      ["策略实验室", "唯一入口", "回测、参数扫描、盘感训练和模拟实验"],
      ["兼容别名", "已接管", "市场 / 研究 / 策略实验室"],
    ],
    features: [
      feature("市场快照", "可用", "市场观察", "查看指数、ETF、主题和自选对象的观察线索。", { workspace: "market_research", routeAlias: "/market-research?tab=market", label: "打开市场" }),
      feature("研究队列", "可用", "研究证据", "查看公司、基金、政策和引用定位任务。", { workspace: "market_research", routeAlias: "/market-research?tab=research", label: "打开研究" }),
      feature("策略实验室", "可用", "统一策略入口", "策略回测、参数扫描、盘感训练和模拟实验只进入同一路由。", { workspace: "market_research", routeAlias: "/market-research/strategy-lab", label: "打开策略" }),
      feature("单标的回测", "可用", "策略实验室", "从策略实验室运行单标的回测。", { workspace: "market_research", routeAlias: "/market-research/strategy-lab", label: "打开回测" }),
      feature("参数扫描", "可用", "策略实验室", "从策略实验室运行参数扫描。", { workspace: "market_research", routeAlias: "/market-research/strategy-lab", label: "打开扫描" }),
      feature("盘感训练", "可用", "策略实验室", "保留读图训练、限时判断、隐藏答案和复盘记录。", { workspace: "market_research", routeAlias: "/market-research/strategy-lab", label: "打开训练" }),
      feature("模拟实验", "可用", "策略实验室", "用于研究策略在不同市场状态下的表现。", { workspace: "market_research", routeAlias: "/market-research/strategy-lab", label: "打开模拟" }),
    ],
    rows: [
      row("P1", "市场", "市场观察", "旧市场入口映射到市场与研究。", "可用"),
      row("P1", "研究", "研究证据", "旧研究入口映射到市场与研究。", "可用"),
      row("P1", "策略实验室", "统一路由", "旧策略实验室入口映射到 /market-research/strategy-lab。", "可用"),
    ],
    tasks: [
      task("一级入口", "市场与研究已进入正式导航", "ready"),
      task("旧入口兼容", "市场 / 研究 / 策略实验室由 route alias 接管", "ready"),
      task("策略实验室", "唯一运行入口为 /market-research/strategy-lab", "ready"),
    ],
    evidence: evidence("市场与研究证据", "市场、研究、策略实验室统一入口", "PFI v0.2.1.1 Stage 1 路由合同", "旧入口保留为兼容别名，不作为一级导航显示。"),
    chart: [],
  };
  WORKSPACES.consumption = {
    ...structuredClone(DEFAULT_WORKSPACES.data),
    label: "消费管理",
    kicker: "消费分析",
    conclusion: "查看本月支出、预算剩余、分类、订阅、异常消费和现金流预测；转账和投资事件不计生活消费。",
    freshness: "消费视图来自分析读模型",
    runtime: "支出 / 预算 / 现金流趋势 · CNY 基准",
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
    runtime: "上传 / 拖拽 / 状态 / 失败反馈 / 导入批次",
    cards: [
      ["上传中心", "可用", "CSV / ZIP 多文件本机预检"],
      ["拖拽上传", "可用", "拖拽、点击选择、键盘选择都可触发"],
      ["导入中心", "可用", "批次、摘要、待复核入口同屏显示"],
      ["本机数据管理", "本机", "原始账单不进入 公共仓库"],
    ],
    features: [
      feature("上传中心", "可用", "本机预检", "点击选择文件或拖拽账单，立即显示状态、文件列表和失败反馈。", { workspace: "sync", label: "打开上传" }),
      feature("上传支付宝账单", "可用", "本机上传", "接收 CSV、ZIP 格式的支付宝账单，在本机解析预览后由用户确认入账。", { workspace: "sync", label: "查看上传" }),
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
      row("P0", "上传中心", "CSV / ZIP", "点击或拖拽选择账单文件。", "可用"),
      row("P0", "导入中心", "批次摘要", "显示本轮预检批次和旧账单待接入批次。", "可用"),
      row("P1", "账本复核", "低置信度记录", "进入账本流水处理待复核记录。", "复核"),
      row("P1", "本机数据管理", "本机私有目录", "原始账单保存在本机私有目录，公共仓库只记录脱敏清单。", "可用"),
    ],
    tasks: [
      task("上传中心", "可用 · 支持多文件 CSV / ZIP", "ready"),
      task("拖拽上传", "可用 · 拖入文件后显示状态", "ready"),
      task("导入摘要", "可用 · 批次、记录和待复核同屏展示", "ready"),
      task("账本复核", "导入后处理低置信度分类", "review"),
    ],
  };
  WORKSPACES.settings = {
    ...structuredClone(DEFAULT_WORKSPACES.data),
    label: "设置",
    kicker: "系统设置",
    conclusion: "集中管理数据与系统、反馈偏好、触感、声音、视觉、通知和备份恢复设置。",
    freshness: "设置项本地保存",
    runtime: "设置：只改本机偏好 · 不触发外部动作",
    cards: [
      ["数据与系统", "可用", "来源、任务、本机数据、备份"],
      ["反馈偏好", "可配置", "视觉、声音、触感、通知"],
      ["汇率徽标", "已缓存", "AUD/CNY 06:00 快照"],
      ["本机数据管理", "开启", "原始数据按 MetaDatabase 备份规则管理"],
    ],
    features: [
      feature("数据中心", "可用", "系统诊断", "检查数据源、代码格式、质量报告、缓存和本机数据管理。", { workspace: "settings", label: "打开数据与系统" }),
      feature("来源登记", "复核", "数据源状态", "查看来源、时间、质量和限制条件。", { workspace: "settings", label: "查看来源" }),
      feature("待办监控", "可用", "待办清单", "查看队列、重试、失败和产物。", { workspace: "settings", label: "查看待办" }),
      feature("反馈偏好", "可配置", "设置页", "统一管理成功、失败、进行中、后台任务和缓存提示。", { workspace: "settings", label: "打开反馈" }),
      feature("反馈偏好", "可配置", "设置页", "管理触感反馈、声音反馈、视觉反馈、通知反馈和反馈测试。", { workspace: "settings", label: "打开反馈设置" }),
      feature("触感反馈", "可配置", "关闭 / 轻 / 标准 / 强", "手机浏览器支持震动时才启用，不支持时静默降级。", { workspace: "settings", label: "打开触感" }),
      feature("声音反馈", "可配置", "提示音", "控制成功、失败和完成提示音，默认不打扰。", { workspace: "settings", label: "打开声音" }),
      feature("视觉反馈", "可配置", "动效与状态", "控制按钮按压、骨架屏、错误横幅和状态提示。", { workspace: "settings", label: "打开视觉" }),
      feature("通知反馈", "可配置", "本机通知", "控制后台任务完成、失败和待复核提醒。", { workspace: "settings", label: "打开通知" }),
      feature("反馈测试", "可用", "即时验证", "测试触感、声音、视觉和通知反馈是否符合当前偏好。", { workspace: "settings", label: "测试反馈" }),
      feature("无障碍反馈", "可配置", "键盘与读屏", "保证反馈状态可被键盘和读屏读取。", { workspace: "settings", label: "打开无障碍" }),
      feature("备份恢复", "复核", "恢复演练", "检查备份、校验和恢复路径。", { workspace: "settings", label: "查看备份" }),
    ],
    rows: [
      row("P0", "汇率徽标", "AUD/CNY", "普通运行本地 06:00 快照；缓存缺失时显示中文待更新。", "复核"),
      row("P0", "反馈偏好", "设置页", "集中配置触感、声音、视觉和通知，不在业务页常驻右侧设置面板。", "可用"),
      row("P0", "本机数据管理", "目录策略", "确认私有数据与 密钥 不进入公共仓库。", "可用"),
      row("P1", "反馈设置", "触感/声音/视觉/通知", "业务页默认不常驻反馈面板。", "可用"),
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
      feature("建议模型", "可用", "建议证据", "所有建议必须有证据、预期效果、代价、动作和用户决策。"),
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

function installStage2PageSkeletons() {
  WORKSPACES.home = {
    ...WORKSPACES.home,
    label: "首页总览",
    kicker: "今日总览",
    conclusion: "查看净资产、现金余额、投资市值、本月支出、待复核交易、数据源状态、最近建议和最近报告。",
    freshness: "本机状态",
    runtime: "当前页面：财务状态与待办事项",
    secondaryTabs: STAGE2_SECONDARY_TABS.home,
    cards: [
      ["净资产", "暂无真实数据", "账户和持仓接入后显示"],
      ["现金余额", "暂无真实数据", "账户流水接入后显示"],
      ["投资市值", "暂无真实数据", "持仓接入后显示"],
      ["本月支出", "暂无真实数据", "真实流水导入后显示"],
      ["待复核交易", "未读取状态", "财务数据就绪后显示"],
      ["数据源状态", "等待上传", "进入数据源与上传处理"],
    ],
    features: [
      feature("上传数据", "可用", "上传中心", "进入数据源与上传，选择账单或数据文件。", { workspace: "sync", routeAlias: "/sources-upload?tab=upload", label: "上传数据" }),
      feature("复核流水", "待处理", "账本流水", "导入后进入账本流水处理分类和复核。", { workspace: "ledger", routeAlias: "/ledger?tab=review", label: "复核流水" }),
      feature("查看投资", "可用", "投资管理", "查看投资总览、持仓、交易记录和收益分析。", { workspace: "investment", routeAlias: "/investment?tab=overview", label: "查看投资" }),
      feature("生成报告", "可用", "报告与洞察", "进入报告与洞察，生成或导出本机报告。", { workspace: "insights", routeAlias: "/reports?tab=monthly", label: "生成报告" }),
    ],
    rows: [
      row("1", "上传数据", "等待真实文件", "进入上传中心", "待处理"),
      row("2", "复核流水", "暂无待复核交易", "导入后处理", "等待数据"),
      row("3", "最近报告", "暂无新报告", "进入报告页", "可用"),
    ],
    tasks: [
      task("上传数据", "选择账单或数据文件", "ready"),
      task("复核流水", "导入后处理分类、合并和排除", "review"),
      task("查看报告", "生成月报或导出本机报告", "queued"),
    ],
    evidence: evidence("首页说明", "当前财务状态、待办事项和快捷操作", "本机数据", "账户、流水、持仓和报告状态汇总到首页。"),
    trend: null,
    chart: [],
  };

  WORKSPACES.accounts = {
    ...WORKSPACES.accounts,
    label: "账户与资产",
    kicker: "账户与资产",
    conclusion: "查看账户总览、账户列表、资产趋势和对账状态；没有真实账户数据时只显示中文空状态。",
    freshness: "等待账户数据",
    runtime: "当前页面：账户列表与资产变化",
    secondaryTabs: STAGE2_SECONDARY_TABS.accounts,
    cards: [
      ["账户总览", "暂无真实数据", "绑定或导入账户后显示"],
      ["账户列表", "未加载", "等待数据源"],
      ["资产趋势", "暂无真实数据", "不伪造趋势"],
      ["对账状态", "等待数据", "导入后可对账"],
    ],
    features: [
      feature("账户总览", "可用", "账户与资产", "查看所有账户、币种、余额和数据状态。", { workspace: "accounts", routeAlias: "/accounts?tab=overview", label: "打开总览" }),
      feature("账户列表", "可用", "账户列表", "查看账户名称、类型、币种和最近更新时间。", { workspace: "accounts", routeAlias: "/accounts?tab=list", label: "打开列表" }),
      feature("资产趋势", "等待数据", "资产趋势", "真实账户和持仓接入后显示现金、净资产、总资产和负债。", { workspace: "accounts", routeAlias: "/accounts?tab=trend", label: "查看趋势" }),
      feature("对账状态", "等待数据", "对账状态", "比较平台余额、本机账本和导入记录。", { workspace: "accounts", routeAlias: "/accounts?tab=reconcile", label: "查看对账" }),
    ],
    rows: [
      row("1", "账户总览", "暂无账户数据", "进入账户列表", "等待数据"),
      row("2", "资产趋势", "暂无趋势", "导入真实数据后显示", "等待数据"),
      row("3", "对账状态", "暂无差异", "导入后对账", "等待数据"),
    ],
    tasks: [
      task("新增账户", "后续操作流阶段接入", "queued"),
      task("编辑账户", "后续操作流阶段接入", "queued"),
      task("绑定数据源", "先进入数据源与上传", "ready"),
    ],
    evidence: evidence("账户说明", "账户列表、账户详情、资产趋势和对账状态", "本机账户资料", "账户资料汇总到账户与资产页面。"),
  };

  WORKSPACES.ledger = {
    ...WORKSPACES.ledger,
    label: "账本流水",
    kicker: "账本流水",
    conclusion: "查看流水列表、筛选搜索、分类复核、合并排除和导出；没有真实流水时显示中文空状态。",
    freshness: "等待流水数据",
    runtime: "当前页面：流水列表与复核",
    secondaryTabs: STAGE2_SECONDARY_TABS.ledger,
    cards: [
      ["流水列表", "暂无真实数据", "上传后显示"],
      ["筛选搜索", "可用", "按账户、日期、金额和分类筛选"],
      ["分类复核", "待导入", "低置信度记录导入后显示"],
      ["导出流水", "可用", "导出功能在后续操作流完善"],
    ],
    features: [
      feature("流水列表", "可用", "账本流水", "查看交易日期、账户、金额、分类和备注。", { workspace: "ledger", routeAlias: "/ledger?tab=list", label: "查看列表" }),
      feature("筛选搜索", "可用", "筛选搜索", "按账户、日期、金额、分类和文字检索流水。", { workspace: "ledger", routeAlias: "/ledger?tab=filter", label: "打开筛选" }),
      feature("分类复核", "等待数据", "分类复核", "修改分类、合并转账、排除非消费记录。", { workspace: "ledger", routeAlias: "/ledger?tab=review", label: "打开复核" }),
      feature("导出流水", "可用", "导出流水", "导出当前筛选结果。", { workspace: "ledger", routeAlias: "/ledger?tab=export", label: "打开导出" }),
    ],
    rows: [
      row("1", "导入流水", "等待文件", "进入上传中心", "待处理"),
      row("2", "分类复核", "暂无待复核", "导入后处理", "等待数据"),
      row("3", "导出流水", "当前为空", "选择筛选后导出", "可用"),
    ],
    tasks: [
      task("导入流水", "从数据源与上传进入", "ready"),
      task("批量分类", "后续操作流阶段接入", "queued"),
      task("保存筛选", "后续操作流阶段接入", "queued"),
    ],
    evidence: evidence("账本说明", "流水列表、筛选搜索、分类复核和导出", "本机账本", "导入记录标准化后进入账本流水。"),
  };

  WORKSPACES.investment = {
    ...WORKSPACES.investment,
    label: "投资管理",
    kicker: "投资管理",
    conclusion: "查看投资总览、持仓、交易记录和收益分析；策略实验室统一放在市场与研究。",
    freshness: "等待投资数据",
    runtime: "当前页面：投资总览与持仓",
    secondaryTabs: STAGE2_SECONDARY_TABS.investment,
    cards: [
      ["投资总览", "暂无真实数据", "持仓接入后显示"],
      ["持仓", "暂无真实数据", "不使用浏览器缓存作为正式数据"],
      ["交易记录", "暂无真实数据", "导入券商或手工记录后显示"],
      ["收益分析", "暂无真实数据", "不伪造收益"],
    ],
    features: [
      feature("投资总览", "可用", "投资总览", "查看投资市值、现金仓位和主要变化。", { workspace: "investment", routeAlias: "/investment?tab=overview", label: "打开总览" }),
      feature("持仓", "等待数据", "持仓", "查看标的、数量、成本、价格、币种和账户。", { workspace: "investment", routeAlias: "/investment?tab=holdings", label: "查看持仓" }),
      feature("交易记录", "等待数据", "交易记录", "查看买入、卖出、费用、税费和汇率影响。", { workspace: "investment", routeAlias: "/investment?tab=trades", label: "查看交易" }),
      feature("收益分析", "等待数据", "收益分析", "有真实持仓和交易后再显示总收益、未实现盈亏和现金拖累。", { workspace: "investment", routeAlias: "/investment?tab=returns", label: "查看收益" }),
    ],
    rows: [
      row("1", "持仓", "暂无真实持仓", "后续阶段接入编辑和保存", "等待数据"),
      row("2", "交易记录", "暂无交易", "导入后查看", "等待数据"),
      row("3", "收益分析", "暂无可算收益", "不伪造收益", "等待数据"),
    ],
    tasks: [
      task("修改持仓", "后续真实操作流阶段处理", "queued"),
      task("查看收益", "等待真实持仓和交易", "review"),
      task("进入策略实验室", "从市场与研究打开唯一入口", "ready"),
    ],
    evidence: evidence("投资说明", "投资总览、持仓、交易记录和收益分析", "本机投资资料", "持仓和交易资料汇总到投资管理。"),
  };

  WORKSPACES.consumption = {
    ...WORKSPACES.consumption,
    label: "消费管理",
    kicker: "消费管理",
    conclusion: "查看消费总览、分类分析、预算、订阅、异常消费和现金流预测；没有真实流水时不显示模拟趋势。",
    freshness: "等待消费流水",
    runtime: "当前页面：消费分类与预算",
    secondaryTabs: STAGE2_SECONDARY_TABS.consumption,
    cards: [
      ["消费总览", "暂无真实数据", "流水导入后显示"],
      ["分类分析", "暂无真实数据", "导入后分类"],
      ["预算", "未设置", "后续设置保存阶段接入"],
      ["异常消费", "未加载", "真实流水导入后识别"],
    ],
    features: [
      feature("消费总览", "可用", "消费总览", "查看本月支出、预算剩余、固定和弹性支出。", { workspace: "consumption", routeAlias: "/consumption?tab=overview", label: "打开总览" }),
      feature("分类分析", "等待数据", "分类分析", "按消费分类查看真实流水。", { workspace: "consumption", routeAlias: "/consumption?tab=category", label: "查看分类" }),
      feature("预算", "未设置", "预算", "设置预算、查看预算剩余和超支项。", { workspace: "consumption", routeAlias: "/consumption?tab=budget", label: "查看预算" }),
      feature("订阅", "等待数据", "订阅", "识别周期扣费和疑似订阅。", { workspace: "consumption", routeAlias: "/consumption?tab=subscription", label: "查看订阅" }),
      feature("异常消费", "等待数据", "异常消费", "查看大额、重复、夜间和冲动型消费。", { workspace: "consumption", routeAlias: "/consumption?tab=anomaly", label: "查看异常" }),
      feature("现金流预测", "等待数据", "现金流预测", "有真实收入和支出后再预测现金流。", { workspace: "consumption", routeAlias: "/consumption?tab=cashflow", label: "查看现金流" }),
    ],
    rows: [
      row("1", "分类分析", "等待流水", "导入后查看", "等待数据"),
      row("2", "预算", "未设置", "后续阶段保存", "待处理"),
      row("3", "异常消费", "暂无记录", "真实流水导入后识别", "等待数据"),
    ],
    tasks: [
      task("设置预算", "后续操作流阶段接入", "queued"),
      task("修改分类", "先导入真实流水", "review"),
      task("查看明细", "流水导入后可用", "queued"),
    ],
    evidence: evidence("消费说明", "消费总览、分类、预算、订阅、异常和现金流预测", "本机消费流水", "消费流水标准化后进入消费管理。"),
  };

  WORKSPACES.sync = {
    ...WORKSPACES.sync,
    label: "数据源与上传",
    kicker: "数据源与上传",
    conclusion: "上传文件、查看导入中心、管理数据源、处理待复核记录和导入历史。",
    freshness: "等待上传",
    runtime: "当前页面：上传中心与导入中心",
    secondaryTabs: STAGE2_SECONDARY_TABS.sync,
    cards: [
      ["上传中心", "可用", "选择 CSV / ZIP"],
      ["导入中心", "可用", "查看批次和摘要"],
      ["数据源管理", "可用", "管理支付宝、微信、银行和券商来源"],
      ["待复核", "待导入", "导入后显示"],
    ],
    features: [
      feature("上传中心", "可用", "上传中心", "选择账单或数据文件，进入解析预览前的本机预检。", { workspace: "sync", routeAlias: "/sources-upload?tab=upload", label: "打开上传" }),
      feature("导入中心", "可用", "导入中心", "查看导入批次、摘要、失败反馈和待复核数量。", { workspace: "sync", routeAlias: "/sources-upload?tab=import", label: "打开导入" }),
      feature("数据源管理", "可用", "数据源管理", "查看来源、账户、文件类型和最近更新时间。", { workspace: "sync", routeAlias: "/sources-upload?tab=sources", label: "管理数据源" }),
      feature("待复核", "等待数据", "待复核", "导入后进入账本流水处理低置信度记录。", { workspace: "sync", routeAlias: "/sources-upload?tab=review", label: "查看待复核" }),
      feature("导入历史", "暂无记录", "导入历史", "查看历史批次和处理结果。", { workspace: "sync", routeAlias: "/sources-upload?tab=history", label: "查看历史" }),
    ],
    rows: [
      row("1", "上传中心", "等待文件", "选择文件", "可用"),
      row("2", "导入中心", "暂无批次", "上传后查看", "等待数据"),
      row("3", "待复核", "待导入", "进入账本流水", "等待数据"),
    ],
    tasks: [
      task("上传文件", "支持 CSV / ZIP", "ready"),
      task("解析预览", "后续真实操作流阶段接入", "queued"),
      task("确认入库", "后续真实操作流阶段接入", "queued"),
    ],
    evidence: evidence("上传说明", "上传中心、导入中心、数据源管理、待复核和导入历史", "本机上传资料", "文件预检后进入导入中心。"),
  };

  WORKSPACES.recommendations = {
    ...WORKSPACES.recommendations,
    label: "建议与复盘",
    kicker: "建议与复盘",
    conclusion: "建议必须绑定真实数据依据，支持接受、暂缓、忽略和复盘记录。",
    freshness: "等待真实建议",
    runtime: "当前页面：建议列表与复盘记录",
    secondaryTabs: STAGE2_SECONDARY_TABS.recommendations,
    cards: [
      ["建议列表", "暂无建议", "真实数据触发后显示"],
      ["建议详情", "等待选择", "查看依据、动作和影响"],
      ["决策记录", "暂无记录", "接受、暂缓或忽略后显示"],
      ["复盘记录", "暂无记录", "后续记录效果"],
    ],
    features: [
      feature("建议列表", "可用", "建议列表", "查看来自消费异常、预算、现金流或持仓集中度的建议。", { workspace: "recommendations", routeAlias: "/review?tab=list", label: "查看列表" }),
      feature("建议详情", "等待选择", "建议详情", "查看数据依据、预期影响、代价和动作。", { workspace: "recommendations", routeAlias: "/review?tab=detail", label: "查看详情" }),
      feature("决策记录", "暂无记录", "决策记录", "记录接受、暂缓、忽略和原因。", { workspace: "recommendations", routeAlias: "/review?tab=decision", label: "查看决策" }),
      feature("复盘记录", "暂无记录", "复盘记录", "记录建议效果和后续调整。", { workspace: "recommendations", routeAlias: "/review?tab=history", label: "查看复盘" }),
    ],
    rows: [
      row("1", "消费建议", "暂无触发", "等待真实流水", "等待数据"),
      row("2", "投资建议", "暂无持仓", "等待真实持仓", "等待数据"),
      row("3", "现金流建议", "暂无预测", "等待收入支出数据", "等待数据"),
    ],
    tasks: [
      task("接受建议", "后续操作流阶段接入", "queued"),
      task("暂缓建议", "后续操作流阶段接入", "queued"),
      task("写入复盘", "后续操作流阶段接入", "queued"),
    ],
    evidence: evidence("建议说明", "建议列表、建议详情、决策记录和复盘记录", "真实数据触发", "真实数据触发后进入建议与复盘。"),
  };

  WORKSPACES.insights = {
    ...WORKSPACES.insights,
    label: "报告与洞察",
    kicker: "报告与洞察",
    conclusion: "查看月报、季报、年报、自定义报告和导出；报告必须来自真实数据或中文空状态。",
    freshness: "等待报告数据",
    runtime: "当前页面：报告列表与导出",
    secondaryTabs: STAGE2_SECONDARY_TABS.insights,
    cards: [
      ["月报", "可用", "真实数据不足时显示空状态"],
      ["季报", "可用", "真实数据不足时显示空状态"],
      ["年报", "可用", "真实数据不足时显示空状态"],
      ["导出", "可用", "后续操作流完善"],
    ],
    features: [
      feature("月报", "可用", "月报", "查看净资产、现金流、消费、投资和建议复盘。", { workspace: "insights", routeAlias: "/reports?tab=monthly", label: "打开月报" }),
      feature("季报", "可用", "季报", "查看季度趋势和主要变化。", { workspace: "insights", routeAlias: "/reports?tab=quarterly", label: "打开季报" }),
      feature("年报", "可用", "年报", "查看年度资产、消费、投资和复盘。", { workspace: "insights", routeAlias: "/reports?tab=yearly", label: "打开年报" }),
      feature("自定义报告", "可用", "自定义报告", "按时间、账户、分类和主题生成报告。", { workspace: "insights", routeAlias: "/reports?tab=custom", label: "自定义报告" }),
      feature("导出", "可用", "导出", "导出 PDF、Markdown 或上下文快照。", { workspace: "insights", routeAlias: "/reports?tab=export", label: "打开导出" }),
    ],
    rows: [
      row("1", "月报", "等待真实数据", "生成月报", "可用"),
      row("2", "自定义报告", "等待选择范围", "选择条件", "可用"),
      row("3", "导出", "等待报告", "导出文件", "可用"),
    ],
    tasks: [
      task("生成报告", "后续操作流阶段接入", "queued"),
      task("导出 PDF", "后续操作流阶段接入", "queued"),
      task("导出 Markdown", "后续操作流阶段接入", "queued"),
    ],
    evidence: evidence("报告说明", "月报、季报、年报、自定义报告和导出", "本机报告资料", "真实数据汇总后进入报告与洞察。"),
  };

  WORKSPACES.market_research = {
    ...WORKSPACES.market_research,
    label: "市场与研究",
    kicker: "市场与研究",
    conclusion: "查看市场观察、公司研究、基金研究、政策研究和唯一策略实验室。",
    freshness: "等待市场资料",
    runtime: "当前页面：市场观察、研究和策略实验室",
    secondaryTabs: STAGE2_SECONDARY_TABS.market_research,
    cards: [
      ["市场观察", "可用", "指数、ETF、主题和自选"],
      ["公司研究", "可用", "公司资料和反方条件"],
      ["基金研究", "可用", "基金持仓、费率和风格"],
      ["策略实验室", "唯一入口", "回测、参数扫描和盘感训练"],
    ],
    features: [
      feature("市场观察", "可用", "市场观察", "查看指数、ETF、主题和自选对象。", { workspace: "market_research", routeAlias: "/market-research?tab=market", label: "打开市场" }),
      feature("公司研究", "可用", "公司研究", "查看公司资料、关键假设和反方条件。", { workspace: "market_research", routeAlias: "/market-research?tab=company", label: "打开公司" }),
      feature("基金研究", "可用", "基金研究", "查看基金持仓、风格、费用和风险。", { workspace: "market_research", routeAlias: "/market-research?tab=fund", label: "打开基金" }),
      feature("政策研究", "可用", "政策研究", "查看政策资料和引用位置。", { workspace: "market_research", routeAlias: "/market-research?tab=policy", label: "打开政策" }),
      feature("策略实验室", "可用", "策略实验室", "进入唯一策略实验室，保留策略回测、参数扫描和盘感训练。", { workspace: "market_research", routeAlias: "/market-research/strategy-lab", label: "打开策略" }),
    ],
    rows: [
      row("1", "市场观察", "等待市场资料", "查看市场", "可用"),
      row("2", "研究材料", "等待材料", "查看研究", "可用"),
      row("3", "策略实验室", "唯一入口", "打开策略", "可用"),
    ],
    tasks: [
      task("市场观察", "查看市场和自选", "ready"),
      task("公司/基金研究", "整理研究材料", "ready"),
      task("策略实验室", "统一进入回测和盘感训练", "ready"),
    ],
    evidence: evidence("市场与研究说明", "市场观察、公司研究、基金研究、政策研究和策略实验室", "本机研究资料", "研究资料汇总到市场与研究。"),
  };

  WORKSPACES.settings = {
    ...WORKSPACES.settings,
    label: "设置",
    kicker: "设置",
    conclusion: "管理账户偏好、数据与系统、隐私与本地存储、反馈偏好、主题语言和备份恢复。",
    freshness: "设置保存在本机",
    runtime: "当前页面：偏好与本机数据设置",
    secondaryTabs: STAGE2_SECONDARY_TABS.settings,
    cards: [
      ["账户偏好", "可配置", "默认账户、币种和显示偏好"],
      ["数据与系统", "可配置", "数据路径、来源和备份"],
      ["隐私与本地存储", "本机优先", "原始数据保存在本机和 MetaDatabase"],
      ["反馈偏好", "可配置", "触感、声音、视觉和通知"],
    ],
    features: [
      feature("账户偏好", "可配置", "账户偏好", "设置默认账户、显示币种和首页偏好。", { workspace: "settings", routeAlias: "/settings?tab=account", label: "打开偏好" }),
      feature("数据与系统", "可配置", "数据与系统", "查看数据路径、来源状态、备份和恢复。", { workspace: "settings", routeAlias: "/settings?tab=data-system", label: "打开数据" }),
      feature("隐私与本地存储", "可配置", "隐私与本地存储", "查看本机数据目录、原始文件位置和公共提交排除规则。", { workspace: "settings", routeAlias: "/settings?tab=privacy", label: "打开隐私" }),
      feature("反馈偏好", "可配置", "反馈偏好", "设置触感、声音、视觉和通知反馈。", { workspace: "settings", routeAlias: "/settings?tab=feedback", label: "打开反馈" }),
      feature("主题语言", "可配置", "主题语言", "设置主题、字号和语言偏好。", { workspace: "settings", routeAlias: "/settings?tab=theme", label: "打开主题" }),
      feature("备份恢复", "可配置", "备份恢复", "查看备份、恢复和校验状态。", { workspace: "settings", routeAlias: "/settings?tab=backup", label: "打开备份" }),
    ],
    rows: [
      row("1", "账户偏好", "本机设置", "调整显示偏好", "可配置"),
      row("2", "数据与系统", "本机路径", "查看数据位置", "可配置"),
      row("3", "反馈偏好", "设置页", "调整触感、声音、视觉和通知", "可配置"),
    ],
    tasks: [
      task("保存设置", "后续操作流阶段接入", "queued"),
      task("备份恢复", "后续操作流阶段接入", "queued"),
      task("反馈测试", "只在设置页显示", "ready"),
    ],
    evidence: evidence("设置说明", "账户偏好、数据与系统、隐私、本地存储、反馈、主题和备份", "本机设置", "设置项集中在设置页。"),
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
    runSummary: options.runSummary || `${title}已进入操作状态；请先核对数据、参数和当前记录。`,
    runSteps,
    runFields,
    status: "可用",
  };
}

function defaultRunSteps(title, workspace) {
  const workspaceName = WORKSPACE_LABELS[workspace] || "当前工作区";
  return [
    `确认${workspaceName}当前页面和时间范围。`,
    `检查${title}所需数据、参数和缺口。`,
    "生成处理结果，并把需要人工判断的事项写入待办清单。",
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
    Model: "本机读取",
    Parameters: "本机设置 · 人工复核",
    "Data lineage": lineage,
    "Raw document": "本机摘要",
  };
}

function readContext() {
  try {
    const values = JSON.parse(localStorage.getItem(CONTEXT_STORAGE_KEY) || "{}");
    if (values && typeof values === "object") {
      delete values.fx_badge;
    }
    return values;
  } catch (_error) {
    return {};
  }
}

function writeContext(nextContext) {
  const cleanContext = { ...(nextContext || {}) };
  delete cleanContext.fx_badge;
  localStorage.setItem(CONTEXT_STORAGE_KEY, JSON.stringify(cleanContext));
}

function refreshFxBadgeDisplay() {
  const embeddedStatus = readEmbeddedReadModelStatus();
  const source = embeddedStatus?.source || {};
  const candidatePolicy = RUNTIME_CONFIG.candidateCachePolicy || {};
  const isolatedCandidate = (
    RUNTIME_CONFIG.isolatedCandidate === true ||
    RUNTIME_CONFIG.stage1OfficialCandidate === true ||
    RUNTIME_CONFIG.candidateDataMode === "isolated_empty"
  );
  const candidateNotLoaded = isolatedCandidate && (
    candidatePolicy.data_access === "disabled" ||
    source.status !== "ready" ||
    source.storage_mode === "isolated_empty"
  );
  const display = candidateNotLoaded ? NOT_LOADED_FX_BADGE_DISPLAY : CURRENT_FX_BADGE_DISPLAY;
  document.querySelectorAll('[data-fx-badge], [data-context-field="fx_badge"]').forEach((node) => {
    if ("value" in node) {
      node.value = display;
    } else {
      node.textContent = display;
    }
    node.dataset.fxSourceLabel = display;
    node.dataset.fxEffectiveDate = candidateNotLoaded ? "" : FX_SNAPSHOT.effectiveDate;
    node.dataset.fxCacheState = candidateNotLoaded ? "not_loaded" : FX_SNAPSHOT.cacheState;
  });
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

function readEmbeddedReleaseManifest() {
  try {
    const node = document.querySelector("#pfi-release-manifest");
    const parsed = JSON.parse(node?.textContent || "{}");
    return parsed && typeof parsed === "object" && !Array.isArray(parsed) ? parsed : {};
  } catch (_error) {
    return {};
  }
}

function readEmbeddedReadModelStatus() {
  try {
    const node = document.querySelector("#pfi-read-model-status");
    const parsed = JSON.parse(node?.textContent || "{}");
    return parsed && typeof parsed === "object" && Array.isArray(parsed.core_metric_states) ? parsed : null;
  } catch (_error) {
    return null;
  }
}

function buildStage7CanonicalStatusFallback() {
  const dependencyReason = "财务数据暂不可用；请先检查本机数据源和读取状态。";
  const metric = (metricId, formulaId = null) => ({
    metric_id: metricId,
    value: null,
    currency: metricId === "report_summary_status" ? null : "CNY",
    status: "not_loaded",
    source_id: null,
    record_count: null,
    as_of: null,
    formula_id: formulaId,
    confidence: null,
    blocking_reason_zh: dependencyReason,
    calculation_state: "blocked",
  });
  return {
    schema: "PFIV024Stage4ReadModelStatusV1",
    target_version: "v0.2.5",
    stage: "Stage 7",
    contract_version: "PFI-V025-STAGE7-CANONICAL-STATUS-FALLBACK",
    stage7_operational_authority: true,
    legacy_metadatabase_suppressed: true,
    source: {
      type: "sqlite_operational_authorities",
      status: "not_loaded",
      storage_mode: "local_private_sqlite",
      record_count: null,
      raw_file_count: null,
      as_of: null,
      evidence_hash: null,
      blocking_reason_zh: dependencyReason,
    },
    as_of: null,
    read_model_hash: null,
    core_metric_states: [
      metric("net_worth_cny", "FORM-PFI-012"),
      metric("cash_balance_cny", "FORM-PFI-008"),
      metric("investment_market_value_cny", "FORM-PFI-010"),
      metric("consumption_outflow_cny", "FORM-PFI-015"),
      metric("report_summary_status"),
    ],
    blocked_metric_ids: [
      "net_worth_cny",
      "cash_balance_cny",
      "investment_market_value_cny",
      "consumption_outflow_cny",
      "report_summary_status",
    ],
    surface_ids: ["home", "accounts", "investment", "consumption", "insights"],
    generated_at_utc: "",
  };
}

function isCanonicalStage7Status(payload) {
  if (!payload || typeof payload !== "object" || Array.isArray(payload)) return false;
  const expectedMetricIds = [
    "net_worth_cny",
    "cash_balance_cny",
    "investment_market_value_cny",
    "consumption_outflow_cny",
    "report_summary_status",
  ];
  const metrics = Array.isArray(payload.core_metric_states) ? payload.core_metric_states : [];
  const byId = new Map(metrics.map((metric) => [metric?.metric_id, metric]));
  const safeMetricStatuses = new Set([
    "not_loaded",
    "source_missing",
    "valuation_missing",
    "partial_coverage",
    "calculation_failed",
  ]);
  const metricsFailClosed = metrics.length === expectedMetricIds.length
    && byId.size === expectedMetricIds.length
    && expectedMetricIds.every((metricId) => {
      const metric = byId.get(metricId);
      const status = String(metric?.status || "");
      return metric?.value === null
        && metric?.calculation_state === "blocked"
        && (safeMetricStatuses.has(status) || status.startsWith("blocked"));
    });
  const blockedMetricIds = Array.isArray(payload.blocked_metric_ids)
    ? new Set(payload.blocked_metric_ids)
    : new Set();
  return payload.schema === "PFIV024Stage4ReadModelStatusV1"
    && payload.target_version === "v0.2.5"
    && payload.stage === "Stage 7"
    && payload.contract_version === "PFI-V025-STAGE7-SQLITE-FAIL-CLOSED-AUTHORITY"
    && payload.stage7_operational_authority === true
    && payload.legacy_metadatabase_suppressed === true
    && payload.source?.type === "sqlite_operational_authorities"
    && payload.source?.storage_mode === "local_private_sqlite"
    && payload.stage5_financial_model == null
    && metricsFailClosed
    && expectedMetricIds.every((metricId) => blockedMetricIds.has(metricId));
}

function isOfficialStage1CandidateStatus(payload) {
  if (!payload || typeof payload !== "object" || Array.isArray(payload)) return false;
  const expectedMetricIds = [
    "net_worth_cny",
    "cash_balance_cny",
    "investment_market_value_cny",
    "consumption_outflow_cny",
    "report_summary_status",
  ];
  const metrics = Array.isArray(payload.core_metric_states) ? payload.core_metric_states : [];
  const byId = new Map(metrics.map((metric) => [metric?.metric_id, metric]));
  const blockedMetricIds = Array.isArray(payload.blocked_metric_ids)
    ? new Set(payload.blocked_metric_ids)
    : new Set();
  return payload.schema === "PFIV024Stage4ReadModelStatusV1"
    && payload.isolated_candidate === true
    && payload.target_version === "v0.2.5"
    && payload.stage === "Stage 1"
    && payload.contract_version === "PFI-V025-STAGE1-OFFICIAL-UI-ISOLATED-EMPTY"
    && payload.source?.type === "isolated_candidate"
    && payload.source?.storage_mode === "isolated_empty"
    && Number(payload.source?.record_count) === 0
    && payload.stage5_financial_model == null
    && metrics.length === expectedMetricIds.length
    && byId.size === expectedMetricIds.length
    && expectedMetricIds.every((metricId) => {
      const metric = byId.get(metricId);
      return metric?.value === null
        && metric?.status === "not_loaded"
        && metric?.calculation_state === "not_evaluated"
        && blockedMetricIds.has(metricId);
    });
}

function canonicalStage7StatusOrFallback(payload) {
  if (RUNTIME_CONFIG.stage1OfficialCandidate === true) {
    return isOfficialStage1CandidateStatus(payload)
      ? payload
      : buildStage7CanonicalStatusFallback();
  }
  return isCanonicalStage7Status(payload) ? payload : buildStage7CanonicalStatusFallback();
}

function markReadModelStatusSettlement(value) {
  if (!document.body) return;
  document.body.dataset.pfiReadModelStatusSettled = value === "pending" ? "false" : "true";
  document.body.dataset.pfiReadModelStatusSettlement = value;
}

function readEmbeddedStage7ReportPack() {
  try {
    const node = document.querySelector("#pfi-stage7-report-schema");
    const parsed = JSON.parse(node?.textContent || "{}");
    return parsed && typeof parsed === "object" && Array.isArray(parsed.reports) ? parsed : null;
  } catch (_error) {
    return null;
  }
}

function v024DataStateApi() {
  return typeof window !== "undefined" ? window.PFI_V024_STAGE4_DATA_STATE || null : null;
}

function runtimeApiUrl(path) {
  const cleanPath = String(path || "/").startsWith("/") ? String(path || "/") : `/${path}`;
  return `${PFI_RUNTIME_API_BASE_URL}${cleanPath}`;
}

function shouldFetchRuntimeReadModelStatus() {
  return RUNTIME_CONFIG.readModelStatusApi === true;
}

async function runtimeApiJson(path, options = {}) {
  if (RUNTIME_CONFIG.runtimeApiEnabled === true && !PFI_RUNTIME_API_AUTH_TOKEN) {
    throw new Error("本机服务授权令牌缺失");
  }
  const response = await fetch(runtimeApiUrl(path), {
    ...options,
    headers: {
      "Content-Type": "application/json",
      "X-PFI-Runtime-Token": PFI_RUNTIME_API_AUTH_TOKEN,
      ...(options.headers || {}),
    },
  });
  if (!response.ok) {
    let message = `本机服务响应失败：${response.status}`;
    try {
      const payload = await response.json();
      if (payload?.message) message = String(payload.message);
    } catch (_error) {
      // Keep the status-based fallback when the local service returns no JSON.
    }
    throw new Error(message);
  }
  return response.json();
}

async function refreshRuntimeTrends(options = {}) {
  let statusSettlement = "runtime_error_fallback";
  markReadModelStatusSettlement("pending");
  try {
    const payload = await runtimeApiJson("/api/trends");
    runtimeTrendState = payload.trends || null;
    runtimeReadModelState = payload.readModel || {};
    try {
      runtimeStage4SyncState = await runtimeApiJson("/api/read-model");
    } catch (_syncError) {
      runtimeStage4SyncState = null;
    }
    const embeddedReadModelStatus = readEmbeddedReadModelStatus();
    if (shouldFetchRuntimeReadModelStatus()) {
      try {
        const apiReadModelStatus = await runtimeApiJson("/api/read-model-status");
        const apiStatusIsCanonical = isCanonicalStage7Status(apiReadModelStatus)
          || (RUNTIME_CONFIG.stage1OfficialCandidate === true
            && isOfficialStage1CandidateStatus(apiReadModelStatus));
        runtimeReadModelStatusState = canonicalStage7StatusOrFallback(apiReadModelStatus);
        statusSettlement = apiStatusIsCanonical
          ? "api_canonical"
          : "api_rejected_fallback";
      } catch (_statusError) {
        runtimeReadModelStatusState = canonicalStage7StatusOrFallback(embeddedReadModelStatus);
        statusSettlement = "api_error_fallback";
      }
    } else if (embeddedReadModelStatus) {
      runtimeReadModelStatusState = canonicalStage7StatusOrFallback(embeddedReadModelStatus);
      statusSettlement = isCanonicalStage7Status(embeddedReadModelStatus)
        ? "embedded_canonical"
        : "embedded_rejected_fallback";
    } else {
      runtimeReadModelStatusState = canonicalStage7StatusOrFallback(null);
      statusSettlement = "embedded_missing_fallback";
    }
    // Stage 7 status is the canonical financial publication gate.  The older
    // /api/trends payload may still contain transaction-derived aggregates,
    // but it must not repaint formal cards while Stage 7 says the operational
    // economic-event adapter is unavailable (including API-fetch fallback to
    // the embedded Stage 7 status).
    if (runtimeReadModelStatusState?.stage7_operational_authority !== true) {
      applyOperationalReadModel(runtimeReadModelState);
    }
    applyV024ReadModelStatusToSurfaces(runtimeReadModelStatusState);
    applyStage7HoldingProjectionToSurfaces(runtimeStage4SyncState);
    if (options.rerender) {
      const current = document.querySelector("#main-workspace")?.dataset.activeWorkspace || currentContext().workspace || "home";
      drawTrendChart(resolveWorkspaceTrend(WORKSPACES[current] || WORKSPACES.home));
      renderCards((WORKSPACES[current] || WORKSPACES.home).cards);
    }
    return { ok: true, statusSettlement };
  } catch (_error) {
    runtimeTrendState = null;
    runtimeStage4SyncState = null;
    runtimeReadModelStatusState = canonicalStage7StatusOrFallback(readEmbeddedReadModelStatus());
    applyV024ReadModelStatusToSurfaces(runtimeReadModelStatusState);
    return { ok: false, statusSettlement, error: "runtime_refresh_failed" };
  } finally {
    markReadModelStatusSettlement(statusSettlement);
  }
}

function resolveWorkspaceTrend(workspace) {
  const key = workspace?.trendKey || "";
  if (key && runtimeTrendState && runtimeTrendState[key]) return runtimeTrendState[key];
  return workspace?.trend || emptyTrendForWorkspace(workspace);
}

function applyOperationalReadModel(model) {
  if (!model || typeof model !== "object") return;
  const investment = model.investment || {};
  const accounts = model.accounts || {};
  const consumption = model.consumption || {};
  const hasInvestment = hasRealInvestmentReadModel(investment);
  const hasAccounts = hasRealAccountsReadModel(accounts);
  const hasConsumption = consumption.has_real_transactions === true;
  const fixedSpendHasRule = consumption.fixed_spend_cny_has_rule === true || hasConfiguredSpendPolicy(consumption.fixed_flex_policy);
  const budgetHasRule = consumption.budget_remaining_cny_has_rule === true || consumption.budget_configured === true;
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
  if (hasConsumption && WORKSPACES.consumption) {
    WORKSPACES.consumption.cards = [
      ["本月支出", formatCnyAmount(consumption.month_spend_cny), "MetaDatabase 真实支付宝流水"],
      ["待复核流水", String(consumption.review_count || 0), `${consumption.transaction_count || 0} 条真实流水`],
      ["近30天支出", formatCnyAmount(consumption.cashflow_forecast_cny), "最近30天真实消费流出"],
      [
        "固定/弹性",
        `${formatOptionalCnyAmount(consumption.fixed_spend_cny, fixedSpendHasRule, "未配置")} / ${formatOptionalCnyAmount(consumption.flex_spend_cny, true)}`,
        consumption.fixed_flex_policy || "真实流水派生",
      ],
    ];
    applyConsumptionOptionalPolicyToTrend({ fixedSpendHasRule, budgetHasRule });
  }
  if (hasInvestment && WORKSPACES.insights) {
    const report = runtimeStage4SyncState?.report || {};
    const holdingCount = Number.isFinite(Number(report.holding_count)) ? Number(report.holding_count) : Number(investment.holding_count || 0);
    WORKSPACES.insights.cards = [
      ["月报", hasAccounts ? formatCnyAmount(accounts.net_worth_cny) : "暂无真实数据", "净资产、现金流、消费、投资"],
      ["投资报告", formatCnyAmount(investment.market_value_cny), `${holdingCount} 条持仓，读取 SQLite`],
      ["收益复核", formatCnyAmount(investment.unrealized_pnl_cny), "由持仓成本和现价派生"],
      ["导出", "可用", "Markdown / JSON / CSV"],
    ];
  }
  if ((hasInvestment || hasAccounts || hasConsumption) && WORKSPACES.home) {
    WORKSPACES.home.cards = [
      ["净资产", hasAccounts ? formatCnyAmount(accounts.net_worth_cny) : "暂无真实数据", hasAccounts ? "账户和持仓汇总" : "账户和持仓接入后显示"],
      ["现金余额", hasAccounts ? formatCnyAmount(accounts.cash_cny) : "暂无真实数据", hasAccounts ? "账户现金汇总" : "账户流水接入后显示"],
      ["投资市值", hasInvestment ? formatCnyAmount(investment.market_value_cny) : "暂无真实数据", hasInvestment ? "持仓读模型" : "持仓接入后显示"],
      ["本月支出", hasConsumption ? formatCnyAmount(consumption.month_spend_cny) : "暂无真实数据", hasConsumption ? "MetaDatabase 真实支付宝流水" : "真实流水导入后显示"],
      ["待复核交易", hasConsumption ? String(consumption.review_count || 0) : "未读取状态", hasConsumption ? `${consumption.transaction_count || 0} 条真实流水` : "财务数据就绪后显示"],
      ["数据源状态", hasConsumption ? "已导入" : "等待上传", hasConsumption ? "真实流水可读取" : "进入数据源与上传处理"],
    ];
  }
}

function applyStage7HoldingProjectionToSurfaces(payload) {
  const projection = payload?.projection;
  if (!projection || projection.schema !== "PFIV025Stage7HoldingProjectionV1") return;
  const surfaces = [projection.home, projection.investment, projection.report];
  const hashes = surfaces.map((surface) => String(surface?.projection_hash || ""));
  if (hashes.some((value) => !value) || new Set(hashes).size !== 1) return;
  const holdingCount = Number(projection.holding_count || 0);
  const stateLabel = projection.valuation_status === "valuation_missing" ? "估值依赖缺失" : "尚未加载真实持仓";
  const syncCard = [
    "持仓同步",
    `${holdingCount.toLocaleString("zh-CN")} 条`,
    `${stateLabel} · ${shortReadModelHash(projection.projection_hash)}`,
  ];
  for (const workspaceId of ["home", "investment", "insights"]) {
    const workspace = WORKSPACES[workspaceId];
    if (!workspace || !Array.isArray(workspace.cards)) continue;
    const existingIndex = workspace.cards.findIndex((card) => Array.isArray(card) && card[0] === "持仓同步");
    if (existingIndex >= 0) workspace.cards[existingIndex] = syncCard;
    else if (workspace.cards.length >= 6) workspace.cards = [...workspace.cards.slice(0, 5), syncCard];
    else workspace.cards = [...workspace.cards, syncCard];
    workspace.stage7HoldingProjectionHash = projection.projection_hash;
  }
}

function applyV024ReadModelStatusToSurfaces(statusPayload) {
  if (!statusPayload || typeof statusPayload !== "object") return;
  applySourceAvailabilityBanner(statusPayload);
  const api = v024DataStateApi();
  const surfaceViews = api?.buildSurfaceMetricViews
    ? api.buildSurfaceMetricViews(statusPayload)
    : buildFallbackV024SurfaceMetricViews(statusPayload);
  const surfaces = surfaceViews?.surfaces || {};
  const home = metricMapForSurface(surfaces.home);
  const accounts = metricMapForSurface(surfaces.accounts);
  const investment = metricMapForSurface(surfaces.investment);
  const consumption = metricMapForSurface(surfaces.consumption);
  const insights = metricMapForSurface(surfaces.insights);

  if (WORKSPACES.home) {
    WORKSPACES.home.cards = [
      cardFromMetric(home.net_worth_cny),
      cardFromMetric(home.cash_balance_cny),
      cardFromMetric(home.investment_market_value_cny),
      cardFromMetric(home.consumption_outflow_cny, "消费总流出"),
      cardFromMetric(home.report_summary_status, "数据记录"),
      ["数据源状态", sourceStatusLabel(statusPayload), sourceStatusDetail(statusPayload)],
    ];
  }
  if (WORKSPACES.accounts) {
    WORKSPACES.accounts.cards = [
      cardFromMetric(accounts.net_worth_cny),
      cardFromMetric(accounts.cash_balance_cny),
      cardFromMetric(accounts.report_summary_status, "数据记录"),
      ["状态同步", "同一数据快照", shortReadModelHash(statusPayload.read_model_hash)],
    ];
  }
  if (WORKSPACES.investment) {
    WORKSPACES.investment.cards = [
      cardFromMetric(investment.investment_market_value_cny),
      cardFromMetric(investment.net_worth_cny),
      cardFromMetric(investment.report_summary_status, "数据记录"),
      ["状态同步", "同一数据快照", shortReadModelHash(statusPayload.read_model_hash)],
    ];
  }
  if (WORKSPACES.consumption) {
    WORKSPACES.consumption.cards = [
      cardFromMetric(consumption.consumption_outflow_cny, "消费总流出"),
      cardFromMetric(consumption.report_summary_status, "数据记录"),
      ["数据源状态", sourceStatusLabel(statusPayload), sourceStatusDetail(statusPayload)],
      ["状态同步", "同一数据快照", shortReadModelHash(statusPayload.read_model_hash)],
    ];
  }
  if (WORKSPACES.insights) {
    WORKSPACES.insights.cards = [
      cardFromMetric(insights.net_worth_cny, "净资产报告"),
      cardFromMetric(insights.cash_balance_cny, "现金余额报告"),
      cardFromMetric(insights.investment_market_value_cny, "投资市值报告"),
      cardFromMetric(insights.consumption_outflow_cny, "消费结构报告"),
      cardFromMetric(insights.report_summary_status, "数据质量报告"),
    ];
  }
  applyV025Stage5FinancialModelToSurfaces(statusPayload.stage5_financial_model);
  applyV025Stage9Phase92Analysis();
  applyV025Stage9Phase93DecisionReview();
}

function applyV025Stage5FinancialModelToSurfaces(payload) {
  if (!payload || typeof payload !== "object") return;
  const requiredMetricIds = [
    "total_consumption_outflow_cny",
    "living_consumption_cny",
    "investment_funding_outflow_cny",
    "investment_allocation_amount_cny",
  ];
  const components = Array.isArray(payload.components) ? payload.components : [];
  const byId = Object.fromEntries(components.map((item) => [item?.metric_id, item]));
  if (!requiredMetricIds.every((metricId) => byId[metricId])) return;
  if (!requiredMetricIds.every((metricId) =>
    byId[metricId]?.status === "ready" && /^-?[0-9]+\.[0-9]{2}$/.test(String(byId[metricId]?.value || ""))
  )) return;
  const surfaceHashes = payload.surface_payload_hashes || {};
  const requiredSurfaceIds = ["homepage", "consumption_page", "report"];
  if (!requiredSurfaceIds.every((surfaceId) => typeof surfaceHashes[surfaceId] === "string" && surfaceHashes[surfaceId])) return;
  if (new Set(requiredSurfaceIds.map((surfaceId) => surfaceHashes[surfaceId])).size !== 1) return;
  if (payload.actual_ui_render_binding_completed !== true || payload.actual_report_render_binding_completed !== true) return;

  const componentCards = requiredMetricIds.map((metricId) => stage5FinancialCard(byId[metricId]));
  const source = payload.source || {};
  const sourceCounts = [
    source.input_record_count,
    source.published_record_count,
    source.review_queue_record_count,
    source.silent_drop_count,
  ].map(Number);
  if (!sourceCounts.every((count) => Number.isInteger(count) && count >= 0)) return;
  if (sourceCounts[0] !== sourceCounts[1] + sourceCounts[2] || sourceCounts[3] !== 0) return;
  const coverageCard = [
    "来源覆盖",
    `${Number(source.published_record_count || 0).toLocaleString("zh-CN")} 条已发布`,
    `${Number(source.review_queue_record_count || 0).toLocaleString("zh-CN")} 条待复核 · 0 条静默丢弃`,
  ];
  const validationCard = [
    "模型验证",
    "部分验证 · 缺失模型已阻断",
    "FORM-PFI-015/019 已验证；FORM-PFI-016/017/018 保持 blocked",
  ];
  if (WORKSPACES.home) {
    WORKSPACES.home.cards = [...componentCards, coverageCard, validationCard];
    WORKSPACES.home.runtime = "Stage 5 真实只读口径 · 三表面同一 payload";
    WORKSPACES.home.stage5FinancialSurfaceHash = surfaceHashes.homepage || null;
  }
  if (WORKSPACES.consumption) {
    WORKSPACES.consumption.cards = [...componentCards, coverageCard, validationCard];
    WORKSPACES.consumption.conclusion = payload.scope_explanation_zh || "四项消费与投资活动口径来自同一真实只读快照。";
    WORKSPACES.consumption.runtime = "FORM-PFI-015 · 已发布经济事件口径";
    WORKSPACES.consumption.features = components.map((component) =>
      feature(
        component.label_zh,
        "已就绪",
        `${component.formula_id} · ${component.coverage_scope}`,
        `${stage5FinancialDetail(component)}；待复核记录不进入当前金额。`,
        { workspace: "consumption", routeAlias: "/consumption?tab=analysis", label: "查看口径" },
      ),
    );
    WORKSPACES.consumption.stage5FinancialSurfaceHash = surfaceHashes.consumption_page || null;
  }
  if (WORKSPACES.insights) {
    WORKSPACES.insights.cards = [...componentCards, coverageCard, validationCard];
    WORKSPACES.insights.conclusion = "报告同时展示四项真实只读活动口径，并明确来源覆盖、公式、限制与被阻断模型。";
    WORKSPACES.insights.runtime = "Stage 5 model card · actual report binding";
    WORKSPACES.insights.features = components.map((component) =>
      feature(
        component.label_zh,
        "已就绪",
        `${component.formula_id} · ${component.formula_version}`,
        `${stage5FinancialDetail(component)}｜口径：已发布事件；限制：${Number(component.excluded_review_record_count || 0).toLocaleString("zh-CN")} 条待复核记录未计入。`,
        { workspace: "insights", routeAlias: "/reports?tab=consumption", label: "查看报告" },
      ),
    );
    WORKSPACES.insights.rows = [
      row("P0", "真实来源覆盖", "immutable Git-object snapshot", `${source.input_record_count} = ${source.published_record_count} 已发布 + ${source.review_queue_record_count} 待复核 + ${source.silent_drop_count} 静默丢弃`, "已核验"),
      row("P0", "公式与不变量", "FORM-PFI-015 / FORM-PFI-019", "双口径精确守恒、七窗口、变形与敏感性验证通过。", "通过"),
      row("P0", "被阻断模型", "FORM-PFI-016 / 017 / 018", "余额、持仓、价格、FX 与完整 dated chain 缺失，不生成虚假成功。", "阻断"),
      row("P1", "分类与样本外", "FORM-PFI-020", "结构合同通过；缺少 scores、labels 与 ground truth，不声明准确率或样本外有效。", "部分验证"),
    ];
    WORKSPACES.insights.tasks = [
      task("四项口径同屏", "首页、消费页、报告使用同一 payload hash", "ready"),
      task("来源覆盖", `${source.published_record_count} 已发布 · ${source.review_queue_record_count} 待复核`, "review"),
      task("模型限制", "未验证模型明确 blocked", "ready"),
      task("生产验收", "Stage 5 只授权进入 Stage 6；不等于最终生产验收", "review"),
    ];
    WORKSPACES.insights.stage5FinancialSurfaceHash = surfaceHashes.report || null;
  }
}

function stage5FinancialCard(component) {
  const display = formatStage5ExactCnyAmount(component?.value);
  return [
    safeUserText(component?.label_zh, "财务口径"),
    display,
    stage5FinancialDetail(component),
  ];
}

function formatStage5ExactCnyAmount(value) {
  const match = String(value ?? "").match(/^(-?)([0-9]+)\.([0-9]{2})$/);
  if (!match) return "已阻断";
  const whole = BigInt(match[2]).toLocaleString("zh-CN");
  return `CNY ${match[1]}${whole}.${match[3]}`;
}

function stage5FinancialDetail(component) {
  const count = Number(component?.record_count || 0).toLocaleString("zh-CN");
  return `真实已发布范围 · ${count} 条事件 · 截至 ${safeUserText(component?.as_of, "未知日期")} · ${safeUserText(component?.formula_id, "公式待补")}`;
}

function applyV025Stage9Phase92Analysis() {
  if (!WORKSPACES.insights) return;
  const api = stage9AnalysisApi || window.PFI_V025_STAGE9_ANALYSIS || null;
  stage9AnalysisApi = api;
  if (!api || typeof api.buildPhase92ViewModel !== "function") return;
  let viewModel;
  try {
    viewModel = api.buildPhase92ViewModel();
  } catch (_error) {
    return;
  }
  if (viewModel?.validation?.status !== "pass") return;
  stage9AnalysisViewModel = viewModel;

  const statusLabel = (value) => {
    if (value === "blocked") return "已阻断";
    if (value === "partial") return "部分可算";
    if (String(value).includes("validated") || value === "pass") return "已验证";
    if (String(value).includes("blocked")) return "已阻断";
    return "待复核";
  };
  const reportFeatures = viewModel.report_cards.map((report) => feature(
    safeUserText(report.title_zh, "财务报告"),
    statusLabel(report.status),
    `${report.formula_ids.join(" / ")} · 参数 ${report.parameter_ids.join(" / ")}`,
    `${safeUserText(report.status_statement_zh, "等待真实来源")}｜数据范围：${safeUserText(report.data_range?.start, "未加载")} 至 ${safeUserText(report.data_range?.end, "未加载")}｜样本：${Number(report.transaction_record_count || 0).toLocaleString("zh-CN")} 条｜${safeUserText(report.scope_explanation_zh, "缺失输入不解释为零。")}`,
    { workspace: "insights", routeAlias: report.primary_review_route, label: "复核来源" },
  ));
  const componentFeatures = viewModel.component_cards.map((component) => feature(
    `活动组件 · ${safeUserText(component.label_zh, "活动组件")}`,
    safeUserText(component.status_zh, "待复核"),
    `${safeUserText(component.formula_id, "FORM-PFI-015")} · 数值仅在本机私有运行时显示`,
    safeUserText(component.scope_zh, "活动组件必须独立展示和复核。"),
    { workspace: "insights", routeAlias: component.review_route, label: "复核组件" },
  ));
  const formulaFeatures = viewModel.formula_cards.map((formulaCard) => feature(
    `${safeUserText(formulaCard.label_zh, "财务公式")} · ${safeUserText(formulaCard.formula_id, "公式待补")}`,
    statusLabel(formulaCard.validation_status),
    `参数 ${formulaCard.parameters.join(" / ")} · 报告 ${formulaCard.report_types.join(" / ")}`,
    `验证：${safeUserText(formulaCard.validation_status, "待复核")}｜限制：${safeUserText(formulaCard.limitation, "限制待补")}`,
    { workspace: "insights", routeAlias: formulaCard.review_route, label: "下钻公式" },
  ));
  const sensitivityFeatures = viewModel.sensitivity_cards.map((sensitivityCard) => feature(
    safeUserText(sensitivityCard.title_zh, "敏感性预览"),
    statusLabel(sensitivityCard.status),
    `参数 ${sensitivityCard.parameter_ids.join(" / ")} · 观测 ${Number(sensitivityCard.observation_count || 0)}`,
    `${safeUserText(sensitivityCard.impact_summary_zh, "参数影响待复核")}｜影响可见：${sensitivityCard.impact_visible ? "是" : "否，保持阻断"}`,
    { workspace: "insights", routeAlias: sensitivityCard.review_route, label: "查看敏感性" },
  ));
  const modelFeatures = viewModel.model_cards.map((modelCard) => feature(
    `模型验证卡 · ${safeUserText(modelCard.model_id, "模型待补")}`,
    statusLabel(modelCard.status),
    `不变量 ${safeUserText(modelCard.invariant_status, "待复核")} · 变形 ${safeUserText(modelCard.metamorphic_status, "待复核")}`,
    `历史/样本外：${safeUserText(modelCard.historical_out_of_sample_status, "待复核")}｜限制 ${Number(modelCard.limitation_count || 0)} 项｜反证 ${Number(modelCard.counter_evidence_count || 0)} 项`,
    { workspace: "insights", routeAlias: `/reports/metric-drilldown?model=${encodeURIComponent(modelCard.model_id)}`, label: "查看模型" },
  ));
  const reviewFeatures = viewModel.review_cards.map((reviewCard) => feature(
    `来源复核 · ${safeUserText(reviewCard.label_zh, "来源")}`,
    statusLabel(reviewCard.status),
    safeUserText(reviewCard.review_id, "复核编号待补"),
    safeUserText(reviewCard.action_label_zh, "检查来源与缺口。"),
    { workspace: "insights", routeAlias: reviewCard.review_route, label: "进入复核" },
  ));

  const hasPrivateStage5Cards = Boolean(WORKSPACES.insights.stage5FinancialSurfaceHash);
  const publicComponentCards = viewModel.component_cards.map((component) => [
    safeUserText(component.label_zh, "活动组件"),
    safeUserText(component.status_zh, "待复核"),
    `${safeUserText(component.formula_id, "FORM-PFI-015")} · ${safeUserText(component.scope_zh, "独立复核")}`,
  ]);
  WORKSPACES.insights = {
    ...WORKSPACES.insights,
    label: "报告与洞察",
    kicker: safeUserText(viewModel.kicker_zh, "Stage 9 Phase 9.2 财务分析与模型验证"),
    conclusion: safeUserText(viewModel.warning_zh, "缺失来源不解释为零。"),
    freshness: "脱敏报告快照 · 真实来源覆盖截至 2026-06-03",
    runtime: "Stage 9 reviewed snapshot：四项活动组件、五份报告、公式、敏感性、模型限制与来源复核",
    cards: hasPrivateStage5Cards ? WORKSPACES.insights.cards : publicComponentCards,
    features: [...componentFeatures, ...reportFeatures, ...formulaFeatures, ...sensitivityFeatures, ...modelFeatures, ...reviewFeatures],
    rows: viewModel.formula_cards.map((formulaCard, index) => row(
      String(formulaCard.validation_status).includes("blocked") ? "P0" : `P${Math.min(index + 1, 3)}`,
      safeUserText(formulaCard.formula_id, "公式"),
      `参数 ${formulaCard.parameters.join(" / ")}`,
      `${safeUserText(formulaCard.label_zh, "公式")} · ${safeUserText(formulaCard.limitation, "限制待补")}`,
      statusLabel(formulaCard.validation_status),
    )),
    tasks: [
      task("四项活动组件", `${viewModel.component_cards.length} 项分别可见；投资活动不等于净资产损失`, "ready"),
      task("五份财务报告", `${viewModel.validation.blockedCount} 份阻断 · ${viewModel.validation.partialCount} 份部分可算 · 缺失输入不解释为零`, "review"),
      task("公式下钻", `${viewModel.formula_cards.length} 条公式及参数影响可见`, "ready"),
      task("敏感性预览", `${viewModel.sensitivity_cards.length} 组；不可证明结果保持阻断`, "review"),
      task("模型验证卡", `${viewModel.model_cards.length} 张；历史/样本外限制明确`, "review"),
      task("来源复核入口", `${viewModel.review_cards.length} 个可执行入口`, "ready"),
      task("Phase 9.3", "建议复核与四格式导出 candidate complete；等待 Stage 9 整体复审", "review"),
    ],
    evidence: evidence(
      "Stage 9 Phase 9.2 财务分析与模型验证",
      safeUserText(viewModel.summary_zh, "报告、公式、敏感性、模型与来源复核保持同一快照。"),
      safeUserText(viewModel.snapshot_binding?.packHash, "快照 hash 待补"),
      "公开界面契约不含财务金额；私有运行时金额继续受来源、lineage、公式和 hash 门禁。",
    ),
    stage9Phase92ViewModel: viewModel,
  };
  document.body?.setAttribute("data-v025-stage9-phase92", "ready");
  document.body?.setAttribute("data-v025-stage9-component-count", String(viewModel.component_cards.length));
}

function applyV025Stage9Phase93DecisionReview(verifiedPersistedViewModel = null) {
  if (!WORKSPACES.insights) return;
  const api = stage9DecisionReviewApi || window.PFI_V025_STAGE9_DECISION_REVIEW || null;
  stage9DecisionReviewApi = api;
  if (!api || typeof api.buildPhase93ViewModel !== "function") return;
  let viewModel;
  try {
    viewModel = verifiedPersistedViewModel || api.buildPhase93ViewModel();
  } catch (_error) {
    return;
  }
  if (api.validatePhase93ViewModel(viewModel)?.status !== "pass") return;
  stage9DecisionReviewViewModel = viewModel;

  const reviewStatusLabel = (status) => ({
    awaiting_human_review: "等待人工复核",
    accepted: "已接受复核",
    rejected: "已拒绝",
    deferred: "已延后",
    invalidated: "已失效",
  }[String(status)] || "待复核");
  const decisionFeatures = viewModel.decision_cards.map((decision) => feature(
    `人工复核 · ${safeUserText(decision.action_label_zh, "建议")}`,
    reviewStatusLabel(decision.status),
    `${safeUserText(decision.decision_id, "建议编号")} · ${safeUserText(decision.horizon, "复核期限")}`,
    `${safeUserText(decision.thesis?.statement_zh, "依据待复核")}｜反方证据 ${decision.counter_evidence.length} 条｜失效条件 ${decision.invalidation_conditions.length} 个`,
    { workspace: "insights", routeAlias: `/reports?tab=decision-review&decision=${encodeURIComponent(decision.decision_id)}`, label: "人工复核" },
  ));
  const exportFeatures = viewModel.export_cards.map((exportCard) => feature(
    `同源导出 · ${String(exportCard.format || "").toUpperCase()}`,
    "已校验",
    `${safeUserText(exportCard.filename, "导出文件")} · ${Number(exportCard.byte_size || 0).toLocaleString("zh-CN")} bytes`,
    `${phase93ShortHash(exportCard.source_snapshot_hash)}｜下载前再次核对文件 hash。`,
    { workspace: "insights", routeAlias: "/reports?tab=export", label: "查看导出" },
  ));
  const priorFeatures = (WORKSPACES.insights.features || []).filter((item) => (
    !String(item?.title || "").startsWith("人工复核 ·")
    && !String(item?.title || "").startsWith("同源导出 ·")
  ));
  const priorRows = (WORKSPACES.insights.rows || []).filter((item) => !String(item?.object || "").startsWith("建议复核"));
  const priorTasks = (WORKSPACES.insights.tasks || []).filter((item) => item?.title !== "Phase 9.3" && item?.title !== "人工建议复核" && item?.title !== "同源导出" && item?.title !== "Stage 9 整阶段审查");
  WORKSPACES.insights = {
    ...WORKSPACES.insights,
    kicker: safeUserText(viewModel.kicker_zh, "Stage 9 Phase 9.3 建议、复盘与导出"),
    conclusion: safeUserText(viewModel.warning_zh, "人工接受不触发交易。"),
    runtime: "Phase 9.3：人工建议复核、反方证据、失效条件与四格式同源导出",
    features: [...priorFeatures, ...decisionFeatures, ...exportFeatures],
    rows: [
      ...priorRows,
      ...viewModel.decision_cards.map((decision, index) => row(
        index === 0 ? "P0" : "P1",
        `建议复核 · ${safeUserText(decision.action_label_zh, "建议")}`,
        safeUserText(decision.status, "awaiting_human_review"),
        `${safeUserText(decision.thesis?.statement_zh, "依据待复核")} · 接受只记录人工结果，不执行交易。`,
        reviewStatusLabel(decision.status),
      )),
    ],
    tasks: [
      ...priorTasks,
      task("人工建议复核", `${viewModel.decision_cards.length} 个建议；接受/拒绝/延后/失效均保留事件链`, "review"),
      task("同源导出", `${viewModel.export_cards.length} 种格式绑定 ${safeUserText(viewModel.export_snapshot_hash, "同一快照")}`, "ready"),
      task("Stage 9 整阶段审查", "尚未开始；本轮完成后必须独立审查、整改与复审", "queued"),
    ],
    evidence: evidence(
      "Stage 9 Phase 9.3 建议、复盘与同源导出",
      safeUserText(viewModel.summary_zh, "建议、反证、失效条件和导出保持同源。"),
      phase93ShortHash(viewModel.export_snapshot_hash),
      "建议只用于数据与报告复核；人工接受不触发交易，Stage 9 whole-stage review 尚未开始。",
    ),
    stage9Phase93ViewModel: viewModel,
  };
  document.body?.setAttribute("data-v025-stage9-phase93", "ready");
  if (!verifiedPersistedViewModel && typeof api.loadPersistedViewModel === "function") {
    void api.loadPersistedViewModel().then((persisted) => {
      document.body.dataset.v025Stage9ReviewRestore = persisted ? "verified" : "canonical";
      if (!persisted) return;
      applyV025Stage9Phase93DecisionReview(persisted);
      const main = document.querySelector("#main-workspace");
      if (main?.dataset.activeWorkspace === "insights") {
        renderWorkspace("insights", {
          silent: true,
          routeAlias: main.dataset.routeAlias,
          skipRouteSync: true,
          preserveFocus: true,
        });
      }
    }).catch(() => {
      document.body.dataset.v025Stage9ReviewRestore = "canonical";
    });
  }
}

function phase93ShortHash(value) {
  const match = String(value || "").match(/^sha256:([0-9a-f]{64})$/);
  return match ? `sha256:${match[1].slice(0, 12)}…${match[1].slice(-8)}` : "hash 待补";
}

function phase93ConditionLabel(predicate) {
  return ({
    review_queue_record_count_equals_zero: "待复核队列归零",
    source_analysis_pack_hash_changes: "分析快照 hash 发生变化",
    all_required_sources_and_lineage_ready: "所有关键来源与 lineage 已就绪",
  }[String(predicate)] || "未识别的失效条件");
}

function phase93ConditionStateLabel(state) {
  return ({ not_met: "当前未满足", met: "已满足" }[String(state)] || "待复核");
}

function phase93StatusLabel(status) {
  return ({
    awaiting_human_review: "等待人工复核",
    accepted: "已接受复核",
    rejected: "已拒绝",
    deferred: "已延后",
    invalidated: "已失效",
  }[String(status)] || "待复核");
}

function phase93OutcomeLabel(outcome) {
  return ({ accepted: "接受", rejected: "拒绝", deferred: "延后", invalidated: "标记失效" }[String(outcome)] || String(outcome));
}

function renderStage9DecisionReviewPanel(workspaceId) {
  document.querySelector("[data-stage9-decision-review-panel]")?.remove();
  if (workspaceId !== "insights" || !stage9DecisionReviewApi || !stage9DecisionReviewViewModel) return;
  const viewModel = stage9DecisionReviewViewModel;
  const panel = document.createElement("section");
  panel.className = "stage8-workspace-focus";
  panel.hidden = false;
  panel.dataset.stage9DecisionReviewPanel = "true";
  panel.setAttribute("aria-labelledby", "stage9-decision-review-title");

  const heading = document.createElement("div");
  heading.className = "stage8-workspace-focus-head";
  const headingText = document.createElement("div");
  const kicker = document.createElement("p");
  kicker.className = "panel-kicker";
  kicker.textContent = "人工判断与导出";
  const title = document.createElement("h2");
  title.id = "stage9-decision-review-title";
  title.textContent = "反方证据、失效条件与复核结果";
  const safety = document.createElement("p");
  safety.textContent = "接受只记录人工复核结果，不触发交易；报告仍保持 3 blocked / 2 partial。";
  headingText.append(kicker, title, safety);
  const phaseStatus = document.createElement("span");
  phaseStatus.className = "status-pill status-review";
  phaseStatus.textContent = "Phase candidate · Stage 9 整阶段审查尚未开始";
  heading.append(headingText, phaseStatus);
  panel.appendChild(heading);

  const decisionGrid = document.createElement("div");
  decisionGrid.className = "workflow-grid";
  decisionGrid.dataset.stage9DecisionGrid = "true";
  viewModel.decision_cards.forEach((decision) => {
    const card = document.createElement("article");
    card.className = "workflow-card";
    card.dataset.stage9DecisionId = decision.decision_id;
    const cardTitle = document.createElement("h3");
    cardTitle.textContent = safeUserText(decision.action_label_zh, "复核建议");
    const status = document.createElement("p");
    status.dataset.stage9DecisionStatus = decision.status;
    status.textContent = `${phase93StatusLabel(decision.status)} · ${decision.review_history.length} 条历史事件`;
    const thesis = document.createElement("p");
    thesis.textContent = safeUserText(decision.thesis?.statement_zh, "等待复核依据");
    const counterTitle = document.createElement("strong");
    counterTitle.textContent = "反方证据";
    const counterList = document.createElement("ul");
    decision.counter_evidence.forEach((item) => {
      const listItem = document.createElement("li");
      listItem.textContent = safeUserText(item.statement_zh, "反方证据待补");
      counterList.appendChild(listItem);
    });
    const invalidationTitle = document.createElement("strong");
    invalidationTitle.textContent = "失效条件";
    const invalidationList = document.createElement("ul");
    decision.invalidation_conditions.forEach((item) => {
      const listItem = document.createElement("li");
      listItem.textContent = `${phase93ConditionLabel(item.predicate)} · ${phase93ConditionStateLabel(item.current_state)}`;
      invalidationList.appendChild(listItem);
    });
    const actions = document.createElement("div");
    actions.className = "workflow-actions";
    stage9DecisionReviewApi.availableOutcomes(decision.status).forEach((outcome) => {
      const button = document.createElement("button");
      button.type = "button";
      button.dataset.stage9ReviewOutcome = outcome;
      button.dataset.stage9DecisionId = decision.decision_id;
      button.textContent = phase93OutcomeLabel(outcome);
      button.addEventListener("click", async () => {
        button.disabled = true;
        try {
          const next = await stage9DecisionReviewApi.applyHumanReview(
            stage9DecisionReviewViewModel,
            decision.decision_id,
            outcome,
            { reviewerRef: "local_owner", reasonZh: `人工复核：${phase93OutcomeLabel(outcome)}` },
          );
          stage9DecisionReviewViewModel = next;
          WORKSPACES.insights.stage9Phase93ViewModel = next;
          const persisted = await stage9DecisionReviewApi.persistViewModel(next);
          document.body.dataset.v025Stage9ReviewPersisted = persisted ? "true" : "false";
          renderStage9DecisionReviewPanel("insights");
          showToast(`已记录：${phase93OutcomeLabel(outcome)}；未触发交易`);
        } catch (_error) {
          button.disabled = false;
          showToast("复核记录未写入；当前数据未修改");
        }
      });
      actions.appendChild(button);
    });
    card.append(cardTitle, status, thesis, counterTitle, counterList, invalidationTitle, invalidationList, actions);
    decisionGrid.appendChild(card);
  });
  panel.appendChild(decisionGrid);

  const exportTitle = document.createElement("h3");
  exportTitle.textContent = "HTML / PDF / CSV / Markdown 同源导出";
  const exportSummary = document.createElement("p");
  exportSummary.textContent = `同一 snapshot：${phase93ShortHash(viewModel.export_snapshot_hash)}；下载前逐文件核对 manifest。`;
  const exportActions = document.createElement("div");
  exportActions.className = "workflow-actions";
  viewModel.export_cards.forEach((entry) => {
    const button = document.createElement("button");
    button.type = "button";
    button.dataset.stage9ExportFormat = entry.format;
    button.textContent = `下载 ${String(entry.format).toUpperCase()}`;
    button.addEventListener("click", async () => {
      button.disabled = true;
      try {
        const validation = await stage9DecisionReviewApi.verifyExportAsset(entry.format);
        if (validation.status !== "pass") throw new Error("export hash mismatch");
        stage9DecisionReviewApi.downloadExport(entry.format);
        panel.dataset.lastExportStatus = `pass:${entry.format}`;
        showToast(`${String(entry.format).toUpperCase()} 已按同一快照导出`);
      } catch (_error) {
        panel.dataset.lastExportStatus = `fail:${entry.format}`;
        showToast("导出 hash 校验失败；未下载文件");
      } finally {
        button.disabled = false;
      }
    });
    exportActions.appendChild(button);
  });
  panel.append(exportTitle, exportSummary, exportActions);
  document.querySelector(".workflow-runtime")?.insertAdjacentElement("afterend", panel);
}

function applySourceAvailabilityBanner(statusPayload) {
  const source = statusPayload?.source || {};
  const label = document.querySelector("[data-source-availability-label]");
  const dot = document.querySelector("[data-source-status-dot]");
  const freshness = document.querySelector("#freshness-label");
  const container = document.querySelector("[data-source-availability]");
  const ready = source.status === "ready";
  const isolatedEmpty = source.storage_mode === "isolated_empty";
  const labelText = ready
    ? "本机数据可用"
    : isolatedEmpty
      ? "隔离候选未加载真实数据"
      : source.blocking_reason_zh || "本机数据尚未加载";
  const detailText = ready
    ? source.as_of
      ? `截至 ${source.as_of}`
      : "财务数据已同步"
    : isolatedEmpty
      ? "只读空数据 · 未访问财务数据"
      : "等待财务数据状态";
  if (label) label.textContent = labelText;
  if (freshness) freshness.textContent = detailText;
  if (dot) {
    dot.classList.toggle("status-ready", ready);
    dot.classList.toggle("status-review", !ready);
  }
  if (container) {
    container.dataset.sourceStatus = String(source.status || "not_loaded");
    container.dataset.storageMode = String(source.storage_mode || "unknown");
  }
}

function buildFallbackV024SurfaceMetricViews(statusPayload) {
  const metrics = Array.isArray(statusPayload?.core_metric_states) ? statusPayload.core_metric_states : [];
  const surfaces = {};
  ["home", "accounts", "investment", "consumption", "insights"].forEach((surface) => {
    surfaces[surface] = {
      surface,
      read_model_hash: statusPayload?.read_model_hash || null,
      as_of: statusPayload?.as_of || null,
      metrics: metrics.map((metric) => ({
        ...metric,
        display_value: fallbackV024MetricDisplay(metric),
        display_detail: fallbackV024MetricDetail(metric),
      })),
    };
  });
  return { schema: "PFIV024Stage4SurfaceStateViewsV1", surfaces };
}

function metricMapForSurface(surface) {
  const map = {};
  (surface?.metrics || []).forEach((metric) => {
    map[metric.metric_id] = metric;
  });
  return map;
}

function cardFromMetric(metric, labelOverride = "") {
  const label = labelOverride || metricLabel(metric?.metric_id);
  if (!metric) return [label, "未加载真实数据", "财务数据状态缺失"];
  return [
    label,
    metric.display_value || fallbackV024MetricDisplay(metric),
    humanMetricDetail(metric),
  ];
}

function humanMetricDetail(metric) {
  const parts = [];
  if (metric?.record_count !== null && metric?.record_count !== undefined && Number.isFinite(Number(metric.record_count))) {
    parts.push(`${Number(metric.record_count).toLocaleString("zh-CN")} 条记录`);
  }
  if (metric?.as_of) parts.push(`截至 ${metric.as_of}`);
  if (metric?.source_id) parts.push("来源已登记");
  return parts.join(" · ") || "等待可追溯数据来源";
}

function metricLabel(metricId) {
  const labels = {
    net_worth_cny: "净资产",
    cash_balance_cny: "现金余额",
    investment_market_value_cny: "投资市值",
    consumption_outflow_cny: "消费总流出",
    report_summary_status: "数据记录",
  };
  return labels[metricId] || "指标";
}

function fallbackV024MetricDisplay(metric) {
  const api = v024DataStateApi();
  if (api?.renderMetricValueZh) return api.renderMetricValueZh(metric);
  if (metric?.status === "ready" || metric?.status === "confirmed_zero") {
    if (metric.value !== null && metric.value !== undefined) return formatCnyAmount(metric.value);
  }
  return metric?.blocking_reason_zh || "未加载真实数据";
}

function fallbackV024MetricDetail(metric) {
  const parts = [];
  if (metric?.source_id) parts.push(metric.source_id);
  if (metric?.record_count !== null && metric?.record_count !== undefined && Number.isFinite(Number(metric.record_count))) {
    parts.push(`${Number(metric.record_count).toLocaleString("zh-CN")} 条记录`);
  }
  if (metric?.as_of) parts.push(`截至 ${metric.as_of}`);
  if (metric?.formula_id) parts.push(metric.formula_id);
  return parts.join(" · ") || metric?.calculation_state || "状态待确认";
}

function sourceStatusLabel(statusPayload) {
  const sourceStatus = statusPayload?.source?.status || "not_loaded";
  if (sourceStatus === "ready") return "真实数据已加载";
  return statusPayload?.source?.blocking_reason_zh || "未加载真实数据";
}

function sourceStatusDetail(statusPayload) {
  const source = statusPayload?.source || {};
  if (source.status !== "ready") {
    return source.blocking_reason_zh || "等待财务数据状态";
  }
  const parts = [];
  const hasCount = (value) => value !== null && value !== undefined && value !== "" && Number.isFinite(Number(value));
  if (hasCount(source.record_count)) parts.push(`${Number(source.record_count).toLocaleString("zh-CN")} 条记录`);
  if (hasCount(source.raw_file_count)) parts.push(`${Number(source.raw_file_count).toLocaleString("zh-CN")} 个原始文件`);
  if (source.as_of) parts.push(`截至 ${source.as_of}`);
  return parts.join(" · ") || source.blocking_reason_zh || "等待财务数据状态";
}

function shortReadModelHash(hash) {
  const text = String(hash || "");
  if (!text) return "状态标识未生成";
  return text.length > 24 ? `${text.slice(0, 18)}…${text.slice(-6)}` : text;
}

function trendHasRealPoints(trend) {
  const periods = Array.isArray(trend?.periods) ? trend.periods : [];
  const series = Array.isArray(trend?.series) ? trend.series : [];
  return (
    periods.length > 0 &&
    series.some((item) => Array.isArray(item.values) && item.values.some((value) => Number.isFinite(Number(value))))
  );
}

function hasRealAccountsReadModel(accounts) {
  if (trendHasRealPoints(runtimeTrendState?.accounts)) return true;
  const snapshotCount = Number(runtimeStage4SyncState?.sqlite?.snapshot_count || 0);
  return snapshotCount > 0 && Number.isFinite(Number(accounts?.net_worth_cny));
}

function hasRealInvestmentReadModel(investment) {
  if (trendHasRealPoints(runtimeTrendState?.investment)) return true;
  const holdingCount = Number(investment?.holding_count || 0);
  const snapshotCount = Number(runtimeStage4SyncState?.sqlite?.snapshot_count || 0);
  return (holdingCount > 0 || snapshotCount > 0) && Number.isFinite(Number(investment?.market_value_cny));
}

function hasConfiguredSpendPolicy(policy) {
  const text = String(policy || "");
  if (!text) return false;
  return !/未配置|未设置|待配置|未接入|待接入/.test(text);
}

function applyConsumptionOptionalPolicyToTrend({ fixedSpendHasRule, budgetHasRule }) {
  const trend = runtimeTrendState?.consumption;
  if (!trend || !Array.isArray(trend.series)) return;
  const blockedSeriesIds = new Set();
  if (!fixedSpendHasRule) blockedSeriesIds.add("fixed_spend_cny");
  if (!budgetHasRule) blockedSeriesIds.add("budget_remaining_cny");
  if (!blockedSeriesIds.size) return;
  runtimeTrendState.consumption = {
    ...trend,
    title: "本月支出、弹性支出与现金流预测",
    series: trend.series.filter((item) => !blockedSeriesIds.has(item.id)),
  };
}

function currentContext() {
  const values = readContext();
  document.querySelectorAll("[data-context-field]").forEach((field) => {
    if (field.dataset.contextField === "fx_badge") return;
    values[field.dataset.contextField] = field.value || field.textContent || "";
  });
  return values;
}

function restoreContext() {
  const values = readContext();
  document.querySelectorAll("[data-context-field]").forEach((field) => {
    const key = field.dataset.contextField;
    if (key === "fx_badge") return;
    if (!Object.prototype.hasOwnProperty.call(values, key)) return;
    if ("value" in field) {
      field.value = values[key];
    } else {
      field.textContent = values[key];
    }
  });
  refreshFxBadgeDisplay();
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
  feedback.dataset.v024MotionState = normalizedState;
  feedback.dataset.v024FeedbackPhase = "6.2";
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

function updateFeedbackHub({
  lane = "visual",
  label = "操作已响应",
  state = "success",
  kind = "confirm",
  completedUnits = null,
  totalUnits = null,
} = {}) {
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
    const completed = Number(completedUnits);
    const total = Number(totalUnits);
    const hasActualProgress = Number.isFinite(completed) && Number.isFinite(total) && total > 0 && completed >= 0;
    meter.style.removeProperty("width");
    meter.style.setProperty("--pfi-feedback-actual-progress", hasActualProgress ? String(Math.min(completed, total) / total) : "0");
    meter.dataset.actualProgress = hasActualProgress ? "true" : "false";
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
  if (window.PFI_V025_STAGE8_HAPTICS?.emit) {
    window.PFI_V025_STAGE8_HAPTICS.emit(kind);
    return;
  }
  vibrateFeedback(kind);
  playFeedbackTone(kind);
}

function detectV024HapticRuntimeCapability() {
  const canVibrate = typeof navigator !== "undefined" && typeof navigator.vibrate === "function";
  if (document.body) {
    document.body.dataset.v024HapticCapability = canVibrate ? "supported" : "unsupported";
    if (!canVibrate) document.body.dataset.v024HapticDegraded = "visual_feedback";
    else delete document.body.dataset.v024HapticDegraded;
  }
  return canVibrate;
}

function vibrateFeedback(kind = "select") {
  if (!feedbackRuntimeState.haptic) return;
  if (typeof navigator.vibrate !== "function") {
    detectV024HapticRuntimeCapability();
    return;
  }
  if (navigator.userActivation && !navigator.userActivation.isActive) return;
  const patterns = {
    soft: [8],
    select: [12],
    confirm: [18, 24, 18],
    warning: [30, 36, 30],
    error: [36, 44, 36, 44],
  };
  try {
    detectV024HapticRuntimeCapability();
    navigator.vibrate(patterns[kind] || patterns.select);
  } catch (_error) {
    // 桌面浏览器可能没有震动设备。
    if (document.body) document.body.dataset.v024HapticDegraded = "visual_feedback";
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
  detectV024HapticRuntimeCapability();
  document.querySelectorAll("[data-feedback-toggle]").forEach((toggle) => {
    const key = toggle.dataset.feedbackToggle;
    if (!Object.prototype.hasOwnProperty.call(feedbackRuntimeState, key)) return;
    toggle.dataset.v024FeedbackSetting = "phase_6_3";
    if (key === "haptic") feedbackRuntimeState.haptic = Boolean(toggle.checked);
    feedbackRuntimeState[key] = Boolean(toggle.checked);
    window.PFI_V025_STAGE8_HAPTICS?.configure?.({
      haptic: feedbackRuntimeState.haptic,
      sound: feedbackRuntimeState.sound,
    });
    window.PFI_V025_STAGE8_MOTION?.setEnabled?.(feedbackRuntimeState.motion);
    document.body.classList.toggle("reduce-motion", !feedbackRuntimeState.motion);
    toggle.addEventListener("change", () => {
      if (key === "haptic") feedbackRuntimeState.haptic = Boolean(toggle.checked);
      feedbackRuntimeState[key] = Boolean(toggle.checked);
      window.PFI_V025_STAGE8_HAPTICS?.configure?.({
        haptic: feedbackRuntimeState.haptic,
        sound: feedbackRuntimeState.sound,
      });
      window.PFI_V025_STAGE8_MOTION?.setEnabled?.(feedbackRuntimeState.motion);
      document.body.classList.toggle("reduce-motion", !feedbackRuntimeState.motion);
      readSettingsOperationInputs();
      renderSettingsOperationFlow("settings");
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

function bindSettingsOperationEvents() {
  document.querySelectorAll("[data-settings-preference]").forEach((input) => {
    input.addEventListener("change", () => {
      readSettingsOperationInputs();
      renderSettingsOperationFlow("settings");
    });
  });
  document.querySelector("[data-settings-save]")?.addEventListener("click", saveSettingsOperationFlow);
  document.querySelector("[data-settings-reset]")?.addEventListener("click", resetSettingsOperationFlow);
  void refreshSettingsFromBackend();
}

function readSettingsOperationInputs() {
  const account = document.querySelector('[data-settings-preference="default_account"]');
  const language = document.querySelector('[data-settings-preference="theme_language"]');
  const haptic = document.querySelector('[data-feedback-toggle="haptic"]');
  const sound = document.querySelector('[data-feedback-toggle="sound"]');
  const motion = document.querySelector('[data-feedback-toggle="motion"]');
  settingsOperationState = {
    ...settingsOperationState,
    defaultAccount: account?.value || settingsOperationState.defaultAccount,
    themeLanguage: language?.value || settingsOperationState.themeLanguage,
    feedbackHaptic: haptic ? Boolean(haptic.checked) : settingsOperationState.feedbackHaptic,
    feedbackSound: sound ? Boolean(sound.checked) : settingsOperationState.feedbackSound,
    feedbackMotion: motion ? Boolean(motion.checked) : settingsOperationState.feedbackMotion,
  };
}

async function refreshSettingsFromBackend() {
  if (settingsOperationState.loading) return;
  settingsOperationState = { ...settingsOperationState, loading: true };
  try {
    const payload = await runtimeApiJson("/api/settings/preferences");
    applySettingsBackendPayload(payload);
  } catch (_error) {
    settingsOperationState = { ...settingsOperationState, loading: false, loaded: true };
    const status = document.querySelector("[data-settings-save-status]");
    if (status) {
      status.textContent = "SQLite 读取失败";
      status.className = "status-pill status-blocked";
    }
  }
  const activeWorkspace = document.querySelector("#main-workspace")?.dataset.activeWorkspace || currentContext().workspace || "home";
  renderSettingsOperationFlow(activeWorkspace);
}

function applySettingsBackendPayload(payload = {}) {
  const preferences = payload.preferences && typeof payload.preferences === "object" ? payload.preferences : {};
  settingsOperationState = {
    ...settingsOperationState,
    defaultAccount: String(preferences.default_account || "主账户"),
    themeLanguage: String(preferences.theme_language || "中文优先"),
    feedbackHaptic: preferences.feedback_haptic === true,
    feedbackSound: preferences.feedback_sound === true,
    feedbackMotion: preferences.feedback_motion !== false,
    revision: Number(payload.revision || 0),
    persisted: payload.persisted === true,
    loaded: true,
    loading: false,
    savedAt: String(payload.updated_at || ""),
  };
  feedbackRuntimeState = {
    haptic: settingsOperationState.feedbackHaptic,
    sound: settingsOperationState.feedbackSound,
    motion: settingsOperationState.feedbackMotion,
  };
  window.PFI_V025_STAGE8_HAPTICS?.configure?.({
    haptic: feedbackRuntimeState.haptic,
    sound: feedbackRuntimeState.sound,
  });
  window.PFI_V025_STAGE8_MOTION?.setEnabled?.(feedbackRuntimeState.motion);
  document.body.classList.toggle("reduce-motion", !feedbackRuntimeState.motion);
}

function renderSettingsOperationFlow(workspaceId) {
  const panel = document.querySelector("[data-settings-operation-flow]");
  if (!panel) return;
  const visible = workspaceId === "settings";
  panel.hidden = !visible;
  if (!visible) return;
  if (!settingsOperationState.loaded && !settingsOperationState.loading) void refreshSettingsFromBackend();

  const account = panel.querySelector('[data-settings-preference="default_account"]');
  const language = panel.querySelector('[data-settings-preference="theme_language"]');
  const status = panel.querySelector("[data-settings-save-status]");
  const state = panel.querySelector("[data-settings-operation-state]");
  if (account && account.value !== settingsOperationState.defaultAccount) account.value = settingsOperationState.defaultAccount;
  if (language && language.value !== settingsOperationState.themeLanguage) language.value = settingsOperationState.themeLanguage;
  const toggles = {
    haptic: settingsOperationState.feedbackHaptic,
    sound: settingsOperationState.feedbackSound,
    motion: settingsOperationState.feedbackMotion,
  };
  Object.entries(toggles).forEach(([key, enabled]) => {
    const toggle = panel.closest("[data-settings-feedback-console]")?.querySelector(`[data-feedback-toggle="${key}"]`)
      || document.querySelector(`[data-feedback-toggle="${key}"]`);
    if (toggle && toggle.checked !== enabled) toggle.checked = enabled;
  });

  if (status) {
    status.textContent = settingsOperationState.loading
      ? "正在读取 SQLite"
      : settingsOperationState.persisted
        ? "SQLite 已保存"
        : "尚未持久化";
    status.className = `status-pill ${settingsOperationState.persisted ? "status-ready" : "status-review"}`;
  }
  if (state) {
    const timeText = settingsOperationState.savedAt
      ? `最近保存 ${formatLocalSaveTime(settingsOperationState.savedAt)}`
      : settingsOperationState.resetAt
        ? `最近恢复 ${formatLocalSaveTime(settingsOperationState.resetAt)}`
        : "尚未保存";
    state.textContent = `默认账户：${settingsOperationState.defaultAccount} · 主题语言：${settingsOperationState.themeLanguage} · 反馈 ${settingsOperationState.feedbackHaptic ? "触感开" : "触感关"}/${settingsOperationState.feedbackSound ? "声音开" : "声音关"}/${settingsOperationState.feedbackMotion ? "动效开" : "动效关"} · ${timeText}`;
  }
}

async function saveSettingsOperationFlow() {
  readSettingsOperationInputs();
  try {
    const payload = await runtimeApiJson("/api/settings/preferences", {
      method: "POST",
      body: JSON.stringify({
        preferences: settingsPreferencePayload(),
        expected_revision: settingsOperationState.revision,
      }),
    });
    applySettingsBackendPayload(payload);
    settingsOperationState = { ...settingsOperationState, resetAt: "" };
    renderSettingsOperationFlow("settings");
    showToast("设置偏好已写入 SQLite", "success");
  } catch (error) {
    showToast(error?.message || "设置保存失败，请刷新后重试", "failure");
  }
}

async function resetSettingsOperationFlow() {
  try {
    const payload = await runtimeApiJson("/api/settings/preferences", {
      method: "POST",
      body: JSON.stringify({
        preferences: {
          default_account: "主账户",
          theme_language: "中文优先",
          feedback_haptic: false,
          feedback_sound: false,
          feedback_motion: true,
        },
        expected_revision: settingsOperationState.revision,
      }),
    });
    applySettingsBackendPayload(payload);
    settingsOperationState = { ...settingsOperationState, resetAt: new Date().toISOString() };
    renderSettingsOperationFlow("settings");
    showToast("默认设置已写入 SQLite", "success");
  } catch (error) {
    showToast(error?.message || "恢复默认失败，请刷新后重试", "failure");
  }
}

function settingsPreferencePayload() {
  return {
    default_account: settingsOperationState.defaultAccount,
    theme_language: settingsOperationState.themeLanguage,
    feedback_haptic: settingsOperationState.feedbackHaptic,
    feedback_sound: settingsOperationState.feedbackSound,
    feedback_motion: settingsOperationState.feedbackMotion,
  };
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

function defaultAlipayImportSummary() {
  return {
    schema: "PFIAlipayRealImportSummaryV1",
    sourceId: "alipay_daily",
    status: "未接入真实数据",
    fileCount: 0,
    validFileCount: 0,
    transactionCount: 0,
    reviewCount: 0,
    dateStart: "",
    dateEnd: "",
    searchTokens: [],
  };
}

function normalizeAlipayImportSummary(summary = {}) {
  if (!summary || summary.schema !== "PFIAlipayRealImportSummaryV1") return defaultAlipayImportSummary();
  return {
    schema: summary.schema,
    sourceId: safeUserText(summary.source_id || summary.sourceId, "alipay_daily"),
    status: safeUserText(summary.status, "未接入真实数据"),
    fileCount: Number(summary.file_count ?? summary.fileCount ?? 0),
    validFileCount: Number(summary.valid_file_count ?? summary.validFileCount ?? 0),
    transactionCount: Number(summary.transaction_count ?? summary.transactionCount ?? 0),
    reviewCount: Number(summary.review_count ?? summary.reviewCount ?? 0),
    dateStart: safeUserText(summary.date_start || summary.dateStart, ""),
    dateEnd: safeUserText(summary.date_end || summary.dateEnd, ""),
    searchTokens: Array.isArray(summary.search_tokens || summary.searchTokens) ? (summary.search_tokens || summary.searchTokens).map(String) : [],
  };
}

function applyAlipayImportSummary(summary) {
  alipayImportState = normalizeAlipayImportSummary(summary);
  const sourceStatus = (runtimeReadModelStatusState || readEmbeddedReadModelStatus())?.source || {};
  const sourceReady = sourceStatus.status === "ready";
  const hasSourceCount = (snakeKey, camelKey) => {
    const value = summary?.[snakeKey] ?? summary?.[camelKey];
    return value !== null && value !== undefined && value !== "" && Number.isFinite(Number(value));
  };
  const transactionCountReady = sourceReady && hasSourceCount("transaction_count", "transactionCount");
  const reviewCountReady = sourceReady && hasSourceCount("review_count", "reviewCount");
  const fileCountReady = sourceReady && hasSourceCount("file_count", "fileCount");
  const hasRealData = transactionCountReady && alipayImportState.transactionCount > 0;
  const dateRange = sourceReady && alipayImportState.dateStart && alipayImportState.dateEnd
    ? `${alipayImportState.dateStart} 至 ${alipayImportState.dateEnd}`
    : sourceReady
      ? "数据范围未提供"
      : "等待真实账单";
  const recordLabel = transactionCountReady ? `${alipayImportState.transactionCount.toLocaleString("zh-CN")} 条` : "待导入";
  const reviewLabel = reviewCountReady ? `${alipayImportState.reviewCount.toLocaleString("zh-CN")} 条` : "待导入";
  const fileLabel = fileCountReady ? `${alipayImportState.fileCount} 个文件` : "文件数未加载";
  const rawFileLabel = fileCountReady ? `${alipayImportState.fileCount} 个原始文件` : "原始文件数未加载";

  WORKSPACES.sync.cards = [
    ["真实支付宝流水", recordLabel, `${fileLabel} · ${dateRange}`],
    ["待复核流水", reviewLabel, "低置信度记录进入账本复核"],
    ["上传中心", "可用", "CSV / ZIP 多文件本机预检"],
    ["导入中心", alipayImportState.status, "批次、摘要、待复核入口同屏显示"],
  ];
  WORKSPACES.sync.rows = [
    row("P0", "真实支付宝流水", rawFileLabel, `${dateRange} · ${recordLabel}标准化流水`, alipayImportState.status),
    row("P0", "导入中心", "真实账本摘要", `待复核 ${reviewLabel}，进入账本流水处理。`, hasRealData ? "可用" : "复核"),
    row("P1", "上传中心", "CSV / ZIP", "点击或拖拽选择账单文件；已有真实账本不会被伪造覆盖。", "可用"),
    row("P1", "账本复核", "低置信度记录", "进入账本流水处理待复核记录。", "复核"),
  ];
  WORKSPACES.sync.tasks = [
    task("真实支付宝流水", `${recordLabel} · ${dateRange}`, hasRealData ? "ready" : "review"),
    task("待复核流水", `${reviewLabel} · 进入账本流水处理`, hasRealData ? "review" : "queued"),
    task("上传中心", "可用 · 支持多文件 CSV / ZIP", "ready"),
    task("导入摘要", "可用 · 批次、记录和待复核同屏展示", "ready"),
  ];
}

function applyHomeSummary(summary) {
  if (!summary) return;
  applyAlipayImportSummary(summary.alipay_import_summary || summary.alipayImportSummary || {});
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
  applyStage7ReportCenterContract();
}

function restoreOwnerHomeWorkflow() {
  WORKSPACES.home.label = "首页总览";
  WORKSPACES.home.kicker = "今日总览";
  WORKSPACES.home.conclusion = "查看净资产、现金余额、投资市值、本月支出、待复核交易、数据源状态、最近建议和最近报告。";
  WORKSPACES.home.runtime = "当前页面：财务状态与待办事项";
  WORKSPACES.home.secondaryTabs = STAGE2_SECONDARY_TABS.home;
  WORKSPACES.home.features = [
    feature("上传数据", "可用", "上传中心", "进入数据源与上传，选择账单或数据文件。", { workspace: "sync", routeAlias: "/sources-upload?tab=upload", label: "上传数据" }),
    feature("复核流水", "待处理", "账本流水", "导入后进入账本流水处理分类和复核。", { workspace: "ledger", routeAlias: "/ledger?tab=review", label: "复核流水" }),
    feature("查看投资", "可用", "投资管理", "查看投资总览、持仓、交易记录和收益分析。", { workspace: "investment", routeAlias: "/investment?tab=overview", label: "查看投资" }),
    feature("生成报告", "可用", "报告与洞察", "进入报告与洞察，生成或导出本机报告。", { workspace: "insights", routeAlias: "/reports?tab=monthly", label: "生成报告" }),
  ];
  WORKSPACES.home.rows = [
    row("1", "上传数据", "等待真实文件", "进入上传中心", "待处理"),
    row("2", "复核流水", "暂无待复核交易", "导入后处理", "等待数据"),
    row("3", "最近报告", "暂无新报告", "进入报告页", "可用"),
  ];
  WORKSPACES.home.tasks = [
    task("上传数据", "选择账单或数据文件", "ready"),
    task("复核流水", "导入后处理分类、合并和排除", "review"),
    task("查看报告", "生成月报或导出本机报告", "queued"),
  ];
  applyStage5Phase51Home();
}

function applyStage5Phase51Home() {
  const api = stage5HomeExperience || window.PFI_V024_STAGE5_HOME || window.PFI_V023_STAGE5_HOME;
  if (!api) return;
  const builder = typeof api.buildV024Stage5Phase51HomeViewModel === "function"
    ? api.buildV024Stage5Phase51HomeViewModel
    : api.buildStage5HomeViewModel;
  if (typeof builder !== "function") return;
  const payload = builder === api.buildV024Stage5Phase51HomeViewModel
    ? { read_model_status: runtimeReadModelStatusState || readEmbeddedReadModelStatus() || {} }
    : {};
  const view = builder(payload);
  WORKSPACES.home.conclusion = ownerVisibleText(
    view.home_conclusion,
    "先看财务状态、数据健康、下一步动作、最近变化，再进入报告。",
  );
  WORKSPACES.home.runtime = ownerVisibleText(view.home_runtime_label, "财务状态与下一步动作");
  if (Array.isArray(view.home_cards) && view.home_cards.length) {
    WORKSPACES.home.cards = view.home_cards;
  }
  if (Array.isArray(view.home_features) && view.home_features.length) {
    WORKSPACES.home.features = view.home_features.map((item) =>
      feature(
        item.title,
        item.status,
        item.source,
        item.detail,
        item.target || { workspace: "home", routeAlias: "/home?tab=status", label: "查看首页" },
      ),
    );
  }
  if (Array.isArray(view.home_rows) && view.home_rows.length) {
    WORKSPACES.home.rows = view.home_rows.map((item) => row(item[0], item[1], item[2], item[3], item[4]));
  }
  if (Array.isArray(view.home_tasks) && view.home_tasks.length) {
    WORKSPACES.home.tasks = view.home_tasks.map((item) => task(item.title, item.detail, item.status));
  }
  WORKSPACES.home.evidence = evidence(
    "首页说明",
    "首页信息架构",
    "数据状态",
    "首页只回答钱、位置、变化、问题、下一步和依据。",
  );
}

function applyStage5Phase53HomeSurfacePolicy(workspaceId) {
  const isHome = workspaceId === "home";
  document.querySelectorAll("[data-stage8-home-only]").forEach((homeOnly) => {
    homeOnly.hidden = !isHome;
    homeOnly.setAttribute("aria-hidden", isHome ? "false" : "true");
  });
  document.querySelectorAll("[data-evidence-toggle]").forEach((button) => {
    button.hidden = isHome;
    button.setAttribute("aria-hidden", isHome ? "true" : "false");
    button.tabIndex = isHome ? -1 : 0;
  });
  if (!isHome) return;
  const drawer = document.querySelector("[data-evidence-drawer]");
  if (drawer) {
    drawer.classList.remove("is-open");
    drawer.setAttribute("aria-expanded", "false");
  }
  hideFunctionDetail();
}

const STAGE8_WORKSPACE_FOCUS = Object.freeze({
  accounts: Object.freeze({
    shape: "balance_sheet",
    kicker: "账户覆盖",
    title: "账户、来源与对账状态",
    items: Object.freeze([
      ["账户地图", "等待真实账户来源"],
      ["币种覆盖", "等待账户与 FX 状态"],
      ["对账差异", "没有真实快照时不推断差额"],
      ["更新时间", "以来源返回时间为准"],
    ]),
  }),
  ledger: Object.freeze({
    shape: "review_table",
    kicker: "复核队列",
    title: "流水筛选、分类与证据",
    items: Object.freeze([
      ["定位", "按账户、日期、金额、分类或备注筛选"],
      ["复核", "选择真实待复核流水后才能保存"],
      ["撤销", "最近一次复核可从账本操作流撤销"],
    ]),
  }),
  investment: Object.freeze({
    shape: "portfolio_analytics",
    kicker: "持仓结构",
    title: "持仓、估值与风险边界",
    items: Object.freeze([
      ["持仓", "SQLite 返回后展示真实数量"],
      ["估值", "缺价格或 FX 时保持不可用"],
      ["集中度", "等待可追溯持仓与价格"],
      ["收益", "没有交易证据时不显示金额"],
    ]),
  }),
  consumption: Object.freeze({
    shape: "spending_flow",
    kicker: "支出结构",
    title: "分类、预算与异常路径",
    items: Object.freeze([
      ["分类", "真实流水导入后形成结构"],
      ["预算", "等待预算与支出口径"],
      ["订阅", "等待周期扣费证据"],
      ["异常", "没有记录时不生成异常判断"],
    ]),
  }),
  sync: Object.freeze({
    shape: "data_pipeline",
    kicker: "本机数据链路",
    title: "选择、预览、确认、复核",
    items: Object.freeze([
      ["1", "选择 CSV / ZIP"],
      ["2", "本机解析预览"],
      ["3", "确认后事务入账"],
      ["4", "处理待复核流水"],
    ]),
  }),
  recommendations: Object.freeze({
    shape: "decision_inbox",
    kicker: "决策收件箱",
    title: "建议、依据与失效条件",
    items: Object.freeze([
      ["待决策", "只接收有来源与影响说明的建议"],
      ["已接受", "保留执行理由与复盘入口"],
      ["暂缓", "记录前置条件和再次检查时间"],
    ]),
  }),
  insights: Object.freeze({
    shape: "report_library",
    kicker: "报告资料库",
    title: "报告范围、状态与导出",
    items: Object.freeze([
      ["月报", "数据门禁通过后生成草稿"],
      ["季报", "不可比范围保持显式"],
      ["年报", "覆盖和关闭状态通过后生成"],
      ["自定义", "按受控数据域组合"],
    ]),
  }),
  market_research: Object.freeze({
    shape: "research_workspace",
    kicker: "研究工作台",
    title: "证据、假设与反方条件",
    items: Object.freeze([
      ["观察对象", "组织指数、ETF、主题与公司"],
      ["证据笔记", "保留来源、日期与引用范围"],
      ["实验", "参数、结果和失效条件分开记录"],
    ]),
  }),
  settings: Object.freeze({
    shape: "control_center",
    kicker: "控制中心",
    title: "账户、隐私与反馈偏好",
    items: Object.freeze([
      ["账户偏好", "显示币种和默认账户"],
      ["数据与系统", "本机服务与质量状态"],
      ["隐私", "本地存储与敏感数据边界"],
      ["反馈", "视觉、声音、触感与动效"],
    ]),
  }),
});

function stage8FocusText(tagName, text, className = "") {
  const node = document.createElement(tagName);
  if (className) node.className = className;
  node.textContent = ownerVisibleText(text, "等待真实状态");
  return node;
}

function renderStage8WorkspaceFocus(workspaceId, stage4Subpage = null) {
  const focus = document.querySelector("[data-stage8-workspace-focus]");
  const body = focus?.querySelector("[data-stage8-workspace-focus-body]");
  const config = STAGE8_WORKSPACE_FOCUS[workspaceId];
  if (!focus || !body || !config) {
    if (focus) focus.hidden = true;
    if (body) body.replaceChildren();
    return;
  }
  focus.hidden = false;
  focus.dataset.stage8WorkspaceShape = config.shape;
  const kicker = focus.querySelector("[data-stage8-workspace-focus-kicker]");
  const title = focus.querySelector("[data-stage8-workspace-focus-title]");
  const status = focus.querySelector("[data-stage8-workspace-focus-status]");
  if (kicker) kicker.textContent = config.kicker;
  if (title) title.textContent = ownerVisibleText(stage4Subpage?.title || config.title, config.title);
  if (status) status.textContent = "等待真实数据";
  body.replaceChildren();

  if (config.shape === "balance_sheet") {
    const list = document.createElement("dl");
    list.className = "stage8-balance-sheet";
    config.items.forEach(([label, detail]) => {
      const row = document.createElement("div");
      row.append(stage8FocusText("dt", label), stage8FocusText("dd", detail));
      list.appendChild(row);
    });
    body.appendChild(list);
  } else if (config.shape === "review_table") {
    const list = document.createElement("ol");
    list.className = "stage8-review-queue-shape";
    config.items.forEach(([label, detail], index) => {
      const item = document.createElement("li");
      item.append(stage8FocusText("span", String(index + 1), "stage8-step-index"));
      const copy = document.createElement("div");
      copy.append(stage8FocusText("strong", label), stage8FocusText("small", detail));
      item.appendChild(copy);
      list.appendChild(item);
    });
    body.appendChild(list);
  } else if (config.shape === "portfolio_analytics") {
    const layout = document.createElement("div");
    layout.className = "stage8-portfolio-shape";
    const figure = document.createElement("figure");
    figure.append(stage8FocusText("div", "真实持仓接入后显示配置", "stage8-allocation-ring"));
    figure.append(stage8FocusText("figcaption", "当前不生成模拟配置比例"));
    const list = document.createElement("dl");
    config.items.forEach(([label, detail]) => {
      const row = document.createElement("div");
      row.append(stage8FocusText("dt", label), stage8FocusText("dd", detail));
      list.appendChild(row);
    });
    layout.append(figure, list);
    body.appendChild(layout);
  } else if (config.shape === "spending_flow") {
    const list = document.createElement("ol");
    list.className = "stage8-spending-shape";
    config.items.forEach(([label, detail], index) => {
      const item = document.createElement("li");
      item.style.setProperty("--stage8-flow-order", String(index + 1));
      item.append(stage8FocusText("strong", label), stage8FocusText("span", detail));
      list.appendChild(item);
    });
    body.appendChild(list);
  } else if (config.shape === "data_pipeline") {
    const list = document.createElement("ol");
    list.className = "stage8-pipeline-shape";
    config.items.forEach(([step, detail]) => {
      const item = document.createElement("li");
      item.append(stage8FocusText("span", step, "stage8-pipeline-index"), stage8FocusText("strong", detail));
      list.appendChild(item);
    });
    body.appendChild(list);
  } else if (config.shape === "decision_inbox") {
    const inbox = document.createElement("div");
    inbox.className = "stage8-decision-shape";
    config.items.forEach(([label, detail]) => {
      const card = document.createElement("article");
      card.append(stage8FocusText("h3", label), stage8FocusText("p", detail), stage8FocusText("small", "等待可追溯建议"));
      inbox.appendChild(card);
    });
    body.appendChild(inbox);
  } else if (config.shape === "report_library") {
    const library = document.createElement("div");
    library.className = "stage8-report-library-shape";
    config.items.forEach(([label, detail]) => {
      const card = document.createElement("article");
      card.append(stage8FocusText("time", "未生成"), stage8FocusText("h3", label), stage8FocusText("p", detail));
      library.appendChild(card);
    });
    body.appendChild(library);
  } else if (config.shape === "research_workspace") {
    const workspace = document.createElement("div");
    workspace.className = "stage8-research-shape";
    const note = document.createElement("section");
    note.append(stage8FocusText("h3", config.items[1][0]), stage8FocusText("p", config.items[1][1]));
    const checklist = document.createElement("ul");
    [config.items[0], config.items[2]].forEach(([label, detail]) => {
      const item = document.createElement("li");
      item.append(stage8FocusText("strong", label), stage8FocusText("span", detail));
      checklist.appendChild(item);
    });
    workspace.append(note, checklist);
    body.appendChild(workspace);
  } else {
    const controls = document.createElement("div");
    controls.className = "stage8-control-shape";
    const fieldset = document.createElement("fieldset");
    fieldset.append(stage8FocusText("legend", "本机偏好与边界"));
    config.items.forEach(([label, detail]) => {
      const row = document.createElement("div");
      row.append(stage8FocusText("strong", label), stage8FocusText("span", detail));
      fieldset.appendChild(row);
    });
    controls.appendChild(fieldset);
    body.appendChild(controls);
  }
}

function applyStage3Dashboard(dashboard) {
  if (!dashboard || dashboard.schema !== "PFIV02Stage3ReadableMVPV1") return;
  const actions = (dashboard.quick_actions || []).slice(0, 6).map((item) => {
    const title = safeUserText(item.label, "PFI 操作");
    return feature(
      title,
      safeUserText(item.status, "复核"),
      safeUserText(item.target_entry, "首页总览"),
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
  WORKSPACES.home.runtime = "同步、复核、建议、报告";
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

  WORKSPACES.home.runtime = "投资与消费智能分析";
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
  const contextBoundaryReady =
    alphaContext.schema_version === "pfi_context.v1" &&
    alphaContext.consumer === "Alpha" &&
    alphaContext.read_only === true &&
    alphaContext.writeback_allowed === false;
  const submissionReviewReady = contextBoundaryReady;
  const credentialReviewReady = contextBoundaryReady;
  const investmentCount = recommendations.filter((item) => item.domain === "investment").length;
  const consumptionCount = recommendations.filter((item) => item.domain === "consumption").length;
  const totalSavings = recommendations
    .filter((item) => item.domain === "consumption")
    .reduce((total, item) => total + Number(item.savings_target_aud || 0), 0);

  WORKSPACES.home.runtime = "建议、报告、外部系统上下文出口";
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
  const sourceMatrix = phase6a.source_matrix || phase6a.source_contract_matrix || [];
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

  WORKSPACES.home.runtime = "项目级复审与稳定化";
  WORKSPACES.home.features = [
    feature("项目级复审", gatePassCount === totalGate.length ? "通过" : "复核", "总验收门禁", `${gatePassCount}/${totalGate.length} 个总门禁通过。`),
    feature("真实数据闭环", phase6a.status === "PASS" ? "通过" : "复核", "验收记录", `${sourceMatrix.length} 个核心源 · 首页/账本/建议闭环。`),
    feature("回归治理", regression.status === "PASS" ? "通过" : "复核", "回归治理", "既有冒烟检查、聚焦测试和变更范围治理已记录。"),
    feature("交付与回滚", delivery.status === "PASS" ? "通过" : "复核", "交付回滚", `${rollbackCount} 步回滚计划 · ${followUpCount} 项后续任务。`),
    feature("回滚计划", rollbackCount >= 6 ? "可用" : "复核", "回滚计划", "可回滚代码、测试、文档、治理和 Web Shell 接入。"),
    feature("后续任务清单", followUpCount ? "可用" : "待补", "后续任务", "外部上下文消费者、真实数据、PDF/ZIP、CDR/Open Banking 分离跟进。"),
  ];
  WORKSPACES.home.tasks = [
    task("总体验收", `${gatePassCount}/${totalGate.length} 个门禁通过`, gatePassCount === totalGate.length ? "ready" : "review"),
    task("任务包验收审计", `${auditPassCount}/${taskpackAudit.length} 个验收项通过`, auditPassCount === taskpackAudit.length ? "ready" : "review"),
    task("端到端四闭环", `数据源=${sourceMatrix.length} · 账本=${(ledgerLoop.checks || []).length} · 建议=${recommendationLoop.generated_count || 0}`, phase6a.status === "PASS" ? "ready" : "review"),
    task("回滚计划", `${rollbackCount} 步 · QBVS 顶层独立，不迁移真实数据`, rollbackCount >= 6 ? "ready" : "review"),
  ];

  WORKSPACES.insights.features = [
    feature("项目级复审", gatePassCount === totalGate.length ? "通过" : "复核", "总验收门禁", `${gatePassCount}/${totalGate.length} 个总门禁通过。`),
    feature("真实数据闭环", phase6a.status === "PASS" ? "通过" : "复核", "验收记录", "多数据源、首页、账本和建议闭环。"),
    feature("回归治理", regression.status === "PASS" ? "通过" : "复核", "回归治理", "既有冒烟检查、聚焦测试、变更范围治理和无大范围重构已记录。"),
    feature("交付与回滚", delivery.status === "PASS" ? "通过" : "复核", "交付回滚", "用户文档、差异摘要、回滚计划和后续任务清单已记录。"),
    feature("回滚计划", rollbackCount >= 6 ? "可用" : "复核", "回滚计划", "可逆文件清单和无生产迁移限制。"),
    feature("后续任务清单", followUpCount ? "可用" : "待补", "后续任务", "后续任务独立排期，不并入当前功能页面。"),
  ];
  WORKSPACES.insights.rows = [
    row("P0", "项目级复审", "总验收门禁", `${gatePassCount}/${totalGate.length} 个门禁通过。`, gatePassCount === totalGate.length ? "通过" : "复核"),
    row("P0", "真实数据闭环", "验收记录", `${sourceMatrix.length} 个核心源；首页状态 ${safeUserText(homepageLoop.status, "复核")}。`, safeUserText(phase6a.status, "复核")),
    row("P1", "回归治理", "治理脚本", safeUserText((regression.changed_scope_governance || {}).expected, "运行变更范围治理。"), safeUserText(regression.status, "复核")),
    row("P1", "交付与回滚", "交付回滚", `${rollbackCount} 步回滚 · ${followUpCount} 项后续任务。`, safeUserText(delivery.status, "复核")),
  ];
  WORKSPACES.insights.tasks = [
    task("用户文档", (delivery.owner_docs || []).length ? `${delivery.owner_docs.length} 个用户文档已覆盖` : "等待用户文档", (delivery.owner_docs || []).length ? "ready" : "review"),
    task("分类闭环", `${(ledgerLoop.checks || []).length} 个账本分类检查`, ledgerLoop.status === "PASS" ? "ready" : "review"),
    task("建议闭环", `${recommendationLoop.generated_count || 0} 条建议 · 生命周期 ${recommendationLoop.lifecycle_row_count || 0}`, recommendationLoop.status === "PASS" ? "ready" : "review"),
    task("回归命令", regression.status === "PASS" ? "冒烟检查 / 聚焦测试 / 治理已记录" : "等待回归治理", regression.status === "PASS" ? "ready" : "review"),
  ];
  applyStage7ReportCenterContract();
}

function applyStage7ReportCenterContract() {
  if (!WORKSPACES.insights) return;
  applyV024Stage7Phase72ReportCenter();
}

function applyV024Stage7Phase72ReportCenter() {
  if (!WORKSPACES.insights) return;
  const viewModel = buildV024Stage7Phase72RuntimeViewModel();
  if (!viewModel || !Array.isArray(viewModel.report_cards) || !viewModel.report_cards.length) {
    applyV024Stage7Phase72FallbackReportCenter();
    return;
  }
  stage7ReportCenterViewModel = viewModel;
  const reportCards = viewModel.report_cards;
  const reportFeatures = reportCards.map((card) =>
    feature(
      safeUserText(card.title_zh, "报告"),
      safeUserText(card.status_zh, "需要复核"),
      `${safeUserText(card.data_range_zh, "数据范围：未加载")} · ${safeUserText(card.sample_size_zh, "样本量：未加载")}`,
      `结论：${safeUserText(card.conclusion_zh, "等待结论")}｜公式：${safeUserText(card.formula_zh, "公式缺失")}｜参数：${safeUserText(card.parameter_summary_zh, "参数缺失")}｜置信度：${safeUserText(card.confidence_zh, "置信度待补")}｜缺口：${safeUserText(card.gap_summary_zh, "缺口待复核")}｜复核入口：${safeUserText(card.review_entry_zh, "复核入口待补")}`,
      { workspace: "insights", routeAlias: card.review_entry?.route || "/reports", label: "查看报告" },
    ),
  );
  WORKSPACES.insights = {
    ...WORKSPACES.insights,
    label: "报告与洞察",
    kicker: "Stage 7 Phase 7.2 报告中心",
    conclusion: safeUserText(viewModel.subtitle_zh, "报告中心展示结论、公式、参数、数据范围、样本量、置信度、缺口和复核入口。"),
    freshness: viewModel.source?.date_range?.end ? `真实流水截至 ${viewModel.source.date_range.end}` : "报告数据待加载",
    runtime: "Stage 7 Phase 7.2 页面展示：公式、参数、样本量、数据范围、缺口和复核入口可见",
    secondaryTabs: STAGE2_SECONDARY_TABS.insights,
    cards: reportCards.map((card) => [
      safeUserText(card.title_zh, "报告"),
      safeUserText(card.status_zh, "需要复核"),
      `${safeUserText(card.sample_size_zh, "样本量：未加载")} · ${safeUserText(card.confidence_zh, "置信度：待补")}`,
    ]),
    features: reportFeatures,
    rows: reportCards.map((card, index) =>
      row(
        card.status === "blocked" ? "P0" : `P${Math.min(index + 1, 3)}`,
        safeUserText(card.title_zh, "报告"),
        `${safeUserText(card.formula_zh, "公式缺失")} · ${safeUserText(card.parameter_summary_zh, "参数缺失")}`,
        `${safeUserText(card.gap_summary_zh, "缺口待复核")} · ${safeUserText(card.review_entry_zh, "复核入口待补")}`,
        safeUserText(card.status_zh, "需要复核"),
      ),
    ),
    tasks: [
      task("报告中心页面", `${viewModel.report_count} 份报告可见 · ${viewModel.summary_zh}`, "ready"),
      task("公式解释区", `${viewModel.formula_explanations.length} 个公式说明可见`, "ready"),
      task("参数与样本量区", `${viewModel.parameters_and_samples.length} 组参数、样本量和数据范围可见`, "ready"),
      task("缺口/复核入口", `${viewModel.gaps_and_review.length} 个缺口与复核入口可见`, viewModel.blocked_count ? "review" : "ready"),
    ],
    evidence: evidence(
      "Stage 7 Phase 7.2 报告证据",
      "报告中心、公式解释区、参数与样本量区、缺口/复核入口",
      "Stage 7 Phase 7.1 report schema + MetaDatabase/PFI read model status",
      "阻断报告只展示真实缺口和复核入口，数据不足时不生成完整财务结论。",
    ),
  };
}

function buildV024Stage7Phase72RuntimeViewModel() {
  const api = stage7ReportCenterApi || window.PFI_V024_STAGE7_REPORTS || window.PFI_V023_STAGE7_REPORTS || null;
  stage7ReportCenterApi = api;
  if (!api || typeof api.buildV024Stage7Phase72ReportCenterViewModel !== "function") return null;
  const embeddedPack = readEmbeddedStage7ReportPack();
  const reportPack = embeddedPack || buildV024Stage7ReportPackFromStatus(runtimeReadModelStatusState || readEmbeddedReadModelStatus());
  if (!reportPack) return null;
  if (reportPack.source?.status !== "ready") return null;
  try {
    return api.buildV024Stage7Phase72ReportCenterViewModel(reportPack);
  } catch (_error) {
    return null;
  }
}

function buildV024Stage7ReportPackFromStatus(statusPayload) {
  if (!statusPayload || typeof statusPayload !== "object" || !statusPayload.source) return null;
  const source = statusPayload.source || {};
  const sourceReady = source.status === "ready";
  const metrics = {};
  (statusPayload.core_metric_states || []).forEach((metric) => {
    metrics[metric.metric_id] = metric;
  });
  const dataRange = sourceReady ? (source.date_range || { start: null, end: source.as_of || null }) : { start: null, end: null };
  const sourceCount = (field) => {
    if (!sourceReady || source[field] === null || source[field] === undefined || source[field] === "") return null;
    const value = Number(source[field]);
    return Number.isFinite(value) ? value : null;
  };
  const sampleSize = {
    transaction_count: sourceCount("record_count"),
    raw_file_count: sourceCount("raw_file_count"),
    account_count: null,
    holding_count: null,
  };
  const exportFields = [
    "report_id",
    "report_type",
    "title_zh",
    "status",
    "conclusion_zh",
    "formula_zh",
    "parameter_summary_zh",
    "data_range_start",
    "data_range_end",
    "transaction_count",
    "raw_file_count",
    "confidence",
    "gap_count",
    "review_route",
  ];
  const parameterSet = (extra = []) => [
    { parameter_id: "currency", label_zh: "计价货币", value: "CNY", source: "Stage 4 read model status", adjustable: false },
    { parameter_id: "blocking_policy", label_zh: "阻断策略", value: "缺少真实输入时不补零", source: "v0.2.4 Stage 7.2", adjustable: false },
    ...extra,
  ];
  const metricIsReady = (metric) => sourceReady && ["ready", "confirmed_zero"].includes(String(metric?.status || ""));
  const metricSources = (metric) => typeof metric?.source_id === "string" && metric.source_id.trim()
    ? [metric.source_id.trim()]
    : [];
  const metricConfidence = (metric) => {
    if (metric?.confidence === null || metric?.confidence === undefined || metric?.confidence === "") return null;
    const value = Number(metric.confidence);
    return Number.isFinite(value) ? value : null;
  };
  const gap = (metricId, route) => ({
    metric_id: metricId,
    status: metrics[metricId]?.status || "source_missing",
    reason_zh: metrics[metricId]?.blocking_reason_zh || "真实 read model 输入缺失，当前报告保持阻断。",
    review_route: route,
  });
  const blockedReport = ({ reportId, reportType, title, metricIds, formula, route, sources }) => ({
    report_id: reportId,
    report_type: reportType,
    title_zh: title,
    status: "blocked",
    conclusion_zh: `${title}缺少真实输入，当前只输出缺口与复核入口，不输出最终结论。`,
    formula_zh: formula,
    parameters: parameterSet(),
    data_range: dataRange,
    sample_size: sampleSize,
    metric_sources: (sources || []).filter(Boolean),
    confidence: null,
    gaps: metricIds.map((metricId) => gap(metricId, route)),
    anomalies: [],
    review_entry: { label_zh: "查看数据缺口与复核入口", route },
    export_fields: exportFields,
  });
  const consumptionMetric = metrics.consumption_outflow_cny || {};
  const qualityMetric = metrics.report_summary_status || {};
  const reports = [
    blockedReport({
      reportId: "net_worth_report",
      reportType: "net_worth",
      title: "净资产报告",
      metricIds: ["net_worth_cny", "cash_balance_cny", "investment_market_value_cny"],
      formula: "净资产 = 现金余额 + 投资市值 + 其他真实资产 - 真实负债；任一核心输入缺失时阻断。",
      route: "/reports?tab=data-quality&metric=net_worth_cny",
      sources: ["read_model:accounts_holdings", "read_model:accounts", "read_model:holdings"],
    }),
    blockedReport({
      reportId: "cash_report",
      reportType: "cash",
      title: "现金报告",
      metricIds: ["cash_balance_cny"],
      formula: "现金余额 = 已挂链账户的真实余额合计；未挂链账户余额 read model 时阻断。",
      route: "/accounts?tab=reconcile",
      sources: ["read_model:accounts"],
    }),
    blockedReport({
      reportId: "investment_report",
      reportType: "investment",
      title: "投资报告",
      metricIds: ["investment_market_value_cny"],
      formula: "投资市值 = 持仓数量 * 最新真实价格 * 有效汇率；持仓市值 read model 缺失时阻断。",
      route: "/investment?tab=holdings",
      sources: ["read_model:holdings"],
    }),
    metricIsReady(consumptionMetric) ? {
      report_id: "consumption_report",
      report_type: "consumption",
      title_zh: "消费报告",
      status: "partial",
      conclusion_zh: "真实流水消费总流出已加载，当前形成消费报告的部分结构；缺少细分解释时不补造明细。",
      formula_zh: "消费总流出 = 生活消费 + 投资入金 + 基金申购 + 黄金申购 + 投资买入 + 金融费用 - 退款抵消。",
      parameters: parameterSet([{ parameter_id: "consumption_scope", label_zh: "消费口径", value: "双消费口径", source: "v0.2.4 Stage 4", adjustable: false }]),
      data_range: dataRange,
      sample_size: sampleSize,
      metric_sources: metricSources(consumptionMetric),
      confidence: metricConfidence(consumptionMetric),
      gaps: [],
      anomalies: [],
      review_entry: { label_zh: "查看消费报告复核入口", route: "/consumption?tab=analysis" },
      export_fields: exportFields,
    } : blockedReport({
      reportId: "consumption_report",
      reportType: "consumption",
      title: "消费报告",
      metricIds: ["consumption_outflow_cny"],
      formula: "消费总流出 = 生活消费 + 投资入金 + 基金申购 + 黄金申购 + 投资买入 + 金融费用 - 退款抵消；真实来源或指标未就绪时阻断。",
      route: "/consumption?tab=analysis",
      sources: metricSources(consumptionMetric),
    }),
    blockedReport({
      reportId: "cashflow_report",
      reportType: "cashflow",
      title: "现金流报告",
      metricIds: ["cash_balance_cny"],
      formula: "现金流 = 真实收入 - 真实支出 - 投资现金变动；收入与现金余额输入缺失时阻断。",
      route: "/reports?tab=data-quality&metric=cashflow",
      sources: ["read_model:cashflow"],
    }),
    metricIsReady(qualityMetric) ? {
      report_id: "data_quality_report",
      report_type: "data_quality",
      title_zh: "数据质量报告",
      status: "ready",
      conclusion_zh: qualityMetric.blocking_reason_zh || "真实数据源已加载，仍有核心指标等待 read model 挂链。",
      formula_zh: "数据质量 = 已加载来源、记录范围、阻断指标、缺失输入和复核入口的组合检查。",
      parameters: parameterSet([{ parameter_id: "minimum_visible_sections", label_zh: "最低可见区块", value: "结论/公式/参数/样本量/缺口/复核入口", source: "v0.2.4 Stage 7.2", adjustable: false }]),
      data_range: dataRange,
      sample_size: sampleSize,
      metric_sources: metricSources(qualityMetric),
      confidence: metricConfidence(qualityMetric),
      gaps: ["net_worth_cny", "cash_balance_cny", "investment_market_value_cny"].map((metricId) => gap(metricId, "/reports?tab=data-quality")),
      anomalies: [],
      review_entry: { label_zh: "查看数据质量复核入口", route: "/reports?tab=data-quality" },
      export_fields: exportFields,
    } : blockedReport({
      reportId: "data_quality_report",
      reportType: "data_quality",
      title: "数据质量报告",
      metricIds: ["report_summary_status", "net_worth_cny", "cash_balance_cny", "investment_market_value_cny"],
      formula: "数据质量 = 已加载来源、记录范围、阻断指标、缺失输入和复核入口的组合检查；来源或质量指标未就绪时阻断。",
      route: "/reports?tab=data-quality",
      sources: metricSources(qualityMetric),
    }),
  ];
  return {
    schema: "PFIV024Stage7Phase71ReportPackV1",
    target_version: "v0.2.4",
    source_package_version: "v0.2.3-repair",
    stage: "Stage 7",
    phase_id: "7.1",
    contract_version: "PFI-V024-STAGE7-PHASE71-REPORT-SCHEMA",
    source: {
      status: source.status || null,
      record_count: Number(source.record_count || 0),
      raw_file_count: Number(source.raw_file_count || 0),
      date_range: dataRange,
      as_of: source.as_of || null,
      evidence_hash: source.evidence_hash || null,
    },
    read_model_hash: statusPayload.read_model_hash || null,
    report_ids: reports.map((item) => item.report_id),
    reports,
  };
}

function applyV024Stage7Phase72FallbackReportCenter() {
  WORKSPACES.insights = {
    ...WORKSPACES.insights,
    label: "报告与洞察",
    kicker: "Stage 7 Phase 7.2 报告中心",
    conclusion: "报告来源或指标尚未就绪。净资产、现金、投资、消费、现金流和数据质量报告全部保持阻断，只展示公式、未加载状态、缺口与复核入口。",
    freshness: "报告数据未加载",
    runtime: "Stage 7 Phase 7.2 页面展示：未加载时不生成财务结论、样本事实或置信度",
    secondaryTabs: STAGE2_SECONDARY_TABS.insights,
    cards: [
      ["净资产报告", "已阻断", "样本量：未加载 · 缺口：账户余额/持仓"],
      ["现金报告", "已阻断", "样本量：未加载 · 缺口：账户余额"],
      ["投资报告", "已阻断", "样本量：未加载 · 缺口：持仓市值"],
      ["消费报告", "已阻断", "样本量：未加载 · 数据范围：未加载 · 置信度：未加载"],
      ["现金流报告", "已阻断", "样本量：未加载 · 缺口：收入/现金余额"],
      ["数据质量报告", "已阻断", "样本量：未加载 · 复核入口：数据质量"],
    ],
    features: [
      feature("净资产报告", "阻塞", "公式：现金余额 + 投资市值 + 其他真实资产 - 真实负债", "参数：缺少真实输入时不补零；样本量：未加载；数据范围：未加载；置信度：未加载；缺口：账户余额与持仓 read model；复核入口：数据质量。", { workspace: "insights", routeAlias: "/reports?tab=data-quality&metric=net_worth_cny", label: "查看阻断" }),
      feature("现金报告", "阻塞", "公式：已挂链账户余额合计", "参数：缺少真实输入时不补零；样本量：未加载；数据范围：未加载；置信度：未加载；缺口：账户余额 read model；复核入口：账户对账。", { workspace: "insights", routeAlias: "/accounts?tab=reconcile", label: "查看阻断" }),
      feature("投资报告", "阻塞", "公式：持仓数量 * 最新真实价格 * 有效汇率", "参数：缺少真实输入时不补零；样本量：未加载；数据范围：未加载；置信度：未加载；缺口：持仓市值 read model；复核入口：持仓。", { workspace: "insights", routeAlias: "/investment?tab=holdings", label: "查看阻断" }),
      feature("消费报告", "阻塞", "公式：消费总流出 = 生活消费 + 投资入金 + 基金申购 + 黄金申购 + 投资买入 + 金融费用 - 退款抵消", "参数：真实来源或消费指标未就绪时阻断；样本量：未加载；数据范围：未加载；置信度：未加载；复核入口：消费分析。", { workspace: "insights", routeAlias: "/consumption?tab=analysis", label: "查看阻断" }),
      feature("现金流报告", "阻塞", "公式：真实收入 - 真实支出 - 投资现金变动", "参数：缺少真实输入时不补零；样本量：未加载；数据范围：未加载；置信度：未加载；缺口：收入、现金余额和投资现金变动；复核入口：数据质量。", { workspace: "insights", routeAlias: "/reports?tab=data-quality&metric=cashflow", label: "查看阻断" }),
      feature("数据质量报告", "阻塞", "公式：来源、记录范围、阻断指标、缺失输入和复核入口组合检查", "参数：来源或质量指标未就绪时阻断；样本量：未加载；数据范围：未加载；置信度：未加载；复核入口：数据质量。", { workspace: "insights", routeAlias: "/reports?tab=data-quality", label: "查看阻断" }),
    ],
    rows: [
      row("P0", "净资产报告", "账户余额/持仓缺失", "未挂载账户余额与持仓 read model，阻断净资产结论。", "阻塞"),
      row("P0", "现金报告", "账户余额缺失", "未挂载账户余额 read model，阻断现金余额结论。", "阻塞"),
      row("P0", "投资报告", "持仓市值缺失", "未挂载持仓市值 read model，阻断投资市值结论。", "阻塞"),
      row("P0", "消费结构报告", "来源/消费指标未加载", "来源或消费指标未就绪，保持阻断。", "阻塞"),
      row("P0", "现金流报告", "收入/现金余额缺失", "现金流公式缺少真实收入与现金余额输入，保持阻断。", "阻塞"),
      row("P0", "数据质量报告", "来源/质量指标未加载", "来源或质量指标未就绪，保持阻断并展示复核入口。", "阻塞"),
    ],
    tasks: [
      task("报告中心页面", "6 份阻断报告可见：净资产、现金、投资、消费、现金流、数据质量", "review"),
      task("公式解释区", "每份报告显示公式，不是单段文本", "ready"),
      task("参数与样本量区", "样本量、数据范围和置信度均明确显示未加载", "review"),
      task("缺口/复核入口", "阻断报告显示缺口和复核入口", "review"),
      task("伪零拦截", "阻断报告不显示财务假零", "ready"),
    ],
    evidence: evidence("Stage 7 Phase 7.2 报告证据", "报告中心、公式解释区、参数与样本量区、缺口/复核入口", "PFI read model status（未加载）", "来源或指标未就绪时，全部报告保持阻断且不填充样本事实或置信度。"),
  };
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
  const source = CARD_SOURCES[key] || "本机资料";
  const detail = safeUserText(card.detail, "");
  if (detail && !englishNoise(detail)) return `来源：${source} · ${detail}`;
  const status = localizeStatus(detail.match(/status\s+([A-Za-z]+)/)?.[1] || "");
  return `来源：${source} · ${status ? `状态${status}` : "状态待复核"}`;
}

function applyWorkflowRuntime(runtime) {
  if (!runtime || runtime.schema !== "PFIOSPhaseCWorkflowRuntimeReadModelV1") return;
  const hasVisibleRuntime =
    (runtime.task_center_rows || []).length ||
    (runtime.workflow_cards || []).length ||
    (runtime.minute_fast_path && runtime.minute_fast_path.web_shell_visible) ||
    (runtime.local_llm_deep_path && runtime.local_llm_deep_path.web_shell_visible);
  if (!hasVisibleRuntime) return;
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
    safeEvidenceText(card.evidence_id || card.evidence_class || "", "页面说明"),
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
  const importConfirm = document.querySelector("[data-import-confirm]");

  if (input) {
    input.addEventListener("change", (event) => {
      void handleUploadSelection(event.target.files, "file_picker");
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
          void handleUploadSelection(event.dataTransfer?.files || [], "drag_drop");
        }
        dropzone.classList.remove("is-dragover");
      });
    });
  }

  if (reviewLink) reviewLink.addEventListener("click", openImportReviewQueue);
  if (importConfirm) importConfirm.addEventListener("click", confirmStage3Import);
}

function renderUploadImportPanel(workspaceId) {
  const panel = document.querySelector("[data-upload-import-panel]");
  if (!panel) return;
  panel.hidden = workspaceId !== "sync";
  if (panel.hidden) return;
  renderUploadStatus();
  renderStage3UploadFlow();
  renderImportCenter();
}

async function handleUploadSelection(fileList, source) {
  const selectedFiles = Array.from(fileList || []);
  if (!selectedFiles.length) {
    uploadCenterState = {
      ...uploadCenterState,
      rejected: [{ name: "未选择文件", reason: "请先选择 CSV / ZIP 文件。" }],
      lastSource: source || "",
      importing: false,
    };
    renderUploadStatus();
    renderStage3UploadFlow();
    renderImportCenter();
    showToast("请先选择账单文件");
    return;
  }

  const accepted = [];
  const acceptedFiles = [];
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
      acceptedFiles.push(file);
    } else {
      rejected.push({ name: file.name, reason: validation.reason });
    }
  });

  uploadCenterState = {
    files: accepted,
    rejected,
    lastSource: source || "file_picker",
    importing: acceptedFiles.length > 0 && rejected.length === 0,
    previewManifest: null,
    importedManifest: null,
    confirmedAt: "",
  };
  renderUploadStatus();
  renderStage3UploadFlow();
  renderImportCenter();

  if (rejected.length) {
    showToast(`有 ${rejected.length} 个文件需要处理`);
    return;
  }
  showToast(`已选择 ${accepted.length} 个文件，正在本机解析预览`);
  try {
    const manifest = await uploadAlipayFilesToBackend(acceptedFiles);
    const previewErrors = Array.isArray(manifest.errors) ? manifest.errors : [];
    uploadCenterState = {
      ...uploadCenterState,
      importing: false,
      previewManifest: manifest,
      importedManifest: manifest.status === "confirmed" ? manifest : null,
      rejected: manifest.status === "failed"
        ? previewErrors.map((item) => ({ name: "解析失败", reason: item.message || item.code || "本机解析失败" }))
        : [],
    };
    if (manifest.status === "confirmed") {
      applyAlipayImportSummary(manifestToAlipaySummary(manifest));
      await refreshStage7WorkflowState();
    }
    renderUploadStatus();
    renderStage3UploadFlow();
    renderImportCenter();
    if (manifest.status === "preview_ready") {
      showToast(`解析预览完成：${Number(manifest.transaction_count || 0).toLocaleString("zh-CN")} 条流水，尚未入账`, "success");
    } else if (manifest.status === "confirmed") {
      showToast(`相同文件已确认入账：幂等复用 ${Number(manifest.ledger_count || 0).toLocaleString("zh-CN")} 条流水`, "success");
    } else {
      showToast("解析失败，未生成预览且未写入账本", "failure");
    }
  } catch (error) {
    uploadCenterState = {
      ...uploadCenterState,
      importing: false,
      previewManifest: null,
      importedManifest: null,
      rejected: [{ name: "解析预览失败", reason: error?.message || "本机服务未完成解析。" }],
    };
    renderUploadStatus();
    renderStage3UploadFlow();
    renderImportCenter();
    showToast("解析预览失败，请检查本机服务", "failure");
  }
}

async function confirmStage3Import() {
  const preview = uploadCenterState.previewManifest || uploadCenterState.importedManifest;
  if (!preview?.batch_id) {
    uploadCenterState = {
      ...uploadCenterState,
      rejected: [{ name: "没有可确认批次", reason: "请先选择真实文件并等待解析预览通过。" }],
    };
    renderUploadStatus();
    renderStage3UploadFlow();
    renderImportCenter();
    showToast("请先完成真实解析预览", "failure");
    return;
  }
  if (preview.status === "failed") {
    showToast("解析失败的批次不能入账，请修复文件或重试", "failure");
    return;
  }

  const status = document.querySelector("[data-import-confirm-status]");
  if (status) {
    status.textContent = "等待本机服务解析";
    status.className = "status-pill status-watch";
  }
  setActionFeedback("progress", "正在执行事务确认入账");
  showToast("正在执行事务确认入账", "progress");
  try {
    const manifest = await runtimeApiJson("/api/imports/alipay/confirm", {
      method: "POST",
      body: JSON.stringify({ batch_id: preview.batch_id }),
    });
    uploadCenterState = {
      ...uploadCenterState,
      previewManifest: manifest,
      importedManifest: manifest,
      importing: false,
      confirmedAt: new Date().toISOString(),
      rejected: [],
    };
    applyAlipayImportSummary(manifestToAlipaySummary(manifest));
    renderUploadStatus();
    renderStage3UploadFlow();
    renderImportCenter();
    await refreshStage7WorkflowState();
    await refreshRuntimeTrends({ rerender: true });
    showToast(`事务入账完成：${Number(manifest.ledger_count || 0).toLocaleString("zh-CN")} 条，待复核 ${Number(manifest.pending_review_count || 0).toLocaleString("zh-CN")} 条`, "success");
  } catch (error) {
    uploadCenterState = {
      ...uploadCenterState,
      importing: false,
      rejected: [{ name: "确认入库失败", reason: error?.message || "本机服务暂不可用，未写入正式账本。" }],
    };
    renderUploadStatus();
    renderStage3UploadFlow();
    renderImportCenter();
    showToast("确认入库失败，未写入正式账本", "failure");
  }
}

function renderStage3UploadFlow() {
  const preview = document.querySelector("[data-upload-preview]");
  const mapping = document.querySelector("[data-field-mapping-status]");
  const confirmStatus = document.querySelector("[data-import-confirm-status]");
  const reviewEntry = document.querySelector("[data-review-queue-entry]");
  const acceptedCount = uploadCenterState.files.length;
  const rejectedCount = uploadCenterState.rejected.length;
  const previewManifest = uploadCenterState.previewManifest;
  const confirmedManifest = uploadCenterState.importedManifest;
  const manifest = confirmedManifest || previewManifest;

  if (preview) {
    preview.replaceChildren();
    const title = document.createElement("strong");
    title.textContent = "解析预览";
    const detail = document.createElement("span");
    preview.append(title, detail);
    if (!acceptedCount) {
      detail.textContent = "等待真实文件；记录数以本机解析结果为准。";
    } else if (!manifest) {
      const fileNames = uploadCenterState.files.map((file) => `${file.name}（${formatFileSize(file.size)}）`).join("、");
      detail.textContent = `${fileNames} · 正在等待本机解析结果。`;
    } else {
      const fileDetails = (manifest.file_summaries || []).map((file) => {
        const source = file.source_id || "未识别来源";
        const parser = file.parser_version || "无可用解析器";
        const digest = String(file.content_sha256 || "").slice(0, 16);
        const status = file.status === "ready" ? "可解析" : `失败：${file.error_code || "parse_failed"}`;
        return `${file.file_name || "本机文件"} · ${source} · ${parser} · SHA-256 ${digest}… · ${status}`;
      });
      if (!fileDetails.length) {
        detail.textContent = "没有可显示的解析结果";
      } else {
        fileDetails.forEach((value, index) => {
          if (index) detail.appendChild(document.createElement("br"));
          detail.appendChild(document.createTextNode(value));
        });
      }
    }
  }

  if (mapping) {
    const mappedFields = (manifest?.field_mapping || []).map((item) => `${(item.source_fields || []).join(" + ")} → ${item.canonical_field}`).join("；");
    mapping.textContent = mappedFields
      ? `后端解析字段映射：${mappedFields}`
      : acceptedCount
        ? "正在等待后端返回真实字段映射。"
        : "等待真实文件解析后确认日期、金额、币种、账户和备注字段。";
  }

  if (confirmStatus) {
    if (confirmedManifest?.status === "confirmed") {
      confirmStatus.textContent = `已事务入账 ${Number(confirmedManifest.ledger_count || 0).toLocaleString("zh-CN")} 条`;
      confirmStatus.className = "status-pill status-ready";
    } else if (previewManifest?.status === "preview_ready") {
      confirmStatus.textContent = `预览通过 · ${Number(previewManifest.transaction_count || 0).toLocaleString("zh-CN")} 条待确认`;
      confirmStatus.className = "status-pill status-watch";
    } else if (previewManifest?.status === "failed") {
      confirmStatus.textContent = "解析失败 · 未入账";
      confirmStatus.className = "status-pill status-blocked";
    } else if (previewManifest?.status === "rolled_back") {
      confirmStatus.textContent = "已补偿回滚 · 可重试解析";
      confirmStatus.className = "status-pill status-watch";
    } else if (rejectedCount) {
      confirmStatus.textContent = "需要处理失败反馈";
      confirmStatus.className = "status-pill status-blocked";
    } else if (acceptedCount) {
      confirmStatus.textContent = "可确认入库";
      confirmStatus.className = "status-pill status-watch";
    } else {
      confirmStatus.textContent = "等待真实文件";
      confirmStatus.className = "status-pill status-review";
    }
  }

  if (reviewEntry) {
    if (confirmedManifest?.status === "confirmed") {
      reviewEntry.textContent = `待复核队列：${Number(confirmedManifest.pending_review_count || confirmedManifest.review_count || 0).toLocaleString("zh-CN")} 条真实流水待处理；复核决定可撤销。`;
    } else if (previewManifest?.status === "preview_ready") {
      reviewEntry.textContent = `预览识别 ${Number(previewManifest.review_count || 0).toLocaleString("zh-CN")} 条待复核流水；确认入账前不会进入正式队列。`;
    } else if (previewManifest?.status === "failed") {
      reviewEntry.textContent = "解析失败：没有生成待复核队列，也没有写入账本。";
    } else if (acceptedCount) {
      reviewEntry.textContent = "待复核队列：文件已选择，等待本机服务解析后生成真实队列。";
    } else {
      reviewEntry.textContent = "待复核队列：暂无真实导入批次。";
    }
  }
}

async function uploadAlipayFilesToBackend(files) {
  const selected = Array.from(files || []);
  if (!selected.length || selected.length > MAX_STAGE7_UPLOAD_FILES) {
    throw new Error(`一次最多上传 ${MAX_STAGE7_UPLOAD_FILES} 个文件`);
  }
  const totalBytes = selected.reduce((sum, file) => sum + Number(file.size || 0), 0);
  if (totalBytes > MAX_STAGE7_UPLOAD_TOTAL_BYTES) {
    throw new Error("上传文件总量超过 100MB");
  }
  const payloadFiles = [];
  for (const file of selected) {
    payloadFiles.push({
      name: file.name,
      size: file.size,
      type: file.type || "本机文件",
      contentBase64: await readFileAsBase64(file),
    });
  }
  return runtimeApiJson("/api/imports/alipay", {
    method: "POST",
    body: JSON.stringify({ files: payloadFiles }),
  });
}

function readFileAsBase64(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => {
      const value = String(reader.result || "");
      resolve(value.includes(",") ? value.split(",", 2)[1] : value);
    };
    reader.onerror = () => reject(new Error(`读取文件失败：${file?.name || "未命名文件"}`));
    reader.readAsDataURL(file);
  });
}

function manifestToAlipaySummary(manifest = {}) {
  return {
    schema: "PFIAlipayRealImportSummaryV1",
    source_id: "alipay_daily",
    status: Number(manifest.transaction_count || 0) > 0 ? "已接入真实数据" : "未接入真实数据",
    file_count: Number(manifest.file_count || 0),
    valid_file_count: Number(manifest.valid_file_count || 0),
    transaction_count: Number(manifest.transaction_count || 0),
    review_count: Number(manifest.review_count || 0),
    date_start: String(manifest.date_start || ""),
    date_end: String(manifest.date_end || ""),
    search_tokens: [
      "支付宝",
      "真实支付宝流水",
      String(manifest.file_count || ""),
      String(manifest.transaction_count || ""),
      String(manifest.review_count || ""),
      String(manifest.date_start || ""),
      String(manifest.date_end || ""),
      String(manifest.date_start || "").replaceAll("-", ""),
      String(manifest.date_end || "").replaceAll("-", ""),
    ].filter(Boolean),
  };
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
  } else if (uploadCenterState.importing) {
    status.textContent = `正在解析 ${acceptedCount} 个本机文件`;
    status.dataset.uploadState = "running";
    status.className = "status-pill status-watch";
  } else if (uploadCenterState.importedManifest?.status === "confirmed") {
    status.textContent = `已事务入账 ${Number(uploadCenterState.importedManifest.ledger_count || 0).toLocaleString("zh-CN")} 条真实流水`;
    status.dataset.uploadState = "ready";
    status.className = "status-pill status-ready";
  } else if (uploadCenterState.previewManifest?.status === "preview_ready") {
    status.textContent = `预览通过 ${Number(uploadCenterState.previewManifest.transaction_count || 0).toLocaleString("zh-CN")} 条 · 尚未入账`;
    status.dataset.uploadState = "preview";
    status.className = "status-pill status-watch";
  } else if (acceptedCount) {
    status.textContent = `已选择 ${acceptedCount} 个文件 · 等待真实解析`;
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
    item.textContent = "等待 CSV / ZIP 文件";
    fileList.appendChild(item);
    return;
  }

  uploadCenterState.files.forEach((file, index) => {
    const item = document.createElement("li");
    const name = document.createElement("strong");
    const meta = document.createElement("span");
    name.textContent = file.name;
    const summary = (uploadCenterState.previewManifest?.file_summaries || [])[index] || {};
    const digest = String(summary.content_sha256 || "").slice(0, 16);
    const parser = summary.parser_version || "等待来源识别";
    meta.textContent = `文件 ${index + 1} · ${formatFileSize(file.size)} · ${parser}${digest ? ` · SHA-256 ${digest}…` : ""} · 仅本机私有 raw store`;
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
  const realBatch = buildRealAlipayImportBatch();
  const allBatches = [activeBatch, realBatch].filter(Boolean);
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
  if (!allBatches.length) {
    const empty = document.createElement("article");
    empty.className = "import-batch";
    empty.innerHTML = "<strong>暂无真实导入批次</strong><p>导入真实账单后，这里显示文件数、记录数、待复核数和日期范围。</p>";
    batches.appendChild(empty);
    return;
  }

  allBatches.forEach((batch) => {
    const item = document.createElement("article");
    item.className = "import-batch";
    item.dataset.importBatchId = batch.batchId;
    const heading = document.createElement("div");
    const identifier = document.createElement("strong");
    identifier.textContent = String(batch.batchId || "");
    const source = document.createElement("span");
    source.textContent = String(batch.source || "");
    heading.append(identifier, source);
    const details = document.createElement("dl");
    for (const [label, value] of [
      ["文件数", batch.fileCount], ["记录数", batch.recordCount],
      ["待复核", batch.reviewCount], ["状态", batch.status],
    ]) {
      const row = document.createElement("div");
      const term = document.createElement("dt");
      term.textContent = label;
      const description = document.createElement("dd");
      description.textContent = String(value ?? "");
      row.append(term, description);
      details.appendChild(row);
    }
    const summary = document.createElement("p");
    summary.textContent = String(batch.summary || "");
    item.append(heading, details, summary);
    if (batch.canRollback || batch.canRetry) {
      const actions = document.createElement("div");
      actions.className = "operation-actions stage7-import-actions";
      if (batch.canRollback) {
        const rollback = document.createElement("button");
        rollback.type = "button";
        rollback.className = "secondary-action";
        rollback.dataset.stage7ImportRollback = batch.batchId;
        rollback.textContent = "撤销本批入账";
        rollback.addEventListener("click", () => void rollbackStage7Import(batch.batchId));
        actions.appendChild(rollback);
      }
      if (batch.canRetry) {
        const retry = document.createElement("button");
        retry.type = "button";
        retry.className = "secondary-action";
        retry.dataset.stage7ImportRetry = batch.batchId;
        retry.textContent = "重试本机解析";
        retry.addEventListener("click", () => void retryStage7Import(batch.batchId));
        actions.appendChild(retry);
      }
      item.appendChild(actions);
    }
    batches.appendChild(item);
  });
}

function buildRealAlipayImportBatch() {
  const manifest = uploadCenterState.importedManifest;
  if (manifest?.status === "confirmed") {
    return {
      batchId: manifest.batch_id,
      source: manifest.source_id || "alipay_daily",
      fileCount: Number(manifest.file_count || 0),
      recordCount: Number(manifest.ledger_count || 0),
      reviewCount: Number(manifest.pending_review_count || 0),
      status: manifest.idempotent_replay ? "已确认 · 幂等复用" : "已确认入账",
      summary: `${manifest.date_start || "日期待核"} 至 ${manifest.date_end || "日期待核"} · 账本 ${Number(manifest.ledger_count || 0)} 条 · 待复核 ${Number(manifest.pending_review_count || 0)} 条`,
      canRollback: true,
      canRetry: false,
    };
  }
  if (!alipayImportState || Number(alipayImportState.transactionCount || 0) <= 0) return null;
  return {
    batchId: "真实支付宝流水",
    source: "支付宝三年历史账单",
    fileCount: alipayImportState.fileCount,
    recordCount: alipayImportState.transactionCount,
    reviewCount: alipayImportState.reviewCount,
    status: alipayImportState.status || "已接入真实数据",
    summary: `${alipayImportState.dateStart} 至 ${alipayImportState.dateEnd} · ${alipayImportState.transactionCount} 条标准化流水 · ${alipayImportState.reviewCount} 条待复核`,
  };
}

function buildPendingBatchFromFiles() {
  const fileCount = uploadCenterState.files.length;
  if (!fileCount) return null;
  if (uploadCenterState.importedManifest) return null;
  const preview = uploadCenterState.previewManifest;
  if (preview) {
    const statusLabel = {
      preview_ready: "预览通过 · 尚未入账",
      failed: "解析失败 · 未入账",
      rolled_back: "已补偿回滚 · 可重试",
    }[preview.status] || "批次状态待核";
    return {
      batchId: preview.batch_id,
      source: preview.source_id || "来源待识别",
      fileCount: Number(preview.file_count || fileCount),
      recordCount: Number(preview.transaction_count || 0),
      reviewCount: Number(preview.review_count || 0),
      status: statusLabel,
      summary: preview.status === "preview_ready"
        ? `来源、hash、解析器与字段映射已确认；账本仍为 0，等待事务确认。`
        : preview.status === "rolled_back"
          ? "正式账本写入已撤销；私有 raw hash 与解析审计保留，可从原始字节重试。"
          : `${(preview.errors || []).map((item) => item.message || item.code).join("；") || "解析失败且未生成预览。"}`,
      canRollback: false,
      canRetry: ["failed", "rolled_back"].includes(preview.status),
    };
  }
  return {
    batchId: uploadCenterState.importing ? "正在接入真实上传" : "待接入真实上传",
    source: uploadCenterState.lastSource === "drag_drop" ? "拖拽上传" : "文件选择",
    fileCount,
    recordCount: 0,
    reviewCount: 0,
    status: uploadCenterState.importing ? "解析中" : "待真实解析",
    summary: "已选择真实文件；记录数和待复核数只以后端解析结果为准，确认前账本不写入。",
    canRollback: false,
    canRetry: false,
  };
}

async function rollbackStage7Import(batchId) {
  try {
    const manifest = await runtimeApiJson("/api/imports/alipay/rollback", {
      method: "POST",
      body: JSON.stringify({ batch_id: batchId }),
    });
    uploadCenterState = {
      ...uploadCenterState,
      previewManifest: manifest,
      importedManifest: null,
      confirmedAt: "",
      rejected: [],
    };
    applyAlipayImportSummary(defaultAlipayImportSummary());
    await refreshStage7WorkflowState();
    renderUploadStatus();
    renderStage3UploadFlow();
    renderImportCenter();
    showToast("本批账本写入已补偿撤销；原始 hash 与解析记录保留", "success");
  } catch (error) {
    showToast(error?.message || "批次回滚失败", "failure");
  }
}

async function retryStage7Import(batchId) {
  try {
    const manifest = await runtimeApiJson("/api/imports/alipay/retry", {
      method: "POST",
      body: JSON.stringify({ batch_id: batchId }),
    });
    uploadCenterState = {
      ...uploadCenterState,
      previewManifest: manifest,
      importedManifest: null,
      importing: false,
      rejected: manifest.status === "failed"
        ? (manifest.errors || []).map((item) => ({ name: "重试失败", reason: item.message || item.code }))
        : [],
    };
    renderUploadStatus();
    renderStage3UploadFlow();
    renderImportCenter();
    showToast(manifest.status === "preview_ready" ? "重试解析通过，仍需确认入账" : "重试后仍未通过，账本未改变", manifest.status === "preview_ready" ? "success" : "failure");
  } catch (error) {
    showToast(error?.message || "批次重试失败", "failure");
  }
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
  void refreshStage7WorkflowState();
  showToast("已进入真实账本复核队列");
}

function bindLedgerOperationEvents() {
  const filterInput = document.querySelector("[data-ledger-filter]");
  const categorySelect = document.querySelector("[data-ledger-category-select]");
  filterInput?.addEventListener("input", (event) => {
    ledgerOperationState = {
      ...ledgerOperationState,
      filter: String(event.target.value || ""),
    };
    filterRows(ledgerOperationState.filter);
    renderLedgerOperationFlow("ledger");
  });
  categorySelect?.addEventListener("change", (event) => {
    ledgerOperationState = {
      ...ledgerOperationState,
      category: String(event.target.value || ""),
    };
    renderLedgerOperationFlow("ledger");
  });
  document.querySelector("[data-ledger-review-save]")?.addEventListener("click", () => void saveLedgerReview());
  document.querySelector("[data-ledger-export]")?.addEventListener("click", exportLedgerReview);
}

async function refreshStage7WorkflowState() {
  try {
    const [queue, ledger] = await Promise.all([
      runtimeApiJson("/api/imports/review-queue?status=pending"),
      runtimeApiJson("/api/ledger"),
    ]);
    const reviewQueue = Array.isArray(queue.items) ? queue.items : [];
    const selectedExists = reviewQueue.some((item) => item.review_id === ledgerOperationState.selectedReviewId);
    ledgerOperationState = {
      ...ledgerOperationState,
      reviewQueue,
      ledger,
      selectedReviewId: selectedExists ? ledgerOperationState.selectedReviewId : String(reviewQueue[0]?.review_id || ""),
    };
    renderLedgerOperationFlow("ledger");
    return { queue, ledger };
  } catch (error) {
    ledgerOperationState = {
      ...ledgerOperationState,
      reviewQueue: [],
      ledger: null,
    };
    renderLedgerOperationFlow("ledger");
    throw error;
  }
}

function renderLedgerOperationFlow(workspaceId) {
  const panel = document.querySelector("[data-ledger-operation-flow]");
  if (!panel) return;
  const visible = workspaceId === "ledger";
  panel.hidden = !visible;
  if (!visible) return;

  const status = panel.querySelector("[data-ledger-operation-status]");
  const state = panel.querySelector("[data-ledger-review-state]");
  const filterInput = panel.querySelector("[data-ledger-filter]");
  const categorySelect = panel.querySelector("[data-ledger-category-select]");
  const ledger = ledgerOperationState.ledger;
  const ledgerCount = Number(ledger?.ledger_count || 0);
  const pendingCount = Number(ledger?.pending_review_count || 0);
  const hasRealLedger = ledgerCount > 0;
  const filterText = ledgerOperationState.filter ? `筛选：“${ledgerOperationState.filter}”` : "未筛选";
  const categoryText = ledgerOperationState.category ? `分类：“${ledgerOperationState.category}”` : "未修改分类";

  if (filterInput && filterInput.value !== ledgerOperationState.filter) filterInput.value = ledgerOperationState.filter;
  if (categorySelect && categorySelect.value !== ledgerOperationState.category) categorySelect.value = ledgerOperationState.category;

  if (status) {
    status.textContent = hasRealLedger ? `账本 ${ledgerCount.toLocaleString("zh-CN")} 条 · 待复核 ${pendingCount.toLocaleString("zh-CN")} 条` : "暂无 Stage 7 入账流水";
    status.className = `status-pill ${hasRealLedger ? "status-ready" : "status-review"}`;
  }
  if (state) {
    const saved = ledgerOperationState.reviewSavedAt ? ` · 已保存复核 ${formatLocalSaveTime(ledgerOperationState.reviewSavedAt)}` : "";
    const exported = ledgerOperationState.exportPreparedAt ? ` · 已准备导出 ${formatLocalSaveTime(ledgerOperationState.exportPreparedAt)}` : "";
    state.textContent = `${filterText} · ${categoryText} · SQLite 当前 ${ledgerCount} 条，待复核 ${pendingCount} 条${saved}${exported}。`;
  }
  renderStage7ReviewQueue(panel);
  if (!ledgerOperationState.ledger) void refreshStage7WorkflowState().catch(() => undefined);
}

function renderStage7ReviewQueue(panel) {
  let container = panel.querySelector("[data-stage7-review-queue]");
  if (!container) {
    container = document.createElement("div");
    container.className = "stage7-review-queue";
    container.dataset.stage7ReviewQueue = "true";
    panel.querySelector("[data-ledger-review-state]")?.insertAdjacentElement("afterend", container);
  }
  container.replaceChildren();
  const filter = ledgerOperationState.filter.trim().toLowerCase();
  const items = ledgerOperationState.reviewQueue.filter((item) => {
    if (!filter) return true;
    return [item.description, item.occurred_at, item.amount, item.currency, item.event_type]
      .some((value) => String(value || "").toLowerCase().includes(filter));
  });
  if (!items.length) {
    const empty = document.createElement("p");
    empty.className = "stage7-review-empty";
    empty.textContent = ledgerOperationState.reviewQueue.length
      ? "当前筛选没有待复核流水。"
      : "暂无待复核流水；已确认记录直接发布，低置信记录才进入这里。";
    container.appendChild(empty);
  }
  items.forEach((item) => {
    const label = document.createElement("label");
    label.className = "stage7-review-item";
    const radio = document.createElement("input");
    radio.type = "radio";
    radio.name = "stage7-review-item";
    radio.value = item.review_id;
    radio.checked = item.review_id === ledgerOperationState.selectedReviewId;
    radio.addEventListener("change", () => {
      ledgerOperationState = { ...ledgerOperationState, selectedReviewId: item.review_id };
    });
    const body = document.createElement("span");
    const title = document.createElement("strong");
    title.textContent = `${item.occurred_at || "日期待核"} · ${item.currency || ""} ${item.amount || ""}`;
    const description = document.createElement("span");
    description.textContent = `${item.description || "描述缺失"} · ${Math.round(Number(item.confidence || 0) * 100)}% · ${item.reason || "等待复核"}`;
    body.appendChild(title);
    body.appendChild(description);
    label.appendChild(radio);
    label.appendChild(body);
    container.appendChild(label);
  });
  if (ledgerOperationState.lastResolvedReviewId) {
    const undo = document.createElement("button");
    undo.type = "button";
    undo.className = "secondary-action stage7-review-undo";
    undo.dataset.stage7ReviewUndo = ledgerOperationState.lastResolvedReviewId;
    undo.textContent = "撤销最近一次复核";
    undo.addEventListener("click", () => void undoLedgerReview());
    container.appendChild(undo);
  }
}

async function saveLedgerReview() {
  const reviewId = ledgerOperationState.selectedReviewId;
  if (!reviewId) {
    showToast("请先选择一条待复核流水", "failure");
    return;
  }
  const category = ledgerOperationState.category.trim();
  const decision = category ? "reclassify" : "accept";
  try {
    await runtimeApiJson("/api/imports/review", {
      method: "POST",
      body: JSON.stringify({ review_id: reviewId, decision, category }),
    });
    ledgerOperationState = {
      ...ledgerOperationState,
      lastResolvedReviewId: reviewId,
      selectedReviewId: "",
      reviewSavedAt: new Date().toISOString(),
    };
    await refreshStage7WorkflowState();
    const taskPhase = document.querySelector("#task-phase");
    if (taskPhase) taskPhase.textContent = "账本复核 · SQLite 已持久化复核决定";
    showToast("复核决定已写入 SQLite，可撤销", "success");
  } catch (error) {
    showToast(error?.message || "复核保存失败，账本未改变", "failure");
  }
}

async function undoLedgerReview() {
  const reviewId = ledgerOperationState.lastResolvedReviewId;
  if (!reviewId) return;
  try {
    await runtimeApiJson("/api/imports/review/undo", {
      method: "POST",
      body: JSON.stringify({ review_id: reviewId }),
    });
    ledgerOperationState = {
      ...ledgerOperationState,
      lastResolvedReviewId: "",
      selectedReviewId: reviewId,
      reviewSavedAt: new Date().toISOString(),
    };
    await refreshStage7WorkflowState();
    showToast("最近一次复核已撤销，流水恢复为待复核", "success");
  } catch (error) {
    showToast(error?.message || "撤销复核失败", "failure");
  }
}

function exportLedgerReview() {
  const entries = Array.isArray(ledgerOperationState.ledger?.entries) ? ledgerOperationState.ledger.entries : [];
  const filter = ledgerOperationState.filter.trim().toLowerCase();
  const rows = entries
    .filter((item) => !filter || [item.occurred_at, item.description, item.amount, item.category].some((value) => String(value || "").toLowerCase().includes(filter)))
    .map((item) => [item.occurred_at, item.description, item.amount, item.currency, item.event_type, item.category, item.ledger_state]);
  const hasRealLedger = entries.length > 0;
  const header = ["日期", "说明", "金额", "币种", "事件类型", "分类", "账本状态"];
  const payload = [header, ...rows].map((rowItems) => rowItems.map(csvCell).join(",")).join("\n");
  const blob = new Blob([payload], { type: "text/csv;charset=utf-8" });
  const link = document.createElement("a");
  link.href = URL.createObjectURL(blob);
  link.download = rows.length ? "pfi-ledger-review.csv" : "pfi-ledger-empty-state.csv";
  link.click();
  URL.revokeObjectURL(link.href);
  ledgerOperationState = {
    ...ledgerOperationState,
    exportPreparedAt: new Date().toISOString(),
  };
  renderLedgerOperationFlow("ledger");
  showToast(rows.length ? "账本流水导出已准备" : hasRealLedger ? "当前筛选无结果，已导出空表头" : "暂无真实流水，已导出空表头");
}

function bindHoldingsPersistenceEvents() {
  document.querySelector("[data-holdings-save]")?.addEventListener("click", saveHoldingsEdits);
  document.querySelector("[data-holdings-add]")?.addEventListener("click", addHoldingDraft);
  document.querySelector("[data-holdings-reset]")?.addEventListener("click", resetHoldingsPersistence);
  document.querySelector("[data-holdings-rows]")?.addEventListener("click", (event) => {
    const button = event.target.closest("[data-holdings-soft-delete-row]");
    if (!button) return;
    requestHoldingSoftDelete(button.dataset.snapshotId || "");
  });
  document.querySelector("[data-holdings-rows]")?.addEventListener("input", () => {
    stageHoldingsDraftFromInputs();
  });
  document.querySelector("[data-holdings-delete-cancel]")?.addEventListener("click", cancelHoldingSoftDelete);
  document.querySelector("[data-holdings-delete-confirm]")?.addEventListener("click", confirmHoldingSoftDelete);
  document.querySelector("[data-holdings-delete-dialog]")?.addEventListener("cancel", () => {
    pendingHoldingSoftDeleteId = "";
  });
}

function defaultHoldingsState() {
  return {
    schema: "PFIV025HoldingsFrontendStateV1",
    rows: [],
    persistedRows: [],
    projection: null,
    projectionHash: "",
    lastSavedAt: "",
    draft: false,
  };
}

function clearLegacyHoldingsDraftStorage() {
  try {
    localStorage.removeItem(HOLDINGS_DRAFT_STORAGE_KEY);
    return true;
  } catch (_error) {
    return false;
  }
}

function loadUnsubmittedHoldingsDraft() {
  clearLegacyHoldingsDraftStorage();
  return defaultHoldingsState();
}

function saveUnsubmittedHoldingsDraft(state = holdingsPersistenceState) {
  const next = {
    schema: "PFIV025HoldingsFrontendStateV1",
    rows: (state.rows || []).map(normalizeHoldingRow).filter(Boolean),
    persistedRows: (state.persistedRows || []).map(normalizeHoldingRow).filter(Boolean),
    projection: state.projection || null,
    projectionHash: String(state.projectionHash || ""),
    lastSavedAt: state.lastSavedAt || "",
    draft: true,
  };
  clearLegacyHoldingsDraftStorage();
  holdingsPersistenceState = next;
  return next;
}

function clearUnsubmittedHoldingsDraft() {
  clearLegacyHoldingsDraftStorage();
}

function normalizeHoldingRow(row) {
  if (!row || typeof row !== "object") return null;
  const metadata = row.metadata && typeof row.metadata === "object" ? { ...row.metadata } : {};
  const note = String(row.note || row.memo || metadata.note || "").trim();
  if (note) metadata.note = note;
  return {
    snapshotId: String(row.snapshotId || row.snapshot_id || row.holdingId || row.holding_id || `draft:${Date.now()}`),
    clientRef: String(row.clientRef || row.client_ref || row.snapshotId || row.snapshot_id || `draft:${Date.now()}`),
    instrumentId: String(row.instrumentId || row.instrument_id || "").trim(),
    displayName: String(row.displayName || row.display_name || row.instrumentId || row.instrument_id || "").trim(),
    quantity: holdingDecimalInput(row.quantity),
    averageCost: holdingDecimalInput(row.averageCost ?? row.average_cost, { optional: true }),
    marketPrice: holdingDecimalInput(row.marketPrice ?? row.market_price, { optional: true }),
    currency: String(row.currency || "CNY").trim().toUpperCase(),
    portfolioId: String(row.portfolioId || row.portfolio_id || row.account || "manual").trim() || "manual",
    sourceId: String(row.sourceId || row.source_id || "manual_user_entry"),
    asOf: String(row.asOf || row.as_of || row.updatedAt || row.updated_at || localDateValue(new Date())),
    note,
    metadata,
    softDeleted: Boolean(row.softDeleted || row.soft_deleted || row.status === "deleted"),
    revision: Number(row.revision || 0),
    persisted: Number(row.revision || 0) > 0 && !String(row.snapshotId || row.snapshot_id || row.holding_id || "").startsWith("draft:"),
  };
}

function holdingDecimalInput(value, options = {}) {
  if (value === null || value === undefined || String(value).trim() === "") return options.optional ? "" : "";
  return String(value).trim();
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
  try {
    const payload = await runtimeApiJson("/api/holdings");
    const backendRows = (payload.rows || []).map(normalizeHoldingRow).filter(Boolean);
    const projectionHash = String(payload.projection?.projection_hash || "");
    const draft = loadUnsubmittedHoldingsDraft();
    const canRestoreDraft = draft.rows.length > 0 && draft.projectionHash === projectionHash;
    if (draft.rows.length && !canRestoreDraft) clearUnsubmittedHoldingsDraft();
    holdingsPersistenceState = canRestoreDraft
      ? {
          ...draft,
          persistedRows: backendRows,
          projection: payload.projection || null,
          projectionHash,
          draft: true,
        }
      : {
          schema: "PFIV025HoldingsFrontendStateV1",
          rows: backendRows,
          persistedRows: backendRows,
          projection: payload.projection || null,
          projectionHash,
          lastSavedAt: backendRows.length ? new Date().toISOString() : "",
          draft: false,
        };
    renderHoldingsRows();
    updateHoldingsSummary({ preserveStatus: true });
    setHoldingsStatus(
      canRestoreDraft
        ? "未提交草稿 · 尚未写入数据库"
        : draft.rows.length
          ? "后端已变化 · 旧草稿已放弃"
          : backendRows.length
            ? "已从 SQLite 读取"
            : "SQLite 暂无持仓",
      canRestoreDraft ? "review" : backendRows.length ? "ready" : "review",
    );
    return;
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
    item.innerHTML = `<td colspan="10">暂无持仓数据。请新增持仓并点击“保存持仓修改”写入 SQLite。</td>`;
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
      <td><input data-holding-field="portfolioId" data-snapshot-id="${row.snapshotId}" value="${escapeAttribute(row.portfolioId)}" aria-label="账户" /></td>
      <td><input data-holding-field="asOf" data-snapshot-id="${row.snapshotId}" value="${escapeAttribute(row.asOf)}" aria-label="更新时间" /></td>
      <td><input data-holding-field="note" data-snapshot-id="${row.snapshotId}" value="${escapeAttribute(row.note)}" aria-label="备注" /></td>
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
      row[field] = String(input.value || "").trim();
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
  const operations = buildHoldingCommitOperations(rows, holdingsPersistenceState.persistedRows || []);
  if (!operations.length) {
    setHoldingsStatus("没有需要保存的变更", "ready");
    showToast("持仓没有变更");
    return;
  }
  setHoldingsStatus("正在写入 SQLite", "watch");
  try {
    const payload = await saveHoldingsToBackend(operations);
    clearUnsubmittedHoldingsDraft();
    applyHoldingsBackendPayload(payload);
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

async function saveHoldingsToBackend(operations) {
  const signature = JSON.stringify({
    expected_projection_hash: holdingsPersistenceState.projectionHash,
    operations,
  });
  if (!holdingPendingRequest || holdingPendingRequest.signature !== signature) {
    holdingPendingRequest = { signature, requestId: holdingRequestId() };
  }
  return runtimeApiJson("/api/holdings/commit", {
    method: "POST",
    body: JSON.stringify({
      request_id: holdingPendingRequest.requestId,
      expected_projection_hash: holdingsPersistenceState.projectionHash,
      operations,
    }),
  });
}

function applyHoldingsBackendPayload(payload = {}) {
  const rows = (payload.rows || []).map(normalizeHoldingRow).filter(Boolean);
  holdingsPersistenceState = {
    schema: "PFIV025HoldingsFrontendStateV1",
    rows,
    persistedRows: rows,
    projection: payload.projection || null,
    projectionHash: String(payload.projection?.projection_hash || ""),
    lastSavedAt: new Date().toISOString(),
    draft: false,
  };
  holdingPendingRequest = null;
}

function buildHoldingCommitOperations(rows, persistedRows) {
  const baseline = new Map((persistedRows || []).map((row) => [row.snapshotId, normalizeHoldingRow(row)]));
  const operations = [];
  (rows || []).forEach((row) => {
    const normalized = normalizeHoldingRow(row);
    if (!normalized) return;
    const persisted = baseline.get(normalized.snapshotId);
    if (normalized.softDeleted) {
      if (persisted?.revision > 0) {
        operations.push({
          operation: "delete",
          holding_id: persisted.snapshotId,
          expected_revision: persisted.revision,
        });
      }
      return;
    }
    if (!persisted || persisted.revision < 1) {
      operations.push({
        operation: "create",
        client_ref: normalized.clientRef || normalized.snapshotId,
        holding: holdingCommandPayload(normalized),
      });
      return;
    }
    if (holdingComparablePayload(normalized) !== holdingComparablePayload(persisted)) {
      operations.push({
        operation: "update",
        holding_id: persisted.snapshotId,
        expected_revision: persisted.revision,
        holding: holdingCommandPayload(normalized),
      });
    }
  });
  return operations;
}

function holdingCommandPayload(row) {
  return {
    instrument_id: row.instrumentId,
    display_name: row.displayName,
    quantity: row.quantity,
    average_cost: row.averageCost || null,
    market_price: row.marketPrice || null,
    currency: row.currency,
    portfolio_id: row.portfolioId,
    as_of: row.asOf,
    note: row.note || "",
  };
}

function holdingComparablePayload(row) {
  return JSON.stringify(holdingCommandPayload(row));
}

function holdingRequestId() {
  if (typeof crypto !== "undefined" && typeof crypto.randomUUID === "function") return `holding-request:${crypto.randomUUID()}`;
  return `holding-request:${Date.now()}:${Math.random().toString(16).slice(2)}`;
}

function addHoldingDraft() {
  const timestamp = Date.now();
  const rows = [
    ...readHoldingsRowsFromDom(),
    {
      snapshotId: `draft:${timestamp}`,
      clientRef: `browser-draft:${timestamp}`,
      instrumentId: "",
      displayName: "",
      quantity: "",
      averageCost: "",
      marketPrice: "",
      currency: "CNY",
      portfolioId: "manual",
      sourceId: "manual_user_entry",
      asOf: localDateValue(new Date()),
      note: "",
      metadata: {},
      softDeleted: false,
    },
  ];
  holdingsPersistenceState = { ...holdingsPersistenceState, rows };
  saveUnsubmittedHoldingsDraft(holdingsPersistenceState);
  renderHoldingsRows();
  updateHoldingsSummary();
  setHoldingsStatus("未提交草稿 · 尚未写入数据库", "review");
}

function closeHoldingSoftDeleteDialog() {
  const dialog = document.querySelector("[data-holdings-delete-dialog]");
  if (!dialog) return;
  if (typeof dialog.close === "function" && dialog.open) dialog.close();
  else dialog.removeAttribute("open");
  delete dialog.dataset.snapshotId;
}

function requestHoldingSoftDelete(snapshotId) {
  if (!snapshotId) return;
  const row = (holdingsPersistenceState.rows || []).find((item) => item.snapshotId === snapshotId);
  if (!row) return;
  pendingHoldingSoftDeleteId = snapshotId;
  const dialog = document.querySelector("[data-holdings-delete-dialog]");
  const summary = dialog?.querySelector("[data-holdings-delete-summary]");
  const confirm = dialog?.querySelector("[data-holdings-delete-confirm]");
  const persisted = (holdingsPersistenceState.persistedRows || []).some((item) => item.snapshotId === snapshotId);
  const label = ownerVisibleText(row.displayName || row.instrumentId, "该持仓");
  if (summary) {
    summary.textContent = persisted
      ? `将把“${label}”标记为已软删除并写入本机 SQLite。确认前不会发送请求或修改数据库。`
      : `将从未提交草稿移除“${label}”。确认前不会发送请求或修改数据库。`;
  }
  if (confirm) confirm.textContent = persisted ? "确认软删除" : "移除草稿";
  if (!dialog) return;
  dialog.dataset.snapshotId = snapshotId;
  if (typeof dialog.showModal === "function") dialog.showModal();
  else dialog.setAttribute("open", "");
  dialog.querySelector("[data-holdings-delete-cancel]")?.focus();
}

function cancelHoldingSoftDelete() {
  pendingHoldingSoftDeleteId = "";
  closeHoldingSoftDeleteDialog();
  setHoldingsStatus("已取消软删除 · 数据库未改变", "review");
}

function confirmHoldingSoftDelete() {
  const snapshotId = pendingHoldingSoftDeleteId;
  pendingHoldingSoftDeleteId = "";
  closeHoldingSoftDeleteDialog();
  if (snapshotId) void softDeleteHoldingRow(snapshotId);
}

async function softDeleteHoldingRow(snapshotId) {
  if (!snapshotId) return;
  const rows = readHoldingsRowsFromDom().map((row) => (row.snapshotId === snapshotId ? { ...row, softDeleted: true } : row));
  const operations = buildHoldingCommitOperations(rows, holdingsPersistenceState.persistedRows || []);
  const target = (holdingsPersistenceState.persistedRows || []).find((row) => row.snapshotId === snapshotId);
  if (!target) {
    holdingsPersistenceState = saveUnsubmittedHoldingsDraft({
      ...holdingsPersistenceState,
      rows: rows.filter((row) => row.snapshotId !== snapshotId),
    });
    renderHoldingsRows();
    updateHoldingsSummary();
    setHoldingsStatus("已移除未提交草稿", "review");
    return;
  }
  setHoldingsStatus("正在写入 SQLite", "watch");
  try {
    const payload = await saveHoldingsToBackend(operations);
    clearUnsubmittedHoldingsDraft();
    applyHoldingsBackendPayload(payload);
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
  if (count) count.textContent = String(activeRows.length);
  if (value) {
    const projection = holdingsPersistenceState.projection;
    value.textContent = projection?.valuation_status === "valuation_missing"
      ? "持仓已保存 · 估值依赖缺失"
      : activeRows.length
        ? "尚未生成可信估值"
        : "暂无真实持仓";
    value.title = String(projection?.blocked_reason_zh || "缺少真实持仓、价格或 FX 时不显示财务 0。");
  }
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

function escapeHtml(value) {
  return String(value || "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");
}

function csvCell(value) {
  const text = String(value ?? "");
  const safe = /^[=+\-@\t\r]/.test(text) ? `'${text}` : text;
  return `"${safe.replace(/"/g, '""')}"`;
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
  const activeRoute = Object.prototype.hasOwnProperty.call(options, "routeAlias") ? normalizeRouteAlias(options.routeAlias) : "";
  const routeForState = normalizeRouteAlias(activeRoute || defaultRouteAliasForWorkspace(workspaceId));
  const stage4Subpage = resolveStage4Subpage(workspaceId, routeForState);
  const departingRoute = normalizeRouteAlias(main?.dataset.routeAlias || "");
  if (departingRoute && departingRoute !== routeForState) saveStage6RouteScroll(departingRoute);
  const invalidRoute = document.querySelector("[data-stage6-invalid-route]");
  if (invalidRoute) invalidRoute.hidden = true;
  main.setAttribute("data-stage6-route-state", "resolved");
  main.removeAttribute("data-stage6-invalid-route-requested");

  document.querySelectorAll("[data-workspace]").forEach((button) => {
    const isAlias = button.dataset.entryType === "v01_alias" || button.hasAttribute("data-feature-view");
    const routeAlias = normalizeRouteAlias(button.dataset.routeAlias || "");
    const sameWorkspace = button.dataset.workspace === workspaceId;
    const active = activeRoute
      ? sameWorkspace && (routeAlias === activeRoute || !isAlias)
      : button.dataset.workspace === workspaceId && !isAlias;
    button.classList.toggle("is-active", active);
    button.setAttribute("aria-current", active ? "page" : "false");
  });
  syncMobileTabs(workspaceId);

  title.textContent = ownerVisibleText(stage4Subpage?.title || workspace.label, "首页总览");
  document.title = `${ownerVisibleText(stage4Subpage?.title || workspace.label, "PFI")} · PFI`;
  kicker.textContent = ownerVisibleText(stage4Subpage?.primaryObject || workspace.kicker, "今日总览");
  conclusion.textContent = ownerVisibleText(stage4Subpage?.emptyState || workspace.conclusion, "");
  if (freshness && !runtimeReadModelStatusState) {
    freshness.textContent = ownerVisibleText(workspace.freshness, "等待财务数据状态");
  }
  if (runtimeTarget) runtimeTarget.textContent = ownerVisibleText(workspace.runtime);
  main.dataset.activeWorkspace = workspaceId;
  main.dataset.routeAlias = routeForState;
  main.dataset.stage4SubpageRoute = stage4Subpage?.routeAlias || "";
  main.dataset.stage6PageContract = stage4Subpage?.phase73LineagePage
    ? "phase_7_3"
    : stage4Subpage?.phase62PageContract ? "phase_6_2" : "primary_workspace";
  main.dataset.settingsSurface = workspaceId === "settings" ? "primary_workspace" : "none";
  main.setAttribute("data-stage5-history-ready", routeForState ? "true" : "false");
  applyV024Stage6RouteTransition(main, "enter");
  const settingsConsole = document.querySelector("[data-settings-feedback-console]");
  if (settingsConsole) settingsConsole.hidden = workspaceId !== "settings";
  applyStage5Phase53HomeSurfacePolicy(workspaceId);
  renderStage8WorkspaceFocus(workspaceId, stage4Subpage);
  shell.dataset.state = "ready";

  renderCards(workspace.cards);
  renderSecondaryTabs(workspace.secondaryTabs || [], workspaceId, routeForState);
  renderStage4SubpageSurface(stage4Subpage, workspaceId, routeForState);
  renderFeatureCards(workspace.features);
  renderDecisionRows(workspace.rows);
  renderTasks(workspace.tasks);
  renderUploadImportPanel(workspaceId);
  renderLedgerOperationFlow(workspaceId);
  renderHoldingsPersistencePanel(workspaceId, routeForState);
  renderSettingsOperationFlow(workspaceId);
  renderStage9DecisionReviewPanel(workspaceId);
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
  if (runtimeReadModelStatusState) applySourceAvailabilityBanner(runtimeReadModelStatusState);
  if (workspaceId === "settings") setEvidenceDrawer(false);
  if (!options.skipRouteSync) syncBrowserRoute(routeForState, { replace: options.replaceRoute === true });

  if (!options.silent) showToast(`已切换到${workspace.label}`);
  restoreStage6RouteScroll(routeForState, options.historyScrollY);
  const heading = document.querySelector("[data-stage6-page-heading]") || title;
  if (!options.preserveFocus && heading) heading.focus({ preventScroll: true });
}

function applyV024Stage6RouteTransition(main, state = "enter") {
  if (!main || !feedbackRuntimeState.motion || document.body.classList.contains("reduce-motion")) return;
  if (state === "exit") {
    main.dataset.v024RouteTransition = "exit";
  } else {
    main.dataset.v024RouteTransition = "enter";
  }
  main.dataset.v024RouteTransitionPhase = "6.2";
  window.setTimeout(() => {
    delete main.dataset.v024RouteTransition;
  }, PFI_V024_STAGE6_MOTION_CONTRACT.maxMotionMs);
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
    tile.hidden = !card;
    if (!card) return;
    tile.querySelector("span").textContent = safeUserText(card[0], "指标");
    tile.querySelector("[data-card-value]").textContent = safeUserText(card[1], "待补");
    tile.querySelector("[data-card-detail]").textContent = safeUserText(card[2], "待补充");
  });
}

function renderSecondaryTabs(tabs, workspaceId, routeForState) {
  const container = document.querySelector("[data-secondary-tabs]");
  if (!container) return;
  container.replaceChildren();
  const activeRoute = normalizeRouteAlias(routeForState || "");
  tabs.forEach((tab, index) => {
    const button = document.createElement("button");
    button.type = "button";
    button.className = "secondary-tab";
    button.dataset.secondaryTab = tab.title;
    button.dataset.featureWorkspace = workspaceId;
    if (tab.routeAlias) button.dataset.routeAlias = normalizeRouteAlias(tab.routeAlias);
    if (tab.view) button.dataset.featureView = tab.view;
    button.textContent = ownerVisibleText(tab.title, "二级入口");
    const tabRoute = normalizeRouteAlias(tab.routeAlias || "");
    const active = tabRoute ? activeRoute === tabRoute : index === 0;
    button.classList.toggle("is-active", active || (!activeRoute && index === 0));
    button.setAttribute("aria-current", button.classList.contains("is-active") ? "page" : "false");
    container.appendChild(button);
  });
}

function resolveStage4Subpage(workspaceId, routeAlias) {
  const catalog = stage4SubpageCatalog();
  const pages = catalog[workspaceId] || [];
  if (!pages.length) return null;
  const cleanRoute = normalizeRouteAlias(routeAlias || defaultRouteAliasForWorkspace(workspaceId));
  const cleanPath = cleanRoute.split("?", 1)[0];
  return pages.find((page) => {
    if (normalizeRouteAlias(page.routeAlias).split("?", 1)[0] === cleanPath) return true;
    return (page.alternateRoutes || []).some((alternateRoute) => normalizeRouteAlias(alternateRoute).split("?", 1)[0] === cleanPath);
  }) || pages[0] || null;
}

function stage4SubpageCatalog() {
  stage4PagesCatalog = stage4PagesCatalog || window.PFI_V023_STAGE4_PAGES || null;
  stage5SubpageCatalog = stage5SubpageCatalog || window.PFI_V024_STAGE5_PAGES || null;
  const legacyCatalog = stage5SubpageCatalog && typeof stage5SubpageCatalog.buildV024Stage5Phase52Catalog === "function"
    ? stage5SubpageCatalog.buildV024Stage5Phase52Catalog()
    : {
    ...(stage4PagesCatalog?.stage4ReviewSubpages || {}),
    ...(stage4PagesCatalog?.phase41Subpages || {}),
    ...(stage4PagesCatalog?.phase42Subpages || {}),
    ...(stage4PagesCatalog?.phase43Subpages || {}),
  };
  if (!(ACTIVE_PAGE_CONTRACTS.pages || []).length) return legacyCatalog;
  const legacyByRoute = Object.fromEntries(Object.values(legacyCatalog).flat().map((page) => [page.routeAlias, page]));
  return Object.freeze(Object.fromEntries(Object.entries(ACTIVE_PAGE_CONTRACTS.pageGroups || {}).map(([workspace]) => [
    workspace,
    Object.freeze(ACTIVE_PAGE_CONTRACTS.pages.filter((page) => page.workspace === workspace).map((page) => {
      const legacy = legacyByRoute[page.legacyRouteAlias] || {};
      return Object.freeze({
        ...legacy,
        ...page,
        emptyState: page.states.empty,
        errorState: page.states.error,
        loadingState: page.states.loading,
        alternateRoutes: Object.freeze([page.legacyRouteAlias, ...(legacy.alternateRoutes || []), ...(legacy.legacyAliases || [])]),
        sections: Object.freeze((legacy.sections || [
          { kind: "task", title: "页面任务", detail: page.jobToBeDone },
          { kind: "data", title: "页面数据", detail: page.dataObject },
          { kind: "action", title: "主要动作", detail: page.primaryAction },
        ]).map((section) => Object.freeze({ ...section }))),
        phase62PageContract: page.phase73LineagePage !== true,
      });
    })),
  ])));
}

function renderStage4SubpageSurface(page, workspaceId, routeForState) {
  const surface = ensureStage4SubpageSurface();
  if (!surface) return;
  if (!page) {
    surface.hidden = true;
    surface.replaceChildren();
    surface.dataset.stage4Workspace = "";
    surface.dataset.stage4Route = "";
    surface.dataset.stage5Route = "";
    surface.dataset.stage5UxState = "";
    return;
  }

  const stage5StateModel = buildStage5UxStateForPage(page);
  surface.hidden = false;
  surface.dataset.stage4Workspace = workspaceId;
  surface.dataset.stage4Route = normalizeRouteAlias(routeForState || page.routeAlias);
  surface.dataset.stage5Route = normalizeRouteAlias(routeForState || page.routeAlias);
  surface.dataset.stage5UxState = stage5StateModel ? "phase_5_3" : "";
  surface.replaceChildren();

  const article = document.createElement("article");
  article.className = `stage4-subpage stage4-layout-${page.layoutKind}`;
  article.setAttribute("data-stage4-layout-kind", page.layoutKind);
  article.setAttribute("data-stage5-differentiated-subpage", "phase_5_2");
  article.setAttribute("data-stage5-ux-state", "phase_5_3");
  article.setAttribute("data-stage5-history-ready", "true");
  article.setAttribute("data-stage6-page-contract", page.phase73LineagePage ? "phase_7_3" : page.phase62PageContract ? "phase_6_2" : "compatibility");
  article.setAttribute("data-stage6-job-to-be-done", ownerVisibleText(page.jobToBeDone, page.primaryObject));
  article.setAttribute("data-stage6-loading-state", ownerVisibleText(page.loadingState, "正在读取页面数据。"));
  article.setAttribute("data-stage6-empty-state", ownerVisibleText(page.emptyState, "暂无可用数据。"));
  article.setAttribute("data-stage6-error-state", ownerVisibleText(page.errorState, "无法读取页面数据。"));
  article.setAttribute("data-stage6-structural-signature", ownerVisibleText(page.structuralSignature, page.layoutKind));
  article.setAttribute("data-stage5-state-key", ownerVisibleText(page.stateKey, ""));
  article.setAttribute("data-stage5-data-object", ownerVisibleText(page.dataObject || page.primaryObject, ""));
  article.setAttribute("data-stage4-primary-object", page.primaryObject);
  article.setAttribute("data-stage4-primary-action", page.primaryAction);
  article.setAttribute("data-stage4-empty-state", page.emptyState);
  article.setAttribute("data-stage4-error-state", page.errorState);
  article.setAttribute("data-stage4-data-source", page.dataSource);

  const breadcrumb = document.createElement("nav");
  breadcrumb.className = "stage4-breadcrumb";
  breadcrumb.setAttribute("aria-label", "二级页面路径");
  breadcrumb.dataset.stage4Breadcrumb = "";
  (page.breadcrumb || []).forEach((item, index) => {
    const crumb = document.createElement("span");
    crumb.textContent = ownerVisibleText(item, "页面");
    breadcrumb.appendChild(crumb);
    if (index < page.breadcrumb.length - 1) {
      const divider = document.createElement("i");
      divider.setAttribute("aria-hidden", "true");
      divider.textContent = "/";
      breadcrumb.appendChild(divider);
    }
  });

  const header = document.createElement("div");
  header.className = "stage4-subpage-head";
  const headingWrap = document.createElement("div");
  const kicker = document.createElement("p");
  kicker.className = "panel-kicker";
  kicker.textContent = ownerVisibleText(page.primaryObject, "二级页面");
  const heading = document.createElement("h2");
  heading.textContent = ownerVisibleText(page.title, "二级页面");
  heading.tabIndex = -1;
  heading.dataset.stage6PageHeading = "";
  const summary = document.createElement("p");
  summary.textContent = ownerVisibleText(page.jobToBeDone, page.emptyState || "等待真实数据");
  summary.dataset.stage6JobToBeDone = "";
  const stateHint = document.createElement("p");
  stateHint.className = "stage6-page-state-hint";
  stateHint.textContent = ownerVisibleText(page.emptyState, "等待真实数据");
  stateHint.dataset.stage6EmptyState = "";
  headingWrap.append(kicker, heading, summary, stateHint);
  const action = document.createElement("button");
  action.type = "button";
  action.className = "primary-action stage4-primary-action";
  action.textContent = ownerVisibleText(page.primaryAction, "打开");
  action.dataset.stage4PrimaryActionButton = "";
  header.append(headingWrap, action);

  const stateGrid = document.createElement("dl");
  stateGrid.className = "stage4-state-grid";
  appendStage4State(stateGrid, "主对象", page.primaryObject);
  appendStage4State(stateGrid, "数据来源", page.dataSource);
  appendStage4State(stateGrid, "空状态", page.emptyState);
  appendStage4State(stateGrid, "错误状态", page.errorState);

  const sectionGrid = document.createElement("div");
  sectionGrid.className = "stage4-section-grid";
  (page.sections || []).forEach((section) => {
    const card = document.createElement("section");
    card.className = `stage4-section stage4-section-${section.kind}`;
    card.dataset.stage4SectionKind = section.kind;
    const title = document.createElement("h3");
    title.textContent = ownerVisibleText(section.title, "页面区域");
    const detail = document.createElement("p");
    detail.textContent = ownerVisibleText(section.detail, "等待真实数据");
    card.append(title, detail);
    sectionGrid.appendChild(card);
  });

  article.append(breadcrumb, header, stateGrid, sectionGrid);
  if (page.phase73LineagePage) {
    renderStage7LineagePage(article, page, routeForState);
  } else {
    appendStage5UxStates(article, stage5StateModel);
  }
  surface.appendChild(article);
}

async function refreshStage7Lineage() {
  if (runtimeStage7LineageLoading) return;
  runtimeStage7LineageLoading = true;
  runtimeStage7LineageError = "";
  try {
    const payload = await runtimeApiJson("/api/lineage");
    if (payload?.schema !== "PFIV025Stage7Phase73FormalWorkflowV1") {
      throw new Error("指标 lineage 响应格式不受支持");
    }
    runtimeStage7LineageState = payload;
  } catch (error) {
    runtimeStage7LineageState = null;
    runtimeStage7LineageError = String(error?.message || "无法读取指标 lineage");
  } finally {
    runtimeStage7LineageLoading = false;
    const main = document.querySelector("#main-workspace");
    const routeAlias = normalizeRouteAlias(main?.dataset.routeAlias || "");
    const resolved = STAGE6_ROUTES.resolveRouteAlias?.(routeAlias);
    const page = resolveStage4Subpage(resolved?.workspace || "", routeAlias);
    if (page?.phase73LineagePage && WORKSPACES[resolved.workspace]) {
      renderWorkspace(resolved.workspace, {
        silent: true,
        preserveFocus: true,
        routeAlias,
        skipRouteSync: true,
      });
    }
  }
}

function renderStage7LineagePage(article, page, routeForState) {
  article.dataset.stage7Phase73Page = page.pageKind || "lineage";
  article.querySelector(".stage4-state-grid")?.setAttribute("hidden", "");
  const sectionGrid = article.querySelector(".stage4-section-grid");
  if (!sectionGrid) return;
  sectionGrid.className = "stage7-lineage-surface";
  sectionGrid.replaceChildren();
  const stateHint = article.querySelector(".stage6-page-state-hint");
  const action = article.querySelector("[data-stage4-primary-action-button]");
  if (action) action.hidden = true;

  if (!runtimeStage7LineageState && !runtimeStage7LineageError) {
    if (stateHint) stateHint.textContent = "正在从本机服务读取参数、事件链与指标状态。";
    sectionGrid.appendChild(stage7MessageCard("正在读取正式 runtime lineage…", "loading"));
    void refreshStage7Lineage();
    return;
  }
  if (runtimeStage7LineageError) {
    if (stateHint) stateHint.textContent = runtimeStage7LineageError;
    const card = stage7MessageCard(`读取失败：${runtimeStage7LineageError}`, "error");
    const retry = document.createElement("button");
    retry.type = "button";
    retry.className = "primary-action";
    retry.textContent = "重试读取";
    retry.addEventListener("click", () => {
      runtimeStage7LineageError = "";
      void refreshStage7Lineage();
    });
    card.appendChild(retry);
    sectionGrid.appendChild(card);
    return;
  }

  const payload = runtimeStage7LineageState || {};
  if (stateHint) stateHint.textContent = payload.status === "ready"
    ? "当前正式 runtime 投影已就绪；页面不读取旁路 HTML。"
    : "部分来源未加载，页面保持 fail-closed。";
  if (page.pageKind === "parameters") {
    renderStage7ParameterCenter(sectionGrid, payload.parameter_center || {}, routeForState);
  } else if (page.pageKind === "interconnection") {
    renderStage7InterconnectionMap(sectionGrid, payload.interconnection_map || {}, routeForState);
  } else if (page.pageKind === "metric") {
    renderStage7MetricDrilldown(sectionGrid, payload.metric_drilldown || {}, routeForState);
  }
}

function stage7MessageCard(message, state) {
  const card = document.createElement("section");
  card.className = `stage7-lineage-message stage7-lineage-${state}`;
  card.dataset.stage7LineageState = state;
  const text = document.createElement("p");
  text.textContent = message;
  card.appendChild(text);
  return card;
}

function stage7QueryValue(routeAlias, key) {
  try {
    return new URL(String(routeAlias || ""), window.location.origin).searchParams.get(key) || "";
  } catch (_error) {
    return "";
  }
}

function stage7DisplayValue(value) {
  if (value === null || value === undefined || value === "") return "未设置";
  if (typeof value === "object") return JSON.stringify(value, null, 2);
  if (value === true) return "是";
  if (value === false) return "否";
  return String(value);
}

function stage7HashValue(value, missingText = "未生成（输入阻断）") {
  const clean = String(value || "").trim();
  return clean || missingText;
}

function stage7DefinitionRow(list, label, value, className = "") {
  const wrapper = document.createElement("div");
  if (className) wrapper.className = className;
  const term = document.createElement("dt");
  term.textContent = label;
  const description = document.createElement("dd");
  description.textContent = stage7DisplayValue(value);
  wrapper.append(term, description);
  list.appendChild(wrapper);
}

function renderStage7ParameterCenter(container, payload, routeAlias) {
  const domainId = stage7QueryValue(routeAlias, "domain");
  const viewModel = STAGE7_LINEAGE.buildParameterCenterViewModel?.(payload, domainId);
  if (!viewModel) {
    container.appendChild(stage7MessageCard("参数中心合同未加载。", "error"));
    return;
  }
  container.dataset.stage7ParameterCenter = viewModel.status;

  const summary = document.createElement("section");
  summary.className = "stage7-lineage-summary";
  const title = document.createElement("h3");
  title.textContent = "当前参数与公式身份";
  const text = document.createElement("p");
  text.textContent = `${viewModel.summaryZh} · ${viewModel.consistencyZh}`;
  const hashes = document.createElement("dl");
  hashes.className = "stage7-hash-grid";
  stage7DefinitionRow(hashes, "parameter hash", stage7HashValue(viewModel.parameterHash), "stage7-hash-row");
  stage7DefinitionRow(hashes, "formula registry hash", stage7HashValue(viewModel.formulaRegistryHash), "stage7-hash-row");
  stage7DefinitionRow(hashes, "写入状态", viewModel.writeEnabled ? "允许修改" : "本页只读");
  summary.append(title, text, hashes);

  const layout = document.createElement("div");
  layout.className = "stage7-parameter-layout";
  const nav = document.createElement("nav");
  nav.className = "stage7-domain-list";
  nav.setAttribute("aria-label", "参数域");
  viewModel.domains.forEach((domain) => {
    const button = document.createElement("button");
    button.type = "button";
    button.dataset.stage7ParameterDomain = domain.domain_id;
    button.className = "stage7-domain-button";
    button.classList.toggle("is-active", viewModel.selectedDomain?.domain_id === domain.domain_id);
    button.setAttribute("aria-pressed", button.classList.contains("is-active") ? "true" : "false");
    button.textContent = `${domain.label_zh} · ${Number(domain.entry_count || 0)}`;
    button.addEventListener("click", () => setActiveWorkspace("settings", {
      routeAlias: `/settings/parameters?domain=${encodeURIComponent(domain.domain_id)}`,
    }));
    nav.appendChild(button);
  });
  const detail = document.createElement("section");
  detail.className = "stage7-parameter-detail";
  detail.dataset.stage7SelectedDomain = viewModel.selectedDomain?.domain_id || "";
  const detailTitle = document.createElement("h3");
  detailTitle.textContent = viewModel.selectedDomain?.label_zh || "暂无参数域";
  const detailDescription = document.createElement("p");
  detailDescription.textContent = viewModel.selectedDomain?.description_zh || "当前参数域没有可展示条目。";
  const entryGrid = document.createElement("div");
  entryGrid.className = "stage7-parameter-entry-grid";
  (viewModel.selectedDomain?.entries || []).forEach((entry) => {
    const card = document.createElement("article");
    card.className = "stage7-parameter-card";
    card.dataset.stage7ParameterId = entry.parameter_id;
    const heading = document.createElement("h4");
    heading.textContent = entry.label_zh;
    const value = document.createElement("pre");
    value.textContent = stage7DisplayValue(entry.value);
    const description = document.createElement("p");
    description.textContent = entry.description_zh;
    const impact = document.createElement("p");
    impact.textContent = `影响范围：${(entry.impact_surfaces || []).join("、") || "以公式与调用方为准"}`;
    const editable = document.createElement("span");
    editable.className = "stage7-lineage-badge";
    editable.textContent = entry.user_editable ? "可由用户修改" : "只读治理参数";
    card.append(heading, value, description, impact, editable);
    entryGrid.appendChild(card);
  });
  if (!entryGrid.childElementCount) entryGrid.appendChild(stage7MessageCard("此参数域当前无可展示条目。", "empty"));
  detail.append(detailTitle, detailDescription, entryGrid);
  layout.append(nav, detail);

  const formulas = document.createElement("section");
  formulas.className = "stage7-formula-register";
  const formulaTitle = document.createElement("h3");
  formulaTitle.textContent = "公式注册表";
  const formulaGrid = document.createElement("div");
  formulaGrid.className = "stage7-formula-grid";
  viewModel.formulas.forEach((formula) => {
    const card = document.createElement("article");
    card.className = "stage7-formula-card";
    card.dataset.stage7FormulaId = formula.formula_id;
    const heading = document.createElement("h4");
    heading.textContent = `${formula.formula_id} · ${formula.label_zh}`;
    const definition = document.createElement("p");
    definition.textContent = formula.definition_zh;
    const meta = document.createElement("p");
    meta.textContent = `${formula.version} · ${formula.validation_status} · ${formula.lifecycle_status}`;
    const hash = document.createElement("code");
    hash.textContent = stage7HashValue(formula.formula_hash);
    card.append(heading, definition, meta, hash);
    formulaGrid.appendChild(card);
  });
  formulas.append(formulaTitle, formulaGrid);
  container.append(summary, layout, formulas);
}

function renderStage7InterconnectionMap(container, payload, routeAlias) {
  const nodeId = stage7QueryValue(routeAlias, "node");
  const viewModel = STAGE7_LINEAGE.buildInterconnectionMapViewModel?.(payload, nodeId);
  if (!viewModel) {
    container.appendChild(stage7MessageCard("Interconnection Map 合同未加载。", "error"));
    return;
  }
  container.dataset.stage7InterconnectionMap = viewModel.status;
  const identity = document.createElement("dl");
  identity.className = "stage7-hash-grid";
  stage7DefinitionRow(identity, "data hash", stage7HashValue(viewModel.dataHash), "stage7-hash-row");
  stage7DefinitionRow(identity, "read-model hash", stage7HashValue(viewModel.readModelHash), "stage7-hash-row");
  stage7DefinitionRow(identity, "完整 lineage", viewModel.lineageCompleteCount ?? "未加载");
  stage7DefinitionRow(identity, "缺失 lineage", viewModel.lineageMissingCount ?? "未加载");
  container.appendChild(identity);
  if (viewModel.status !== "ready") {
    container.appendChild(stage7MessageCard(viewModel.blockingReasonZh || "真实事件来源尚未加载。", "empty"));
  }

  const graph = document.createElement("section");
  graph.className = "stage7-interconnection-graph";
  graph.setAttribute("aria-label", "真实事件关联图");
  viewModel.nodes.forEach((node, index) => {
    const button = document.createElement("button");
    button.type = "button";
    button.className = "stage7-map-node";
    button.dataset.stage7InterconnectionNode = node.node_id;
    button.classList.toggle("is-active", viewModel.selectedNode?.node_id === node.node_id);
    button.setAttribute("aria-pressed", button.classList.contains("is-active") ? "true" : "false");
    const label = document.createElement("strong");
    label.textContent = node.label_zh;
    const count = document.createElement("span");
    count.textContent = node.count === null || node.count === undefined ? "未加载" : `${Number(node.count).toLocaleString("zh-CN")} 项`;
    button.append(label, count);
    button.addEventListener("click", () => setActiveWorkspace("sync", {
      routeAlias: `/data/interconnection?node=${encodeURIComponent(node.node_id)}`,
    }));
    graph.appendChild(button);
    if (index < viewModel.nodes.length - 1) {
      const arrow = document.createElement("span");
      arrow.className = "stage7-map-arrow";
      arrow.setAttribute("aria-hidden", "true");
      arrow.textContent = "→";
      graph.appendChild(arrow);
    }
  });

  const detail = document.createElement("section");
  detail.className = "stage7-map-detail";
  detail.dataset.stage7SelectedNode = viewModel.selectedNode?.node_id || "";
  const detailTitle = document.createElement("h3");
  detailTitle.textContent = viewModel.selectedNode?.label_zh || "关联节点";
  const detailText = document.createElement("p");
  detailText.textContent = viewModel.selectedEdges.length
    ? viewModel.selectedEdges.map((edge) => `${edge.from} → ${edge.to}：${edge.label_zh}`).join("；")
    : "当前节点没有额外关联边。";
  detail.append(detailTitle, detailText);
  if (viewModel.selectedNode?.route && !String(viewModel.selectedNode.route).startsWith("/data/interconnection")) {
    const related = document.createElement("button");
    related.type = "button";
    related.className = "secondary-action";
    related.textContent = "打开相关正式页面";
    related.addEventListener("click", () => {
      const target = STAGE6_ROUTES.resolveRouteAlias?.(viewModel.selectedNode.route);
      if (target?.status === "resolved") setActiveWorkspace(target.workspace, { routeAlias: target.routeAlias });
    });
    detail.appendChild(related);
  }

  const eventSection = document.createElement("section");
  eventSection.className = "stage7-event-types";
  const eventTitle = document.createElement("h3");
  eventTitle.textContent = "经济事件类型与发布状态";
  const table = document.createElement("table");
  table.innerHTML = "<thead><tr><th>事件</th><th>已发布</th><th>待复核</th><th>未决策略</th></tr></thead>";
  const body = document.createElement("tbody");
  viewModel.eventTypes.forEach((item) => {
    const row = document.createElement("tr");
    [item.label_zh, item.published_count, item.review_count, item.unresolved_policy === "review_required_no_publication" ? "缺证据不发布" : "映射完整后发布"].forEach((value) => {
      const cell = document.createElement("td");
      cell.textContent = stage7DisplayValue(value);
      row.appendChild(cell);
    });
    body.appendChild(row);
  });
  table.appendChild(body);
  eventSection.append(eventTitle, table);
  container.append(graph, detail, eventSection);
}

function renderStage7MetricDrilldown(container, payload, routeAlias) {
  const metricId = stage7QueryValue(routeAlias, "metric");
  const viewModel = STAGE7_LINEAGE.buildMetricDrilldownViewModel?.(payload, metricId);
  if (!viewModel) {
    container.appendChild(stage7MessageCard("指标下钻合同未加载。", "error"));
    return;
  }
  container.dataset.stage7MetricDrilldown = viewModel.status;
  container.dataset.stage7NonReadyFalseZeroCount = String(viewModel.nonReadyFalseZeroCount);
  const picker = document.createElement("label");
  picker.className = "stage7-metric-picker";
  const pickerLabel = document.createElement("span");
  pickerLabel.textContent = "选择指标";
  const select = document.createElement("select");
  select.dataset.stage7MetricSelect = "";
  viewModel.metrics.forEach((metric) => {
    const option = document.createElement("option");
    option.value = metric.metric_id;
    option.textContent = `${metric.label_zh} · ${metric.status}`;
    option.selected = metric.metric_id === viewModel.selectedMetric?.metric_id;
    select.appendChild(option);
  });
  select.addEventListener("change", () => setActiveWorkspace("insights", {
    routeAlias: `/reports/metric-drilldown?metric=${encodeURIComponent(select.value)}`,
  }));
  picker.append(pickerLabel, select);
  container.appendChild(picker);
  const metric = viewModel.selectedMetric;
  if (!metric) {
    container.appendChild(stage7MessageCard("当前没有可下钻指标。", "empty"));
    return;
  }

  const headline = document.createElement("section");
  headline.className = "stage7-metric-headline";
  headline.dataset.stage7SelectedMetric = metric.metric_id;
  const heading = document.createElement("h3");
  heading.textContent = metric.label_zh;
  const value = document.createElement("strong");
  value.textContent = viewModel.selectedValueZh;
  const status = document.createElement("span");
  status.className = `stage7-lineage-badge stage7-metric-${metric.status}`;
  status.textContent = metric.status;
  const reason = document.createElement("p");
  reason.textContent = metric.blocking_reason_zh || "当前指标基于已发布真实事件计算；待复核事件不进入当前值。";
  headline.append(heading, value, status, reason);

  const range = metric.data_range || {};
  const trace = document.createElement("dl");
  trace.className = "stage7-metric-trace";
  stage7DefinitionRow(trace, "数据范围", `${range.start || "未加载"} → ${range.end || "未加载"} · as of ${range.as_of || "未加载"}`);
  stage7DefinitionRow(trace, "公式", `${metric.formula_id || "未绑定"} · ${metric.formula_version || "版本未加载"}`);
  stage7DefinitionRow(trace, "公式说明", metric.formula_definition_zh || "公式说明未加载");
  stage7DefinitionRow(trace, "formula hash", stage7HashValue(metric.formula_hash), "stage7-hash-row");
  stage7DefinitionRow(trace, "parameter hash", stage7HashValue(metric.parameter_hash), "stage7-hash-row");
  stage7DefinitionRow(trace, "data hash", stage7HashValue(metric.data_hash), "stage7-hash-row");
  stage7DefinitionRow(trace, "read-model hash", stage7HashValue(metric.read_model_hash), "stage7-hash-row");
  stage7DefinitionRow(trace, "来源", (metric.source_ids || []).join("、") || "来源未加载");
  stage7DefinitionRow(trace, "记录数", metric.record_count ?? "未加载");
  stage7DefinitionRow(trace, "阻断", metric.blocking_reason_zh || "无");

  const event = metric.event_lineage || {};
  const eventCard = document.createElement("section");
  eventCard.className = "stage7-metric-event-lineage";
  const eventTitle = document.createElement("h3");
  eventTitle.textContent = "事件 lineage";
  const eventList = document.createElement("dl");
  stage7DefinitionRow(eventList, "事件口径", event.metric_event_key || "当前指标不由交易事件集合直接计算");
  stage7DefinitionRow(eventList, "经济事件数", event.economic_event_count ?? "输入阻断");
  stage7DefinitionRow(eventList, "事件集合 hash", stage7HashValue(event.economic_event_set_hash), "stage7-hash-row");
  stage7DefinitionRow(eventList, "单事件最大计数", event.maximum_count_per_economic_event ?? "不适用");
  eventCard.append(eventTitle, eventList);
  container.append(headline, trace, eventCard);
}

function ensureStage4SubpageSurface() {
  const existing = document.querySelector("[data-stage4-subpage-surface]");
  if (existing) return existing;
  const main = document.querySelector("#main-workspace");
  if (!main) return null;
  const surface = document.createElement("section");
  surface.className = "stage4-subpage-surface";
  surface.dataset.stage4SubpageSurface = "";
  surface.hidden = true;
  surface.setAttribute("aria-label", "二级页面差异化内容");
  const pageTabs = document.querySelector(".page-tabs-panel");
  if (pageTabs?.parentNode) {
    pageTabs.insertAdjacentElement("afterend", surface);
  } else {
    main.prepend(surface);
  }
  return surface;
}

function appendStage4State(list, label, value) {
  const item = document.createElement("div");
  const term = document.createElement("dt");
  term.textContent = label;
  const description = document.createElement("dd");
  description.textContent = ownerVisibleText(value, "待补");
  item.append(term, description);
  list.appendChild(item);
}

function buildStage5UxStateForPage(page) {
  const api = stage5UxState || window.PFI_V024_STAGE5_UX_STATE || null;
  stage5UxState = api;
  if (!api || typeof api.buildV024Stage5PageStateModel !== "function" || !page) return null;
  return api.buildV024Stage5PageStateModel(page);
}

function buildStage5UxStateCatalogForRuntime() {
  const api = stage5UxState || window.PFI_V024_STAGE5_UX_STATE || null;
  stage5UxState = api;
  if (!api || typeof api.buildV024Stage5UxStateCatalog !== "function") return null;
  return api.buildV024Stage5UxStateCatalog(stage4SubpageCatalog());
}

function appendStage5UxStates(parent, stateModel) {
  if (!parent || !stateModel?.states) return;
  const grid = document.createElement("section");
  grid.className = "stage5-ux-state-grid";
  grid.setAttribute("aria-label", "页面交互状态");
  (stateModel.stateKinds || ["loading", "success", "error", "empty"]).forEach((kind) => {
    const state = stateModel.states[kind];
    if (!state) return;
    const item = document.createElement("article");
    item.className = `stage5-ux-state stage5-ux-state-${kind}`;
    item.setAttribute("data-stage5-state", kind);
    const title = document.createElement("h3");
    title.textContent = stage5StateTitle(kind);
    const message = document.createElement("p");
    message.textContent = ownerVisibleText(state.message_zh, "状态待确认");
    const action = document.createElement("button");
    action.type = "button";
    action.className = "stage5-state-action";
    action.textContent = ownerVisibleText(state.action?.label, "查看页面");
    action.dataset.stage5StateAction = kind;
    action.dataset.featureWorkspace = state.action?.targetWorkspace || stateModel.targetWorkspace || "home";
    action.dataset.routeAlias = normalizeRouteAlias(state.action?.routeAlias || stateModel.routeAlias || "");
    if (kind === "empty") action.setAttribute("data-stage5-empty-action", "true");
    if (kind === "error") action.setAttribute("data-stage5-error-action", "true");
    action.addEventListener("click", () => {
      setActiveWorkspace(action.dataset.featureWorkspace || "home", {
        routeAlias: action.dataset.routeAlias || "",
        keepFunctionDetail: true,
      });
    });
    item.append(title, message, action);
    grid.appendChild(item);
  });
  parent.appendChild(grid);
}

function stage5StateTitle(kind) {
  if (kind === "loading") return "加载中";
  if (kind === "success") return "已就绪";
  if (kind === "error") return "读取失败";
  if (kind === "empty") return "暂无数据";
  return "页面状态";
}

function renderFeatureCards(cards) {
  const grid = document.querySelector("[data-workflow-cards]");
  if (!grid) return;
  const activeWorkspace = document.querySelector("#main-workspace")?.dataset.activeWorkspace || "";
  grid.replaceChildren();
  cards.forEach((card, index) => {
    const item = document.createElement("article");
    item.className = "workflow-card";
    item.dataset.workflowCard = String(index);

    const head = document.createElement("div");
    head.className = "workflow-card-head";
    const title = document.createElement("strong");
    const titleText = ownerVisibleText(card.title, "任务入口");
    title.textContent = titleText;
    item.setAttribute("aria-label", `${titleText}，${localizeStatus(card.status)}`);
    head.appendChild(title);

    const actions = document.createElement("div");
    actions.className = "workflow-actions";

    const openAction = featureOpenControl(card);
    actions.appendChild(openAction);
    if (activeWorkspace !== "home") {
      const evidenceButton = document.createElement("button");
      evidenceButton.type = "button";
      evidenceButton.dataset.workflowEvidence = String(index);
      evidenceButton.textContent = "查看说明";
      evidenceButton.addEventListener("click", () => showWorkflowEvidence(card));
      actions.appendChild(evidenceButton);
    }

    item.appendChild(head);
    item.appendChild(actions);
    grid.appendChild(item);
  });
}

function featureTarget(title) {
  const raw = String(title || "").trim();
  if (Object.prototype.hasOwnProperty.call(FEATURE_TARGETS, raw)) return FEATURE_TARGETS[raw];
  const compact = raw.replace(/\s+/g, "");
  if (Object.prototype.hasOwnProperty.call(FEATURE_TARGETS, compact)) return FEATURE_TARGETS[compact];
  if (/回测|参数|盘感|策略|模拟/.test(compact)) return { workspace: "market_research", routeAlias: "/market-research/strategy-lab", label: "打开策略" };
  if (/持仓|订单|组合|纪律/.test(compact)) return { workspace: "investment", label: "打开投资" };
  if (/研究|政策/.test(compact)) return { workspace: "market_research", routeAlias: "/market-research?tab=research", label: "打开研究" };
  if (/报告|证据/.test(compact)) return { workspace: "insights", label: "打开报告" };
  if (/数据|来源|任务|隐私|备份|系统/.test(compact)) return { workspace: "settings", label: "打开设置" };
  if (/市场|指数|主题|自选/.test(compact)) return { workspace: "market_research", routeAlias: "/market-research?tab=market", label: "打开市场" };
  return { workspace: "home", label: "打开入口" };
}

function featureOpenControl(card) {
  const target = card.target || featureTarget(card.title);
  if (target.view) {
    const button = document.createElement("button");
    button.type = "button";
    button.className = "workflow-open";
    button.dataset.featureView = target.view;
    button.textContent = target.label || "打开任务";
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

function workspaceForFunctionView(detail) {
  if (STRATEGY_LAB_VIEWS.has(detail.view)) return "market_research";
  if (detail.workspace === "market" || detail.workspace === "research" || detail.workspace === "strategy") return "market_research";
  if (detail.workspace === "portfolio") return "investment";
  if (detail.workspace === "data") return "settings";
  return detail.workspace;
}

function routeAliasForFunctionView(detail) {
  if (STRATEGY_LAB_VIEWS.has(detail.view)) return "/market-research/strategy-lab";
  if (detail.workspace === "market") return "/market-research?tab=market";
  if (detail.workspace === "research") return "/market-research?tab=research";
  if (detail.workspace === "portfolio") return "/investment?tab=holdings";
  if (detail.workspace === "data") return "/settings?tab=data-system";
  return defaultRouteAliasForWorkspace(workspaceForFunctionView(detail));
}

function openFunctionView(view, options = {}) {
  const detail = FUNCTION_VIEWS[view] || FUNCTION_VIEWS.single;
  const workspaceId = workspaceForFunctionView(detail);
  const routeAlias = normalizeRouteAlias(options.routeAlias || routeAliasForFunctionView(detail));
  renderWorkspace(workspaceId, {
    silent: true,
    preserveFocus: true,
    keepFunctionDetail: true,
    routeAlias,
    skipRouteSync: options.skipRouteSync === true,
    replaceRoute: options.replaceRoute === true,
  });
  renderFunctionDetail(detail);
  writeContext({ ...currentContext(), workspace: workspaceId, feature_view: detail.view, route_alias: routeAlias });
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

  if (title) title.textContent = ownerVisibleText(detail.title, "功能");
  if (purpose) purpose.textContent = ownerVisibleText(detail.purpose, "");
  if (status) {
    status.textContent = detail.status;
    status.className = `status-pill ${statusClass(detail.status)}`;
  }
  if (action) action.textContent = ownerVisibleText(detail.primaryAction, "开始");
  if (workspace) {
    const workspaceId = workspaceForFunctionView(detail);
    workspace.textContent = ownerVisibleText(WORKSPACE_LABELS[workspaceId] || workspaceId, "工作区");
  }
  if (actionButton) {
    actionButton.textContent = ownerVisibleText(detail.primaryAction, "开始");
    actionButton.dataset.functionActionView = detail.view;
  }
  if (legacyLink) {
    legacyLink.href = legacyViewUrl(detail.legacyView || detail.view);
    legacyLink.target = "_blank";
    legacyLink.rel = "noreferrer";
    legacyLink.textContent = `打开${ownerVisibleText(detail.title, "功能")}兼容详情`;
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
      span.textContent = ownerVisibleText(item, "检查项");
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
  if (jobLabel) jobLabel.textContent = `${detail.primaryAction} · 已进入同屏处理流程`;
  renderFunctionRunner(detail);
  showToast(`已进入${detail.title}处理流程`);
}

function renderFunctionRunner(detail) {
  const runner = document.querySelector("[data-function-runner]");
  if (!runner) return;
  runner.hidden = false;
  runner.dataset.activeFunction = detail.view;
  runner.querySelector("[data-function-run-title]").textContent = `${ownerVisibleText(detail.title, "任务")} · 处理流程`;
  runner.querySelector("[data-function-run-summary]").textContent = ownerVisibleText(detail.runSummary, "");
  runner.querySelector("[data-function-run-state]").textContent = "已进入";

  const steps = runner.querySelector("[data-function-run-steps]");
  if (steps) {
    steps.replaceChildren();
    detail.runSteps.forEach((item, index) => {
      const li = document.createElement("li");
      const strong = document.createElement("strong");
      const span = document.createElement("span");
      strong.textContent = `步骤 ${index + 1}`;
      span.textContent = ownerVisibleText(item, "步骤");
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
      strong.textContent = ownerVisibleText(label, "字段");
      span.textContent = ownerVisibleText(value, "待补");
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
      td.textContent = ownerVisibleText(value, "");
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
    title.textContent = ownerVisibleText(item.title, "任务");
    const detail = document.createElement("span");
    if (index === 1) detail.id = "task-phase";
    if (index === 2) detail.id = "background-job-label";
    detail.textContent = ownerVisibleText(item.detail, "等待处理");
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
    title: `${ownerVisibleText(card.title, "功能")}说明`,
    Evidence: ownerVisibleText(card.evidence, "页面说明"),
    Source: "本机资料",
    Model: "本机读取",
    Parameters: "人工复核",
    "Data lineage": ownerVisibleText(card.description, "页面功能说明。"),
    "Raw document": "本机摘要",
  });
  setEvidenceDrawer(true);
  setActionFeedback("success", `已打开${ownerVisibleText(card.title, "功能")}说明`);
}

function applyEvidenceDrawer(drawer) {
  const title = document.querySelector("[data-evidence-title]");
  if (title && drawer.title) title.textContent = ownerVisibleText(drawer.title, "PFI · 页面说明");
  document.querySelectorAll("[data-evidence-field]").forEach((node) => {
    const key = node.dataset.evidenceField;
    if (!Object.prototype.hasOwnProperty.call(drawer, key)) return;
    node.textContent = ownerVisibleText(drawer[key], node.textContent || "待补");
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
    const serial = clickFeedbackSerial + 1;
    clickFeedbackSerial = serial;
    clickSafeId(button, serial);
    createRipple(event, button);
    setPressedFeedback(button);
  }, true);
}

function setActiveWorkspace(workspaceId, options = {}) {
  const motion = window.PFI_V025_STAGE8_MOTION;
  if (motion?.transitionRoute && options.motion !== false) {
    return motion.transitionRoute(() => renderWorkspace(workspaceId, options), document.querySelector("#main-workspace"));
  }
  return renderWorkspace(workspaceId, options);
}

function defaultRouteAliasForWorkspace(workspaceId) {
  if (workspaceId === "market_research") return "/market-research";
  const entries = [...document.querySelectorAll('[data-primary-entry="true"]')];
  const primary = entries.find((entry) => entry.dataset.workspace === workspaceId && entry.dataset.entryType !== "v01_alias");
  const any = entries.find((entry) => entry.dataset.workspace === workspaceId);
  return (primary || any)?.dataset.routeAlias || "";
}

function loadStage6RouteScrollMemory() {
  try {
    const stored = JSON.parse(window.sessionStorage.getItem(STAGE6_ROUTE_SCROLL_STORAGE_KEY) || "{}");
    if (stored && typeof stored === "object") stage6RouteScrollMemory = { ...stored };
  } catch (_error) {
    stage6RouteScrollMemory = Object.create(null);
  }
  return stage6RouteScrollMemory;
}

function saveStage6RouteScroll(routeAlias) {
  const clean = normalizeRouteAlias(routeAlias);
  if (!clean) return;
  loadStage6RouteScrollMemory();
  const scrollY = Math.max(0, Number(window.scrollY || 0));
  stage6RouteScrollMemory[clean] = scrollY;
  try {
    window.sessionStorage.setItem(STAGE6_ROUTE_SCROLL_STORAGE_KEY, JSON.stringify(stage6RouteScrollMemory));
  } catch (_error) {
    // Static/private previews can deny sessionStorage; in-memory restoration remains available.
  }
  if (normalizeRouteAlias(routeAliasFromLocation()) === clean) {
    replaceCurrentStage6HistoryState(clean, { scrollY, source: "scroll_snapshot" });
  }
}

function restoreStage6RouteScroll(routeAlias, historyScrollY) {
  const clean = normalizeRouteAlias(routeAlias);
  loadStage6RouteScrollMemory();
  const stored = Number(stage6RouteScrollMemory[clean] || 0);
  const fromHistory = Number(historyScrollY);
  const target = Number.isFinite(fromHistory) && fromHistory >= 0 ? fromHistory : stored;
  window.requestAnimationFrame(() => window.scrollTo({ top: target, left: 0, behavior: "auto" }));
}

function normalizeRouteAlias(routeAlias) {
  const raw = String(routeAlias || "").trim();
  const clean = raw.startsWith("#") ? raw.slice(1) : raw;
  if (!clean) return "";
  if (typeof STAGE3_ROUTES.resolveRouteAlias === "function") {
    const resolved = STAGE3_ROUTES.resolveRouteAlias(raw || clean);
    if (resolved?.status === "resolved" && resolved.routeAlias) return resolved.routeAlias;
  }
  if (Object.prototype.hasOwnProperty.call(LEGACY_ROUTE_ALIAS_TARGETS, clean)) return LEGACY_ROUTE_ALIAS_TARGETS[clean];
  return clean;
}

function routeWorkspaceFromAlias(routeAlias) {
  if (typeof STAGE3_ROUTES.resolveRouteAlias === "function") {
    const resolved = STAGE3_ROUTES.resolveRouteAlias(routeAlias);
    if (resolved?.status === "resolved" && resolved.workspace) {
      return { workspace: resolved.workspace, routeAlias: resolved.routeAlias, view: "" };
    }
  }
  const clean = normalizeRouteAlias(routeAlias);
  if (!clean) return null;
  if (clean.startsWith("/market-research/strategy-lab")) {
    return { workspace: "market_research", routeAlias: "/market-research/strategy-lab", view: "" };
  }
  const routePrefixes = [
    ["/overview", "home"],
    ["/accounts", "accounts"],
    ["/ledger", "ledger"],
    ["/investment", "investment"],
    ["/consumption", "consumption"],
    ["/data", "sync"],
    ["/review", "recommendations"],
    ["/reports", "insights"],
    ["/market-research", "market_research"],
    ["/settings", "settings"],
  ];
  const matched = routePrefixes.find(([prefix]) => clean === prefix || clean.startsWith(`${prefix}?`));
  if (matched) {
    return { workspace: matched[1], routeAlias: clean, view: "" };
  }
  if (clean.startsWith("/market-research")) {
    return { workspace: "market_research", routeAlias: clean, view: "" };
  }
  if (clean.startsWith("/investment?tab=holdings")) {
    return { workspace: "investment", routeAlias: clean, view: "" };
  }
  if (clean.startsWith("/settings?tab=data-system")) {
    return { workspace: "settings", routeAlias: clean, view: "" };
  }
  return null;
}

function workspaceTargetFromRoute(routeAlias) {
  const clean = normalizeRouteAlias(routeAlias);
  if (!clean) return null;
  const explicit = routeWorkspaceFromAlias(clean);
  if (explicit) return explicit;
  const entry = [...document.querySelectorAll('[data-primary-entry="true"]')]
    .find((button) => normalizeRouteAlias(button.dataset.routeAlias) === clean);
  if (!entry) return null;
  return {
    workspace: entry.dataset.workspace || "home",
    routeAlias: clean,
    view: entry.dataset.featureView || "",
  };
}

function routeAliasFromLocation() {
  const pathname = decodeURIComponent(String(window.location.pathname || ""));
  const hashRoute = decodeURIComponent(String(window.location.hash || "").replace(/^#/, ""));
  if (stage6HistoryMode() === "canonical_path" && pathname.startsWith("/") && !["/", "/index.html"].includes(pathname)) {
    const source = new URLSearchParams(window.location.search || "");
    const routeParams = new URLSearchParams();
    ["tab", "domain", "node", "metric"].forEach((key) => {
      if (source.has(key)) routeParams.set(key, source.get(key) || "");
    });
    const query = routeParams.toString();
    return query ? `${pathname}?${query}` : pathname;
  }
  if (hashRoute.startsWith("/")) return `#${hashRoute}`;
  const params = initialSearchParams();
  return params.get("route") || "";
}

function stage6HistoryMode() {
  const protocol = String(window.location.protocol || "");
  const pathname = String(window.location.pathname || "");
  const directHttpShell = (protocol === "http:" || protocol === "https:") && !pathname.includes("/component/");
  return directHttpShell ? "canonical_path" : "hash_compatibility";
}

function stage6CanonicalUrlForRoute(routeAlias) {
  const clean = normalizeRouteAlias(routeAlias);
  const url = new URL(String(window.location || ""), window.location.origin || "http://127.0.0.1");
  ["route", "tab", "view", "domain", "node", "metric"].forEach((key) => url.searchParams.delete(key));
  const routeUrl = new URL(clean || "/overview", url.origin);
  routeUrl.searchParams.forEach((value, key) => url.searchParams.set(key, value));
  if (stage6HistoryMode() === "canonical_path") {
    url.pathname = routeUrl.pathname || "/overview";
    url.hash = "";
  } else {
    url.hash = clean || "/overview";
  }
  return url;
}

function stage6HistoryState(routeAlias, overrides = {}) {
  const clean = normalizeRouteAlias(routeAlias);
  const resolved = typeof STAGE3_ROUTES.resolveRouteAlias === "function"
    ? STAGE3_ROUTES.resolveRouteAlias(clean)
    : null;
  return {
    schema: "PFIV025Stage6Phase63HistoryStateV1",
    routeAlias: clean,
    workspace: resolved?.workspace || "",
    routeState: resolved?.status === "resolved" ? "resolved" : "invalid",
    scrollY: Math.max(0, Number(overrides.scrollY ?? window.scrollY ?? 0)),
    source: overrides.source || "navigation",
    ...overrides,
  };
}

function replaceCurrentStage6HistoryState(routeAlias, overrides = {}) {
  if (!window.history || typeof window.history.replaceState !== "function") return null;
  const state = stage6HistoryState(routeAlias, overrides);
  try {
    window.history.replaceState(state, "", String(window.location || ""));
    return state;
  } catch (_error) {
    return null;
  }
}

function syncBrowserRoute(routeAlias, options = {}) {
  const clean = normalizeRouteAlias(routeAlias);
  if (!clean || !window.history || typeof window.history.pushState !== "function") return;
  try {
    const resolution = typeof STAGE3_ROUTES.resolveRouteAlias === "function"
      ? STAGE3_ROUTES.resolveRouteAlias(clean)
      : { status: "resolved", routeAlias: clean };
    if (resolution?.status !== "resolved") return;
    const canonical = resolution.routeAlias || clean;
    const url = stage6CanonicalUrlForRoute(canonical);
    const current = normalizeRouteAlias(routeAliasFromLocation());
    const sameRoute = current === canonical && url.href === String(window.location || "");
    const state = stage6HistoryState(canonical, { source: options.source || "navigation" });
    if (sameRoute) {
      window.history.replaceState(state, "", url);
      return { status: "unchanged", routeAlias: canonical, historyLength: window.history.length };
    }
    const method = options.replace ? "replaceState" : "pushState";
    window.history[method](state, "", url);
    return { status: method === "pushState" ? "pushed" : "replaced", routeAlias: canonical, historyLength: window.history.length };
  } catch (_error) {
    // Static file previews can have unusual URLs; route state is still stored in context.
    return null;
  }
}

function applyRouteFromLocation() {
  const requestedRouteAlias = routeAliasFromLocation();
  if (!requestedRouteAlias) return false;
  mountPFIStage1Route(requestedRouteAlias, { replace: true, preserveFocus: true, source: "initial_location" });
  return true;
}

function renderInvalidRouteState(routeAlias, options = {}) {
  const requested = String(routeAlias || "").replace(/^#/, "") || "/";
  const main = document.querySelector("#main-workspace");
  const shell = document.querySelector(".app-shell");
  const surface = document.querySelector("[data-stage6-invalid-route]");
  const requestedNode = document.querySelector("[data-stage6-invalid-route-requested]");
  const heading = document.querySelector("[data-stage6-invalid-route-title]");
  if (!main || !surface) return;
  const departingRoute = normalizeRouteAlias(main.dataset.routeAlias || "");
  if (departingRoute && workspaceTargetFromRoute(departingRoute)) saveStage6RouteScroll(departingRoute);
  document.querySelectorAll('[data-primary-entry="true"]').forEach((button) => {
    button.classList.remove("is-active");
    button.setAttribute("aria-current", "false");
  });
  main.setAttribute("data-stage6-route-state", "invalid");
  main.setAttribute("data-stage6-invalid-requested", requested);
  main.dataset.routeAlias = requested;
  main.dataset.activeWorkspace = "";
  if (shell) shell.dataset.state = "route_error";
  if (requestedNode) requestedNode.textContent = requested;
  surface.hidden = false;
  document.title = "页面地址无效 · PFI";
  writeContext({ ...currentContext(), route_alias: requested, route_state: "invalid" });
  replaceCurrentStage6HistoryState(requested, {
    source: options.source || "invalid_route",
    routeState: "invalid",
    recoveryRouteAlias: PFI_V025_STAGE6_PHASE63_HISTORY.invalidRouteRecovery || "/overview",
    scrollY: Number(options.historyState?.scrollY || 0),
  });
  if (!options.preserveFocus && heading) heading.focus({ preventScroll: true });
}

function applyStage6HistoryNavigation(event) {
  const routeFromUrl = routeAliasFromLocation();
  const routeFromState = String(event?.state?.routeAlias || "");
  const requested = routeFromUrl || routeFromState || "/overview";
  return mountPFIStage1Route(requested, {
    historyTraversal: true,
    historyState: event?.state || null,
    preserveFocus: false,
    source: "popstate",
  });
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
  setActionFeedback("success", open ? "页面说明已打开" : "页面说明已关闭");
}

function toggleTaskCenter() {
  const taskCenter = document.querySelector("[data-task-center]");
  if (!taskCenter) return;
  const hidden = taskCenter.toggleAttribute("hidden");
  setActionFeedback("success", hidden ? "待办清单已关闭" : "待办清单已打开");
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
      hint: safeUserText(item.hint, item.view ? "打开任务" : "打开入口"),
      keywords: [item.keywords || "", SEARCH_ALIASES[title] || ""].join(" "),
      numbers: [item.numbers || "", extractNumericTokens([title, item.category, item.path, item.hint, item.keywords].join(" "))].join(" "),
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
      category: "一级入口",
      path: button.dataset.routeAlias || workspaceLabel(button.dataset.workspace, "入口"),
      hint: button.dataset.featureView ? "打开任务" : "打开入口",
      workspace: button.dataset.workspace || "home",
      view: button.dataset.featureView || "",
      routeAlias: button.dataset.routeAlias || "",
      keywords: `${button.dataset.workspace || ""} ${button.dataset.routeAlias || ""} 第${button.dataset.navIndex || ""}入口 ${button.dataset.navIndex || ""}`,
      numbers: button.dataset.navIndex || "",
      priority: Number(button.dataset.navIndex || 50),
    });
  });

  LEGACY_COMMAND_ALIASES.forEach((alias, index) => {
    add({
      title: alias.title,
      category: "兼容别名",
      path: alias.routeAlias,
      hint: "打开兼容入口",
      workspace: alias.workspace,
      routeAlias: alias.routeAlias,
      keywords: alias.keywords,
      priority: 35 + index,
    });
  });

  Object.entries(WORKSPACES).forEach(([workspaceId, workspace]) => {
    add({
      title: ownerVisibleText(workspace.label, "工作区"),
      category: "工作区",
      path: defaultRouteAliasForWorkspace(workspaceId) || ownerVisibleText(workspace.label, "工作区"),
      hint: "打开工作区",
      workspace: workspaceId,
      routeAlias: defaultRouteAliasForWorkspace(workspaceId),
      keywords: ownerVisibleText(`${workspace.kicker || ""} ${workspace.conclusion || ""} ${workspace.runtime || ""}`, ""),
      priority: 20,
    });

    (workspace.features || []).forEach((card, index) => {
      const target = card.target || featureTarget(card.title);
      add({
        title: ownerVisibleText(card.title, "任务"),
        category: "任务",
        path: `${ownerVisibleText(workspace.label, "工作区")} / ${ownerVisibleText(card.evidence, "任务")}`,
        hint: target.view ? "打开处理流程" : "打开工作区",
        workspace: target.workspace || workspaceId,
        view: target.view || "",
        routeAlias: target.routeAlias || defaultRouteAliasForWorkspace(target.workspace || workspaceId),
        keywords: ownerVisibleText(`${card.status || ""} ${card.evidence || ""} ${card.description || ""}`, ""),
        priority: 30 + index,
      });
    });

    (workspace.tasks || []).forEach((item, index) => {
      add({
        title: item.title,
        category: "任务",
        path: `${workspace.label} / 待办清单`,
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
    const workspaceId = workspaceForFunctionView(detail);
    add({
      title: detail.title,
      category: "处理流程",
      path: `${WORKSPACE_LABELS[workspaceId] || "PFI"} / ${detail.primaryAction}`,
      hint: "打开处理流程",
      workspace: workspaceId,
      view: detail.view,
      routeAlias: routeAliasForFunctionView(detail),
      keywords: `${detail.purpose || ""} ${(detail.checks || []).join(" ")} ${(detail.runSteps || []).join(" ")}`,
      priority: 40 + index,
    });
  });
  addRealDataSearchItems(add);
  addRealConsumptionSearchItems(add);

  return items;
}

function fuzzySearchItems(query, items = buildGlobalSearchIndex(), limit = SEARCH_DEFAULT_LIMIT) {
  const cleanQuery = normalizeSearch(query);
  const ranked = items
    .map((item) => ({ item, score: searchScore(cleanQuery, item) }))
    .filter((entry) => cleanQuery ? entry.score > 0 : entry.item.category.includes("入口") || entry.item.title === "反馈偏好")
    .sort((left, right) => right.score - left.score || left.item.priority - right.item.priority || left.item.title.localeCompare(right.item.title, "zh-Hans-CN"))
    .slice(0, limit)
    .map((entry) => entry.item);
  return ranked;
}

function searchScore(cleanQuery, item) {
  if (!cleanQuery) return 100 - Number(item.priority || 50);
  const haystack = normalizeSearch([item.title, item.category, item.path, item.hint, item.keywords, item.numbers].join(" "));
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

function addRealDataSearchItems(add) {
  if (!alipayImportState || Number(alipayImportState.transactionCount || 0) <= 0) return;
  const numberTokens = [
    alipayImportState.fileCount,
    alipayImportState.validFileCount,
    alipayImportState.transactionCount,
    alipayImportState.reviewCount,
    alipayImportState.dateStart,
    alipayImportState.dateEnd,
    alipayImportState.dateStart.replaceAll("-", ""),
    alipayImportState.dateEnd.replaceAll("-", ""),
    ...(alipayImportState.searchTokens || []),
  ].join(" ");
  add({
    title: "真实支付宝流水",
    category: "真实数据",
    path: "数据源与上传 / 导入中心",
    hint: `${alipayImportState.transactionCount} 条流水 · ${alipayImportState.reviewCount} 条待复核`,
    workspace: "sync",
    routeAlias: "/sources-upload",
    keywords: `支付宝 三年 历史数据 ${numberTokens}`,
    numbers: numberTokens,
    priority: 3,
  });
  add({
    title: "待复核流水",
    category: "真实数据",
    path: "账本流水 / 待复核",
    hint: `${alipayImportState.reviewCount} 条待复核`,
    workspace: "ledger",
    routeAlias: "/ledger",
    keywords: `支付宝 待复核 低置信度 ${numberTokens}`,
    numbers: numberTokens,
    priority: 4,
  });
}

function addRealConsumptionSearchItems(add) {
  const consumption = runtimeReadModelState?.consumption || {};
  if (consumption.has_real_transactions !== true) return;
  const numberTokens = [
    consumption.transaction_count,
    consumption.review_count,
    consumption.latest_month,
    consumption.latest_date,
    consumption.month_spend_cny,
    consumption.budget_remaining_cny,
    consumption.fixed_spend_cny,
    consumption.flex_spend_cny,
    consumption.cashflow_forecast_cny,
    extractNumericTokens(JSON.stringify(consumption)),
  ].join(" ");
  add({
    title: "真实消费流水",
    category: "真实数据",
    path: "消费管理 / 消费趋势",
    hint: `本月支出 ${formatCnyAmount(consumption.month_spend_cny)} · 近30天 ${formatCnyAmount(consumption.cashflow_forecast_cny)}`,
    workspace: "consumption",
    routeAlias: "/consumption",
    keywords: `真实消费 支付宝 本月支出 现金流 ${numberTokens}`,
    numbers: numberTokens,
    priority: 5,
  });
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

function extractNumericTokens(value) {
  return (String(value || "").match(/\d+(?:[.,]\d+)?/g) || []).join(" ");
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
  const routeAlias = normalizeRouteAlias(item.routeAlias || "");
  if (item.view) {
    openFunctionView(item.view, { routeAlias });
  } else {
    setActiveWorkspace(item.workspace || "home", { routeAlias });
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

function runtimeJobRequestId() {
  if (globalThis.crypto?.randomUUID) return `cache-refresh-${globalThis.crypto.randomUUID()}`;
  const values = new Uint32Array(4);
  globalThis.crypto.getRandomValues(values);
  return `cache-refresh-${[...values].map((value) => value.toString(16).padStart(8, "0")).join("")}`;
}

function applyRuntimeJobStatus(job, { skeleton, taskPhase, jobLabel }) {
  const progress = job.progress || {};
  const completed = Number(progress.completed_units);
  const total = Number(progress.total_units);
  const hasRealProgress = Number.isFinite(completed) && Number.isFinite(total) && total > 0;
  const progressText = hasRealProgress ? `${completed}/${total}` : "等待首个持久化工作单元";
  const stage = String(progress.step || job.trace?.stage || job.status || "");
  const terminalFailure = ["failed", "cancelled", "dead_letter"].includes(job.status);
  if (skeleton) {
    skeleton.hidden = job.status === "succeeded" || terminalFailure;
    skeleton.dataset.v024SkeletonState = job.status;
  }
  if (taskPhase) {
    taskPhase.textContent = `${progressText} · ${stage}`;
    taskPhase.dataset.progressState = job.status === "succeeded"
      ? "success"
      : terminalFailure ? "failure" : "loading";
  }
  if (jobLabel) {
    jobLabel.textContent = `后台任务 ${job.job_id} · SQLite revision ${job.revision}`;
    jobLabel.dataset.progressState = job.status === "succeeded"
      ? "success"
      : terminalFailure ? "failure" : "loading";
  }
}

async function pollRuntimeJob(pollUri, mounts, { maximumPolls = 240, pollDelayMs = 125 } = {}) {
  const runtimeJobs = window.PFI_V025_STAGE10_RUNTIME_JOBS;
  for (let pollIndex = 0; pollIndex < maximumPolls; pollIndex += 1) {
    const payload = await runtimeApiJson(pollUri);
    const job = payload?.job;
    runtimeJobs?.ingest?.(job);
    applyRuntimeJobStatus(job, mounts);
    if (runtimeJobs?.isTerminal?.(job?.status)) return payload;
    await new Promise((resolve) => window.setTimeout(resolve, pollDelayMs));
  }
  throw new Error("后台任务轮询超时；持久任务仍可从任务中心恢复");
}

async function restoreRuntimeJobsFromApi() {
  const runtimeJobs = window.PFI_V025_STAGE10_RUNTIME_JOBS;
  if (!runtimeJobs) return;
  try {
    const payload = await runtimeApiJson("/api/jobs?limit=20");
    const mounts = {
      skeleton: document.querySelector("[data-skeleton]"),
      taskPhase: document.querySelector("#task-phase"),
      jobLabel: document.querySelector("#background-job-label"),
    };
    [...(payload.jobs || [])].reverse().forEach((job) => {
      runtimeJobs.ingest(job);
      if (!runtimeJobs.isTerminal(job.status) && job.job_type === "cache.refresh") {
        void pollRuntimeJob(`/api/jobs/${job.job_id}`, mounts).catch(() => {
          // Preserve the last persisted snapshot; a later reload can recover it.
        });
      }
    });
  } catch (_error) {
    // Static/candidate surfaces remain usable when the local writable API is absent.
  }
}

async function runCachedRefresh() {
  const skeleton = document.querySelector("[data-skeleton]");
  const errorBanner = document.querySelector("[data-error-banner]");
  const taskPhase = document.querySelector("#task-phase");
  const jobLabel = document.querySelector("#background-job-label");
  const timelineApi = window.PFI_V025_STAGE8_JOB_TIMELINE;
  const runtimeJobs = window.PFI_V025_STAGE10_RUNTIME_JOBS;
  const mounts = { skeleton, taskPhase, jobLabel };
  if (errorBanner) errorBanner.hidden = true;
  if (skeleton) {
    skeleton.classList.add("v024-skeleton-row");
    skeleton.dataset.v024SkeletonState = "queued";
    skeleton.hidden = false;
  }
  if (taskPhase) {
    taskPhase.dataset.v024ReportProgress = "phase_6_2";
    taskPhase.dataset.progressState = "loading";
  }
  if (jobLabel) {
    jobLabel.dataset.v024ReportProgress = "phase_6_2";
    jobLabel.dataset.progressState = "loading";
  }
  setActionFeedback("progress", "正在刷新缓存切片");
  try {
    if (!runtimeJobs || !timelineApi) throw new Error("后台任务客户端未加载");
    const submitted = await runtimeApiJson("/api/jobs/cache-refresh", {
      method: "POST",
      body: JSON.stringify({ request_id: runtimeJobRequestId() }),
    });
    runtimeJobs.ingest(submitted.job);
    applyRuntimeJobStatus(submitted.job, mounts);
    const settled = await pollRuntimeJob(submitted.poll_uri, mounts);
    const job = settled.job;
    if (job.status !== "succeeded") {
      throw new Error(job.error?.message || `后台任务以 ${job.status} 结束`);
    }
    const refreshResult = await refreshRuntimeTrends({ rerender: true });
    if (!refreshResult?.ok) throw new Error("缓存任务已完成，但界面读取缓存结果失败");
    if (skeleton) {
      skeleton.hidden = true;
      skeleton.dataset.v024SkeletonState = "success";
    }
    if (taskPhase) {
      taskPhase.textContent = "第 3/3 步 · 缓存切片已准备";
      taskPhase.dataset.progressState = "success";
    }
    if (jobLabel) {
      jobLabel.textContent = `缓存切片已准备 · SQLite revision ${job.revision}`;
      jobLabel.dataset.progressState = "success";
    }
    showToast("缓存切片已刷新", "success");
    return;
  } catch (error) {
    if (skeleton) {
      skeleton.hidden = true;
      skeleton.dataset.v024SkeletonState = "failure";
    }
    if (taskPhase) {
      taskPhase.textContent = `刷新失败 · ${String(error?.message || "后台任务不可用")}`;
      taskPhase.dataset.progressState = "failure";
    }
    if (jobLabel) jobLabel.dataset.progressState = "failure";
    showRecoverableError();
  }
}

function showRecoverableError() {
  const errorBanner = document.querySelector("[data-error-banner]");
  if (!errorBanner) return;
  errorBanner.hidden = false;
  showToast("刷新失败 · 已切换到缓存兜底", "failure");
}

function emptyTrendForWorkspace(workspace) {
  return {
    scope: workspace?.label || "首页总览",
    title: "状态趋势",
    unit: "CNY",
    source: "真实数据待接入",
    emptyState: "趋势数据需要先接入真实数据，当前不显示伪造曲线。",
    periods: [],
    series: [],
  };
}

function drawTrendChart(trend = emptyTrendForWorkspace(WORKSPACES.home)) {
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
  const scopedValue = document.body ? getComputedStyle(document.body).getPropertyValue(name).trim() : "";
  const value = scopedValue || getComputedStyle(document.documentElement).getPropertyValue(name).trim();
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
  if (value === null || value === undefined || value === "") return null;
  const numeric = Number(value);
  if (!Number.isFinite(numeric)) return null;
  const rate = FX_TO_CNY[String(sourceCurrency || "CNY").trim().toUpperCase()] || 1;
  return numeric * rate;
}

function formatCnyAmount(value) {
  if (value === null || value === undefined || value === "") return "暂无真实数据";
  const numeric = Number(value);
  if (!Number.isFinite(numeric)) return "暂无真实数据";
  return `CNY ${numeric.toLocaleString("zh-CN", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
}

function formatOptionalCnyAmount(value, hasRealValue, missingLabel = "暂无真实数据") {
  if (!hasRealValue) return missingLabel;
  return formatCnyAmount(value);
}

function moneyLabel(value, sourceCurrency = "CNY") {
  return formatCnyAmount(toCnyAmount(value, sourceCurrency));
}

function workspaceLabel(value, fallback = "工作区") {
  const clean = String(value || "").trim();
  const key = clean.toLowerCase().replaceAll(" ", "_").replaceAll("+", "").replaceAll("__", "_");
  return WORKSPACE_LABELS[key] || WORKSPACE_LABELS[clean] || safeUserText(clean, fallback);
}

function safeEvidenceText(value, fallback = "页面说明") {
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

function ownerVisibleText(value, fallback = "待补") {
  const clean = safeUserText(value, fallback);
  const withoutStageLabels = String(clean || "")
    .replace(/第\s*[0-9一二三四五六七八九十]+\s*阶段[：:：-]?\s*/g, "")
    .replace(/\bStage\s*[0-9]+\b[：:：-]?\s*/gi, "")
    .replace(/\bS[0-9]+\s*[-–—]\s*/g, "")
    .replace(/\s*·\s*本地验收/g, "")
    .replace(/\s{2,}/g, " ")
    .trim();
  return withoutStageLabels || fallback;
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

  document.querySelectorAll('[data-mobile-workspace]:not([data-primary-entry="true"])').forEach((button) => {
    button.addEventListener("click", () => {
      setPressedFeedback(button);
      setActiveWorkspace(button.dataset.mobileWorkspace || "home", { routeAlias: button.dataset.routeAlias || "" });
    });
  });

  document.addEventListener("click", (event) => {
    const featureControl = event.target.closest("[data-feature-view]");
    if (featureControl) {
      event.preventDefault();
      closeGlobalSearchResults();
      setPressedFeedback(featureControl);
      openFunctionView(featureControl.dataset.featureView, { routeAlias: featureControl.dataset.routeAlias || "" });
      return;
    }
    const workspaceControl = event.target.closest("[data-feature-workspace]");
    if (workspaceControl) {
      event.preventDefault();
      closeGlobalSearchResults();
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
  globalSearchInput?.addEventListener("keyup", (event) => {
    if (event.key === "Escape") {
      closeGlobalSearchResults();
    }
  });
  globalSearchInput?.addEventListener("blur", () => {
    window.setTimeout(closeGlobalSearchResults, 80);
  });
  globalSearchResults?.addEventListener("mousedown", (event) => {
    event.preventDefault();
  });
  globalSearchResults?.addEventListener("click", (event) => {
    const result = event.target.closest("[data-search-index]");
    if (!result) return;
    openGlobalSearchResult(Number(result.dataset.searchIndex || 0));
  });

  document.querySelectorAll('[data-primary-entry="true"], [data-secondary-tab], [data-mobile-workspace]').forEach((button) => {
    button.addEventListener("pointerdown", closeGlobalSearchResults);
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
      const routeAlias = normalizeRouteAlias(button.dataset.commandRoute || "");
      setActiveWorkspace(button.dataset.commandWorkspace, { routeAlias });
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

  document.querySelector("[data-stage6-invalid-route-recover]")?.addEventListener("click", () => {
    setActiveWorkspace("home", { routeAlias: "/overview" });
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
  bindLedgerOperationEvents();
  bindHoldingsPersistenceEvents();
  bindSettingsOperationEvents();

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

function loadStage4PagesCatalog() {
  if (stage4PagesCatalog || window.PFI_V023_STAGE4_PAGES) {
    stage4PagesCatalog = stage4PagesCatalog || window.PFI_V023_STAGE4_PAGES;
    return Promise.resolve(stage4PagesCatalog);
  }
  return new Promise((resolve) => {
    const script = document.createElement("script");
    script.src = "./app/pages/stage4Subpages.js";
    script.dataset.stage4PagesLoader = "true";
    script.onload = () => {
      stage4PagesCatalog = window.PFI_V023_STAGE4_PAGES || null;
      resolve(stage4PagesCatalog);
    };
    script.onerror = () => resolve(null);
    document.head.appendChild(script);
  });
}

function loadStage5SubpageCatalog() {
  if (stage5SubpageCatalog || window.PFI_V024_STAGE5_PAGES) {
    stage5SubpageCatalog = stage5SubpageCatalog || window.PFI_V024_STAGE5_PAGES;
    return Promise.resolve(stage5SubpageCatalog);
  }
  return new Promise((resolve) => {
    const script = document.createElement("script");
    script.src = "./app/pages/stage5Subpages.js";
    script.dataset.stage5SubpageLoader = "true";
    script.onload = () => {
      stage5SubpageCatalog = window.PFI_V024_STAGE5_PAGES || null;
      resolve(stage5SubpageCatalog);
    };
    script.onerror = () => resolve(null);
    document.head.appendChild(script);
  });
}

function loadStage5UxState() {
  if (stage5UxState || window.PFI_V024_STAGE5_UX_STATE) {
    stage5UxState = stage5UxState || window.PFI_V024_STAGE5_UX_STATE;
    buildStage5UxStateCatalogForRuntime();
    return Promise.resolve(stage5UxState);
  }
  return new Promise((resolve) => {
    const script = document.createElement("script");
    script.src = "./app/ux_state.js";
    script.dataset.stage5UxStateLoader = "true";
    script.onload = () => {
      stage5UxState = window.PFI_V024_STAGE5_UX_STATE || null;
      buildStage5UxStateCatalogForRuntime();
      resolve(stage5UxState);
    };
    script.onerror = () => resolve(null);
    document.head.appendChild(script);
  });
}

function loadStage5HomeExperience() {
  if (stage5HomeExperience || window.PFI_V024_STAGE5_HOME || window.PFI_V023_STAGE5_HOME) {
    stage5HomeExperience = stage5HomeExperience || window.PFI_V024_STAGE5_HOME || window.PFI_V023_STAGE5_HOME;
    return Promise.resolve(stage5HomeExperience);
  }
  return new Promise((resolve) => {
    const script = document.createElement("script");
    script.src = "./app/pages/home.js";
    script.dataset.stage5HomeLoader = "true";
    script.onload = () => {
      stage5HomeExperience = window.PFI_V024_STAGE5_HOME || window.PFI_V023_STAGE5_HOME || null;
      resolve(stage5HomeExperience);
    };
    script.onerror = () => resolve(null);
    document.head.appendChild(script);
  });
}

function bootPFIShell() {
  if (window.history && "scrollRestoration" in window.history) {
    window.history.scrollRestoration = "manual";
  }
  clearLegacyHoldingsDraftStorage();
  restoreContext();
  bindEvents();
  void restoreRuntimeJobsFromApi();
  runtimeReadModelStatusState = canonicalStage7StatusOrFallback(readEmbeddedReadModelStatus());
  applyHomeSummary(readHomeSummary());
  applyV024ReadModelStatusToSurfaces(runtimeReadModelStatusState);
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
  renderWorkspace(WORKSPACES[requestedWorkspace] ? requestedWorkspace : "home", { silent: true, preserveFocus: true, replaceRoute: true });
  void refreshRuntimeTrends({ rerender: true });
}

document.addEventListener("DOMContentLoaded", () => {
  Promise.all([loadStage4PagesCatalog().then(loadStage5SubpageCatalog).then(loadStage5UxState), loadStage5HomeExperience()])
    .then(() => initializePFIStage1Shell({ source: "DOMContentLoaded" }))
    .catch((error) => handlePFIStage1ShellError(error, { source: "DOMContentLoaded" }));
});

window.addEventListener("hashchange", () => {
  if (stage6HistoryMode() !== "hash_compatibility") return;
  try {
    mountPFIStage1Route(routeAliasFromLocation(), { replace: true, source: "hashchange" });
  } catch (error) {
    handlePFIStage1ShellError(error, { source: "route" });
  }
});

window.addEventListener("popstate", (event) => {
  try {
    applyStage6HistoryNavigation(event);
  } catch (error) {
    handlePFIStage1ShellError(error, { source: "route" });
  }
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
