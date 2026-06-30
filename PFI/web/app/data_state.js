(function attachStage4DataState(root, factory) {
  const api = factory();
  if (typeof module !== "undefined" && module.exports) {
    module.exports = api;
  }
  if (root) {
    root.PFI_V024_STAGE4_DATA_STATE = api;
  }
})(typeof window !== "undefined" ? window : globalThis, function buildStage4DataState() {
  const statuses = Object.freeze([
    "ready",
    "confirmed_zero",
    "not_loaded",
    "source_missing",
    "path_error",
    "parse_failed",
    "outdated_snapshot",
    "permission_denied",
    "calculation_failed",
    "filtered_empty",
  ]);

  const requiredFields = Object.freeze([
    "metric_id",
    "value",
    "currency",
    "status",
    "source_id",
    "record_count",
    "as_of",
    "formula_id",
    "confidence",
    "blocking_reason_zh",
    "calculation_state",
  ]);

  const blockingReasonZh = Object.freeze({
    ready: "真实数据已加载",
    confirmed_zero: "真实数据确认数值为零",
    not_loaded: "未加载真实数据",
    source_missing: "真实数据源未挂链",
    path_error: "数据路径错误，请检查本机数据目录",
    parse_failed: "解析失败，请检查文件、行或字段",
    outdated_snapshot: "快照过期，请刷新或确认日期",
    permission_denied: "权限失败，请检查本机文件权限",
    calculation_failed: "计算失败，请查看公式和输入字段",
    filtered_empty: "当前筛选无结果，不代表全局为零",
  });

  const sharedSurfaces = Object.freeze(["home", "accounts", "investment", "consumption", "insights"]);

  function canDisplayFinancialValue(metric) {
    return Boolean(
      metric &&
        (metric.status === "ready" || metric.status === "confirmed_zero") &&
        metric.value !== null &&
        metric.value !== undefined,
    );
  }

  function renderMetricValueZh(metric) {
    if (!canDisplayFinancialValue(metric)) {
      const status = metric && metric.status ? metric.status : "not_loaded";
      const reason =
        (metric && metric.blocking_reason_zh) || blockingReasonZh[status] || "数据状态未知";
      if (status === "outdated_snapshot" && metric && metric.as_of) {
        return `${reason}（快照日期：${metric.as_of}）`;
      }
      return reason;
    }
    const currency = metric.currency || "CNY";
    return `${currency} ${Number(metric.value).toLocaleString("en-US", {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    })}`;
  }

  function normalizeReadModelStatus(payload) {
    const source = payload && typeof payload === "object" ? payload : {};
    const metrics = Array.isArray(source.core_metric_states) ? source.core_metric_states : [];
    return {
      schema: source.schema || "PFIV024Stage4ReadModelStatusV1",
      read_model_hash: source.read_model_hash || null,
      as_of: source.as_of || null,
      source: source.source || {},
      core_metric_states: metrics.map(normalizeMetricState),
    };
  }

  function buildSurfaceMetricViews(payload) {
    const normalized = normalizeReadModelStatus(payload);
    const surfaces = {};
    sharedSurfaces.forEach((surface) => {
      surfaces[surface] = {
        surface,
        read_model_hash: normalized.read_model_hash,
        as_of: normalized.as_of,
        metrics: normalized.core_metric_states.map((metric) => ({
          ...metric,
          display_value: renderMetricValueZh(metric),
          display_detail: metricDetailZh(metric),
        })),
      };
    });
    return Object.freeze({
      schema: "PFIV024Stage4SurfaceStateViewsV1",
      surfaces,
    });
  }

  function metricById(payload, metricId) {
    const normalized = normalizeReadModelStatus(payload);
    return normalized.core_metric_states.find((metric) => metric.metric_id === metricId) || null;
  }

  function normalizeMetricState(metric) {
    const source = metric && typeof metric === "object" ? metric : {};
    const status = statuses.includes(source.status) ? source.status : "not_loaded";
    return {
      metric_id: source.metric_id || "",
      value: source.value === undefined ? null : source.value,
      currency: source.currency === undefined ? "CNY" : source.currency,
      status,
      source_id: source.source_id || null,
      record_count: Number.isFinite(Number(source.record_count)) ? Number(source.record_count) : null,
      as_of: source.as_of || null,
      formula_id: source.formula_id || null,
      confidence: Number.isFinite(Number(source.confidence)) ? Number(source.confidence) : null,
      blocking_reason_zh: source.blocking_reason_zh || blockingReasonZh[status] || "数据状态未知",
      calculation_state: source.calculation_state || "blocked",
    };
  }

  function metricDetailZh(metric) {
    const parts = [];
    if (metric.source_id) parts.push(metric.source_id);
    if (Number.isFinite(Number(metric.record_count))) parts.push(`${Number(metric.record_count).toLocaleString("zh-CN")} 条记录`);
    if (metric.as_of) parts.push(`截至 ${metric.as_of}`);
    if (metric.formula_id) parts.push(metric.formula_id);
    return parts.join(" · ") || metric.calculation_state || "状态待确认";
  }

  return Object.freeze({
    statuses,
    requiredFields,
    blockingReasonZh,
    sharedSurfaces,
    buildSurfaceMetricViews,
    canDisplayFinancialValue,
    metricById,
    normalizeReadModelStatus,
    renderMetricValueZh,
  });
});
