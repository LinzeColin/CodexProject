(function attachPFIStage3Routes(root, factory) {
  const api = factory();
  if (typeof module !== "undefined" && module.exports) {
    module.exports = api;
  }
  if (root) {
    root.PFI_V023_STAGE3_NAV = api;
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
    Object.freeze({ label: "首页", targetWorkspace: "home", routeAlias: "/home" }),
    Object.freeze({ label: "市场", targetWorkspace: "market_research", routeAlias: "/market-research?tab=market" }),
    Object.freeze({ label: "研究", targetWorkspace: "market_research", routeAlias: "/market-research?tab=research" }),
    Object.freeze({ label: "持仓", targetWorkspace: "investment", routeAlias: "/investment?tab=holdings" }),
    Object.freeze({ label: "策略实验室", targetWorkspace: "market_research", routeAlias: "/market-research/strategy-lab" }),
    Object.freeze({ label: "数据与系统", targetWorkspace: "settings", routeAlias: "/settings?tab=data-system" }),
  ]);

  return Object.freeze({
    version: "v0.2.3",
    stage: "Stage 3",
    phaseId: "V023-S3-P3.1",
    officialPrimaryEntries,
    legacyAliasEntries,
  });
});
