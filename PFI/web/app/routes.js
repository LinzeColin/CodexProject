(function attachPFIStage3Routes(root, factory) {
  const api = factory();
  if (typeof module !== "undefined" && module.exports) {
    module.exports = api;
  }
  if (root) {
    root.PFI_V023_STAGE3_NAV = api;
    root.PFI_V024_STAGE3_ROUTES = api;
    root.PFI_V024_STAGE3_ROUTE_COMPAT = api.v024Phase32RouteContract;
  }
})(typeof window !== "undefined" ? window : globalThis, function buildPFIStage3Routes() {
  const officialPrimaryEntries = Object.freeze([
    Object.freeze({ index: 1, label: "首页总览", workspace: "home", routeAlias: "/home", icon: "⌂" }),
    Object.freeze({ index: 2, label: "账户与资产", workspace: "accounts", routeAlias: "/accounts", icon: "◫" }),
    Object.freeze({ index: 3, label: "账本流水", workspace: "ledger", routeAlias: "/ledger", icon: "≋" }),
    Object.freeze({ index: 4, label: "投资管理", workspace: "investment", routeAlias: "/investment", icon: "↗" }),
    Object.freeze({ index: 5, label: "消费管理", workspace: "consumption", routeAlias: "/consumption", icon: "◌" }),
    Object.freeze({ index: 6, label: "数据源与上传", workspace: "sync", routeAlias: "/sources-upload", icon: "⇄" }),
    Object.freeze({ index: 7, label: "建议与复盘", workspace: "recommendations", routeAlias: "/review", icon: "✦" }),
    Object.freeze({ index: 8, label: "报告与洞察", workspace: "insights", routeAlias: "/reports", icon: "▣" }),
    Object.freeze({ index: 9, label: "市场与研究", workspace: "market_research", routeAlias: "/market-research", icon: "⌁" }),
    Object.freeze({ index: 10, label: "设置", workspace: "settings", routeAlias: "/settings", icon: "⚙" }),
  ]);

  const legacyAliasEntries = Object.freeze([
    Object.freeze({ taskId: "T3.2.1", label: "首页", targetWorkspace: "home", routeAlias: "/home/today", resolvedRouteAlias: "/home" }),
    Object.freeze({ taskId: "T3.2.2", label: "市场", targetWorkspace: "market_research", routeAlias: "/market/watch", resolvedRouteAlias: "/market-research?tab=market" }),
    Object.freeze({ taskId: "T3.2.2", label: "研究", targetWorkspace: "market_research", routeAlias: "/market/research", resolvedRouteAlias: "/market-research?tab=research" }),
    Object.freeze({ taskId: "T3.2.3", label: "持仓", targetWorkspace: "investment", routeAlias: "/investment/holdings", resolvedRouteAlias: "/investment?tab=holdings" }),
    Object.freeze({ taskId: "T3.2.4", label: "策略实验室", targetWorkspace: "market_research", routeAlias: "/market/lab", resolvedRouteAlias: "/market-research/strategy-lab" }),
    Object.freeze({ taskId: "T3.2.4", label: "数据与系统", targetWorkspace: "settings", routeAlias: "/settings/data", resolvedRouteAlias: "/settings?tab=data-system" }),
  ]);

  const primaryRoutes = Object.freeze(officialPrimaryEntries.map((entry) => Object.freeze({
    taskId: "T3.2.1",
    routeType: "primary",
    index: entry.index,
    label: entry.label,
    workspace: entry.workspace,
    routeAlias: entry.routeAlias,
    primaryRouteAlias: entry.routeAlias,
  })));

  const secondaryRouteGroups = Object.freeze({
    home: Object.freeze([
      Object.freeze({ title: "财务状态", routeAlias: "/home?tab=status", tab: "status" }),
      Object.freeze({ title: "待办事项", routeAlias: "/home?tab=todo", tab: "todo" }),
      Object.freeze({ title: "快捷操作", routeAlias: "/home?tab=actions", tab: "actions" }),
      Object.freeze({ title: "最近报告", routeAlias: "/home?tab=reports", tab: "reports" }),
    ]),
    accounts: Object.freeze([
      Object.freeze({ title: "账户总览", routeAlias: "/accounts?tab=overview", tab: "overview" }),
      Object.freeze({ title: "账户列表", routeAlias: "/accounts?tab=list", tab: "list" }),
      Object.freeze({ title: "资产趋势", routeAlias: "/accounts?tab=trend", tab: "trend" }),
      Object.freeze({ title: "对账状态", routeAlias: "/accounts?tab=reconcile", tab: "reconcile" }),
    ]),
    ledger: Object.freeze([
      Object.freeze({ title: "流水列表", routeAlias: "/ledger?tab=list", tab: "list" }),
      Object.freeze({ title: "筛选搜索", routeAlias: "/ledger?tab=filter", tab: "filter" }),
      Object.freeze({ title: "分类复核", routeAlias: "/ledger?tab=review", tab: "review" }),
      Object.freeze({ title: "导出流水", routeAlias: "/ledger?tab=export", tab: "export" }),
    ]),
    investment: Object.freeze([
      Object.freeze({ title: "投资总览", routeAlias: "/investment?tab=overview", tab: "overview" }),
      Object.freeze({ title: "持仓", routeAlias: "/investment?tab=holdings", tab: "holdings" }),
      Object.freeze({ title: "交易记录", routeAlias: "/investment?tab=trades", tab: "trades" }),
      Object.freeze({ title: "收益分析", routeAlias: "/investment?tab=returns", tab: "returns" }),
    ]),
    consumption: Object.freeze([
      Object.freeze({ title: "消费总览", routeAlias: "/consumption?tab=overview", tab: "overview" }),
      Object.freeze({ title: "分类分析", routeAlias: "/consumption?tab=category", tab: "category" }),
      Object.freeze({ title: "预算", routeAlias: "/consumption?tab=budget", tab: "budget" }),
      Object.freeze({ title: "订阅", routeAlias: "/consumption?tab=subscription", tab: "subscription" }),
      Object.freeze({ title: "异常消费", routeAlias: "/consumption?tab=anomaly", tab: "anomaly" }),
    ]),
    sync: Object.freeze([
      Object.freeze({ title: "上传中心", routeAlias: "/sources-upload?tab=upload", tab: "upload" }),
      Object.freeze({ title: "导入中心", routeAlias: "/sources-upload?tab=import", tab: "import" }),
      Object.freeze({ title: "数据源管理", routeAlias: "/sources-upload?tab=sources", tab: "sources" }),
      Object.freeze({ title: "待复核", routeAlias: "/sources-upload?tab=review", tab: "review" }),
      Object.freeze({ title: "导入历史", routeAlias: "/sources-upload?tab=history", tab: "history" }),
    ]),
    recommendations: Object.freeze([
      Object.freeze({ title: "建议列表", routeAlias: "/review?tab=list", tab: "list" }),
      Object.freeze({ title: "建议详情", routeAlias: "/review?tab=detail", tab: "detail" }),
      Object.freeze({ title: "决策记录", routeAlias: "/review?tab=decision", tab: "decision" }),
      Object.freeze({ title: "复盘记录", routeAlias: "/review?tab=history", tab: "history" }),
    ]),
    insights: Object.freeze([
      Object.freeze({ title: "月报", routeAlias: "/reports?tab=monthly", tab: "monthly" }),
      Object.freeze({ title: "季报", routeAlias: "/reports?tab=quarterly", tab: "quarterly" }),
      Object.freeze({ title: "年报", routeAlias: "/reports?tab=yearly", tab: "yearly" }),
      Object.freeze({ title: "自定义报告", routeAlias: "/reports?tab=custom", tab: "custom" }),
      Object.freeze({ title: "导出", routeAlias: "/reports?tab=export", tab: "export" }),
    ]),
    market_research: Object.freeze([
      Object.freeze({ title: "市场观察", routeAlias: "/market-research?tab=market", tab: "market" }),
      Object.freeze({ title: "研究笔记", routeAlias: "/market-research?tab=research", tab: "research" }),
      Object.freeze({ title: "公司研究", routeAlias: "/market-research?tab=company", tab: "company" }),
      Object.freeze({ title: "基金研究", routeAlias: "/market-research?tab=fund", tab: "fund" }),
      Object.freeze({ title: "策略实验室", routeAlias: "/market-research/strategy-lab", tab: "strategy_lab" }),
    ]),
    settings: Object.freeze([
      Object.freeze({ title: "账户偏好", routeAlias: "/settings?tab=account", tab: "account" }),
      Object.freeze({ title: "数据与系统", routeAlias: "/settings?tab=data-system", tab: "data-system" }),
      Object.freeze({ title: "隐私与本地存储", routeAlias: "/settings?tab=privacy", tab: "privacy" }),
      Object.freeze({ title: "反馈偏好", routeAlias: "/settings?tab=feedback", tab: "feedback" }),
      Object.freeze({ title: "备份恢复", routeAlias: "/settings?tab=backup", tab: "backup" }),
    ]),
  });

  const primaryRouteAliasByWorkspace = Object.freeze(Object.fromEntries(
    primaryRoutes.map((entry) => [entry.workspace, entry.routeAlias])
  ));
  const secondaryRoutes = Object.freeze(Object.entries(secondaryRouteGroups).flatMap(([workspace, routes]) => (
    routes.map((entry) => Object.freeze({
      taskId: "T3.2.2",
      routeType: "secondary",
      title: entry.title,
      workspace,
      routeAlias: entry.routeAlias,
      primaryRouteAlias: primaryRouteAliasByWorkspace[workspace],
      tab: entry.tab,
    }))
  )));
  const legacyRouteAliasTargets = Object.freeze(Object.fromEntries(
    legacyAliasEntries.map((entry) => [entry.routeAlias, entry.resolvedRouteAlias])
  ));
  const legacyRedirectRoutes = Object.freeze(legacyAliasEntries.map((entry) => Object.freeze({
    taskId: "T3.2.3",
    routeType: "legacy_redirect",
    label: entry.label,
    inputRouteAlias: entry.routeAlias,
    routeAlias: entry.resolvedRouteAlias,
    workspace: entry.targetWorkspace,
    primaryRouteAlias: primaryRouteAliasByWorkspace[entry.targetWorkspace],
  })));

  const primaryRouteMap = Object.freeze(Object.fromEntries(primaryRoutes.map((entry) => [entry.routeAlias, entry])));
  const secondaryRouteMap = Object.freeze(Object.fromEntries(secondaryRoutes.map((entry) => [entry.routeAlias, entry])));
  const v024Phase31RouteContract = Object.freeze({
    version: "v0.2.4",
    sourcePackageVersion: "v0.2.3-repair",
    stage: "Stage 3",
    phaseId: "3.1",
    phaseName: "导航合同",
    sourceGlobal: "PFI_V024_STAGE3_NAVIGATION",
    officialPrimaryEntryCount: 10,
    marketResearchPrimaryIndex: 9,
    legacyAliasPolicy: "secondary_or_command_alias",
    legacyAliasLabels: Object.freeze(["首页", "市场", "研究", "持仓", "策略实验室", "数据与系统"]),
    legacyAliasPrimaryEntryAllowed: false,
    taskIds: Object.freeze(["T3.1.1", "T3.1.2", "T3.1.3", "T3.1.4"]),
  });
  const v024Phase32RouteContract = Object.freeze({
    version: "v0.2.4",
    sourcePackageVersion: "v0.2.3-repair",
    stage: "Stage 3",
    phaseId: "3.2",
    phaseName: "路由实现",
    routeContractVersion: "PFI-V024-STAGE3-PHASE32-ROUTES",
    taskIds: Object.freeze(["T3.2.1", "T3.2.2", "T3.2.3", "T3.2.4"]),
    primaryRoutes,
    secondaryRoutes,
    legacyRedirectRoutes,
    historyRuntimeContract: Object.freeze({
      taskId: "T3.2.4",
      hashRoutesDeclared: true,
      pushStateDeclared: true,
      replaceStateDeclared: true,
      hashchangeListenerDeclared: true,
      popstateListenerDeclared: true,
      routeAliasFromLocationDeclared: true,
      browserHistoryValidationDone: false,
    }),
    phase31Complete: true,
    phase32Complete: true,
    phase33Complete: false,
    stage3CandidateComplete: false,
    stage3Complete: false,
    githubMainUploadAllowed: false,
  });

  function sanitizeRouteAlias(routeAlias) {
    const clean = String(routeAlias || "").trim();
    if (!clean) return "";
    const withoutHash = clean.startsWith("#") ? clean.slice(1) : clean;
    return withoutHash || "";
  }

  function resolveLegacyRouteAlias(routeAlias) {
    const clean = sanitizeRouteAlias(routeAlias);
    return legacyRouteAliasTargets[clean] || clean;
  }

  function resolveRouteAlias(routeAlias) {
    const inputRouteAlias = sanitizeRouteAlias(routeAlias);
    if (!inputRouteAlias) return Object.freeze({ status: "unmatched", inputRouteAlias: "" });
    const routeAliasAfterRedirect = resolveLegacyRouteAlias(inputRouteAlias);
    const primary = primaryRouteMap[routeAliasAfterRedirect];
    const secondary = secondaryRouteMap[routeAliasAfterRedirect];
    const matched = primary || secondary;
    if (!matched) return Object.freeze({ status: "unmatched", inputRouteAlias });
    const redirected = routeAliasAfterRedirect !== inputRouteAlias;
    return Object.freeze({
      status: "resolved",
      routeType: redirected ? "legacy_redirect" : matched.routeType,
      inputRouteAlias,
      routeAlias: routeAliasAfterRedirect,
      redirectedFrom: redirected ? inputRouteAlias : "",
      workspace: matched.workspace,
      primaryRouteAlias: matched.primaryRouteAlias,
      tab: matched.tab || "",
    });
  }

  return Object.freeze({
    version: "v0.2.3",
    stage: "Stage 3",
    phaseId: "V023-S3-P3.2",
    officialPrimaryEntries,
    legacyAliasEntries,
    legacyRouteAliasTargets,
    primaryRoutes,
    secondaryRoutes,
    legacyRedirectRoutes,
    v024Phase31RouteContract,
    v024Phase32RouteContract,
    resolveLegacyRouteAlias,
    resolveRouteAlias,
  });
});
