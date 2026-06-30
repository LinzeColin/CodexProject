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
  const metricBasis = Object.freeze({
    net_worth_cny: Object.freeze({
      basis_zh: "来自真实账户余额与持仓 read model；未挂载时返回中文阻塞状态。",
    }),
    cash_balance_cny: Object.freeze({
      basis_zh: "来自真实账户余额 read model；当前未挂载账户余额时不得显示金额替代。",
    }),
    investment_market_value_cny: Object.freeze({
      basis_zh: "来自真实持仓市值 read model；当前未挂载持仓市值时不得显示金额替代。",
    }),
    life_consumption_cny: Object.freeze({
      basis_zh: "来自真实 Alipay 交易，口径为生活消费流出减退款。",
    }),
    total_consumption_outflow_cny: Object.freeze({
      basis_zh: "来自真实 Alipay 交易，口径为生活消费、基金申购、资产买入流出减退款。",
    }),
    data_health: Object.freeze({
      basis_zh: "来自真实导入清单的交易记录数、原始文件数和数据时间范围。",
    }),
  });

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

  function metricById(readModel) {
    const normalized = normalizeReadModel(readModel);
    return Object.freeze(
      Object.fromEntries(normalized.core_metrics.map((metric) => [metric.metric_id, Object.freeze(metric)])),
    );
  }

  function renderMetricValueZh(metric) {
    const normalized = normalizeMetric(metric);
    if (!canDisplayValue(normalized)) {
      return normalized.message_zh || "需要人工复核";
    }
    if (normalized.currency === "records") {
      return `${Number(normalized.value).toLocaleString("zh-CN")} records`;
    }
    const currency = normalized.currency || "CNY";
    return `${currency} ${Number(normalized.value).toLocaleString("zh-CN", {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    })}`;
  }

  function buildMetricCard(readModel, metricId, fallback = {}) {
    const byId = metricById(readModel);
    const metric = normalizeMetric(byId[metricId] || {
      metric_id: metricId,
      label: fallback.label || metricId,
      value: null,
      currency: fallback.currency || "CNY",
      status: "not_loaded",
      source: null,
      as_of: null,
      evidence_hash: null,
      message_zh: fallback.message_zh || "未加载真实数据",
    });
    return Object.freeze({
      ...metric,
      basis_zh: basisForMetric(metric.metric_id),
      display_value: renderMetricValueZh(metric),
      detail: metric.source
        ? `${metric.status} · ${metric.source} · as_of ${metric.as_of} · ${metric.evidence_hash}`
        : `${metric.status} · ${metric.message_zh}`,
    });
  }

  function buildMetricCards(readModel, metricIdsForPage) {
    return Object.freeze(metricIdsForPage.map((metricId) => buildMetricCard(readModel, metricId)));
  }

  function basisForMetric(metricId) {
    return metricBasis[metricId] ? metricBasis[metricId].basis_zh : "按核心 read model 状态展示。";
  }

  return Object.freeze({
    metricIds,
    statuses,
    requiredFields,
    displayStatuses,
    metricBasis,
    basisForMetric,
    canDisplayValue,
    buildMetricCard,
    buildMetricCards,
    metricById,
    normalizeMetric,
    normalizeReadModel,
    renderMetricValueZh,
  });
});
