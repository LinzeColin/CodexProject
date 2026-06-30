(function attachPFIStage6Investment(root, factory) {
  const api = factory(root);
  if (typeof module !== "undefined" && module.exports) {
    module.exports = api;
  }
  if (root) {
    root.PFI_V023_STAGE6_INVESTMENT = api;
  }
})(typeof window !== "undefined" ? window : globalThis, function buildPFIStage6Investment(root) {
  const VERSION = "v0.2.3";
  const PHASE_ID = "V023-S6-P6.2";
  const METRIC_IDS = Object.freeze(["investment_market_value_cny", "data_health"]);

  function buildStage6Phase62InvestmentViewModel(readModel = {}) {
    const cards = coreMetricsApi(root).buildMetricCards(readModel, METRIC_IDS);
    return Object.freeze({
      schema: "PFIV023Stage6PageMetricViewModelV1",
      version: VERSION,
      stage: "Stage 6",
      phase_id: PHASE_ID,
      page: "investment",
      title: "投资管理指标",
      cards,
      shell_cards: cards.map((card) => [card.label, card.display_value, card.detail]),
      summary_zh: "投资管理页面只展示投资市值和数据健康的真实状态。",
    });
  }

  return Object.freeze({ buildStage6Phase62InvestmentViewModel });
});

function coreMetricsApi(root) {
  if (root && root.PFI_STAGE6_CORE_METRICS) return root.PFI_STAGE6_CORE_METRICS;
  if (typeof globalThis !== "undefined" && globalThis.PFI_STAGE6_CORE_METRICS) return globalThis.PFI_STAGE6_CORE_METRICS;
  if (typeof require === "function") return require("../data/coreMetrics.js");
  throw new Error("PFI_STAGE6_CORE_METRICS is required");
}
