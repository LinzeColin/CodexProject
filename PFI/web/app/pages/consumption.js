(function attachPFIStage6Consumption(root, factory) {
  const api = factory(root);
  if (typeof module !== "undefined" && module.exports) {
    module.exports = api;
  }
  if (root) {
    root.PFI_V023_STAGE6_CONSUMPTION = api;
  }
})(typeof window !== "undefined" ? window : globalThis, function buildPFIStage6Consumption(root) {
  const VERSION = "v0.2.3";
  const PHASE_ID = "V023-S6-P6.2";
  const METRIC_IDS = Object.freeze(["life_consumption_cny", "total_consumption_outflow_cny", "data_health"]);

  function buildStage6Phase62ConsumptionViewModel(readModel = {}) {
    const cards = coreMetricsApi(root).buildMetricCards(readModel, METRIC_IDS);
    return Object.freeze({
      schema: "PFIV023Stage6PageMetricViewModelV1",
      version: VERSION,
      stage: "Stage 6",
      phase_id: PHASE_ID,
      page: "consumption",
      title: "消费管理指标",
      cards,
      shell_cards: cards.map((card) => [card.label, card.display_value, card.detail]),
      summary_zh: "消费管理页面展示生活消费、消费总流出和数据健康的真实状态。",
    });
  }

  return Object.freeze({ buildStage6Phase62ConsumptionViewModel });
});

function coreMetricsApi(root) {
  if (root && root.PFI_STAGE6_CORE_METRICS) return root.PFI_STAGE6_CORE_METRICS;
  if (typeof globalThis !== "undefined" && globalThis.PFI_STAGE6_CORE_METRICS) return globalThis.PFI_STAGE6_CORE_METRICS;
  if (typeof require === "function") return require("../data/coreMetrics.js");
  throw new Error("PFI_STAGE6_CORE_METRICS is required");
}
