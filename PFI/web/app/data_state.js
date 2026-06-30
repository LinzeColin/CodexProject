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

  return Object.freeze({
    statuses,
    requiredFields,
    blockingReasonZh,
    canDisplayFinancialValue,
    renderMetricValueZh,
  });
});
