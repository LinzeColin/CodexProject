(function attachPFIStage7Reports(root, factory) {
  const api = factory();
  if (typeof module !== "undefined" && module.exports) {
    module.exports = api;
  }
  if (root) {
    root.PFI_V023_STAGE7_REPORTS = api;
    root.PFI_V024_STAGE7_REPORTS = api;
  }
})(typeof window !== "undefined" ? window : globalThis, function buildPFIStage7Reports() {
  const VERSION = "v0.2.3";
  const V024_TARGET_VERSION = "v0.2.4";
  const V024_SOURCE_PACKAGE_VERSION = "v0.2.3-repair";
  const V024_PHASE72_CONTRACT_VERSION = "PFI-V024-STAGE7-PHASE72-PAGE-DISPLAY";
  const PHASE_ID = "V023-S7-P7.1";
  const STATUS_COPY_ZH = Object.freeze({
    ready: "可用",
    complete: "完整",
    partial: "部分可用",
    blocked: "已阻断",
    outdated: "快照过期",
    review_required: "需要复核",
  });

  function buildStage7Phase71ReportsViewModel(reportContract = {}, formulaRegistry = {}) {
    const reports = Array.isArray(reportContract.reports) ? reportContract.reports.map(buildReportCard) : [];
    const formulas = Array.isArray(formulaRegistry.formulas) ? formulaRegistry.formulas.map(buildFormulaCard) : [];
    const blockedOrPartialCount = reports.filter((report) => ["blocked", "partial"].includes(report.status)).length;
    return Object.freeze({
      schema: "PFIV023Stage7ReportsPageViewModelV1",
      version: VERSION,
      stage: "Stage 7",
      phase_id: PHASE_ID,
      page: "reports",
      title: "报告与洞察",
      subtitle_zh: "报告合同页展示公式、参数、样本量、数据范围和缺口，不生成 Phase 7.2 核心报告。",
      report_count: reports.length,
      blocked_or_partial_count: blockedOrPartialCount,
      read_model_hash: reportContract.read_model_hash || null,
      as_of: reportContract.as_of || null,
      sections: Object.freeze([
        Object.freeze({ id: "reports", title: "报告合同", cards: reports }),
        Object.freeze({ id: "formulas", title: "公式与参数", cards: formulas }),
      ]),
      reports,
      formulas,
      warnings_zh: blockedOrPartialCount
        ? "存在 blocked/partial 报告；数据缺口补齐前不得显示正式结论。"
        : "报告合同输入完整。",
    });
  }

  function buildV024Stage7Phase72Contract() {
    return Object.freeze({
      schema: "PFIV024Stage7Phase72ContractV1",
      target_version: V024_TARGET_VERSION,
      source_package_version: V024_SOURCE_PACKAGE_VERSION,
      repair_label: "PFI v0.2.3 Repair",
      stage: "Stage 7",
      stage_name: "分析结论与报告中心",
      phase_id: "7.2",
      phase_name: "页面展示",
      contract_version: V024_PHASE72_CONTRACT_VERSION,
      current_phase_only: true,
      max_one_phase_per_run: true,
      phase_7_1_complete_required: true,
      phase_7_2_page_display_complete: true,
      phase_7_3_started: false,
      stage_7_whole_review_complete: false,
      github_main_uploaded: false,
      app_bundle_reinstall_executed: false,
      data_logic_changes_allowed: false,
      formal_fake_financial_data_allowed: false,
      task_ids: Object.freeze(["T7.2.1", "T7.2.2", "T7.2.3", "T7.2.4"]),
      allowed_files: Object.freeze([
        "PFI/web/app/pages/reports.js",
        "PFI/web/app/shell.js",
        "PFI/web/index.html",
        "PFI/src/pfi_os/app/streamlit_app.py",
        "PFI/tests/test_v024_stage7_phase72_report_page_display.py",
        "PFI/docs/pfi_v024/STAGE7_REPORT_ANALYSIS.md",
        "PFI/docs/pfi_v024/RUN_CONTRACT.md",
        "PFI/reports/pfi_v024/stage_7/phase_7_2/*",
        "PFI/README.md",
        "PFI/HANDOFF.md",
        "PFI/CHANGELOG.md",
        "PFI/功能清单.md",
        "PFI/开发记录.md",
        "PFI/模型参数文件.md",
      ]),
      validation_commands: Object.freeze([
        "pytest PFI/tests/test_v024_stage7_phase72_report_page_display.py -q",
        "pytest PFI/tests/test_v024_stage7_phase71_report_schema.py -q",
        "node --check PFI/web/app/pages/reports.js",
        "node --check PFI/web/app/shell.js",
        "python3 -m json.tool PFI/reports/pfi_v024/stage_7/phase_7_2/evidence.json",
        "python3 -m json.tool PFI/reports/pfi_v024/stage_7/phase_7_2/report_center_view_model.json",
        "git diff --check -- PFI",
      ]),
      explicitly_not_done: Object.freeze([
        "Phase 7.3 验收",
        "Stage 7 whole-stage review",
        "GitHub main upload",
        "app bundle reinstall",
        "financial data mutation or synthesis",
      ]),
    });
  }

  function buildV024Stage7Phase72ReportCenterViewModel(reportPack = {}) {
    const reports = Array.isArray(reportPack.reports) ? reportPack.reports : [];
    const reportCards = reports.map(buildV024ReportCenterCard);
    const formulaCards = reportCards.map((card) => Object.freeze({
      report_id: card.report_id,
      title_zh: `${card.title_zh} · 公式解释区`,
      formula_zh: card.formula_zh,
      metric_sources: card.metric_sources,
      blocked_policy_zh: card.status === "blocked" ? "输入缺口补齐前只显示阻断状态和复核入口。" : "只展示真实来源支持的结论。",
      review_route: card.review_entry.route,
    }));
    const parameterSampleCards = reportCards.map((card) => Object.freeze({
      report_id: card.report_id,
      title_zh: `${card.title_zh} · 参数与样本量区`,
      parameters: card.parameters,
      parameter_summary_zh: card.parameter_summary_zh,
      sample_size: card.sample_size,
      sample_size_zh: card.sample_size_zh,
      data_range: card.data_range,
      data_range_zh: card.data_range_zh,
      confidence: card.confidence,
      confidence_zh: confidenceText(card.confidence),
    }));
    const gapReviewCards = reportCards.map((card) => Object.freeze({
      report_id: card.report_id,
      title_zh: `${card.title_zh} · 缺口/复核入口`,
      status: card.status,
      gaps: card.gaps,
      anomalies: card.anomalies,
      gap_summary_zh: card.gap_summary_zh,
      review_entry: card.review_entry,
      review_entry_zh: card.review_entry_zh,
    }));
    const blockedCount = reportCards.filter((card) => card.status === "blocked").length;
    const partialCount = reportCards.filter((card) => card.status === "partial").length;
    const source = normalizeV024Source(reportPack.source || {});
    return Object.freeze({
      schema: "PFIV024Stage7Phase72ReportCenterViewModelV1",
      target_version: V024_TARGET_VERSION,
      source_package_version: V024_SOURCE_PACKAGE_VERSION,
      stage: "Stage 7",
      phase_id: "7.2",
      phase_name: "页面展示",
      contract_version: V024_PHASE72_CONTRACT_VERSION,
      current_phase_only: true,
      phase_7_1_complete_required: true,
      phase_7_2_page_display_complete: true,
      phase_7_3_started: false,
      stage_7_whole_review_complete: false,
      github_main_uploaded: false,
      page: "reports",
      title_zh: "报告中心",
      subtitle_zh: "报告中心展示结论、公式、参数、数据范围、样本量、置信度、缺口和复核入口；数据不足时只展示数据质量与阻断状态。",
      source,
      read_model_hash: reportPack.read_model_hash || null,
      report_count: reportCards.length,
      blocked_count: blockedCount,
      partial_count: partialCount,
      visible_field_labels_zh: Object.freeze(["结论", "公式", "参数", "样本量", "数据范围", "置信度", "缺口", "复核入口"]),
      sections: Object.freeze([
        Object.freeze({ id: "report-cards", title_zh: "报告中心页面", cards: reportCards }),
        Object.freeze({ id: "formula-explanations", title_zh: "公式解释区", cards: formulaCards }),
        Object.freeze({ id: "parameters-and-samples", title_zh: "参数与样本量区", cards: parameterSampleCards }),
        Object.freeze({ id: "gaps-and-review", title_zh: "缺口/复核入口", cards: gapReviewCards }),
      ]),
      report_cards: Object.freeze(reportCards),
      formula_explanations: Object.freeze(formulaCards),
      parameters_and_samples: Object.freeze(parameterSampleCards),
      gaps_and_review: Object.freeze(gapReviewCards),
      summary_zh: `报告中心共 ${reportCards.length} 份报告，${blockedCount} 份阻断，${partialCount} 份部分可用。`,
      warnings_zh: blockedCount
        ? "存在阻断报告；数据缺口补齐前只显示阻断状态、缺口和复核入口。"
        : "当前报告中心未发现阻断报告。",
    });
  }

  function validateV024Stage7Phase72ReportCenterViewModel(view = {}) {
    const cards = Array.isArray(view.report_cards) ? view.report_cards : [];
    const ids = cards.map((card) => card.report_id);
    const requiredIds = ["net_worth_report", "cash_report", "investment_report", "consumption_report", "cashflow_report", "data_quality_report"];
    const missingReportIds = requiredIds.filter((id) => !ids.includes(id));
    const visibleText = JSON.stringify(view);
    const formulaVisible = visibleText.includes("公式") && cards.every((card) => Boolean(card.formula_zh));
    const parametersAndSampleVisible = visibleText.includes("参数") && visibleText.includes("样本量");
    const rangeVisible = visibleText.includes("数据范围");
    const confidenceVisible = visibleText.includes("置信度");
    const gapsAndReviewVisible = visibleText.includes("缺口") && visibleText.includes("复核入口");
    const blockedConclusionViolations = cards
      .filter((card) => card.status === "blocked")
      .filter((card) => JSON.stringify(card).includes("CNY 0.00") || String(card.conclusion_zh || "").includes("完整财务结论"))
      .map((card) => card.report_id);
    const pass = (
      missingReportIds.length === 0 &&
      formulaVisible &&
      parametersAndSampleVisible &&
      rangeVisible &&
      confidenceVisible &&
      gapsAndReviewVisible &&
      blockedConclusionViolations.length === 0
    );
    return Object.freeze({
      schema: "PFIV024Stage7Phase72PageDisplayValidationV1",
      target_version: V024_TARGET_VERSION,
      stage: "Stage 7",
      phase_id: "7.2",
      status: pass ? "pass" : "fail",
      visible_report_ids: Object.freeze(ids),
      missing_report_ids: Object.freeze(missingReportIds),
      formula_visible: formulaVisible,
      parameters_and_sample_visible: parametersAndSampleVisible,
      data_range_visible: rangeVisible,
      confidence_visible: confidenceVisible,
      gaps_and_review_visible: gapsAndReviewVisible,
      blocked_conclusion_violations: Object.freeze(blockedConclusionViolations),
    });
  }

  function buildStage7Phase72CoreReportsViewModel(coreReports = {}) {
    const reports = Array.isArray(coreReports.reports) ? coreReports.reports.map(buildReportCard) : [];
    const blockedCount = reports.filter((report) => report.status === "blocked").length;
    const partialCount = reports.filter((report) => report.status === "partial").length;
    return Object.freeze({
      schema: "PFIV023Stage7CoreReportsPageViewModelV1",
      version: VERSION,
      stage: "Stage 7",
      phase_id: "V023-S7-P7.2",
      page: "reports",
      title: "核心报告",
      subtitle_zh: "核心报告只使用 Stage 6 真实 read model；未挂载输入保持阻断，消费报告显示部分真实结论。",
      report_count: reports.length,
      blocked_count: blockedCount,
      partial_count: partialCount,
      read_model_hash: coreReports.source_core_metrics ? coreReports.source_core_metrics.read_model_hash : null,
      as_of: coreReports.source_core_metrics ? coreReports.source_core_metrics.as_of : null,
      reports,
      summary_zh: `核心报告 ${reports.length} 个，其中 ${blockedCount} 个阻断，${partialCount} 个部分可用。`,
    });
  }

  function buildStage7Phase73QualityTuningViewModel(qualityTuning = {}) {
    const qualityReport = qualityTuning.data_quality_report ? buildReportCard(qualityTuning.data_quality_report) : null;
    const formulas = Array.isArray(qualityTuning.formula_explanations)
      ? qualityTuning.formula_explanations.map(buildFormulaExplanationCard)
      : [];
    const parameterPreview = Array.isArray(qualityTuning.parameter_impact_preview)
      ? qualityTuning.parameter_impact_preview.map(buildParameterPreviewCard)
      : [];
    const exportPolicy = buildExportPolicyCard(qualityTuning.export_save_policy || {});
    const blockedMetricCount = qualityTuning.summary ? Number(qualityTuning.summary.blocked_metric_count || 0) : 0;
    return Object.freeze({
      schema: "PFIV023Stage7QualityTuningPageViewModelV1",
      version: VERSION,
      stage: "Stage 7",
      phase_id: "V023-S7-P7.3",
      page: "reports",
      title: "数据质量与调参",
      subtitle_zh: "展示数据质量报告、公式解释、参数影响预览与导出/保存策略；缺失 read model 不补零。",
      read_model_hash: qualityTuning.source_core_metrics ? qualityTuning.source_core_metrics.read_model_hash : null,
      as_of: qualityTuning.source_core_metrics ? qualityTuning.source_core_metrics.as_of : null,
      blocked_metric_count: blockedMetricCount,
      section_count: 4,
      sections: Object.freeze([
        Object.freeze({ id: "data-quality", title: "数据质量报告", cards: qualityReport ? [qualityReport] : [] }),
        Object.freeze({ id: "formula-explanations", title: "公式解释", cards: formulas }),
        Object.freeze({ id: "parameter-impact", title: "参数影响预览", cards: parameterPreview }),
        Object.freeze({ id: "export-save", title: "导出/保存策略", cards: [exportPolicy] }),
      ]),
      warnings_zh: blockedMetricCount
        ? `仍有 ${blockedMetricCount} 个核心指标被 read model 缺口阻断。`
        : "核心指标输入未发现阻断项。",
    });
  }

  function buildReportCard(report = {}) {
    const formulas = Array.isArray(report.formulas) ? report.formulas : [];
    const parameters = Array.isArray(report.parameters) ? report.parameters : [];
    const missing = Array.isArray(report.missing_data) ? report.missing_data : [];
    return Object.freeze({
      report_id: report.report_id || "",
      title: report.title || "未命名报告",
      status: report.status || "review_required",
      status_zh: STATUS_COPY_ZH[report.status] || "需要复核",
      conclusion_zh: report.conclusion_zh || "需要复核",
      data_range_zh: dataRangeText(report.data_range),
      sample_size_zh: recordScopeText(report.sample_size),
      formula_summary_zh: formulas.length ? `公式 ${formulas.length} 项：${formulas.map((item) => item.formula_zh).join("；")}` : "公式缺失",
      parameter_summary_zh: parameters.length
        ? `参数 ${parameters.length} 项：${parameters.map((item) => `${item.label_zh || item.parameter_id}=${displayValue(item.value)}`).join("；")}`
        : "参数缺失",
      gap_summary_zh: missing.length ? `缺口：${missing.join("；")}` : "缺口：无",
      next_actions: Array.isArray(report.next_actions) ? report.next_actions : [],
      evidence_hash: report.evidence_hash || null,
    });
  }

  function buildV024ReportCenterCard(report = {}) {
    const parameters = Array.isArray(report.parameters) ? report.parameters : [];
    const sampleSize = report.sample_size || {};
    const dataRange = report.data_range || {};
    const gaps = Array.isArray(report.gaps) ? report.gaps : [];
    const reviewEntry = report.review_entry || {};
    return Object.freeze({
      report_id: report.report_id || "",
      report_type: report.report_type || "",
      title_zh: report.title_zh || "未命名报告",
      status: report.status || "review_required",
      status_zh: STATUS_COPY_ZH[report.status] || "需要复核",
      conclusion_zh: report.conclusion_zh || "结论需要复核。",
      formula_zh: report.formula_zh || "公式缺失。",
      parameters: Object.freeze(parameters.map((item) => Object.freeze({ ...item }))),
      parameter_summary_zh: parameterSummaryText(parameters),
      sample_size: Object.freeze({ ...sampleSize }),
      sample_size_zh: v024SampleSizeText(sampleSize),
      data_range: Object.freeze({ ...dataRange }),
      data_range_zh: dataRangeText(dataRange),
      metric_sources: Object.freeze(Array.isArray(report.metric_sources) ? report.metric_sources : []),
      confidence: report.confidence === undefined ? null : report.confidence,
      confidence_zh: confidenceText(report.confidence),
      gaps: Object.freeze(gaps.map((item) => Object.freeze({ ...item }))),
      gap_summary_zh: v024GapSummaryText(gaps),
      anomalies: Object.freeze(Array.isArray(report.anomalies) ? report.anomalies : []),
      review_entry: Object.freeze({
        label_zh: reviewEntry.label_zh || "复核入口",
        route: reviewEntry.route || "/reports?tab=data-quality",
      }),
      review_entry_zh: `复核入口：${reviewEntry.label_zh || "查看数据缺口"} · ${reviewEntry.route || "/reports?tab=data-quality"}`,
      export_fields: Object.freeze(Array.isArray(report.export_fields) ? report.export_fields : []),
      visible_fields_zh: Object.freeze(["结论", "公式", "参数", "样本量", "数据范围", "置信度", "缺口", "复核入口"]),
    });
  }

  function buildFormulaExplanationCard(formula = {}) {
    return Object.freeze({
      section: "公式解释",
      formula_id: formula.formula_id || "",
      metric_id: formula.metric_id || "",
      label: formula.label || formula.metric_id || "",
      input_status: formula.input_status || "review_required",
      formula_zh: formula.formula_zh || "公式缺失",
      missing_inputs_zh: Array.isArray(formula.missing_inputs) && formula.missing_inputs.length
        ? `缺失输入：${formula.missing_inputs.join("、")}`
        : "缺失输入：无",
      parameter_summary_zh: Array.isArray(formula.parameters)
        ? `参数 ${formula.parameters.length} 项：${formula.parameters.map((item) => `${item.label_zh || item.parameter_id}=${displayValue(item.value)}`).join("；")}`
        : "参数缺失",
      status_policy_zh: formula.status_policy_zh || "输入完整前不得显示正式结论。",
      explanation_zh: formula.explanation_zh || "公式解释缺失。",
    });
  }

  function buildParameterPreviewCard(item = {}) {
    return Object.freeze({
      section: "参数影响预览",
      parameter_id: item.parameter_id || "",
      label_zh: item.label_zh || item.parameter_id || "",
      current_value: displayValue(item.current_value),
      current_source: item.current_source || "未加载",
      impact_status: item.impact_status || "review_required",
      impacted_metrics_zh: Array.isArray(item.impacted_metric_ids) ? item.impacted_metric_ids.join("、") : "",
      blocked_missing_inputs_zh: Array.isArray(item.blocked_missing_inputs) && item.blocked_missing_inputs.length
        ? item.blocked_missing_inputs.join("、")
        : "无",
      impact_summary_zh: item.impact_summary_zh || "参数影响说明缺失。",
      preview_value: item.preview_value === null || item.preview_value === undefined ? null : item.preview_value,
    });
  }

  function buildExportPolicyCard(policy = {}) {
    return Object.freeze({
      section: "导出/保存策略",
      title: policy.title || "导出/保存策略",
      saved_artifacts: Array.isArray(policy.saved_artifacts) ? policy.saved_artifacts : [],
      export_ready_formats: Array.isArray(policy.export_ready_formats) ? policy.export_ready_formats : [],
      explicitly_not_implemented: Array.isArray(policy.explicitly_not_implemented) ? policy.explicitly_not_implemented : [],
      save_policy_zh: policy.save_policy_zh || "导出/保存策略缺失。",
    });
  }

  function buildFormulaCard(formula = {}) {
    const parameters = Array.isArray(formula.parameters) ? formula.parameters : [];
    return Object.freeze({
      formula_id: formula.formula_id || "",
      metric_id: formula.metric_id || "",
      label: formula.label || formula.metric_id || "",
      input_status: formula.input_status || "review_required",
      formula_zh: formula.formula_zh || "公式缺失",
      parameter_count: parameters.length,
      parameters: parameters.map((item) => Object.freeze({
        parameter_id: item.parameter_id,
        label_zh: item.label_zh,
        value: item.value,
        source: item.source,
        adjustable: Boolean(item.adjustable),
      })),
      missing_inputs: Array.isArray(formula.missing_inputs) ? formula.missing_inputs : [],
      status_policy_zh: formula.status_policy_zh || "输入完整前不得显示正式结论。",
    });
  }

  function dataRangeText(range = {}) {
    if (!range || (!range.start && !range.end)) return "数据范围：未加载";
    return `数据范围：${range.start || "未知"} 至 ${range.end || "未知"}`;
  }

  function normalizeV024Source(source = {}) {
    return Object.freeze({
      status: source.status || null,
      record_count: Number(source.record_count || 0),
      raw_file_count: Number(source.raw_file_count || 0),
      date_range: Object.freeze(source.date_range || { start: null, end: null }),
      as_of: source.as_of || null,
      evidence_hash: source.evidence_hash || null,
    });
  }

  function recordScopeText(recordScope = {}) {
    const transactionCount = Number(recordScope.transaction_count || 0).toLocaleString("zh-CN");
    const rawFileCount = Number(recordScope.raw_file_count || 0).toLocaleString("zh-CN");
    const accountCount = Number(recordScope.account_count || 0).toLocaleString("zh-CN");
    const holdingCount = Number(recordScope.holding_count || 0).toLocaleString("zh-CN");
    return `样本量：${transactionCount} 条交易，${rawFileCount} 个原始文件，${accountCount} 个账户，${holdingCount} 个持仓`;
  }

  function v024SampleSizeText(recordScope = {}) {
    const transactionCount = Number(recordScope.transaction_count || 0).toLocaleString("zh-CN");
    const rawFileCount = Number(recordScope.raw_file_count || 0).toLocaleString("zh-CN");
    const accountCount = Number(recordScope.account_count || 0).toLocaleString("zh-CN");
    const holdingCount = Number(recordScope.holding_count || 0).toLocaleString("zh-CN");
    return `样本量：${transactionCount} 条交易，${rawFileCount} 个原始文件，${accountCount} 个账户，${holdingCount} 个持仓`;
  }

  function parameterSummaryText(parameters = []) {
    if (!parameters.length) return "参数：缺失";
    return `参数：${parameters.map((item) => `${item.label_zh || item.parameter_id || "参数"}=${displayValue(item.value)}`).join("；")}`;
  }

  function confidenceText(value) {
    if (value === null || value === undefined || value === "") return "置信度：待补真实输入";
    const numeric = Number(value);
    if (Number.isFinite(numeric)) return `置信度：${Math.round(numeric * 100)}%`;
    return `置信度：${value}`;
  }

  function v024GapSummaryText(gaps = []) {
    if (!gaps.length) return "缺口：无";
    return `缺口：${gaps.map((item) => item.reason_zh || item.metric_id || "待复核").join("；")}`;
  }

  function displayValue(value) {
    if (value === null || value === undefined || value === "") return "未加载";
    return String(value);
  }

  return Object.freeze({
    buildStage7Phase71ReportsViewModel,
    buildStage7Phase72CoreReportsViewModel,
    buildStage7Phase73QualityTuningViewModel,
    buildV024Stage7Phase72Contract,
    buildV024Stage7Phase72ReportCenterViewModel,
    validateV024Stage7Phase72ReportCenterViewModel,
  });
});
