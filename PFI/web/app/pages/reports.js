(function attachPFIStage7Reports(root, factory) {
  const api = factory();
  if (typeof module !== "undefined" && module.exports) {
    module.exports = api;
  }
  if (root) {
    root.PFI_V023_STAGE7_REPORTS = api;
  }
})(typeof window !== "undefined" ? window : globalThis, function buildPFIStage7Reports() {
  const VERSION = "v0.2.3";
  const PHASE_ID = "V023-S7-P7.1";
  const STATUS_COPY_ZH = Object.freeze({
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

  function recordScopeText(recordScope = {}) {
    const transactionCount = Number(recordScope.transaction_count || 0).toLocaleString("zh-CN");
    const rawFileCount = Number(recordScope.raw_file_count || 0).toLocaleString("zh-CN");
    const accountCount = Number(recordScope.account_count || 0).toLocaleString("zh-CN");
    const holdingCount = Number(recordScope.holding_count || 0).toLocaleString("zh-CN");
    return `样本量：${transactionCount} 条交易，${rawFileCount} 个原始文件，${accountCount} 个账户，${holdingCount} 个持仓`;
  }

  function displayValue(value) {
    if (value === null || value === undefined || value === "") return "未加载";
    return String(value);
  }

  return Object.freeze({
    buildStage7Phase71ReportsViewModel,
  });
});
