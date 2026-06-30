(function attachCoreMetricsContract(root, factory) {
  const api = factory();
  if (typeof module !== "undefined" && module.exports) {
    module.exports = api;
  }
  if (root) {
    root.PFI_STAGE6_CORE_METRICS = api;
  }
})(typeof window !== "undefined" ? window : globalThis, function buildCoreMetricsContract() {
  const metricIds = Object.freeze([
    "net_worth_cny",
    "cash_balance_cny",
    "investment_market_value_cny",
    "life_consumption_cny",
    "total_consumption_outflow_cny",
    "data_health",
  ]);

  const statuses = Object.freeze([
    "ready",
    "confirmed_zero",
    "not_loaded",
    "not_mounted",
    "path_error",
    "permission_error",
    "parse_error",
    "outdated",
    "filter_empty",
    "calculation_error",
    "review_required",
  ]);

  const requiredFields = Object.freeze([
    "metric_id",
    "label",
    "value",
    "currency",
    "status",
    "source",
    "as_of",
    "evidence_hash",
    "message_zh",
  ]);

  const displayStatuses = Object.freeze(["ready", "confirmed_zero"]);

  function canDisplayValue(metric) {
    return Boolean(
      metric &&
        displayStatuses.includes(metric.status) &&
        metric.value !== null &&
        metric.value !== undefined &&
        metric.source &&
        metric.as_of &&
        metric.evidence_hash,
    );
  }

  function normalizeMetric(metric) {
    const status = metric && statuses.includes(metric.status) ? metric.status : "review_required";
    return {
      metric_id: metric && metric.metric_id ? metric.metric_id : "",
      label: metric && metric.label ? metric.label : "",
      value: canDisplayValue(metric) ? metric.value : null,
      currency: metric && metric.currency ? metric.currency : null,
      status,
      source: canDisplayValue(metric) ? metric.source : null,
      as_of: canDisplayValue(metric) ? metric.as_of : null,
      evidence_hash: canDisplayValue(metric) ? metric.evidence_hash : null,
      message_zh: metric && metric.message_zh ? metric.message_zh : "需要人工复核",
    };
  }

  function normalizeReadModel(readModel) {
    const input = readModel && typeof readModel === "object" ? readModel : {};
    const metrics = Array.isArray(input.core_metrics) ? input.core_metrics.map(normalizeMetric) : [];
    return {
      schema: input.schema || "PFIV023Stage6CoreMetricsReadModelV1",
      stage: input.stage || "Stage 6",
      phase_id: input.phase_id || "V023-S6-P6.1",
      as_of: input.as_of || null,
      read_model_hash: input.read_model_hash || null,
      source: input.source || null,
      core_metrics: metrics,
      blocked_metric_ids: metrics
        .filter((metric) => !displayStatuses.includes(metric.status))
        .map((metric) => metric.metric_id),
    };
  }

  return Object.freeze({
    metricIds,
    statuses,
    requiredFields,
    displayStatuses,
    canDisplayValue,
    normalizeMetric,
    normalizeReadModel,
  });
});
