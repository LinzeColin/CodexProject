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

  function buildStage8Phase82DashboardViewModel(dashboard = {}) {
    const rows = dashboard.data_source_matrix && Array.isArray(dashboard.data_source_matrix.rows) ? dashboard.data_source_matrix.rows.map(buildDashboardRow) : [];
    const summary = dashboard.summary || {};
    const routeActions = Array.isArray(dashboard.route_actions) ? dashboard.route_actions.map(buildRouteAction) : [];
    const parseEntries = dashboard.parse_preview && Array.isArray(dashboard.parse_preview.entries) ? dashboard.parse_preview.entries : [];
    const fieldMappings = Array.isArray(dashboard.field_mapping_entries) ? dashboard.field_mapping_entries : [];
    const sections = [
      buildSection("data-source-matrix", "数据源矩阵", rows.map((row) => row.matrix_label)),
      buildSection("import-status", "上传/导入状态", buildImportStatusLines(dashboard.upload_import_status || {})),
      buildSection("parse-preview", "解析预览", parseEntries.map((entry) => `${entry.label || entry.data_source_id}: ${entry.detail_zh || "需要人工复核"}`)),
      buildSection("field-mapping", "字段映射", fieldMappings.map(buildFieldMappingLine)),
      buildSection("route-actions", "跳转到报告/复核", routeActions.map((action) => `${action.label_zh}: ${action.route}`)),
    ];
    return Object.freeze({
      schema: "PFIV023Stage8DashboardPageViewModelV1",
      version: VERSION,
      stage: "Stage 8",
      phase_id: "V023-S8-P8.2",
      page: "upload",
      title: "数据源检查板",
      subtitle_zh: "检查真实数据挂链、上传/导入状态、解析预览、字段映射入口与复核跳转。",
      source_count: Number(summary.source_count || rows.length),
      ready_count: Number(summary.ready_count || rows.filter((row) => row.status === "ready" || row.status === "confirmed_zero").length),
      blocked_count: Number(summary.blocked_count || rows.filter((row) => !["ready", "confirmed_zero"].includes(row.status)).length),
      action_count: routeActions.length,
      auto_import_enabled: Boolean(summary.auto_import_enabled),
      read_model_hash: summary.read_model_hash || null,
      as_of: summary.as_of || null,
      rows,
      route_actions: routeActions,
      sections,
      stage_contract: dashboard.stage_contract || {},
      summary_zh: `数据源 ${Number(summary.source_count || rows.length)} 个：${Number(summary.ready_count || 0)} 个已挂链，${Number(summary.blocked_count || 0)} 个阻断。`,
    });
  }

  function buildStage8Phase83NoFallbackViewModel(policy = {}, cases = {}) {
    const stateCases = Array.isArray(cases.state_cases) ? cases.state_cases.map(buildNoFallbackCase) : [];
    const failureCases = stateCases.filter((item) => item.status === "path_error" || item.status === "parse_error");
    const outdatedCases = stateCases.filter((item) => item.status === "outdated");
    const zeroCases = stateCases.filter((item) => item.status === "confirmed_zero");
    const sections = [
      buildSection("no-fallback-policy", "禁止假数据回退", [
        `fallback financial data allowed: ${Boolean(policy.fallback_financial_data_allowed)}`,
        `auto import test data allowed: ${Boolean(policy.auto_import_test_data_allowed)}`,
        `missing data renders financial zero: ${Boolean(policy.missing_data_renders_financial_zero)}`,
      ]),
      buildSection("failure-state", "失败状态截图", failureCases.map((item) => `${item.status}: ${item.display_text_zh}`)),
      buildSection("outdated-state", "过期状态截图", outdatedCases.map((item) => `${item.status}: ${item.display_text_zh}`)),
      buildSection("zero-proof", "真为 0 状态证明", zeroCases.map((item) => `${item.status}: ${item.display_text_zh} · 证据链 ${item.required_evidence_fields.join(", ")}`)),
    ];
    return Object.freeze({
      schema: "PFIV023Stage8NoFallbackPageViewModelV1",
      version: VERSION,
      stage: "Stage 8",
      phase_id: "V023-S8-P8.3",
      page: "upload",
      title: "禁止假数据回退",
      fallback_financial_data_allowed: Boolean(policy.fallback_financial_data_allowed),
      auto_import_test_data_allowed: Boolean(policy.auto_import_test_data_allowed),
      missing_data_renders_financial_zero: Boolean(policy.missing_data_renders_financial_zero),
      state_case_count: stateCases.length,
      sections,
      state_cases: stateCases,
      summary_zh: "失败、过期、未挂链和缺失状态必须展示中文原因；零值只允许由完整证据链确认。",
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

  function buildDashboardRow(row = {}) {
    const blockedMetrics = Array.isArray(row.blocked_metric_ids) ? row.blocked_metric_ids : [];
    const matrixLabel = [
      row.label || row.data_source_id || "未命名数据源",
      row.status_label || `status: ${row.status || "review_required"}`,
      row.records_label || `records: ${recordsText(row.records)}`,
      row.date_range_label || `date range: ${dateRangeText(row.date_range)}`,
      row.last_updated_label || `last updated: ${row.last_updated || "未挂链"}`,
      row.blocked_metrics_label || `blocked metrics: ${blockedMetrics.length ? blockedMetrics.join("、") : "无"}`,
    ].join(" · ");
    return Object.freeze({
      data_source_id: row.data_source_id || "",
      label: row.label || "未命名数据源",
      status: row.status || "review_required",
      status_zh: row.status_zh || STATUS_COPY_ZH[row.status] || "需要人工复核",
      records_label: row.records_label || `records: ${recordsText(row.records)}`,
      date_range_label: row.date_range_label || `date range: ${dateRangeText(row.date_range)}`,
      last_updated_label: row.last_updated_label || `last updated: ${row.last_updated || "未挂链"}`,
      blocked_metrics_label: row.blocked_metrics_label || `blocked metrics: ${blockedMetrics.length ? blockedMetrics.join("、") : "无"}`,
      matrix_label: matrixLabel,
      reason_zh: row.reason_zh || "需要人工复核数据源状态。",
      route_targets: Array.isArray(row.route_targets) ? row.route_targets : [],
      evidence_hash: row.evidence_hash || row.read_model_hash || null,
    });
  }

  function buildImportStatusLines(status = {}) {
    const actions = Array.isArray(status.import_actions) ? status.import_actions : [];
    return [
      `status: ${status.status || "read_only_gate"}`,
      `auto import: ${Boolean(status.auto_import_enabled) ? "enabled" : "disabled"}`,
      status.status_zh || "当前仅展示真实数据挂链状态。",
      ...actions.map((action) => `${action.label_zh || action.action_id}: ${action.route || ""}`),
    ];
  }

  function buildFieldMappingLine(entry = {}) {
    const fields = Array.isArray(entry.source_fields) && entry.source_fields.length ? entry.source_fields.join(", ") : "未挂链";
    return `${entry.title_zh || "字段映射"} · ${entry.data_source_id || ""} · ${entry.mapping_status || "blocked"} · ${fields} · ${entry.route || "/reports"}`;
  }

  function buildRouteAction(action = {}) {
    return Object.freeze({
      action_id: action.action_id || "",
      label_zh: action.label_zh || "打开复核入口",
      type: action.type || "route",
      route: action.route || "/reports",
      reason_zh: action.reason_zh || "查看相关数据源状态。",
    });
  }

  function buildSection(sectionId, title, lines) {
    return Object.freeze({
      section_id: sectionId,
      title_zh: title,
      lines: Array.isArray(lines) ? lines.filter(Boolean) : [],
    });
  }

  function buildNoFallbackCase(item = {}) {
    return Object.freeze({
      case_id: item.case_id || "",
      status: item.status || "review_required",
      title_zh: item.title_zh || "状态证明",
      reason_zh: item.reason_zh || "需要人工复核。",
      failure_detail_zh: item.failure_detail_zh || "",
      display_text_zh: item.display_text_zh || item.reason_zh || "需要人工复核。",
      next_action_zh: item.next_action_zh || "进入复核入口。",
      can_display_financial_value: Boolean(item.can_display_financial_value),
      requires_evidence_chain: Boolean(item.requires_evidence_chain),
      required_evidence_fields: Array.isArray(item.required_evidence_fields) ? item.required_evidence_fields : [],
      current_confirmed_zero_metric_count: Number(item.current_confirmed_zero_metric_count || 0),
      current_personal_financial_zero_rendered: Boolean(item.current_personal_financial_zero_rendered),
    });
  }

  return Object.freeze({
    buildStage8Phase81DataSourceGateViewModel,
    buildStage8Phase82DashboardViewModel,
    buildStage8Phase83NoFallbackViewModel,
  });
});
