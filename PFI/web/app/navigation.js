(function attachPFIV024Stage3Navigation(root, factory) {
  const api = factory();
  if (typeof module !== "undefined" && module.exports) {
    module.exports = api;
  }
  if (root) {
    root.PFI_V024_STAGE3_NAVIGATION = api;
    root.PFI_V024_STAGE3_NAV = api;
  }
})(typeof window !== "undefined" ? window : globalThis, function buildPFIV024Stage3Navigation() {
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
    Object.freeze({
      taskId: "T3.1.2",
      label: "首页",
      targetWorkspace: "home",
      routeAlias: "/home/today",
      resolvedRouteAlias: "/home",
      aliasClass: "secondary_or_command_alias",
      primaryEntryAllowed: false,
    }),
    Object.freeze({
      taskId: "T3.1.2",
      label: "市场",
      targetWorkspace: "market_research",
      routeAlias: "/market/watch",
      resolvedRouteAlias: "/market-research?tab=market",
      aliasClass: "secondary_or_command_alias",
      primaryEntryAllowed: false,
    }),
    Object.freeze({
      taskId: "T3.1.2",
      label: "研究",
      targetWorkspace: "market_research",
      routeAlias: "/market/research",
      resolvedRouteAlias: "/market-research?tab=research",
      aliasClass: "secondary_or_command_alias",
      primaryEntryAllowed: false,
    }),
    Object.freeze({
      taskId: "T3.1.2",
      label: "持仓",
      targetWorkspace: "investment",
      routeAlias: "/investment/holdings",
      resolvedRouteAlias: "/investment?tab=holdings",
      aliasClass: "secondary_or_command_alias",
      primaryEntryAllowed: false,
    }),
    Object.freeze({
      taskId: "T3.1.2",
      label: "策略实验室",
      targetWorkspace: "market_research",
      routeAlias: "/market/lab",
      resolvedRouteAlias: "/market-research/strategy-lab",
      aliasClass: "secondary_or_command_alias",
      primaryEntryAllowed: false,
    }),
    Object.freeze({
      taskId: "T3.1.2",
      label: "数据与系统",
      targetWorkspace: "settings",
      routeAlias: "/settings/data",
      resolvedRouteAlias: "/settings?tab=data-system",
      aliasClass: "secondary_or_command_alias",
      primaryEntryAllowed: false,
    }),
  ]);

  const legacyRouteAliasTargets = Object.freeze(Object.fromEntries(
    legacyAliasEntries.map((entry) => [entry.routeAlias, entry.resolvedRouteAlias])
  ));
  const primaryRouteAliases = Object.freeze(Object.fromEntries(
    officialPrimaryEntries.map((entry) => [entry.routeAlias, entry.workspace])
  ));
  const activeStateRules = Object.freeze({
    navIndexSequence: Object.freeze(officialPrimaryEntries.map((entry) => entry.index)),
    singleActivePrimaryEntry: true,
    desktopAndMobileActiveStateShareWorkspace: true,
    legacyAliasPrimaryEntryAllowed: false,
    legacyAliasResolvesBeforeActiveWorkspace: true,
  });

  function resolveLegacyRouteAlias(routeAlias) {
    const clean = String(routeAlias || "").trim();
    return legacyRouteAliasTargets[clean] || clean;
  }

  function activeWorkspaceFromRoute(routeAlias) {
    const resolved = resolveLegacyRouteAlias(routeAlias).split("?")[0];
    return primaryRouteAliases[resolved] || null;
  }

  return Object.freeze({
    schema: "PFIV024Stage3NavigationContractV1",
    version: "v0.2.4",
    sourcePackageVersion: "v0.2.3-repair",
    repairLabel: "PFI v0.2.3 Repair",
    stage: "Stage 3",
    phaseId: "3.1",
    phaseName: "导航合同",
    taskIds: Object.freeze(["T3.1.1", "T3.1.2", "T3.1.3", "T3.1.4"]),
    navigationContractVersion: "PFI-V024-STAGE3-PHASE31-NAVIGATION",
    officialPrimaryEntries,
    legacyAliasEntries,
    legacyRouteAliasTargets,
    primaryRouteAliases,
    legacyAliasLabels: Object.freeze(legacyAliasEntries.map((entry) => entry.label)),
    activeStateRules,
    resolveLegacyRouteAlias,
    activeWorkspaceFromRoute,
    phase31Complete: true,
    phase32Complete: false,
    phase33Complete: false,
    stage3Complete: false,
    browserHistoryValidationDone: false,
    githubMainUploadAllowed: false,
  });
});
