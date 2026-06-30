(function attachPFIStage8Upload(root, factory) {
  const api = factory();
  if (typeof module !== "undefined" && module.exports) {
    module.exports = api;
  }
  if (root) {
    root.PFI_V023_STAGE8_UPLOAD = api;
  }
})(typeof window !== "undefined" ? window : globalThis, function buildPFIStage8Upload() {
  const VERSION = "v0.2.3";
  const STATUS_COPY_ZH = Object.freeze({
    ready: "真实数据已挂链",
    confirmed_zero: "真实数据确认数值为零",
    not_loaded: "未加载真实数据",
    not_mounted: "数据源未挂链",
    path_error: "数据路径不可用",
    permission_error: "无权限读取",
    parse_error: "解析失败",
    outdated: "快照过期",
    filter_empty: "当前筛选无结果",
    calculation_error: "计算失败",
    review_required: "需要人工复核",
  });

  function buildStage8Phase81DataSourceGateViewModel(dataSourceGate = {}) {
    const sources = Array.isArray(dataSourceGate.data_sources) ? dataSourceGate.data_sources.map(buildDataSourceCard) : [];
    const readyCount = sources.filter((source) => source.status === "ready" || source.status === "confirmed_zero").length;
    const blockedCount = sources.filter((source) => !["ready", "confirmed_zero"].includes(source.status)).length;
    return Object.freeze({
      schema: "PFIV023Stage8DataSourceGatePageViewModelV1",
      version: VERSION,
      stage: "Stage 8",
      phase_id: "V023-S8-P8.1",
      page: "upload",
      title: "数据源与上传",
      subtitle_zh: "数据源模型展示 status、records、date range、last updated 与 blocked metrics；Phase 8.2 才实现正式检查板 UI。",
      data_source_count: sources.length,
      ready_count: readyCount,
      blocked_count: blockedCount,
      read_model_hash: dataSourceGate.source_core_metrics ? dataSourceGate.source_core_metrics.read_model_hash : null,
      as_of: dataSourceGate.source_core_metrics ? dataSourceGate.source_core_metrics.as_of : null,
      sources,
      summary_zh: `数据源 ${sources.length} 个：${readyCount} 个已挂链，${blockedCount} 个阻断。`,
    });
  }

  function buildDataSourceCard(source = {}) {
    const blockedMetrics = Array.isArray(source.blocked_metric_ids) ? source.blocked_metric_ids : [];
    return Object.freeze({
      data_source_id: source.data_source_id || "",
      label: source.label || "未命名数据源",
      status: source.status || "review_required",
      status_zh: source.status_zh || STATUS_COPY_ZH[source.status] || "需要人工复核",
      status_label: `status: ${source.status || "review_required"}`,
      records_label: `records: ${recordsText(source.records)}`,
      date_range_label: `date range: ${dateRangeText(source.date_range)}`,
      last_updated_label: `last updated: ${source.last_updated || "未挂链"}`,
      blocked_metrics_label: blockedMetrics.length ? `blocked metrics: ${blockedMetrics.join("、")}` : "blocked metrics: 无",
      reason_zh: source.reason_zh || "需要人工复核数据源状态。",
      next_actions: Array.isArray(source.next_actions) ? source.next_actions : [],
      route_targets: Array.isArray(source.route_targets) ? source.route_targets : [],
      affected_report_ids: Array.isArray(source.affected_report_ids) ? source.affected_report_ids : [],
      auto_import_enabled: Boolean(source.auto_import_enabled),
      evidence_hash: source.evidence_hash || source.read_model_hash || null,
    });
  }

  function recordsText(records = {}) {
    if (!records || records.normalized_record_count === null || records.normalized_record_count === undefined) {
      return records && records.display_zh ? records.display_zh : "数据源未挂链";
    }
    const normalized = Number(records.normalized_record_count || 0).toLocaleString("en-US");
    const rawFiles = Number(records.raw_file_count || 0).toLocaleString("en-US");
    return records.display_zh || `${normalized} 条记录 / ${rawFiles} 个原始文件`;
  }

  function dateRangeText(range = {}) {
    if (!range || (!range.start && !range.end)) return "未挂链";
    return `${range.start || "未知"} 至 ${range.end || "未知"}`;
  }

  return Object.freeze({
    buildStage8Phase81DataSourceGateViewModel,
  });
});
