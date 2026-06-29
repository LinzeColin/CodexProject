(function attachDataStatusContract(root, factory) {
  const api = factory();
  if (typeof module !== "undefined" && module.exports) {
    module.exports = api;
  }
  if (root) {
    root.PFI_STAGE2_DATA_STATUS = api;
  }
})(typeof window !== "undefined" ? window : globalThis, function buildDataStatusContract() {
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

  const statusCopyZh = Object.freeze({
    ready: "真实数据已加载",
    confirmed_zero: "真实数据确认数值为零",
    not_loaded: "未加载真实数据",
    not_mounted: "真实数据源未挂链",
    path_error: "数据路径不可用",
    permission_error: "无权限读取，请检查本机文件权限",
    parse_error: "解析失败，请检查文件、行或字段",
    outdated: "使用旧快照，请查看快照日期",
    filter_empty: "当前筛选无结果",
    calculation_error: "指标计算失败",
    review_required: "需要人工复核",
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
      return metric && metric.message_zh ? metric.message_zh : "数据状态未知";
    }
    const currency = metric.currency || "CNY";
    return `${currency} ${Number(metric.value).toLocaleString("zh-CN", {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    })}`;
  }

  return Object.freeze({
    statuses,
    requiredFields,
    statusCopyZh,
    canDisplayFinancialValue,
    renderMetricValueZh,
  });
});
