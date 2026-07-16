(function attachStage4DataState(root, factory) {
  const api = factory();
  if (typeof module !== "undefined" && module.exports) {
    module.exports = api;
  }
  if (root) {
    root.PFI_V024_STAGE4_DATA_STATE = api;
    root.PFI_V025_STAGE4_DATA_STATE = api;
  }
})(typeof window !== "undefined" ? window : globalThis, function buildStage4DataState() {
  const strictMetricContract = "PFIV025MetricStateStrictV1";
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
  const v025Statuses = Object.freeze([
    "ready",
    "confirmed_zero",
    "partial_coverage",
    "not_loaded",
    "source_missing",
    "path_error",
    "parse_failed",
    "outdated_snapshot",
    "permission_denied",
    "calculation_failed",
    "reconciliation_failed",
    "valuation_missing",
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
  const v025RequiredFields = Object.freeze([
    "metric_id",
    "value",
    "currency",
    "status",
    "source_ids",
    "record_count",
    "coverage_start",
    "coverage_end",
    "data_as_of",
    "formula_id",
    "formula_version",
    "formula_hash",
    "parameter_hash",
    "data_hash",
    "read_model_hash",
    "dependency_hashes",
    "dependency_set_hash",
    "classification_confidence",
    "source_coverage",
    "reconciliation_coverage",
    "valuation_coverage",
    "model_validation",
    "report_completeness",
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
  const v025BlockingReasonZh = Object.freeze({
    ready: "真实数据已加载",
    confirmed_zero: "真实数据确认数值为零",
    partial_coverage: "数据覆盖不完整，暂不输出完整财务值",
    not_loaded: "未加载真实数据",
    source_missing: "真实数据源未挂链",
    path_error: "数据路径错误，请检查本机数据目录",
    parse_failed: "解析失败，请检查文件、行或字段",
    outdated_snapshot: "快照过期，请刷新或确认日期",
    permission_denied: "权限失败，请检查本机文件权限",
    calculation_failed: "计算失败，请查看公式和输入字段",
    reconciliation_failed: "对账失败，请复核余额、流水和调整项",
    valuation_missing: "缺少价格、汇率或估值时间快照",
    filtered_empty: "当前筛选无结果，不代表全局为零",
  });

  const sharedSurfaces = Object.freeze(["home", "accounts", "investment", "consumption", "insights"]);
  const v025SharedSurfaces = Object.freeze([
    "homepage",
    "accounts",
    "investment",
    "consumption",
    "report",
  ]);
  const legacySurfaceAliases = Object.freeze({
    home: "homepage",
    insights: "report",
  });
  const sha256Pattern = /^sha256:[0-9a-f]{64}$/;

  function isFiniteNumber(value) {
    return typeof value === "number" && Number.isFinite(value);
  }

  function isSha256(value) {
    return typeof value === "string" && sha256Pattern.test(value);
  }

  function strictEvidenceComplete(metric) {
    return Boolean(
      metric &&
        Array.isArray(metric.source_ids) &&
        metric.source_ids.length > 0 &&
        metric.source_ids.every((item) => typeof item === "string" && item.length > 0) &&
        Number.isInteger(metric.record_count) &&
        metric.record_count >= 0 &&
        typeof metric.coverage_start === "string" &&
        metric.coverage_start.length > 0 &&
        typeof metric.coverage_end === "string" &&
        metric.coverage_end.length > 0 &&
        typeof metric.data_as_of === "string" &&
        metric.data_as_of.length > 0 &&
        typeof metric.formula_id === "string" &&
        metric.formula_id.length > 0 &&
        typeof metric.formula_version === "string" &&
        metric.formula_version.length > 0 &&
        isSha256(metric.formula_hash) &&
        isSha256(metric.parameter_hash) &&
        isSha256(metric.data_hash) &&
        isSha256(metric.read_model_hash) &&
        metric.dependency_hashes &&
        typeof metric.dependency_hashes === "object" &&
        Object.keys(metric.dependency_hashes).length > 0 &&
        Object.values(metric.dependency_hashes).every(isSha256) &&
        isSha256(metric.dependency_set_hash) &&
        isFiniteNumber(metric.classification_confidence) &&
        metric.classification_confidence >= 0 &&
        metric.classification_confidence <= 100 &&
        isFiniteNumber(metric.source_coverage) &&
        metric.source_coverage >= 0 &&
        metric.source_coverage <= 1 &&
        isFiniteNumber(metric.reconciliation_coverage) &&
        metric.reconciliation_coverage >= 0 &&
        metric.reconciliation_coverage <= 1 &&
        isFiniteNumber(metric.valuation_coverage) &&
        metric.valuation_coverage >= 0 &&
        metric.valuation_coverage <= 1 &&
        metric.model_validation === "validated" &&
        metric.report_completeness === "complete",
    );
  }

  function legacyConfirmedZeroEvidence(metric) {
    return Boolean(
      metric &&
        metric.metric_contract_version !== strictMetricContract &&
        (metric.source_id || (Array.isArray(metric.source_ids) && metric.source_ids.length > 0)) &&
        Number.isInteger(metric.record_count) &&
        metric.record_count >= 0 &&
        (metric.as_of || metric.data_as_of) &&
        metric.formula_id &&
        (isFiniteNumber(metric.confidence) || isFiniteNumber(metric.classification_confidence)),
    );
  }

  function canDisplayFinancialValue(metric) {
    if (!metric || !isFiniteNumber(metric.value)) return false;
    if (metric.status === "ready") {
      if (metric.value === 0) return false;
      return metric.metric_contract_version === strictMetricContract
        ? strictEvidenceComplete(metric)
        : true;
    }
    if (metric.status !== "confirmed_zero" || metric.value !== 0) return false;
    return metric.metric_contract_version === strictMetricContract
      ? strictEvidenceComplete(metric)
      : legacyConfirmedZeroEvidence(metric);
  }

  function renderMetricValueZh(metric) {
    if (!canDisplayFinancialValue(metric)) {
      const status = metric && metric.status ? metric.status : "not_loaded";
      const reason =
        (metric && metric.blocking_reason_zh) || v025BlockingReasonZh[status] || "数据状态未知";
      const asOf = metric && (metric.data_as_of || metric.as_of);
      if (status === "outdated_snapshot" && asOf) {
        return `${reason}（快照日期：${asOf}）`;
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
    const rawMetrics = Array.isArray(source.core_metric_states)
      ? source.core_metric_states
      : Array.isArray(source.metrics)
        ? source.metrics
        : [];
    const metricFingerprints = Array.isArray(source.metric_fingerprints)
      ? source.metric_fingerprints.slice()
      : [];
    return {
      schema: source.schema || "PFIV025UnifiedReadModelV1",
      read_model_hash: source.read_model_hash || null,
      dependency_set_hash: source.dependency_set_hash || null,
      as_of: source.as_of || null,
      observed_at: source.observed_at || null,
      source: source.source || {},
      surface_ids: Array.isArray(source.surface_ids)
        ? source.surface_ids.slice()
        : source.schema === "PFIV025UnifiedReadModelV1"
          ? v025SharedSurfaces.slice()
          : sharedSurfaces.slice(),
      metric_fingerprints: metricFingerprints,
      core_metric_states: rawMetrics.map(normalizeMetricState),
    };
  }

  function buildSurfaceMetricViews(payload) {
    const normalized = normalizeReadModelStatus(payload);
    const surfaces = {};
    const primarySurfaces = normalized.schema === "PFIV025UnifiedReadModelV1"
      ? v025SharedSurfaces
      : sharedSurfaces;
    primarySurfaces.forEach((surface) => {
      surfaces[surface] = {
        surface,
        canonical_surface: surface,
        read_model_hash: normalized.read_model_hash,
        dependency_set_hash: normalized.dependency_set_hash,
        as_of: normalized.as_of,
        observed_at: normalized.observed_at,
        metric_fingerprints: normalized.metric_fingerprints.slice(),
        metrics: normalized.core_metric_states.map((metric) => ({
          ...metric,
          display_value: renderMetricValueZh(metric),
          display_detail: metricDetailZh(metric),
        })),
      };
    });
    if (normalized.schema === "PFIV025UnifiedReadModelV1") {
      Object.entries(legacySurfaceAliases).forEach(([alias, canonical]) => {
        surfaces[alias] = {
          ...surfaces[canonical],
          surface: alias,
          canonical_surface: canonical,
        };
      });
    }
    return Object.freeze({
      schema: "PFIV025Stage4SurfaceStateViewsV1",
      read_model_hash: normalized.read_model_hash,
      dependency_set_hash: normalized.dependency_set_hash,
      surfaces,
    });
  }

  function metricById(payload, metricId) {
    const normalized = normalizeReadModelStatus(payload);
    return normalized.core_metric_states.find((metric) => metric.metric_id === metricId) || null;
  }

  function normalizeMetricState(metric) {
    const source = metric && typeof metric === "object" ? metric : {};
    const status = v025Statuses.includes(source.status) ? source.status : "not_loaded";
    const sourceIds = Array.isArray(source.source_ids)
      ? source.source_ids.filter((item) => typeof item === "string" && item)
      : source.source_id
        ? [source.source_id]
        : [];
    return {
      ...source,
      metric_contract_version: source.metric_contract_version || null,
      metric_id: source.metric_id || "",
      value: source.value === undefined ? null : source.value,
      currency: source.currency === undefined ? "CNY" : source.currency,
      status,
      source_ids: sourceIds,
      source_id: source.source_id || sourceIds[0] || null,
      record_count: nullableNumber(source.record_count),
      coverage_start: source.coverage_start || null,
      coverage_end: source.coverage_end || null,
      data_as_of: source.data_as_of || source.as_of || null,
      as_of: source.as_of || source.data_as_of || null,
      formula_id: source.formula_id || null,
      formula_version: source.formula_version || null,
      formula_hash: source.formula_hash || null,
      parameter_hash: source.parameter_hash || null,
      data_hash: source.data_hash || null,
      read_model_hash: source.read_model_hash || null,
      dependency_hashes:
        source.dependency_hashes && typeof source.dependency_hashes === "object"
          ? {...source.dependency_hashes}
          : {},
      dependency_set_hash: source.dependency_set_hash || null,
      classification_confidence: nullableNumber(source.classification_confidence),
      confidence: nullableNumber(
        source.confidence === undefined ? source.classification_confidence : source.confidence,
      ),
      source_coverage: nullableNumber(source.source_coverage),
      reconciliation_coverage: nullableNumber(source.reconciliation_coverage),
      valuation_coverage: nullableNumber(source.valuation_coverage),
      model_validation: source.model_validation || null,
      report_completeness: source.report_completeness || null,
      blocking_reason_zh: source.blocking_reason_zh || v025BlockingReasonZh[status] || "数据状态未知",
      calculation_state: source.calculation_state || "blocked",
    };
  }

  function nullableNumber(value) {
    if (value === null || value === undefined || value === "") return null;
    const numeric = Number(value);
    return Number.isFinite(numeric) ? numeric : null;
  }

  function metricDetailZh(metric) {
    const parts = [];
    if (metric.source_ids.length > 0) parts.push(metric.source_ids.join(", "));
    if (
      metric.record_count !== null &&
      metric.record_count !== undefined &&
      Number.isFinite(Number(metric.record_count))
    ) {
      parts.push(`${Number(metric.record_count).toLocaleString("zh-CN")} 条记录`);
    }
    if (metric.data_as_of) parts.push(`截至 ${metric.data_as_of}`);
    if (metric.formula_id) parts.push(metric.formula_id);
    return parts.join(" · ") || metric.calculation_state || "状态待确认";
  }

  return Object.freeze({
    strictMetricContract,
    statuses,
    v025Statuses,
    requiredFields,
    v025RequiredFields,
    blockingReasonZh,
    v025BlockingReasonZh,
    sharedSurfaces,
    v025SharedSurfaces,
    legacySurfaceAliases,
    buildSurfaceMetricViews,
    canDisplayFinancialValue,
    metricById,
    normalizeMetricState,
    normalizeReadModelStatus,
    renderMetricValueZh,
    strictEvidenceComplete,
  });
});
